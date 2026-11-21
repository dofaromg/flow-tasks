"""Read-only ANE resource diagnostic absorption; observations stay separate."""
import hashlib
import json
import re


def absorb(raw):
    text = raw.decode("utf-8-sig", errors="strict")
    first = text.splitlines()[0] if text.strip() else ""
    try:
        header = json.loads(first)
    except ValueError:
        header = {}
    if not isinstance(header, dict):
        header = {}

    def field(name):
        match = re.search(rf"^{re.escape(name)}:\s*(.+)$", text, re.M)
        return match.group(1).strip() if match else None

    writes = re.search(r"([\d.]+) MB of file backed memory dirtied over (\d+) seconds "
                       r"\(([\d.]+) KB per second average\), exceeding limit of "
                       r"([\d.]+) KB per second over (\d+) seconds", text)
    service = text.split("Powerstats for:   ANECompilerService", 1)
    target = service[1].split("\nPowerstats for:", 1)[0] if len(service) == 2 else ""
    pageins = re.search(r"^Pageins:\s*(\d+) pages", target, re.M)
    page_size = field("VM page size")
    derived = {}
    measurements = {}
    if writes:
        total, seconds, rate, baseline, window = writes.groups()
        measurements = dict(dirtied_mb=float(total), duration_s=int(seconds),
                            event_kb_s=float(rate), reference_kb_s=float(baseline),
                            reference_window_s=int(window))
        if float(baseline) > 0:
            derived["event_to_reference_rate_ratio"] = round(float(rate) / float(baseline), 6)
    if pageins and page_size and page_size.isdecimal():
        derived["pagein_page_size_product_bytes"] = int(pageins[1]) * int(page_size)
    return {"schema": "MRL_ANE_Observation/v1", "source_sha256": hashlib.sha256(raw).hexdigest(),
            "observed": {"incident_id": header.get("incident_id") or field("Incident Identifier"),
                         "bug_type": header.get("bug_type"), "event": field("Event"),
                         "action": field("Action taken"), "source": field("Data Source"),
                         "model_field": field("Models"), "writes_raw": field("Writes"),
                         "service_attribution": field("On Behalf Of"),
                         "modules_seen_in_service_section": [name for name in
                             ("ANECompiler", "Espresso", "libBNNS", "libcopyfile")
                             if re.search(r"\(" + name + r" \+", target)],
                         **measurements},
            "derived": derived,
            "hypotheses": [],
            "limits": ["No identification of model, cache hit, file path or root cause.",
                       "Module presence does not establish a single call chain.",
                       "Pageins and dirty pages cannot establish write amplification.",
                       "Unparsed fields remain in the original input. This output omits the raw report."]}
