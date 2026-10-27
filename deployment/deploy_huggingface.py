"""Run after deployment/HF-LOGIN.cmd and python deployment/prepare_space.py."""
from pathlib import Path
from huggingface_hub import HfApi

ROOT=Path(__file__).resolve().parents[1]
SPACE=ROOT/".space-build"
USER="Uniworld7"
SPACE_ID=USER+"/TrustCheck"
MODEL_ID=USER+"/TrustCheck-Model"

if not (SPACE/"demo_data.json").exists():
    raise SystemExit("Run python deployment/build_demo.py or python deployment/prepare_space.py first.")
api=HfApi()
account=api.whoami()["name"]
if account.lower()!=USER.lower():
    raise SystemExit("Sign in as "+USER+" before deploying.")

# This static Space does not allocate paid compute or connect to local MySQL.
api.create_repo(repo_id=SPACE_ID,repo_type="space",space_sdk="static",private=False,exist_ok=True)
allowed=["README.md","index.html","space.js","model.json","metrics.json","demo_data.json",
         "train_model.py","ml_model.py","training_data.csv","MODEL_CARD.md","requirements.txt"]
api.upload_folder(repo_id=SPACE_ID,repo_type="space",folder_path=SPACE,
                  allow_patterns=allowed,commit_message="Deploy trained TrustCheck review model")
api.create_repo(repo_id=MODEL_ID,repo_type="model",private=False,exist_ok=True)
for name in ["model.json","metrics.json","ml_model.py","train_model.py","requirements.txt"]:
    api.upload_file(repo_id=MODEL_ID,path_or_fileobj=SPACE/name,path_in_repo=name,
                    commit_message="Publish TrustCheck logistic regression model")
api.upload_file(repo_id=MODEL_ID,path_or_fileobj=ROOT/"docs/MODEL_CARD.md",path_in_repo="README.md",
                commit_message="Document synthetic data, evaluation and limitations")
print("Space: https://huggingface.co/spaces/"+SPACE_ID)
print("Model: https://huggingface.co/"+MODEL_ID)
