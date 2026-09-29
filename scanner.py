"""
Resume scanner.

Parses raw resume text (paste or file upload) and returns:
  - detected skills (via the taxonomy)
  - experience/seniority estimate
  - education
  - contact info (email/phone)
  - an ATS-readiness score with specific, actionable findings
"""

import re
from skills import extract_skills, categorize

_EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")
_PHONE_RE = re.compile(r"(?:\+91[-\s]?)?[6-9]\d{9}|\d{3}[-.\s]\d{3}[-.\s]\d{4}")

_SENIORITY = [
    (r"\b(intern|trainee|internship)\b", "Intern / Trainee", 0),
    (r"\b(junior|jr\.?|entry[- ]level|fresher|associate)\b", "Junior (0-2 yrs)", 1),
    (r"\b(senior|sr\.?|lead|staff)\b", "Senior (5+ yrs)", 3),
    (r"\b(principal|architect|director|head of)\b", "Principal / Architect", 4),
]

_DEGREES = [
    r"\bB\.?\s?Tech\b", r"\bB\.?E\.?\b", r"\bBachelor(?:'s)?\b", r"\bB\.?\s?Sc\b",
    r"\bM\.?\s?Tech\b", r"\bM\.?\s?Sc\b", r"\bMaster(?:'s)?\b", r"\bMBA\b", r"\bPh\.?D\b",
]


def scan_resume(text: str, filename: str = "") -> dict:
    if not text or not text.strip():
        raise ValueError("resume text is empty")

    skills = extract_skills(text)
    skill_names = [s["skill"] for s in skills]
    emails = _EMAIL_RE.findall(text)[:3]
    phones = re.findall(_PHONE_RE, text)[:2]

    # seniority: pick the highest level mentioned
    level = "Mid-level (2-5 yrs)"
    level_rank = 2
    for pattern, label, rank in _SENIORITY:
        if re.search(pattern, text, re.I) and rank >= level_rank:
            level, level_rank = label, rank

    education = []
    for deg in _DEGREES:
        if re.search(deg, text, re.I):
            m = re.search(deg, text, re.I)
            education.append(m.group(0).strip())

    score, findings = _ats_findings(text, skill_names, emails, phones)

    return {
        "filename": filename,
        "contact": {"emails": emails, "phones": phones},
        "detected_skills": skills,
        "skill_count": len(skill_names),
        "skills_by_category": categorize(skill_names),
        "seniority": level,
        "education": list(dict.fromkeys(education))[:4],
        "ats_score": score,
        "findings": findings,
    }


def _ats_findings(text: str, skills: list[str], emails: list[str], phones: list[str]):
    findings = []
    score = 100
    t = text.lower()

    if not emails:
        score -= 15; findings.append({"severity": "error", "issue": "No email found — recruiters cannot contact you."})
    if not phones:
        score -= 10; findings.append({"severity": "warn", "issue": "No phone number found."})
    if len(text) < 400:
        score -= 15; findings.append({"severity": "warn", "issue": "Resume looks very short (< ~400 chars). Add experience/projects with outcomes."})
    if len(text) > 6000:
        score -= 5; findings.append({"severity": "info", "issue": "Very long resume — 1 page (2 max) is ideal in India."})

    has_numbers = bool(re.search(r"\d+\s?(%|users|ms|k\b|x\b|hours|lakh|crore|₹)", t))
    if not has_numbers:
        score -= 15
        findings.append({"severity": "warn", "issue": "No measurable outcomes found — add numbers (%, users, latency, revenue)."})
    if re.search(r"responsible for|worked on|helped with|duties included", t):
        score -= 10
        findings.append({"severity": "warn", "issue": "Passive phrasing ('responsible for…') — start bullets with strong action verbs."})
    if not re.search(r"\b(github|linkedin|portfolio)\b", t):
        score -= 5; findings.append({"severity": "info", "issue": "Add GitHub / LinkedIn links — 87% of recruiters check them."})

    if len(skills) < 4:
        score -= 15
        findings.append({"severity": "error", "issue": f"Only {len(skills)} skills detected. ATS keyword filters will likely drop this resume."})
    elif len(skills) >= 8:
        findings.append({"severity": "ok", "issue": f"Good skill coverage: {len(skills)} skills detected."})

    if not re.search(r"\b(education|b\.?tech|bachelor|degree|university|college)\b", t):
        score -= 10; findings.append({"severity": "warn", "issue": "No education section detected."})

    return max(score, 0), findings
