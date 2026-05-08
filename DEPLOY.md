# Verit — Free Deployment Guide (zero-cost, no errors)

This guide deploys Verit to **4 free platforms**. Total cost: **$0/month forever**.

| Service | Where it goes | Why |
|---|---|---|
| Frontend (React) | **Vercel** | Free static hosting |
| Orchestrator (FastAPI) | **Render** | Free Python hosting |
| Image AI | **HuggingFace Spaces** | 16 GB RAM free CPU |
| Video AI | **HuggingFace Spaces** | 16 GB RAM free CPU |

**Time estimate:** ~45 minutes if you follow exactly.

---

## Before you start — accounts to create

All free, no credit card:

1. **GitHub** → https://github.com/signup
2. **HuggingFace** → https://huggingface.co/join
3. **Render** → https://render.com (sign up with GitHub)
4. **Vercel** → https://vercel.com (sign up with GitHub)
5. **Git LFS** → install from https://git-lfs.com (Windows installer)

After installing Git LFS, run once in PowerShell:
```powershell
git lfs install
```
Expected output: `Git LFS initialized.`

---

# PART 1 — Push your project to GitHub

### 1.1 Open PowerShell in your project folder

```powershell
cd e:\deepmedia\ai-detection-app
```

### 1.2 Initialize git and commit

```powershell
git init
git add .
git commit -m "initial commit"
```

> ⚠️ If `git commit` complains about identity, run these two lines once:
> ```powershell
> git config --global user.email "you@example.com"
> git config --global user.name "Your Name"
> ```

### 1.3 Create a new GitHub repo

1. Go to https://github.com/new
2. Repository name: **`verit-app`**
3. Visibility: **Public** (required for free Render)
4. **Do NOT** add README, .gitignore, or license
5. Click **Create repository**

### 1.4 Push

Copy the URL GitHub shows you (looks like `https://github.com/YOUR_NAME/verit-app.git`), then:

```powershell
git remote add origin https://github.com/YOUR_NAME/verit-app.git
git branch -M main
git push -u origin main
```

✅ **Verify:** refresh the GitHub repo page — you should see all your folders.

---

# PART 2 — Deploy the Image AI to HuggingFace Spaces

### 2.1 Create the Space

1. Go to https://huggingface.co/new-space
2. Owner: your username
3. Space name: **`verit-image`**
4. License: `mit`
5. SDK: **Docker** → Blank
6. Hardware: **CPU basic** (free)
7. Visibility: **Public**
8. Click **Create Space**

You'll land on the new Space page. The URL pattern is:
```
https://huggingface.co/spaces/YOUR_HF_NAME/verit-image
```

### 2.2 Get an HF access token (needed to push)

1. Go to https://huggingface.co/settings/tokens
2. Click **New token**
3. Name: `verit-deploy`, Role: **write**
4. Click **Generate**
5. Copy the token — save it somewhere safe

### 2.3 Clone the empty Space and copy files

```powershell
cd e:\deepmedia
git clone https://huggingface.co/spaces/YOUR_HF_NAME/verit-image
cd verit-image
```

> When it asks for username: type your HF username
> When it asks for password: paste the token from step 2.2

Copy the prepared files into the Space:

```powershell
Copy-Item -Force e:\deepmedia\ai-detection-app\hf-image-space\* .
```

You should now have these files in `verit-image/`:
- `app.py`
- `requirements.txt`
- `Dockerfile`
- `README.md`

### 2.4 Push

```powershell
git add .
git commit -m "deploy image service"
git push
```

### 2.5 Wait for build

Open `https://huggingface.co/spaces/YOUR_HF_NAME/verit-image` in browser → click the **Logs** tab.

- Build takes **5–8 minutes** (PyTorch + transformers install)
- After build, models download (~600 MB) on first start (~2 min)
- When you see `INFO: Uvicorn running on http://0.0.0.0:7860` → it's ready

### 2.6 Test it

```powershell
curl https://YOUR_HF_NAME-verit-image.hf.space/health
```

