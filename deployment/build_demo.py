"""Build the read-only static demo for Vercel or Hugging Face. No MySQL needed."""
import json
import shutil
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / ".space-build"
# Pin the published synthetic snapshot for reproducible builds.
REVISION = "e178415124b932ea2172f58073bbd8639997b1fd"
BASE = "https://huggingface.co/spaces/Uniworld7/TrustCheck/resolve/" + REVISION + "/"


def download(name, destination):
    request = urllib.request.Request(BASE + name, headers={"User-Agent": "TrustCheck-build"})
    with urllib.request.urlopen(request, timeout=60) as response:
        destination.write_bytes(response.read())


def build(fetch_snapshot=True):
    OUTPUT.mkdir(exist_ok=True)
    for name in ["index.html", "space.js", "README.md"]:
        shutil.copyfile(ROOT / "deployment/space" / name, OUTPUT / name)
    files = {"model.json": ROOT / "model.json",
             "metrics.json": ROOT / "ml/metrics.json",
             "ml_model.py": ROOT / "ml_model.py",
             "train_model.py": ROOT / "ml/train_model.py",
             "MODEL_CARD.md": ROOT / "docs/MODEL_CARD.md"}
    for name, source in files.items():
        shutil.copyfile(source, OUTPUT / name)
    data = ROOT / "ml/training_data.csv"
    if data.exists():
        shutil.copyfile(data, OUTPUT / "training_data.csv")
    else:
        download("training_data.csv", OUTPUT / "training_data.csv")
    (OUTPUT / "requirements.txt").write_text("scikit-learn==1.9.0\nnumpy>=2.0,<3\n")
    if fetch_snapshot:
        download("demo_data.json", OUTPUT / "demo_data.json")
        snapshot = json.loads((OUTPUT / "demo_data.json").read_text(encoding="utf-8"))
        if not all(1 <= row["id"] <= 516 for row in snapshot["reviews"]):
            raise ValueError("Unexpected snapshot records.")
        # Stored snapshot predictions must match the deployed learned model.
        with urllib.request.urlopen(BASE + "model.json", timeout=60) as response:
            published_model = json.load(response)
        if published_model != json.loads((ROOT / "model.json").read_text()):
            raise ValueError("Model changed: refresh/publish the snapshot and update REVISION first.")
    print("Static demo prepared in .space-build; no database credentials included.")


if __name__ == "__main__":
    build()
