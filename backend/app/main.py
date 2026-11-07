import shutil
import uuid
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.schemas import (
    ChatRequest,
    ChatResponse,
    DocumentChatRequest,
    DocumentChatResponse,
    DocumentResponse,
)
from app.services.ai import AIService
from app.services.pdf import OCRUnavailableError, chunk_pages, extract_pdf
from app.services.retrieval import retrieve

settings = get_settings()
ai = AIService(settings)
app = FastAPI(title="Nyaya-Sahayak API", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.frontend_origin,
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

documents: dict[str, dict] = {}
UPLOAD_DIR = Path(__file__).resolve().parents[1] / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)


@app.get("/api/health")
async def health() -> dict:
    return {"status": "ok", "ai_configured": ai.configured}


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    try:
        answer = await ai.complete([message.model_dump() for message in request.messages])
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    return ChatResponse(answer=answer, configured=ai.configured)


@app.post("/api/documents", response_model=DocumentResponse)
async def upload_document(file: UploadFile = File(...)) -> DocumentResponse:
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=415, detail="Please upload a PDF file.")
    document_id = str(uuid.uuid4())
    target = UPLOAD_DIR / f"{document_id}.pdf"
    size = 0
    max_bytes = settings.max_upload_mb * 1024 * 1024
    try:
        with target.open("wb") as output:
            while block := await file.read(1024 * 1024):
                size += len(block)
                if size > max_bytes:
                    raise HTTPException(
                        status_code=413,
                        detail=f"PDFs must be smaller than {settings.max_upload_mb} MB.",
                    )
                output.write(block)
        pages = extract_pdf(target)
        chunks = chunk_pages(pages)
    except HTTPException:
        target.unlink(missing_ok=True)
        raise
    except OCRUnavailableError as exc:
        target.unlink(missing_ok=True)
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        target.unlink(missing_ok=True)
        raise HTTPException(status_code=422, detail="This PDF could not be read.") from exc

    documents[document_id] = {
        "filename": file.filename or "document.pdf",
        "pages": pages,
        "chunks": chunks,
    }
    return DocumentResponse(
        document_id=document_id,
        filename=file.filename or "document.pdf",
        pages=len(pages),
        extracted_characters=sum(len(page.text) for page in pages),
        has_text=any(page.text for page in pages),
    )


@app.post("/api/documents/{document_id}/chat", response_model=DocumentChatResponse)
async def document_chat(document_id: str, request: DocumentChatRequest) -> DocumentChatResponse:
    document = documents.get(document_id)
    if not document:
        raise HTTPException(status_code=404, detail="This document is no longer available. Please upload it again.")
    relevant = retrieve(document["chunks"], request.question)
    if not relevant and document["chunks"]:
        relevant = document["chunks"][:5]
    references = sorted({chunk["page"] for chunk in relevant})
    if not relevant:
        context = "No matching text was found in the extracted document."
    else:
        context = "\n\n".join(f"[Page {chunk['page']}]\n{chunk['text']}" for chunk in relevant)
    messages = [
        *[message.model_dump() for message in request.history[-10:]],
        {
            "role": "user",
            "content": (
                "Answer every part of the question using only the document context below. Start with a "
                "direct answer, then explain it clearly using short Markdown headings and bullet points "
                "or numbered steps where useful. If the answer is not present in the document, say that "
                "explicitly instead of guessing. Cite page numbers in the answer where possible.\n\n"
                f"DOCUMENT CONTEXT:\n{context}\n\nQUESTION:\n{request.question}"
            ),
        },
    ]
    try:
        answer = await ai.complete(messages)
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    if not any(page.text for page in document["pages"]):
        answer = (
            "I could not extract selectable text from this PDF. It may be scanned or image-based. "
            "Please upload a text-based PDF or run OCR first."
        )
    return DocumentChatResponse(answer=answer, references=references, configured=ai.configured)