Expected: `{"status":"healthy"}`

📋 **Save this URL** — you'll need it later: `https://YOUR_HF_NAME-verit-image.hf.space`

---

# PART 2B — Deploy the second image model (UniversalFakeDetect)

This adds a second image-detection Space that the orchestrator ensembles alongside NPR. **Skip this part if you only want the single NPR model.**

### 2B.1 Create the Space

Same as 2.1 but name it **`verit-image-uf`**.

### 2B.2 Clone the empty Space

```powershell
cd e:\deepmedia
git clone https://huggingface.co/spaces/YOUR_HF_NAME/verit-image-uf
cd verit-image-uf
```

### 2B.3 Copy the prepared files

```powershell
Copy-Item e:\deepmedia\ai-detection-app\hf-image-space-uf\Dockerfile .
Copy-Item e:\deepmedia\ai-detection-app\hf-image-space-uf\requirements.txt .
Copy-Item e:\deepmedia\ai-detection-app\hf-image-space-uf\detector.py .
Copy-Item e:\deepmedia\ai-detection-app\hf-image-space-uf\model.yaml .
Copy-Item e:\deepmedia\ai-detection-app\hf-image-space-uf\README.md .
Copy-Item -Recurse e:\deepmedia\DeepSafe\sdk .\sdk
```

Strip cruft so the push is clean:

```powershell
Get-ChildItem -Recurse -Force -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force
Get-ChildItem -Recurse -Force -Directory -Filter "*.egg-info" | Remove-Item -Recurse -Force
Get-ChildItem -Recurse -Force -Directory -Filter "tests" | Where-Object { $_.FullName -like "*\sdk\*" } | Remove-Item -Recurse -Force
```

### 2B.4 Push

```powershell
git add -A
git commit -m "deploy universalfakedetect image space"
git push
```

### 2B.5 Wait for build

Open `https://huggingface.co/spaces/YOUR_HF_NAME/verit-image-uf` → **Logs** tab.

- Build takes **8–12 min** (torch CPU + CLIP ViT-L/14 weights ~890 MB).
- When you see `Uvicorn running on http://0.0.0.0:7860` → ready.

### 2B.6 Test

```powershell
curl https://YOUR_HF_NAME-verit-image-uf.hf.space/health
```

Expected: `{"status":"healthy","model_name":"universalfakedetect","model_loaded":true}`

📋 **Save this URL**: `https://YOUR_HF_NAME-verit-image-uf.hf.space`

> ⚠️ **The orchestrator must know about this Space.** After Part 4, add an env var to Render:
> | Key | Value |
> |---|---|
> | `DEEPSAFE_URL_UF` | `https://YOUR_HF_NAME-verit-image-uf.hf.space` |
>
> When this var is set, the orchestrator calls both image Spaces in parallel and averages their probabilities. When unset (or removed), it falls back to NPR-only — no code change needed.

---

# PART 3 — Deploy the Video AI to HuggingFace Spaces

The video service needs the model weights (`efficientnet.onnx`, `model.pth`) and the inference code from `AI-Generated-Video-Detector/`. We use Git LFS for the large weight files.

### 3.1 Create the Space

Same as 2.1 but name it **`verit-video`**.

### 3.2 Clone and copy files

```powershell
cd e:\deepmedia
git clone https://huggingface.co/spaces/YOUR_HF_NAME/verit-video
cd verit-video
```

