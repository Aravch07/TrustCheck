# Hosting TrustCheck

## Choose the version you need

| Version | View reviews and run ML | Add/update/delete reviews | Data |
| --- | --- | --- | --- |
| Local Python app | Yes | Yes | Your laptop's MySQL |
| Existing Hugging Face Space | Yes | No | Published synthetic snapshot |
| Included Vercel configuration | Yes | No | Same published snapshot |
| Future full online Flask app | Requires additional setup | Possible after setup | Hosted database |

Your working online demo is https://huggingface.co/spaces/Uniworld7/TrustCheck.

## Deploy the demo to Vercel

1. Sign in at https://vercel.com/new using GitHub.
2. Import Aravch07/TrustCheck.
3. Keep Root Directory at the repository root.
4. Set Framework Preset to Other, so Vercel does not select the separate local Flask app.
5. The included vercel.json defines these settings:
   - Build Command: python3 deployment/build_demo.py
   - Output Directory: .space-build
   - Install Command: echo No installation required for the static demo
6. No environment variables or database credentials are required for the static demo.
7. Click Deploy and open the resulting Vercel URL.
8. Test both example buttons, business selection, review search and pagination.

The build copies static source and model artifacts into .space-build. It downloads the synthetic snapshot and, when absent locally, the training CSV from a pinned public Hugging Face commit. It validates that the published snapshot uses the same learned model as the repository. Builds need outbound HTTPS access to huggingface.co. A changed model requires refreshing the published snapshot and updating REVISION before a later Vercel build.

The build uses Python's standard library, not scikit-learn or MySQL. The resulting site performs inference in the visitor's browser. No Flask server or database is deployed in this mode.

To check the package locally:

    python deployment/build_demo.py
    python -m http.server 8080 --bind 127.0.0.1 --directory .space-build

Open http://127.0.0.1:8080.

## Keep hosting on Hugging Face

No new hosting is needed: the existing Static Space already runs the public model demonstration.

To update its original synthetic review snapshot from local MySQL:

    python -m pip install -r ml/requirements.txt
    python deployment/prepare_space.py
    python deployment/deploy_huggingface.py

Sign in locally with deployment/HF-LOGIN.cmd first. Do not place tokens or MySQL credentials in GitHub or static files. The deployment package is ignored by Git and uploads use an explicit allowlist.

Hugging Face currently documents Static Spaces as free. Docker/Gradio compute Spaces have separate account eligibility/subscription requirements; do not assume the same deployment plan applies to them.

## If you need the full editable application online

Vercel supports Flask through its Python runtime, but the current local app is not configured as a full hosted service. The included vercel.json publishes only the static demo.

Full online review management requires:

1. A hosted MySQL database reachable from the chosen application host.
2. Importing the schema/data into that database.
3. Loading credentials from the hosting provider's server-side environment settings instead of requiring a local .env file.
4. Appropriate TLS, authentication, authorization and protection of write actions.
5. Deploying the Flask backend with its HTML template and model files.
6. Testing database persistence, errors and review mutations after deployment.

127.0.0.1 in an online function refers to that online environment, not your laptop. Uploading database.sql also does not start a MySQL server. Neither the Vercel snapshot nor the current Hugging Face snapshot automatically synchronizes local edits.

For Hugging Face compute Spaces, network restrictions also need review before choosing an external MySQL service: standard outbound MySQL port 3306 is not among its documented permitted outbound ports.

## References

- Flask on Vercel: https://vercel.com/docs/frameworks/backend/flask
- Vercel Python runtime: https://vercel.com/docs/functions/runtimes/python
- Vercel build image: https://vercel.com/docs/builds/build-image
- Hugging Face hosting options and networking: https://huggingface.co/docs/hub/spaces-overview
