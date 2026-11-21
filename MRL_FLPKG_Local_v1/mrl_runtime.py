"""Local job store, content cache and rolling write admission for FLPKG."""
import hashlib
import json
import os
import platform
from pathlib import Path
import sqlite3
import sys
import time
import uuid
from contextlib import contextmanager

from mrl_package import BLOCK, create_package, inventory, json_bytes, publish, verify_package
from mrl_diagnostics import absorb

HERE = Path(__file__).resolve().parent
CORE = HERE / "particle_core" / "src"
if not CORE.is_dir():
    CORE = HERE.parent / "particle_core" / "src"
sys.path.insert(0, str(CORE))
from logic_pipeline import LogicPipeline

KINDS = {"generate", "package", "diagnostic"}
MODES = {"alert", "queue", "throttle", "deny"}
WINDOW = 86400
MAX_TEXT = 2 * BLOCK


class Cancelled(Exception):
    pass


class Admission(Exception):
    def __init__(self, status, message):
        super().__init__(message)
        self.status = status


class Metered:
    """Unseekable byte stream; count submitted bytes before physical writes."""

    def __init__(self, stream, charge, check, throttle):
        self.stream = stream
        self.charge = charge
        self.check = check
        self.throttle = throttle
        self.total = 0
        self.started = time.monotonic()

    def tell(self):
        return self.total

    def write(self, data):
        if not data:
            return 0
        self.check()
        if self.throttle:
            due = self.started + (self.total + len(data)) / self.throttle
            while time.monotonic() < due:
                self.check()
                time.sleep(min(0.1, max(0, due - time.monotonic())))
        self.charge(len(data))
        count = self.stream.write(data)
        if count != len(data):
            raise OSError("Short write")
        self.total += count
        return count

    def flush(self):
        self.stream.flush()


