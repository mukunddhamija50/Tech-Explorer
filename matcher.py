"""
Company matching + skill-gap engine.

match_companies(user_skills)
  -> ranks every company by fit %, splits into "ready now" vs "gap" list,
     and for each gap company lists exactly which skills are missing.

gap_analysis(user_skills, target_company)
  -> full gap report for one company + a concrete learning roadmap with
     weekly order, free learning resources, and retest advice.
"""

from job_sources import get_companies, get_jobs

# how much a required skill counts when the user has it
_WEIGHTS = {
    # core engineering skills weigh more than soft skills
    "System Design": 1.5, "Microservices": 1.4, "Data Structures": 1.4,
    "REST APIs": 1.3, "AWS": 1.3, "Kubernetes": 1.3, "Docker": 1.3,
    "Machine Learning": 1.4, "Go": 1.3,
    "Communication": 0.6, "Agile": 0.6, "Problem Solving": 0.7,
}
_DEFAULT_W = 1.0

READY_THRESHOLD = 60  # >= this fit% = "apply now"


def _weight(skill: str) -> float:
    return _WEIGHTS.get(skill, _DEFAULT_W)


def _fit(user_skills: set, required: list[str]) -> tuple[float, list, list]:
    total = sum(_weight(s) for s in required) or 1.0
    have, missing = [], []
    got = 0.0
    for s in required:
        if s in user_skills:
            got += _weight(s)
            have.append(s)
        else:
            missing.append(s)
    return round(100 * got / total, 1), have, missing


def match_companies(user_skills: list[str], limit: int = 500) -> dict:
    user = set(user_skills)
    companies = []
    for c in get_companies():
        fit, have, missing = _fit(user, c["required_skills"])
        companies.append({
            "company": c["name"],
            "about": c["about"],
            "fit_percent": fit,
            "matched_skills": have,
            "missing_skills": missing,
            "verdict": "ready" if fit >= READY_THRESHOLD else
                       ("close" if fit >= 40 else "stretch"),
        })
    companies.sort(key=lambda x: -x["fit_percent"])
    limited = companies[:max(1, min(limit, 500))]
    return {
        "ready_now": [c for c in limited if c["verdict"] == "ready"],
        "close": [c for c in limited if c["verdict"] == "close"],
        "stretch": [c for c in limited if c["verdict"] == "stretch"],
        "all": limited,
        "total_companies": len(companies),
    }


# ------------------------------------------------------------------ gap analysis

_LEARN_PATHS = {
    "Python": "https://docs.python.org/3/tutorial/",
    "JavaScript": "https://javascript.info/",
    "Java": "https://dev.java/learn/",
    "Go": "https://go.dev/tour/",
    "SQL": "https://sqlbolt.com/",
    "React": "https://react.dev/learn",
    "Node.js": "https://nodejs.org/en/learn",
    "Docker": "https://docker-curriculum.com/",
    "Kubernetes": "https://kubernetes.io/docs/tutorials/",
    "AWS": "https://aws.amazon.com/getting-started/",
    "System Design": "https://github.com/donnemartin/system-design-primer",
    "Data Structures": "https://neetcode.io/roadmap",
    "Machine Learning": "https://www.kaggle.com/learn",
    "REST APIs": "https://restfulapi.net/",
    "Microservices": "https://microservices.io/patterns/",
    "Testing": "https://testingjavascript.com/",
    "Git": "https://learngitbranching.js.org/",
    "Linux": "https://linuxjourney.com/",
    "Statistics": "https://khanacademy.org/math/statistics-probability",
    "HTML": "https://web.dev/learn/html",
    "CSS": "https://web.dev/learn/css",
    "TypeScript": "https://www.typescriptlang.org/docs/handbook/intro.html",
}
_DEFAULT_RESOURCE = "https://roadmap.sh/"

_WEEKS = {
    "System Design": 4, "Microservices": 3, "Kubernetes": 3, "AWS": 3,
    "Data Structures": 4, "Machine Learning": 4, "Go": 2, "SQL": 1,
    "Docker": 1, "Git": 0.5, "Linux": 1,
}


def gap_analysis(user_skills: list[str], target_company: str) -> dict:
    user = set(user_skills)
    target = next((c for c in get_companies() if c["name"].lower() == target_company.lower()), None)
    if not target:
        raise ValueError(f"unknown company '{target_company}'")

    fit, have, missing = _fit(user, target["required_skills"])

    # pull any live/seed jobs for this company to ground the recommendation
    live = []
    try:
        jobs = get_jobs(query=target["name"], limit=5, live_first=False)["jobs"]
        live = [j for j in jobs if j["company"].lower() == target["name"].lower()][:3]
    except Exception:  # noqa: BLE001
        pass

    roadmap = []
    week = 1
    # hardest (highest-weight) missing skills first — they move the fit% most
    for skill in sorted(missing, key=_weight, reverse=True):
        weeks = _WEEKS.get(skill, 2)
        roadmap.append({
            "skill": skill,
            "why": f"Required by {target['name']}.",
            "resource": _LEARN_PATHS.get(skill, _DEFAULT_RESOURCE),
            "start_week": week,
            "duration_weeks": weeks,
            "verify_with_test": f"Take the '{skill}' test in this app after finishing — target 75%+.",
        })
        week += weeks

    total_weeks = week - 1
    projected_fit = round(fit + (100 - fit) * (sum(_weight(s) for s in missing) /
                                              max(sum(_weight(s) for s in target["required_skills"]), 1.0)) * 0.9, 1) if missing else fit

    return {
        "company": target["name"],
        "about": target["about"],
        "current_fit_percent": fit,
        "matched_skills": have,
        "missing_skills": missing,
        "roadmap": roadmap,
        "total_weeks": total_weeks,
        "projected_fit_percent_after_roadmap": projected_fit,
        "related_jobs": live,
        "message": (
            f"You are {fit}% ready for {target['name']} today. "
            + (f"Finish the {len(missing)}-skill roadmap (~{total_weeks} weeks) and you should be ~{projected_fit}% ready."
               if missing else "You already match every listed skill — apply now!")
        ),
    }
