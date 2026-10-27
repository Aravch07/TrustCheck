@echo off
echo Sign in locally with a Hugging Face write token for Uniworld7.
echo Create a token at https://huggingface.co/settings/tokens
echo Keep your token out of chat and GitHub.
python -c "from huggingface_hub import login; login(add_to_git_credential=False)"
pause
