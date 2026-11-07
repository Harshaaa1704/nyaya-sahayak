# Nyaya-Sahayak

Nyaya-Sahayak is a focused legal information assistant for Indian-law questions and temporary PDF document Q&A. It is intentionally limited to two workflows: general chat and document-grounded chat.

## What is included

- React + Vite + Tailwind CSS frontend with responsive chat UX.
- FastAPI backend with modular AI, PDF extraction, and retrieval services.
- PyMuPDF extraction with page-aware chunks and lightweight keyword retrieval.
- OCR fallback for scanned or image-based PDFs when Tesseract is installed.
- OpenAI-compatible provider integration; Groq is the default free-tier example.
- In-memory document cache: uploaded PDFs are session-scoped and are not a permanent database.
- Clear handling for missing API keys, oversized files, unreadable PDFs, and scanned PDFs.

## Local setup

### 1. Configure the backend

```powershell
cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item ..\.env.example .env
```

Set `AI_API_KEY` in `backend/.env`. A Groq API key and its current free-tier model can be used at [console.groq.com](https://console.groq.com/). Free tiers have rate and usage limits; this app does not claim unlimited or permanently free AI usage.

Scanned PDF support uses Tesseract OCR. The included Docker image installs Tesseract automatically. For local Windows development, install [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) and make sure `tesseract.exe` is available on `PATH`.

### 2. Start the API

```powershell
uvicorn app.main:app --reload --port 8000
```

### 3. Start the frontend

In another terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open the Vite URL shown in the terminal (normally `http://localhost:5173`).

If the frontend is deployed separately, set `VITE_API_URL` to the public backend URL including `/api`.

## Tests and production build

```powershell
cd backend
pytest
cd ..\frontend
npm run build
```

## Deployment

The recommended first deployment is Render for the backend and Cloudflare Pages for the frontend.

### Backend on Render

1. Push this repository to GitHub.
2. In Render, choose **New → Blueprint** and select the repository. Render will read [`render.yaml`](./render.yaml).
3. Set `AI_API_KEY` to your provider key.
4. After the service is created, copy its public URL, for example `https://nyaya-sahayak-api.onrender.com`.
5. Set `FRONTEND_ORIGIN` to the final Cloudflare Pages URL. You can update it after the frontend is created.

The Render service includes Tesseract OCR through the project Dockerfile. Its local filesystem and in-memory document cache are temporary; uploaded documents and anonymous conversations are lost on restart or scale-to-zero.

### Frontend on Cloudflare Pages

1. Create a Pages project from the same GitHub repository.
2. Set **Root directory** to `frontend`.
3. Set **Build command** to `npm run build`.
4. Set **Build output directory** to `dist`.
5. Add `VITE_API_URL` with the backend URL followed by `/api`, for example `https://nyaya-sahayak-api.onrender.com/api`.
6. Deploy, then put the Pages URL into Render's `FRONTEND_ORIGIN`.

Do not commit `.env` files or real API keys. Enter secrets only in the hosting provider's environment-variable settings.

The backend filesystem is treated as temporary. The current version keeps documents in memory and a temporary upload directory, so documents disappear on restart or scale-to-zero. This avoids pretending that a free persistent database is required for the initial two features. Add object storage and a document store only when multi-user persistence is needed.

## Important limitation

This is general legal information, not legal advice. It should not replace advice from a qualified lawyer or verification against official Indian legal sources. The AI provider can still make mistakes, so important legal decisions require professional review.
