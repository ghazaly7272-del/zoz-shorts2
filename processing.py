import re, subprocess, tempfile
from pathlib import Path

TARGET_W, TARGET_H = 1080, 1920
FPS = 30
CLIP_LEN = 30
MAX_CLIPS = 5
SLIDE = 5

def _run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)

def probe_duration(path):
    out = _run(["ffprobe", "-v", "error", "-show_entries",
        "format=duration", "-of",
        "default=noprint_wrappers=1:nokey=1", str(path)]).stdout.strip()
    try:
        return float(out)
    except ValueError:
        return 0.0

def download_video(url, dest_dir):
    out = str(Path(dest_dir) / "source.mp4")
    subprocess.run([
        "yt-dlp", url,
        "-f", "bv*[height<=720]+ba/b",
        "--merge-output-format", "mp4",
        "-o", out
    ], check=True)
    return out

def loudness_curve(src):
    p = _run(["ffmpeg", "-i", src, "-af",
              "ebur128=metadata=1", "-f", "null", "-"])
    curve = []
    for line in p.stderr.splitlines():
        m = re.search(r"t:\s*([\d.]+).*?M:\s*(-?[\d.]+)", line)
        if m:
            curve.append((float(m.group(1)), float(m.group(2))))
    return curve

def pick_segments(curve, duration):
    clip_len = min(CLIP_LEN, max(3.0, duration))
    if duration <= clip_len:
        return [(0.0, duration, 60)]
    if not curve:
        segs, t = [], 0.0
        while t + clip_len <= duration and len(segs) < MAX_CLIPS:
            segs.append((t, clip_len, 55))
            t += max(clip_len, duration / MAX_CLIPS)
        return segs
    times = [c[0] for c in curve]
    vals = [c[1] for c in curve]
    def window_avg(s, e):
        xs = [vals[i] for i, t in enumerate(times) if s <= t < e]
        return sum(xs) / len(xs) if xs else -120.0
    candidates, t = [], 0.0
    while t + clip_len <= duration:
        candidates.append((t, window_avg(t, t + clip_len)))
        t += SLIDE
    candidates.sort(key=lambda x: x[1], reverse=True)
    chosen = []
    for start, score in candidates:
        if all(abs(start - c[0]) >= clip_len for c in chosen):
            norm = max(1, min(100, int((score + 60) / 50 * 100)))
            chosen.append((start, clip_len, norm))
        if len(chosen) >= MAX_CLIPS:
            break
    chosen.sort(key=lambda x: x[2], reverse=True)
    return chosen

def cut_vertical(src, start, dur, out_mp4):
    vf = (f"scale={TARGET_W}:{TARGET_H}:force_original_aspect_ratio"
          f"=increase,crop={TARGET_W}:{TARGET_H}")
    subprocess.run([
        "ffmpeg", "-ss", str(start), "-t", str(dur),
        "-i", src, "-vf", vf, "-r", str(FPS),
        "-c:v", "libx264", "-preset", "veryfast",
        "-crf", "23", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "128k", "-ar", "44100",
        "-movflags", "+faststart", out_mp4, "-y"
    ], check=True)

def process_video(source_path, work_dir):
    """Main pipeline: analyze + cut clips. Returns list of clip paths + metadata."""
    duration = probe_duration(source_path)
    if duration == 0:
        raise ValueError("Could not read video duration.")
    curve = loudness_curve(source_path)
    segments = pick_segments(curve, duration)
    clips = []
    for i, (start, dur, score) in enumerate(segments):
        clip_path = str(Path(work_dir) / f"clip_{i+1}.mp4")
        cut_vertical(source_path, start, dur, clip_path)
        mm, ss = divmod(int(dur), 60)
        clips.append({
            "path": clip_path,
            "title": f"Clip {i+1}",
            "score": score,
            "duration": f"{mm}:{ss:02d}",
            "start": round(start, 1),
        })
    return clip
