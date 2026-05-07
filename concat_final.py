"""Concat videos — no subtitle burn."""
import subprocess, json
from pathlib import Path

OUT = Path(__file__).parent / "output" / "ds-video-v3"
TOPICS = ["01_linear", "02_linked", "03_stack_queue", "04_tree", "05_graph"]

# Concat
concat_list = OUT / "concat.txt"
with open(concat_list, "w") as f:
    for name in TOPICS:
        f.write(f"file '{(OUT / f'{name}.mp4').as_posix()}'\n")

final = OUT / "data_structures_final.mp4"
r = subprocess.run(
    ["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", str(concat_list), "-c", "copy", str(final)],
    capture_output=True, text=True, encoding="utf-8",
)
if r.returncode == 0:
    print(f"OK: {final} ({final.stat().st_size / 1024 / 1024:.1f} MB)")
else:
    print(f"ERR: {r.stderr[-200:]}")
