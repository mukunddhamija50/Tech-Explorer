"""
Skill taxonomy + extraction engine.

The whole product revolves around this: resume scanning, job matching,
skill-gap analysis and tests all read/write skills through this module.
"""

import re

# ---- Master taxonomy: canonical skill -> aliases / spellings we accept ----
SKILL_TAXONOMY = {
    "Python": ["python3", "py", "python (programming)"],
    "JavaScript": ["js", "es6", "ecmascript", "javascript (programming)"],
    "TypeScript": ["ts"],
    "Java": ["java (programming)", "core java", "java 8", "java 17"],
    "C++": ["cpp", "c plus plus"],
    "C": ["c language", "c programming"],
    "Go": ["golang"],
    "SQL": ["mysql", "postgres", "postgresql", "sqlite", "t-sql", "pl/sql"],
    "NoSQL": ["mongodb", "mongo", "cassandra", "dynamodb", "redis"],
    "HTML": ["html5"],
    "CSS": ["css3", "flexbox", "grid layout"],
    "React": ["react.js", "reactjs", "react js"],
    "Angular": ["angularjs", "angular 2+"],
    "Vue.js": ["vue", "vuejs", "vue js"],
    "Node.js": ["node", "nodejs", "node js", "express", "express.js", "expressjs"],
    "Next.js": ["nextjs", "next js"],
    "Django": ["django rest framework", "drf"],
    "Flask": ["flask-restful"],
    "FastAPI": ["fast api", "fast-api"],
    "Spring Boot": ["spring", "springboot", "spring-boot"],
    "REST APIs": ["rest", "restful", "rest api", "api development", "web services"],
    "GraphQL": ["apollo"],
    "Docker": ["containers", "containerization", "docker-compose"],
    "Kubernetes": ["k8s", "eks", "gke"],
    "AWS": ["amazon web services", "ec2", "s3", "lambda", "cloudwatch"],
    "Azure": ["microsoft azure"],
    "GCP": ["google cloud", "google cloud platform"],
    "CI/CD": ["jenkins", "github actions", "gitlab ci", "circleci", "continuous integration"],
    "Git": ["github", "gitlab", "version control", "bitbucket"],
    "Linux": ["unix", "bash", "shell scripting", "ubuntu"],
    "Data Structures": ["dsa", "data structures and algorithms", "algorithms"],
    "System Design": ["hld", "lld", "distributed systems", "scalability"],
    "Machine Learning": ["ml", "scikit-learn", "sklearn", "supervised learning"],
    "Deep Learning": ["neural networks", "tensorflow", "keras"],
    "NLP": ["natural language processing", "spacy", "text processing"],
    "Pandas": ["numpy", "dataframes"],
    "Data Analysis": ["data analytics", "exploratory data analysis", "eda"],
    "Data Visualization": ["matplotlib", "seaborn", "plotly", "power bi", "tableau"],
    "Statistics": ["probability", "statistical analysis", "hypothesis testing"],
    "Excel": ["advanced excel", "vlookup", "pivot tables", "microsoft excel"],
    "Testing": ["unit testing", "pytest", "jest", "selenium", "cypress", "test automation"],
    "Agile": ["scrum", "kanban", "jira", "sprint planning"],
    "Communication": ["presentation skills", "public speaking", "stakeholder management"],
    "Problem Solving": ["analytical thinking", "analytical skills"],
    "Flutter": ["dart"],
    "React Native": ["rn"],
    "Android": ["android development", "android sdk", "jetpack compose"],
    "Kotlin": ["kotlin android"],
    "iOS": ["swift", "swiftui", "uikit"],
    "MongoDB": [],
    "RabbitMQ": ["kafka", "message queues", "apache kafka"],
    "Microservices": ["microservices architecture", "service oriented architecture", "soa"],
    "Networking": ["tcp/ip", "dns", "http protocol", "load balancing"],
    "Cybersecurity": ["security", "penetration testing", "owasp", "infosec"],
}

# canonical -> category, for grouping in the UI
SKILL_CATEGORY = {
    k: ("Programming" if k in {"Python", "JavaScript", "TypeScript", "Java", "C++", "C", "Go", "Kotlin", "Dart"}
        else "Frontend" if k in {"HTML", "CSS", "React", "Angular", "Vue.js", "Next.js"}
        else "Backend" if k in {"Node.js", "Django", "Flask", "FastAPI", "Spring Boot", "REST APIs", "GraphQL", "Microservices", "RabbitMQ"}
        else "Mobile" if k in {"Flutter", "React Native", "Android", "iOS"}
        else "Data / ML" if k in {"Machine Learning", "Deep Learning", "NLP", "Pandas", "Data Analysis", "Data Visualization", "Statistics"}
        else "Database" if k in {"SQL", "NoSQL", "MongoDB"}
        else "DevOps / Cloud" if k in {"Docker", "Kubernetes", "AWS", "Azure", "GCP", "CI/CD", "Git", "Linux"}
        else "CS Foundations" if k in {"Data Structures", "System Design", "Networking", "Cybersecurity"}
        else "Tools" if k in {"Excel", "Testing", "Agile"}
        else "Soft Skills")
    for k in SKILL_TAXONOMY
}

# Build alias lookup: lowercase alias -> canonical
_ALIAS_TO_CANONICAL = {}
for canon, aliases in SKILL_TAXONOMY.items():
    _ALIAS_TO_CANONICAL[canon.lower()] = canon
    for a in aliases:
        _ALIAS_TO_CANONICAL[a.lower()] = canon

# Longest-first so "spring boot" wins over "boot"-style partial issues
_ALIAS_SORTED = sorted(_ALIAS_TO_CANONICAL.keys(), key=len, reverse=True)

_WORD_RE = re.compile(r"[^a-z0-9+#./-]+", re.I)


def extract_skills(text: str) -> list[dict]:
    """Scan free text (resume, job description) and return found skills.

    Returns list of {"skill": canonical, "category": ..., "evidence": [matched strings]}.
    """
    if not text:
        return []
    # normalise: lowercase, collapse non-word chars to spaces, keep multi-word aliases
    flat = " " + _WORD_RE.sub(" ", text.lower()).replace(".", " ") + " "

    found: dict[str, set] = {}
    for alias in _ALIAS_SORTED:
        alias_norm = _WORD_RE.sub(" ", alias.lower()).replace(".", " ").strip()
        if not alias_norm:
            continue
        token = f" {alias_norm} "
        if token in flat:
            canon = _ALIAS_TO_CANONICAL[alias]
            found.setdefault(canon, set()).add(alias_norm)

    return [
        {"skill": s, "category": SKILL_CATEGORY[s], "evidence": sorted(v)}
        for s, v in found.items()
    ]


def extract_skill_names(text: str) -> list[str]:
    return [x["skill"] for x in extract_skills(text)]


def categorize(skills: list[str]) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for s in skills:
        out.setdefault(SKILL_CATEGORY.get(s, "Other"), []).append(s)
    return out
