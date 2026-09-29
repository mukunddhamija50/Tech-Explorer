"""
AI-powered resume maker.

Takes a structured profile and produces a polished, ATS-friendly resume.
Two output formats: structured JSON (for the UI) and plain-text (download).

Design notes
------------
This is a template + rule engine (action-verb rewriting, quantification
prompts, keyword alignment to the target role). It is deliberately
self-contained with no external LLM call so it works offline and costs
nothing. If you later want LLM-quality phrasing, plug a provider into
_polish() — the rest of the pipeline stays the same.
"""

from skills import extract_skill_names, categorize, SKILL_TAXONOMY

_ROLE_KEYWORDS = {
    "backend": ["REST APIs", "SQL", "Docker", "Microservices", "System Design", "Testing", "Git"],
    "frontend": ["HTML", "CSS", "JavaScript", "React", "Testing", "Git"],
    "full stack": ["HTML", "CSS", "JavaScript", "React", "Node.js", "REST APIs", "SQL", "Git"],
    "data": ["Python", "SQL", "Pandas", "Data Analysis", "Data Visualization", "Statistics"],
    "machine learning": ["Python", "Machine Learning", "Deep Learning", "Statistics", "Pandas"],
    "devops": ["Linux", "Docker", "Kubernetes", "CI/CD", "AWS", "Git"],
    "mobile": ["Flutter", "Android", "Kotlin", "iOS", "REST APIs"],
}

_STRONG_VERBS = [
    "Built", "Developed", "Engineered", "Designed", "Implemented",
    "Optimised", "Automated", "Delivered", "Led", "Shipped",
]

_GERUND_MAP = {
    "building": "Built", "developing": "Developed", "creating": "Created",
    "designing": "Designed", "managing": "Managed", "writing": "Wrote",
    "automating": "Automated", "optimising": "Optimised", "optimizing": "Optimized",
    "working": "Worked", "implementing": "Implemented", "leading": "Led",
    "maintaining": "Maintained", "testing": "Tested", "deploying": "Deployed",
    "integrating": "Integrated", "migrating": "Migrated", "improving": "Improved",
}


def _target_keywords(target_role: str) -> list[str]:
    role = (target_role or "").lower()
    for key, kws in _ROLE_KEYWORDS.items():
        if key in role:
            return kws
    return []


def _rewrite_bullet(bullet: str) -> str:
    """Ensure a bullet starts with a strong action verb instead of
    'responsible for' / 'worked on' / 'helped with'."""
    b = bullet.strip()
    low = b.lower()
    for weak in ("responsible for", "worked on", "helped with", "was involved in", "tasked with"):
        if low.startswith(weak):
            b = b[len(weak):].strip()
            break
    # convert a leading gerund ("building APIs") to a strong past verb ("Built APIs")
    for g, verb in _GERUND_MAP.items():
        if b.lower().startswith(g + " "):
            b = verb + b[len(g):]
            break
    else:
        if b and b[0].islower() and not any(b.lower().startswith(v.lower()) for v in _STRONG_VERBS):
            b = b[0].upper() + b[1:]
        if not any(b.lower().startswith(v.lower()) for v in _STRONG_VERBS):
            b = f"Developed {b[0].lower() + b[1:]}" if b else b
    return b


_CANONICAL = {c.lower(): c for c in SKILL_TAXONOMY}


def _canonicalize(skill: str) -> str:
    """python -> Python, k8s -> Kubernetes, mysql -> SQL ..."""
    return _CANONICAL.get(skill.strip().lower(), skill.strip())


