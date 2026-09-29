import json
import requests

B = "http://localhost:8000"
ok = lambda name: print(f"  PASS {name}")


def section(t):
    print(f"\n== {t}")


section("1. Health")
assert requests.get(f"{B}/api/health").json()["ok"]
ok("health")

section("2. Real-time jobs")
r = requests.get(f"{B}/api/jobs", params={"query": "python", "limit": 5}).json()
print(f"  source={r['source']}  jobs={len(r['jobs'])}")
assert r["jobs"], "no jobs returned"
ok(f"jobs endpoint ({r['source']} fallback active in sandbox)")

section("3. Resume maker")
payload = {
    "name": "Mukund Dhamija", "email": "mukund@gmail.com", "phone": "+91 98xxxxxx10",
    "target_role": "Backend Developer",
    "skills": ["Python", "SQL"],
    "experience": [{"role": "Backend Intern", "company": "FinEdge", "duration": "2025",
                    "highlights": ["responsible for building REST APIs used by 3000 users",
                                   "automated report generation saving 20 hours/week"]}],
    "projects": [{"name": "Expense Splitter", "description": "Flask + React app used by 500 students"}],
    "education": [{"degree": "B.Tech CSE", "institute": "MIT Manipal", "year": "2026"}],
    "extra_text": "I also use docker, git and linux daily.",
}
r = requests.post(f"{B}/api/resume/generate", json=payload).json()["resume"]
print(f"  skills detected: {r['skills']['flat']}")
assert r["experience"][0]["highlights"][0].startswith("Built")  # 'responsible for building…' rewritten
assert "Docker" in r["skills"]["flat"]                    # mined from extra_text
print(f"  bullet 1 -> {r['experience'][0]['highlights'][0]}")
print(f"  tips: {len(r['suggestions'])} generated")
ok("resume generation + rewrite + mining")

section("4. Resume scanner")
txt = """Mukund Dhamija | mukund@gmail.com | +91 98xxxxxx10
Backend intern with experience in Python, Django, REST APIs, MySQL, docker and git.
B.Tech Computer Science, 2026."""
s = requests.post(f"{B}/api/resume/scan", json={"text": txt}).json()
print(f"  skills={[x['skill'] for x in s['detected_skills']]}")
print(f"  ats_score={s['ats_score']}  seniority={s['seniority']}")
assert s["skill_count"] >= 5
assert 0 <= s["ats_score"] <= 100
ok("scanner")

section("5. Company matching")
skills = ["Python", "SQL", "REST APIs", "Docker", "Git", "Linux", "AWS", "System Design", "Microservices"]
m = requests.post(f"{B}/api/match/companies", json={"skills": skills}).json()
print(f"  ready: {[c['company'] for c in m['ready_now']]}")
print(f"  close: {[c['company'] for c in m['close']][:4]}...")
print(f"  stretch count: {len(m['stretch'])}")
assert m["ready_now"], "expected at least one ready company"
top = m["all"][0]
print(f"  top fit: {top['company']} {top['fit_percent']}% missing={top['missing_skills']}")
ok("weighted fit matching")

section("6. Gap analysis (target user can't reach yet)")
g = requests.post(f"{B}/api/match/gap", json={"skills": ["Python", "SQL"], "company": "Razorpay"}).json()
print(f"  {g['message']}")
print("  roadmap:", [(s['skill'], 'week ' + str(s['start_week'])) for s in g['roadmap']])
assert g["missing_skills"]
assert g["projected_fit_percent_after_roadmap"] > g["current_fit_percent"]
ok("gap roadmap")

section("7. Skill tests")
tl = requests.get(f"{B}/api/tests").json()["tests"]
print(f"  available: {[t['skill'] for t in tl]}")
t = requests.get(f"{B}/api/tests/Python").json()
assert "answer" not in json.dumps(t), "answers must not leak to client!"
res = requests.post(f"{B}/api/tests/Python/submit", json={"answers": [1, 2, 1, 0, 1, 1, 1, 1]}).json()
print(f"  scored {res['correct']}/{res['total']} = {res['percent']}% band={res['band']}")
assert res["percent"] == 100.0
bad = requests.post(f"{B}/api/tests/Python/submit", json={"answers": [0, 2, 1, 0, 1, 1, 1, 1]}).json()
assert bad["percent"] < 100 and bad["per_question"][0]["correct"] is False
ok("tests: no answer leak, grading correct")

section("8. Web UI")
html = requests.get(f"{B}/").text
assert "SkillMatch" in html and "Resume Maker" in html
ok("UI served")

print("\nALL CHECKS PASSED")
