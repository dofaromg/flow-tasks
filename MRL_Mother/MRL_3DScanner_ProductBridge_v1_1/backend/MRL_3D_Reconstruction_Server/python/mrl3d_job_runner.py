#!/usr/bin/env python3
import argparse, importlib.util, json, os, shutil, subprocess, sys, time
from pathlib import Path

IMAGE_EXTS = {'.jpg','.jpeg','.png','.heic'}
VIDEO_EXTS = {'.mp4','.mov','.m4v','.avi'}
MESH_EXTS = {'.obj','.ply'}

def write_json(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')

def which(cmd):
    return shutil.which(cmd)

def mrl3d_command():
    exe = which('mrl3d')
    if exe:
        return [exe]
    if importlib.util.find_spec('mrl3d') is not None:
        return [sys.executable, '-m', 'mrl3d.cli']
    return None

def run(cmd, cwd=None):
    p = subprocess.run(cmd, cwd=cwd, text=True, capture_output=True)
    return p.returncode, p.stdout, p.stderr

def find_files(scan_dir):
    files=[]
    for p in Path(scan_dir).rglob('*'):
        if p.is_file() and p.name != 'manifest.json':
            files.append(p)
    return files

def q(value):
    return json.dumps(str(value).replace('\\','/'), ensure_ascii=False)

def make_report(out, status, mode, reason, details):
    report = {
        "status": status,
        "mode": mode,
        "reason": reason,
        "details": details,
        "time": time.strftime('%Y-%m-%dT%H:%M:%S%z')
    }
    write_json(Path(out)/'MRL_JOB_REPORT.json', report)
    Path(out,'RUN_REPORT.md').write_text(
        f"# MRL Job Report\n\nstatus: {status}\nmode: {mode}\nreason: {reason}\n\n```json\n{json.dumps(details, ensure_ascii=False, indent=2)}\n```\n",
        encoding='utf-8'
    )

def common_blocks(objective='error'):
    return f"""attention:
  backend: simple
suggestion:
  objective: {objective}
  tiles: [4, 4]
  topk: 5
context:
  neg_corr_threshold: -0.05
"""

def write_mesh_config(path, mesh_path, out_dir, typ):
    objective = 'coverage'
    path.write_text(f"""out_dir: {q(out_dir)}
input:
  type: {typ}
  mesh_path: {q(mesh_path)}
  synth:
    num_cameras: 8
    radius_scale: 2.2
    resolution: [640, 480]
    fov_deg: 60
{common_blocks(objective)}""", encoding='utf-8')

def write_video_config(path, video_path, frame_dir, out_dir):
    path.write_text(f"""out_dir: {q(out_dir)}
images_dir: {q(frame_dir)}
input:
  type: video
  video_path: {q(video_path)}
  sample_fps: 2
  frame_dir: {q(frame_dir)}
{common_blocks('error')}""", encoding='utf-8')

def write_colmap_config(path, colmap_dir, image_dir, out_dir):
    path.write_text(f"""out_dir: {q(out_dir)}
images_dir: {q(image_dir)}
input:
  type: colmap
  colmap_dir: {q(colmap_dir)}
  images_dir: {q(image_dir)}
  read_images: true
{common_blocks('error')}""", encoding='utf-8')

def parse_mrl_stdout(stdout):
    try:
        return json.loads(stdout)
    except Exception:
        return None

def run_mrl3d(mrl_cmd, cfg, out, mode, expected_adapter, ok_reason, fail_reason, details):
    code, so, se = run(mrl_cmd + ['run', '--config', str(cfg)])
    parsed = parse_mrl_stdout(so)
    adapter = (parsed or {}).get('meta', {}).get('adapter')
    details.update({
        "cmd": ' '.join(mrl_cmd + ['run', '--config', str(cfg)]),
        "stdout": so[-4000:],
        "stderr": se[-4000:],
        "mrl3d_meta_adapter": adapter,
        "mrl3d_output_dir": (parsed or {}).get('output_dir')
    })
    if code != 0:
        make_report(out, 'failed', mode, fail_reason, details)
        return code
    if expected_adapter and adapter != expected_adapter:
        make_report(out, 'failed', mode, f'MRL3D_ADAPTER_MISMATCH expected={expected_adapter} got={adapter}', details)
        return 10
    make_report(out, 'completed', mode, ok_reason, details)
    return 0

def copy_images(images, imgdir):
    if imgdir.exists():
        shutil.rmtree(imgdir)
    imgdir.mkdir(parents=True, exist_ok=True)
    used = set()
    for idx, src in enumerate(images, 1):
        name = src.name
        if name in used:
            name = f"{idx:04d}_{name}"
        used.add(name)
        shutil.copy2(src, imgdir / name)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--scan-dir', required=True)
    ap.add_argument('--output-dir', required=True)
    ap.add_argument('--mode', default='auto')
    args=ap.parse_args()
    scan=Path(args.scan_dir); out=Path(args.output_dir); out.mkdir(parents=True, exist_ok=True)
    files=find_files(scan)
    images=[p for p in files if p.suffix.lower() in IMAGE_EXTS]
    videos=[p for p in files if p.suffix.lower() in VIDEO_EXTS]
    meshes=[p for p in files if p.suffix.lower() in MESH_EXTS]
    details={"scan_dir":str(scan),"images":len(images),"videos":len(videos),"meshes":len(meshes)}

    mrl_cmd = mrl3d_command()
    if not mrl_cmd:
        make_report(out,'failed',args.mode,'MRL3D_PACKAGE_NOT_FOUND: install included mrl3d package first',details)
        return 2

    # Mesh mode can run without COLMAP/OpenMVS.
    if meshes:
        mesh = meshes[0]
        mode = 'mesh_ply' if mesh.suffix.lower()=='.ply' else 'mesh_obj'
        cfg = out/'mesh_job.yaml'
        mrl_out = out/'mrl3d_output'
        write_mesh_config(cfg, mesh, mrl_out, mode)
        return run_mrl3d(mrl_cmd, cfg, out, mode, 'mesh', 'mrl3d mesh runner', 'MRL3D_MESH_RUN_FAILED', details)

    if videos:
        video=videos[0]
        cfg=out/'video_job.yaml'
        frame_dir=out/'video_frames'
        mrl_out=out/'mrl3d_output'
        write_video_config(cfg, video, frame_dir, mrl_out)
        return run_mrl3d(mrl_cmd, cfg, out, 'video', 'video', 'mrl3d video runner', 'MRL3D_VIDEO_RUN_FAILED', details)

    if images:
        colmap = which('colmap')
        if not colmap:
            make_report(out,'failed','images','COLMAP_NOT_FOUND: image reconstruction requires COLMAP on DL580',details)
            return 3
        database = out/'colmap.db'
        sparse = out/'sparse'
        text = out/'colmap_text'
        imgdir = out/'images'
        copy_images(images, imgdir)
        sparse.mkdir(exist_ok=True); text.mkdir(exist_ok=True)
        cmds = [
            [colmap,'feature_extractor','--database_path',str(database),'--image_path',str(imgdir)],
            [colmap,'exhaustive_matcher','--database_path',str(database)],
            [colmap,'mapper','--database_path',str(database),'--image_path',str(imgdir),'--output_path',str(sparse)],
        ]
        logs=[]
        for cmd in cmds:
            code,so,se=run(cmd)
            logs.append({"cmd":cmd,"code":code,"stdout":so[-2000:],"stderr":se[-2000:]})
            if code!=0:
                details['colmap_logs']=logs
                make_report(out,'failed','images','COLMAP_PIPELINE_FAILED',details)
                return code
        model0=sparse/'0'
        if not model0.exists():
            details['colmap_logs']=logs
            make_report(out,'failed','images','COLMAP_NO_MODEL_OUTPUT',details)
            return 4
        code,so,se=run([colmap,'model_converter','--input_path',str(model0),'--output_path',str(text),'--output_type','TXT'])
        logs.append({"cmd":"model_converter","code":code,"stdout":so[-2000:],"stderr":se[-2000:]})
        if code!=0:
            details['colmap_logs']=logs
            make_report(out,'failed','images','COLMAP_MODEL_CONVERTER_FAILED',details)
            return code
        cfg=out/'colmap_text_job.yaml'
        mrl_out=out/'mrl3d_output'
        write_colmap_config(cfg, text, imgdir, mrl_out)
        details['colmap_logs']=logs
        return run_mrl3d(mrl_cmd, cfg, out, 'colmap_text', 'colmap', 'COLMAP + mrl3d completed', 'MRL3D_COLMAP_TEXT_RUN_FAILED', details)

    make_report(out,'failed',args.mode,'NO_SUPPORTED_INPUT_FILES',details)
    return 5

if __name__ == '__main__':
    sys.exit(main())
