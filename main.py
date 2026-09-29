"""
SkillMatch — AI resume maker + scanner, real-time jobs, company matching,
skill-gap roadmaps and skill tests.

Run:  python -m uvicorn main:app --reload
Open: http://localhost:8000  (the web UI)
Docs: http://localhost:8000/docs (interactive API docs)
"""

import json
import time
from io import BytesIO
from pathlib import Path

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles

import resume_maker, scanner, matcher, test_bank, job_sources

app = FastAPI(
    title="SkillMatch API",
    description="AI-powered resume maker & scanner + real-time job matching + skill tests",
    version="1.0.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_PROJECT_ROOT = Path(__file__).resolve().parent
_STATIC = _PROJECT_ROOT / "static"
# Keep the app runnable with the flat workspace layout as well as the documented
# static/ layout.
if not _STATIC.is_dir():
    _STATIC = _PROJECT_ROOT


# ---------------------------------------------------------------- health
@app.get("/api/health")
def health():
    return {"ok": True, "time": time.time()}


# ---------------------------------------------------------------- jobs (real time)
@app.get("/api/jobs")
def jobs(query: str = "", limit: int = 100, live: bool = True):
    """Live job feed. Tries Remotive -> Adzuna -> cache -> seed, never fails."""
    return job_sources.get_jobs(query=query or None, limit=max(1, min(limit, 500)), live_first=live)


@app.get("/api/companies")
def companies():
    """All companies known to the matcher, with required skills."""
    return {"companies": job_sources.get_companies()}


# ---------------------------------------------------------------- resume maker
@app.post("/api/resume/generate")
def generate_resume(payload: dict):
    """payload: {name, email, phone, target_role, skills[], experience[],
    education[], projects[], extra_text} -> structured resume + tips."""
    try:
        resume = resume_maker.generate_resume(payload)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return {"resume": resume, "download": {"plain_text": resume_maker.resume_to_text(resume)}}


@app.post("/api/resume/generate/txt")
def generate_resume_txt(payload: dict):
    try:
        resume = resume_maker.generate_resume(payload)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return PlainTextResponse(resume_maker.resume_to_text(resume), media_type="text/plain")


# ---------------------------------------------------------------- resume scanner
@app.post("/api/resume/scan")
def scan_resume(payload: dict):
    """payload: {text: 'full resume text'} -> skills, seniority, ATS score."""
    try:
        return scanner.scan_resume(payload.get("text", ""))
    except ValueError as e:
        raise HTTPException(400, str(e))


@app.post("/api/resume/scan/file")
async def scan_resume_file(file: UploadFile = File(...)):
    """Upload a PDF resume, extract its text, and return the scanner analysis."""
    raw = await file.read()
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(400, "please upload a PDF resume")
    if not raw:
        raise HTTPException(400, "uploaded PDF is empty")
    try:
        from pypdf import PdfReader

        text = "\n".join(page.extract_text() or "" for page in PdfReader(BytesIO(raw)).pages)
    except Exception as e:  # noqa: BLE001
        raise HTTPException(400, f"could not read PDF: {e}")
    if not text.strip():
        raise HTTPException(400, "No selectable text found in this PDF. Scanned/image-only PDFs require OCR before scanning.")
    try:
        return scanner.scan_resume(text, filename=file.filename)
    except ValueError as e:
        raise HTTPException(400, str(e))


# ---------------------------------------------------------------- matching
@app.post("/api/match/companies")
def match_companies(payload: dict):
    """payload: {skills: [...], limit: 500} -> ranked company profiles split by fit."""
    skills = payload.get("skills") or []
    if not skills:
        raise HTTPException(400, "provide at least one skill (use the scanner or the test results)")
    limit = payload.get("limit") or 500
    return matcher.match_companies(skills, limit=max(1, min(int(limit), 500)))


@app.post("/api/match/gap")
def gap_analysis(payload: dict):
    """payload: {skills: [...], company: 'Razorpay'} -> missing skills + learning roadmap."""
    skills = payload.get("skills") or []
    company = (payload.get("company") or "").strip()
    if not company:
        raise HTTPException(400, "choose a target company")
    try:
        return matcher.gap_analysis(skills, company)
    except ValueError as e:
        raise HTTPException(404, str(e))


# ---------------------------------------------------------------- skill tests
@app.get("/api/tests")
def list_tests():
    return {"tests": test_bank.available_tests()}


@app.get("/api/tests/{skill}")
def get_test(skill: str):
    try:
        return test_bank.get_test(skill)
    except ValueError as e:
        raise HTTPException(404, str(e))


@app.post("/api/tests/{skill}/submit")
def submit_test(skill: str, payload: dict):
    """payload: {answers: [0, 2, null, ...]} -> % score, band, per-question feedback."""
    answers = payload.get("answers")
    if not isinstance(answers, list):
        raise HTTPException(400, "answers must be a list (use null for skipped)")
    try:
        return test_bank.grade_test(skill, answers)
    except ValueError as e:
        raise HTTPException(404 if "no test" in str(e) else 400, str(e))


# ---------------------------------------------------------------- UI
@app.get("/", response_class=HTMLResponse)
def index():
    html = (_STATIC / "index.html").read_text(encoding="utf-8")
    return HTMLResponse(html)


# serve every static asset (style.css, script.js, …) under /
# mounted last so the /api/ routes above always take precedence
app.mount("/", StaticFiles(directory=str(_STATIC)), name="site")
