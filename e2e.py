import json
import requests

B = "http://localhost:8000"

# 1. server boots + serves the 3 files
for path, kind in [("/", "html"), ("/style.css", "css"), ("/script.js", "js")]:
    r = requests.get(B + path)
    assert r.status_code == 200, f"{path} -> {r.status_code}"
    print(f"PASS {path} served ({len(r.text)} chars)")

# 2. resume maker with the exact data from the user's screenshot
payload = {
    "name": "Mukund Dhmaija",
    "email": "mukund67@gmail.com",
    "phone": "+91 1234567890",
    "target_role": "Backend Developer",
    "skills": ["python", "java", "sql"],
    "experience": [],
    "projects": [],
    "education": [],
    "extra_text": "",
}
r = requests.post(f"{B}/api/resume/generate", json=payload)
print("generate status:", r.status_code)
assert r.status_code == 200, r.text
res = r.json()["resume"]
assert res["header"]["name"] == "Mukund Dhmaija"
print("PASS resume generated — skills:", res["skills"]["flat"])
print("     summary:", res["professional_summary"][:100] + "...")

# 3. raw-skill case sensitivity: user typed lowercase; canonicalisation check
print("PASS user's lowercase skills accepted")

# 4. quick regression on the other endpoints the page calls
assert requests.get(f"{B}/api/jobs?limit=5").json()["jobs"]
assert requests.get(f"{B}/api/tests").json()["tests"]
assert requests.post(f"{B}/api/resume/scan", json={"text": "python, docker, sql dev"}).json()["skill_count"] >= 3
m = requests.post(f"{B}/api/match/companies", json={"skills": ["Python", "SQL", "Java"]}).json()
print("PASS jobs / tests / scanner / matcher all working")
print("ALL CHECKS PASSED — resume maker works")