class Runtime:
    def __init__(self, directory):
        self.root = Path(directory).resolve()
        for name in ("cache", "artifacts", "stage"):
            (self.root / name).mkdir(parents=True, exist_ok=True)
        with self.db() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS jobs(
                  id TEXT PRIMARY KEY, parent TEXT REFERENCES jobs(id), kind TEXT NOT NULL,
                  request TEXT NOT NULL, status TEXT NOT NULL, created REAL NOT NULL,
                  updated REAL NOT NULL, result TEXT, error TEXT,
                  cancel INTEGER NOT NULL DEFAULT 0, reservation INTEGER NOT NULL DEFAULT 0);
                CREATE TABLE IF NOT EXISTS writes(
                  time REAL NOT NULL, job TEXT NOT NULL, bytes INTEGER NOT NULL);
                CREATE INDEX IF NOT EXISTS writes_time ON writes(time);
                CREATE TABLE IF NOT EXISTS events(
                  seq INTEGER PRIMARY KEY, time REAL NOT NULL, job TEXT, event TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS config(
                  id INTEGER PRIMARY KEY CHECK(id=1), max_bytes INTEGER NOT NULL,
                  mode TEXT NOT NULL, rate INTEGER NOT NULL);
                INSERT OR IGNORE INTO config VALUES(1, 10737418240, 'alert', 1048576);
            """)

    @contextmanager
    def db(self, immediate=False):
        db = sqlite3.connect(self.root / "jobs.sqlite3", timeout=15)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        db.execute("PRAGMA synchronous=FULL")
        try:
            with db:
                if immediate:
                    db.execute("BEGIN IMMEDIATE")
                yield db
        finally:
            db.close()

    def config(self, limit, mode, rate):
        if type(limit) is not int or not 0 < limit < 2**62 or mode not in MODES or type(rate) is not int or not 0 < rate < 2**62:
            raise ValueError("Invalid quota settings")
        with self.db(True) as db:
            db.execute("UPDATE config SET max_bytes=?,mode=?,rate=? WHERE id=1", (limit, mode, rate))
            db.execute("UPDATE jobs SET status='queued',updated=? WHERE status='waiting'", (time.time(),))
            self.event(db, None, "QUOTA_UPDATED")

    def event(self, db, job, event):
        db.execute("INSERT INTO events(time,job,event) VALUES(?,?,?)", (time.time(), job, event))

    def submit(self, kind, value, *, source_job=None, parent=None, target="portable", options=None):
        if kind not in KINDS or not isinstance(value, str) or not isinstance(target, str):
            raise ValueError("Invalid job")
        if not isinstance(options, (dict, type(None))) or len(json_bytes(options)) > 8192:
            raise ValueError("Options must be a JSON object under 8 KiB")
        if kind == "package" and options and (
                set(options) != {"label"} or not isinstance(options["label"], str)
                or len(options["label"].encode()) > 1024):
            raise ValueError("Package options support only a label up to 1024 UTF-8 bytes")
        if kind != "generate" and not value and not source_job:
            raise ValueError("A local source path is required")
        if kind == "generate" and (not value or len(value.encode()) > MAX_TEXT):
            raise ValueError("Input text must be between 1 byte and 2 MiB")
        if source_job and kind != "package":
            raise ValueError("source_job is only available for packaging")
        if kind != "generate" and not source_job:
            value = str(Path(value).expanduser().resolve())
        with self.db(True) as db:
            if source_job:
                source = db.execute("SELECT kind,status FROM jobs WHERE id=?", (source_job,)).fetchone()
                if not source or (source["kind"], source["status"]) != ("generate", "done"):
                    raise ValueError("source_job must refer to completed generation")
                parent = parent or source_job
            if parent and not db.execute("SELECT 1 FROM jobs WHERE id=?", (parent,)).fetchone():
                raise ValueError("Unknown parent job")
            job = uuid.uuid4().hex
            request = json_bytes(dict(value=value, source_job=source_job, target=target,
                                      options=options or {})).decode()
            now = time.time()
            db.execute("INSERT INTO jobs(id,parent,kind,request,status,created,updated) VALUES(?,?,?,?,?,?,?)",
                       (job, parent, kind, request, "queued", now, now))
            self.event(db, job, "SUBMITTED")
        return job

    def retry(self, job):
        with self.db() as db:
            row = db.execute("SELECT * FROM jobs WHERE id=?", (job,)).fetchone()
        if not row or row["status"] not in {"failed", "cancelled", "interrupted", "denied"}:
            raise ValueError("Only a terminal unsuccessful job can be retried")
        return self.submit(row["kind"], parent=job, **json.loads(row["request"]))

    def cancel(self, job):
        with self.db(True) as db:
            row = db.execute("SELECT status FROM jobs WHERE id=?", (job,)).fetchone()
            if not row or row["status"] not in {"queued", "waiting", "running"}:
                raise ValueError("Job cannot be cancelled")
            status = "running" if row["status"] == "running" else "cancelled"
            db.execute("UPDATE jobs SET cancel=1,status=?,updated=? WHERE id=?", (status, time.time(), job))
            self.event(db, job, "CANCEL_REQUESTED")

    def status(self, job=None):
        with self.db() as db:
            fields = "id,parent,kind,status,created,updated,result,error,reservation"
            if job:
                row = db.execute(f"SELECT {fields} FROM jobs WHERE id=?", (job,)).fetchone()
                if row is None:
                    raise ValueError("Unknown job")
                result = dict(row)
                if result["result"]:
                    result["result"] = json.loads(result["result"])
                result["events"] = [dict(e) for e in db.execute(
                    "SELECT time,event FROM events WHERE job=? ORDER BY seq", (job,))]
                return result
            quota = dict(db.execute("SELECT max_bytes,mode,rate FROM config WHERE id=1").fetchone())
            quota["used_bytes"] = self.used(db)
            quota["reserved_bytes"] = db.execute("SELECT COALESCE(sum(reservation),0) FROM jobs").fetchone()[0]
            return {"quota": quota, "jobs": [dict(row) for row in db.execute(
                f"SELECT {fields} FROM jobs ORDER BY created DESC LIMIT 100")]}

    @staticmethod
    def used(db):
        return db.execute("SELECT COALESCE(sum(bytes),0) FROM writes WHERE time>?",
                          (time.time() - WINDOW,)).fetchone()[0]

    def reserve(self, job, amount):
        with self.db(True) as db:
            cfg = db.execute("SELECT * FROM config").fetchone()
            if self.used(db) + amount > cfg["max_bytes"]:
                mode = cfg["mode"]
                if mode == "deny" or (mode == "queue" and amount > cfg["max_bytes"]):
                    raise Admission("denied", "Write budget cannot admit this job")
                if mode == "queue":
                    raise Admission("waiting", "Waiting for rolling write budget")
                self.event(db, job, "WRITE_BUDGET_EXCEEDED")
            db.execute("UPDATE jobs SET reservation=? WHERE id=?", (amount, job))
            self.event(db, job, "WRITE_RESERVED")
            return cfg["rate"] if cfg["mode"] == "throttle" and self.used(db) + amount > cfg["max_bytes"] else 0

    def charge(self, job, amount):
        with self.db(True) as db:
            row = db.execute("SELECT cancel,reservation FROM jobs WHERE id=?", (job,)).fetchone()
            if row["cancel"]:
                raise Cancelled("Cancelled by operator")
            if amount > row["reservation"]:
                raise ValueError("Output exceeded reserved bound")
            db.execute("INSERT INTO writes VALUES(?,?,?)", (time.time(), job, amount))
            db.execute("UPDATE jobs SET reservation=reservation-? WHERE id=?", (amount, job))

    def check(self, job):
        with self.db() as db:
            if db.execute("SELECT cancel FROM jobs WHERE id=?", (job,)).fetchone()[0]:
                raise Cancelled("Cancelled by operator")

    def recover(self):
        # Called only under the exclusive worker lease. Check published bytes
        # before marking interrupted; a retry never overwrites old artifacts.
        with self.db(True) as db:
            for row in db.execute("SELECT id,result,cancel FROM jobs WHERE status='running'").fetchall():
                job, result, cancelled = row
                status = "cancelled" if cancelled else "interrupted"
                if result:
                    receipt = json.loads(result)
                    final = self.root / "artifacts" / receipt["file"]
                    if final.is_file() and digest_file(final) == receipt["sha256"]:
                        status = "done"
                db.execute("UPDATE jobs SET status=?,reservation=0,updated=?,error=? WHERE id=?",
                           (status, time.time(), None if status == "done" else "Previous worker interrupted", job))
                self.event(db, job, "RECOVERED_" + status.upper())
            for path in (self.root / "stage").glob("*.tmp"):
                path.unlink()

    def step(self):
        lease = sqlite3.connect(self.root / "worker.sqlite3", timeout=0)
        try:
            try:
                lease.execute("BEGIN EXCLUSIVE")
            except sqlite3.OperationalError as exc:
                if "locked" in str(exc):
                    return None
                raise
            self.recover()
            with self.db(True) as db:
                row = db.execute("""SELECT * FROM jobs WHERE cancel=0 AND
                    (status='queued' OR (status='waiting' AND updated<=?))
                    ORDER BY CASE status WHEN 'queued' THEN 0 ELSE 1 END,created LIMIT 1""",
                                 (time.time() - 30,)).fetchone()
                if row is None:
                    return None
                job = row["id"]
                db.execute("UPDATE jobs SET status='running',updated=? WHERE id=?", (time.time(), job))
                self.event(db, job, "STARTED")
            try:
                self.execute(row)
            except Exception as exc:
                with self.db(True) as db:
                    cancelled = db.execute("SELECT cancel FROM jobs WHERE id=?", (job,)).fetchone()[0]
                    status = ("cancelled" if cancelled or isinstance(exc, Cancelled) else
                              exc.status if isinstance(exc, Admission) else "failed")
                    db.execute("UPDATE jobs SET status=?,error=?,reservation=0,updated=? WHERE id=?",
                               (status, str(exc), time.time(), job))
                    self.event(db, job, status.upper())
            return self.status(job)
        finally:
            lease.close()

    def execute(self, row):
        job, kind, parent = row["id"], row["kind"], row["parent"]
        request = json.loads(row["request"])
        staged = self.root / "stage" / (job + ".tmp")
        cache_stage = staged.with_name(job + ".cache.tmp")
        cache = None
        cache_hit = None
        cache_key = None
        extra = {}
        try:
            if kind == "generate":
                implementation = {name: digest_file(CORE / name)
                                  for name in ("logic_pipeline.py", "pipeline_constants.py")}
                key_context = {"schema": "MRL_Generation/v1", "input_sha256": hashlib.sha256(
                    request["value"].encode()).hexdigest(), "implementation": implementation,
                    "target": request["target"], "runtime": sys.version, "host": platform.machine(),
                               "options": request["options"]}
                cache_key = hashlib.sha256(json_bytes(key_context)).hexdigest()
                cache = self.root / "cache" / cache_key
                if cache.exists():
                    # Verify content against a digest in the durable publishing event.
                    with self.db() as db:
                        entry = db.execute("SELECT event FROM events WHERE event LIKE ? ORDER BY seq DESC LIMIT 1",
                                           (f"CACHE:{cache_key}:%",)).fetchone()
                    if entry and digest_file(cache) == entry["event"].split(":")[-1]:
                        cache_hit = True
                    else:
                        quarantine = self.root / "cache" / f"{cache_key}.invalid.{job}"
                        cache.rename(quarantine)
                        with self.db(True) as db:
                            self.event(db, job, "CACHE_QUARANTINED")
                if cache_hit:
                    content = cache.read_bytes()
                    if hashlib.sha256(content).hexdigest() != entry["event"].split(":")[-1]:
                        raise ValueError("Cache changed during readback")
                    self.write_data(job, staged, content)
                else:
                    # LogicPipeline.simulate is the original particle logic operation.
                    payload = {"context": key_context, "cache_key": cache_key,
                               "generation": LogicPipeline(enable_cache=False).simulate(request["value"])}
                    self.write_data(job, staged, json_bytes(payload), cache_stage)
                    cache_hit = False
                ext = ".generation.json"
            elif kind == "package":
                source = request["source_job"]
                if source:
                    receipt = self.status(source)["result"]
                    path = self.root / "artifacts" / receipt["file"]
                    if digest_file(path) != receipt["sha256"]:
                        raise ValueError("Generation artifact failed readback")
                    files = {"generation.json": path}
                else:
                    files = inventory(Path(request["value"]), self.root)
                # Stored ZIP uses deterministic bounded overhead. Reserve enough
                # for headers, UTF-8 JSON escaping, index, ZIP64 and trailers.
                amount = 12288 + sum(p.stat().st_size + 1024 + 16 * len(n.encode())
                                    for n, p in files.items())
                rate = self.reserve(job, amount)
                with staged.open("xb") as handle:
                    create_package(Metered(handle, lambda n: self.charge(job, n),
                                           lambda: self.check(job), rate),
                                   files, parent, lambda: self.check(job), request["options"].get("label"))
                    handle.flush()
                    os.fsync(handle.fileno())
                manifest = verify_package(staged, check=lambda: self.check(job))
                if source and manifest["files"][0]["sha256"] != receipt["sha256"]:
                    raise ValueError("Generation artifact changed during packaging")
                extra = {"payload_count": len(manifest["files"]), "source_job": source}
                ext = ".flpkg.zip"
            else:
                with Path(request["value"]).open("rb") as source:
                    raw = source.read(16 * BLOCK + 1)
                if len(raw) > 16 * BLOCK:
                    raise ValueError("Diagnostic limit is 16 MiB")
                self.write_data(job, staged, json_bytes(absorb(raw)))
                ext = ".observation.json"
            checksum = digest_file(staged)
            receipt = dict(file=job + ext, size=staged.stat().st_size, sha256=checksum,
                           cache_hit=cache_hit, cache_key=cache_key, **extra)
            with self.db(True) as db:
                db.execute("UPDATE jobs SET result=? WHERE id=?", (json_bytes(receipt).decode(), job))
            with self.db(True) as db:
                if db.execute("SELECT cancel FROM jobs WHERE id=?", (job,)).fetchone()[0]:
                    raise Cancelled("Cancelled before publishing")
                if cache is not None and cache_hit is False:
                    publish(cache_stage, cache)
                    self.event(db, job, f"CACHE:{cache_key}:{checksum}")
                publish(staged, self.root / "artifacts" / receipt["file"])
                db.execute("UPDATE jobs SET status='done',error=NULL,reservation=0,updated=? WHERE id=?",
                           (time.time(), job))
                self.event(db, job, "PUBLISHED")
        finally:
            staged.unlink(missing_ok=True)
            cache_stage.unlink(missing_ok=True)

    def write_data(self, job, staged, data, cache_stage=None):
        paths = (staged, cache_stage) if cache_stage else (staged,)
        rate = self.reserve(job, len(data) * len(paths))
        for path in paths:
            with path.open("xb") as handle:
                writer = Metered(handle, lambda n: self.charge(job, n), lambda: self.check(job), rate)
                for offset in range(0, len(data), BLOCK):
                    writer.write(data[offset:offset + BLOCK])
                writer.flush()
                os.fsync(handle.fileno())


def digest_file(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while block := handle.read(BLOCK):
            digest.update(block)
    return digest.hexdigest()