def generate_resume(profile: dict) -> dict:
    """profile keys: name, email, phone, target_role, skills (list, optional),
    experience (list of {role, company, duration, highlights: [str]}),
    education (list of {degree, institute, year}), projects (list of {name, description}),
    extra_text (raw text to mine for skills if skills empty)."""

    name = profile.get("name", "").strip()
    if not name:
        raise ValueError("name is required")

    # mine skills from raw text if none supplied
    skills = [_canonicalize(s) for s in profile.get("skills") or [] if s.strip()]
    extra = profile.get("extra_text") or ""
    mined = extract_skill_names(" ".join([
        extra,
        " ".join(p.get("description", "") for p in profile.get("projects", [])),
        " ".join(h for e in profile.get("experience", []) for h in e.get("highlights", [])),
    ]))
    all_skills = list(dict.fromkeys(skills + mined))

    # align to target role: relevant-known first, then suggested adds
    target = (profile.get("target_role") or "").strip()
    kws = _target_keywords(target)
    relevant = [s for s in all_skills if s in kws]
    others = [s for s in all_skills if s not in kws]
    ordered = relevant + others
    missing = [k for k in kws if k not in all_skills]

    resume = {
        "header": {
            "name": name,
            "email": profile.get("email", ""),
            "phone": profile.get("phone", ""),
            "target_role": target,
        },
        "professional_summary": _summary(name, target, ordered),
        "skills": {
            "categorized": categorize(ordered),
            "flat": ordered,
        },
        "experience": [
            {
                **e,
                "highlights": [_rewrite_bullet(h) for h in e.get("highlights", []) if h.strip()],
            }
            for e in profile.get("experience", [])
        ],
        "projects": profile.get("projects", []),
        "education": profile.get("education", []),
        "suggestions": _suggestions(target, ordered, missing, profile),
    }
    return resume


def _summary(name: str, target: str, skills: list[str]) -> str:
    if not skills:
        return f"{name} is an aspiring {target or 'software professional'} seeking to apply strong fundamentals in a growth-oriented team."
    top = ", ".join(skills[:6])
    role = target or "software professional"
    return (
        f"{role} skilled in {top}. Hands-on experience building, testing and shipping "
        "software end to end, with a focus on clean code and measurable outcomes. "
        "Looking to contribute to a product-driven engineering team."
    )


def _suggestions(target: str, skills: list[str], missing: list[str], profile: dict) -> list[str]:
    tips = []
    if missing:
        tips.append(
            "For a '" + (target or "software") + "' role, your resume will be stronger if you add evidence of: "
            + ", ".join(missing[:5]) + ". (Only add what you have used — then take our skill test to verify it.)"
        )
    if not profile.get("experience"):
        tips.append("No work experience listed — add at least 2 projects with what YOU built, the stack, and a number (users, % faster, hours saved).")
    for e in profile.get("experience", []):
        for h in e.get("highlights", []):
            if not any(ch.isdigit() for ch in h):
                tips.append(f"Quantify this bullet: '{h[:60]}...' — recruiters respond to numbers.")
    if len(skills) < 5:
        tips.append("Very few skills detected. Take the skill tests on this app and add verified skills to your resume.")
    return tips[:6]


def resume_to_text(resume: dict) -> str:
    h = resume["header"]
    lines = [
        h["name"].upper(),
        " | ".join(x for x in [h.get("email"), h.get("phone")] if x),
        "",
    ]
    if h.get("target_role"):
        lines += [f"TARGET ROLE: {h['target_role']}", ""]
    lines += ["PROFESSIONAL SUMMARY", resume["professional_summary"], ""]
    lines += ["SKILLS"]
    for cat, sk in resume["skills"]["categorized"].items():
        lines.append(f"  {cat}: {', '.join(sk)}")
    lines.append("")
    if resume["experience"]:
        lines += ["EXPERIENCE"]
        for e in resume["experience"]:
            lines.append(f"  {e.get('role','')} — {e.get('company','')} ({e.get('duration','')})")
            for hl in e.get("highlights", []):
                lines.append(f"    • {hl}")
        lines.append("")
    if resume["projects"]:
        lines += ["PROJECTS"]
        for p in resume["projects"]:
            lines.append(f"  {p.get('name','')}: {p.get('description','')}")
        lines.append("")
    if resume["education"]:
        lines += ["EDUCATION"]
        for ed in resume["education"]:
            lines.append(f"  {ed.get('degree','')}, {ed.get('institute','')} ({ed.get('year','')})")
        lines.append("")
    return "\n".join(lines)