Enable Git LFS for this repo (it's already initialized globally):

```powershell
Copy-Item e:\deepmedia\ai-detection-app\hf-video-space\.gitattributes .
git add .gitattributes
```

Copy the FastAPI wrapper, Dockerfile, README, requirements:

```powershell
Copy-Item e:\deepmedia\ai-detection-app\hf-video-space\app.py .
Copy-Item e:\deepmedia\ai-detection-app\hf-video-space\Dockerfile .
Copy-Item e:\deepmedia\ai-detection-app\hf-video-space\requirements.txt .
Copy-Item e:\deepmedia\ai-detection-app\hf-video-space\README.md .
```

Copy the inference code from AI-Generated-Video-Detector:

```powershell
Copy-Item e:\deepmedia\AI-Generated-Video-Detector\inference_2.py .
Copy-Item -Recurse e:\deepmedia\AI-Generated-Video-Detector\models .
Copy-Item -Recurse e:\deepmedia\AI-Generated-Video-Detector\utils .
Copy-Item -Recurse e:\deepmedia\AI-Generated-Video-Detector\data .
```

Copy the model weights (these will use Git LFS automatically):

```powershell
New-Item -ItemType Directory -Name checkpoints -Force
Copy-Item e:\deepmedia\AI-Generated-Video-Detector\checkpoints\efficientnet.onnx .\checkpoints\
Copy-Item e:\deepmedia\AI-Generated-Video-Detector\checkpoints\model.pth .\checkpoints\
```

> ⚠️ **Remove any cached `.git/` folders inside the copied subfolders** to avoid push conflicts:
> ```powershell
> Get-ChildItem -Recurse -Force -Directory -Filter ".git" | Where-Object { $_.FullName -ne (Resolve-Path .git).Path } | Remove-Item -Recurse -Force
> ```
>
> Also remove any `__pycache__/` folders that came along:
> ```powershell
> Get-ChildItem -Recurse -Force -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force
> ```

### 3.3 Push (this uploads ~140 MB via Git LFS)

```powershell
git add .
git commit -m "deploy video service with checkpoints"
git push
```

> ⚠️ The push will take **5–10 minutes** because of the 117 MB `model.pth` file.
> If you get authentication errors, use your HF token (same as 2.2) as password.

### 3.4 Wait for build

Open the Space's **Logs** tab. Build takes **8–12 minutes**.

When you see `Uvicorn running on http://0.0.0.0:7860` → ready.

### 3.5 Test

```powershell
curl https://YOUR_HF_NAME-verit-video.hf.space/health
```

Expected: `{"status":"healthy"}`

📋 **Save this URL**: `https://YOUR_HF_NAME-verit-video.hf.space`

---

# PART 4 — Deploy the Orchestrator to Render

### 4.1 Create the web service

1. Go to https://dashboard.render.com
2. Click **New +** → **Web Service**
3. Click **Build and deploy from a Git repository** → **Next**
4. Connect GitHub if not already → select **`verit-app`** → **Connect**

### 4.2 Configure exactly these settings

| Field | Value |
|---|---|
| **Name** | `verit-orchestrator` |
| **Region** | choose closest to you |
| **Branch** | `main` |
| **Root Directory** | `backend` |
| **Runtime** | `Python 3` |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `uvicorn main:app --host 0.0.0.0 --port $PORT` |
| **Instance Type** | **Free** |

### 4.3 Add environment variables

Scroll down to **Environment Variables** → click **Add Environment Variable** for each row below. The last one (`DEEPSAFE_URL_UF`) is **only needed if you completed Part 2B**:

| Key | Value |
|---|---|
| `DEEPSAFE_URL` | `https://YOUR_HF_NAME-verit-image.hf.space` |
| `VIDEO_URL` | `https://YOUR_HF_NAME-verit-video.hf.space` |
| `DEEPSAFE_MODE` | `single_model` |
| `REQUEST_TIMEOUT` | `600` |
| `DEEPSAFE_URL_UF` *(optional)* | `https://YOUR_HF_NAME-verit-image-uf.hf.space` |

> When `DEEPSAFE_URL_UF` is set, the orchestrator runs an ensemble (NPR + UniversalFakeDetect, averaged). It also runs a metadata pre-check on every image — if known AI-generation tags (Stable Diffusion, Midjourney, Adobe Firefly, C2PA AI claims, etc.) are found in EXIF/XMP/C2PA, it short-circuits with `service: "metadata"`. Removing the var disables the ensemble; the metadata check stays.

### 4.4 Deploy

Click **Create Web Service** at the bottom.

Build takes **3–5 minutes**. Watch the **Logs** tab — when you see `Uvicorn running on...` → ready.

### 4.5 Test

Render gives you a URL like `https://verit-orchestrator.onrender.com`. Test:

```powershell
curl https://verit-orchestrator.onrender.com/health
```

Expected:
```json
{"services":{"orchestrator":"healthy","deepsafe":"healthy","video":"healthy"}}
```

> ⚠️ **If `deepsafe` or `video` shows "unreachable":**
> - The HF Spaces may be sleeping. Visit each Space URL once in your browser to wake them up, then retry.

📋 **Save this URL**: `https://verit-orchestrator.onrender.com`

---

# PART 5 — Deploy the Frontend to Vercel

### 5.1 Import the project

1. Go to https://vercel.com/new
2. Find `verit-app` in the list → click **Import**

### 5.2 Configure these settings

| Field | Value |
|---|---|
| **Framework Preset** | `Vite` (auto-detected) |
| **Root Directory** | `frontend` |
| **Build Command** | `npm run build` (default) |
| **Output Directory** | `dist` (default) |

### 5.3 Add environment variable

Expand **Environment Variables**:

| Key | Value |
|---|---|
| `VITE_API_BASE` | `https://verit-orchestrator.onrender.com` |

### 5.4 Deploy

Click **Deploy**. Takes **2 minutes**.

When done, Vercel shows your live URL: `https://verit-app.vercel.app` (or similar).

### 5.5 Test the full flow

Open `https://verit-app.vercel.app` → upload an image → click **Run detection** → should get a verdict in ~15 seconds.

> ⚠️ **First request after long idle is slow** because Render and HF Spaces sleep. Allow up to 90 seconds for the first request, then it's fast.

---

# Troubleshooting

### Image Space build fails — "out of memory" during pip install
Edit the Space's `Dockerfile` (online editor) and split the install into smaller chunks. Or upgrade temporarily to a paid Space, then downgrade after first build.

### Video Space push fails — "this exceeds GitHub's file size limit"
You forgot Git LFS. Run:
```powershell
git lfs install
cd verit-video
git rm --cached checkpoints/efficientnet.onnx checkpoints/model.pth
git lfs track "*.onnx" "*.pth"
git add .gitattributes checkpoints/
git commit -m "use lfs"
git push
```

### Render build fails — "could not find a version that satisfies the requirement"
Check that `backend/runtime.txt` says `python-3.11.9`. Render defaults can pick a Python version where pinned packages aren't available.

### Frontend deploys but uploads fail with "Network Error"
The `VITE_API_BASE` env var was set after deploy. Vercel needs a **redeploy** for env vars to apply:
- Vercel dashboard → your project → **Deployments** tab → click `...` on latest → **Redeploy**

### Orchestrator health says `unreachable (TimeoutException)` for video
Render free has a 100-second request budget. Long videos may exceed it. For demo videos (<20 sec), this is fine.

### CORS error in browser
The orchestrator already allows `*`. If you see CORS errors, you're calling the wrong URL — check `VITE_API_BASE` matches the Render URL exactly (no trailing slash).

---

# Keeping services warm (optional, free)

Render and HF Spaces sleep after ~15 min idle. To keep them awake:

1. Sign up at https://uptimerobot.com (free)
2. Add 3 monitors (HTTP, every 5 minutes):
   - `https://verit-orchestrator.onrender.com/health`
   - `https://YOUR_HF_NAME-verit-image.hf.space/health`
   - `https://YOUR_HF_NAME-verit-video.hf.space/health`

This keeps your demo responsive 24/7.

---

# Summary URLs

After deployment you'll have:

```
Live app:           https://verit-app.vercel.app
Backend API:        https://verit-orchestrator.onrender.com
Image AI:           https://YOUR_HF_NAME-verit-image.hf.space
Video AI:           https://YOUR_HF_NAME-verit-video.hf.space
GitHub repo:        https://github.com/YOUR_NAME/verit-app
```

All hosted, all free, all yours.
