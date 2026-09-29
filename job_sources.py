"""
Real-time job data layer.

Priority order:
  1. LIVE  - Remotive public API (no key) and Adzuna (optional keys via env vars).
  2. CACHE - last successful live response, kept for 10 minutes.
  3. SEED - built-in dataset of companies + roles so the product always works.

All endpoints in the app consume jobs in one shape (see _normalize_*).
"""

import os
import time
import threading
import random
from typing import Optional

import requests

from skills import extract_skill_names

REMOTIVE_URL = "https://remotive.com/api/remote-jobs"
ADZUNA_URL = "https://api.adzuna.com/v1/api/jobs/{country}/search/{page}"

CACHE_TTL_SECONDS = 600  # 10 minutes
FETCH_TIMEOUT = 15

_lock = threading.Lock()
_cache: dict = {"ts": 0.0, "jobs": []}  # in-process cache


# ---------------------------------------------------------------- normalizers

def _normalize_remotive(j: dict) -> dict:
    desc = j.get("description") or ""
    return {
        "id": f"remotive-{j.get('id')}",
        "title": (j.get("title") or "").strip(),
        "company": (j.get("company_name") or "").strip(),
        "location": j.get("candidate_required_location") or "Remote",
        "url": j.get("url"),
        "type": j.get("job_type") or "full_time",
        "published": (j.get("publication_date") or "")[:10],
        "salary": j.get("salary") or "",
        "tags": j.get("tags") or [],
        "description": desc[:4000],
        "required_skills": extract_skill_names(f"{j.get('title','')} {' '.join(j.get('tags') or [])} {desc[:2500]}"),
        "source": "remotive",
    }


def _normalize_adzuna(j: dict) -> dict:
    desc = j.get("description") or ""
    loc = j.get("location") or {}
    return {
        "id": f"adzuna-{j.get('id')}",
        "title": (j.get("title") or "").strip(),
        "company": ((j.get("company") or {}) or {}).get("display_name", "Unknown"),
        "location": loc.get("display_name", "") if isinstance(loc, dict) else str(loc),
        "url": j.get("redirect_url"),
        "type": "full_time",
        "published": (j.get("created") or "")[:10],
        "salary": "",
        "tags": [],
        "description": desc[:4000],
        "required_skills": extract_skill_names(f"{j.get('title','')} {desc[:2500]}"),
        "source": "adzuna",
    }


# ---------------------------------------------------------------- live fetches

def _fetch_remotive(query: Optional[str], limit: int) -> list[dict]:
    params = {"limit": min(max(limit, 1), 50)}
    if query:
        params["search"] = query
    r = requests.get(REMOTIVE_URL, params=params, timeout=FETCH_TIMEOUT)
    r.raise_for_status()
    jobs = r.json().get("jobs", [])
    return [_normalize_remotive(j) for j in jobs]


def _fetch_adzuna(query: Optional[str], limit: int) -> list[dict]:
    app_id = os.environ.get("ADZUNA_APP_ID")
    app_key = os.environ.get("ADZUNA_APP_KEY")
    if not (app_id and app_key):
        return []
    params = {"app_id": app_id, "app_key": app_key, "results_per_page": min(limit, 50)}
    if query:
        params["what"] = query
    r = requests.get(ADZUNA_URL.format(country="in", page=1), params=params, timeout=FETCH_TIMEOUT)
    r.raise_for_status()
    return [_normalize_adzuna(j) for j in r.json().get("results", [])]


# ---------------------------------------------------------------- seed fallback

_SEED_COMPANIES = [
    ("Google", ["Python", "Java", "Go", "System Design", "Machine Learning", "Cloud", "Data Structures"], "Search, cloud, and AI products at global scale."),
    ("Microsoft", ["C++", "C#", "Azure", "System Design", "Python", "Testing", "SQL"], "Enterprise cloud, productivity, and AI platform company."),
    ("Amazon", ["Java", "Python", "AWS", "System Design", "Microservices", "SQL", "Docker"], "Global commerce and cloud at massive scale."),
    ("Meta", ["Python", "C++", "JavaScript", "System Design", "Machine Learning", "SQL"], "Social platforms and AI-driven products at internet scale."),
    ("Apple", ["Swift", "Objective-C", "iOS", "Python", "System Design", "Testing"], "Consumer hardware, software, and services ecosystem."),
    ("Netflix", ["Java", "JavaScript", "AWS", "System Design", "Microservices", "Testing"], "Streaming and large-scale media platform operations."),
    ("Uber", ["Go", "Java", "Python", "System Design", "SQL", "Kubernetes"], "Mobility and logistics platform with large distributed systems."),
    ("Airbnb", ["JavaScript", "Python", "React", "Node.js", "AWS", "SQL"], "Marketplace platform for travel and experiences."),
    ("Stripe", ["Python", "JavaScript", "SQL", "System Design", "REST APIs", "Testing"], "Payment infrastructure and developer-first financial products."),
    ("Atlassian", ["JavaScript", "TypeScript", "React", "Node.js", "AWS", "Testing"], "Developer tooling and collaboration SaaS."),
    ("GitHub", ["Ruby", "JavaScript", "Go", "Testing", "Git", "REST APIs"], "Developer platform and source code collaboration."),
    ("GitLab", ["Ruby", "Go", "JavaScript", "Linux", "Testing", "Docker"], "DevSecOps platform and CI/CD software."),
    ("Adobe", ["JavaScript", "Python", "React", "SQL", "Machine Learning", "Testing"], "Creative software and digital media platform."),
    ("Salesforce", ["Java", "JavaScript", "AWS", "REST APIs", "SQL", "Testing"], "Enterprise SaaS and CRM platform."),
    ("ServiceNow", ["JavaScript", "Java", "SQL", "REST APIs", "AWS", "Testing"], "Enterprise workflow automation and cloud platform."),
    ("Oracle", ["Java", "SQL", "Python", "System Design", "Linux", "Testing"], "Database, enterprise apps, and infrastructure software."),
    ("SAP", ["Java", "SQL", "Python", "REST APIs", "Cloud", "Testing"], "ERP and enterprise business software."),
    ("Intuit", ["Python", "JavaScript", "SQL", "Machine Learning", "REST APIs"], "Consumer finance software and automation platforms."),
    ("NVIDIA", ["C++", "Python", "CUDA", "Machine Learning", "Linux", "Data Structures"], "AI, GPU, and accelerated computing stack."),
    ("Qualcomm", ["C++", "Python", "Embedded", "Linux", "Testing", "Data Structures"], "Semiconductor and wireless platform engineering."),
    ("IBM", ["Python", "Java", "SQL", "Cloud", "System Design", "Testing"], "Enterprise AI, infrastructure, and consulting solutions."),
    ("PayPal", ["Java", "Python", "SQL", "System Design", "REST APIs", "AWS"], "Digital payments and fintech platform."),
    ("Visa", ["Java", "Python", "SQL", "REST APIs", "System Design", "Cloud"], "Global digital payments infrastructure."),
    ("Mastercard", ["Java", "Python", "SQL", "System Design", "AWS", "Testing"], "Global payments and digital commerce infrastructure."),
    ("JPMorgan Chase", ["Java", "Python", "SQL", "System Design", "Cloud", "Testing"], "Global banking and financial technology platform."),
    ("Goldman Sachs", ["Python", "Java", "SQL", "System Design", "Machine Learning"], "Investment banking and quantitative engineering."),
    ("Walmart Global Tech", ["Java", "Python", "SQL", "AWS", "System Design", "Microservices"], "Retail and supply chain technology platform."),
    ("Target", ["Java", "Python", "JavaScript", "SQL", "Cloud", "Testing"], "Retail tech and omnichannel product engineering."),
    ("Dell Technologies", ["Python", "Java", "Linux", "Cloud", "Testing", "SQL"], "Enterprise hardware and cloud operations platform."),
    ("HP", ["Java", "Python", "Linux", "Cloud", "Testing", "REST APIs"], "Enterprise productivity and hardware engineering."),
    ("Cisco", ["Python", "Java", "Linux", "Networking", "Security", "Testing"], "Networking, security, and enterprise infrastructure."),
    ("VMware", ["Python", "Go", "Linux", "Cloud", "Docker", "Kubernetes"], "Virtualization and cloud-native infrastructure."),
    ("Datadog", ["Python", "Go", "AWS", "Docker", "Kubernetes", "SQL"], "Monitoring, observability, and cloud platform."),
    ("New Relic", ["Python", "JavaScript", "Go", "Cloud", "Testing", "SQL"], "Observability and software monitoring platform."),
    ("Confluent", ["Java", "Go", "Kafka", "System Design", "Docker", "Kubernetes"], "Streaming data and event-driven infrastructure."),
    ("MongoDB", ["Python", "JavaScript", "NoSQL", "System Design", "REST APIs"], "Document database and developer data platform."),
    ("Snowflake", ["Python", "SQL", "Java", "Cloud", "Data Analysis", "Machine Learning"], "Cloud data warehouse and analytics platform."),
    ("Databricks", ["Python", "SQL", "Spark", "Machine Learning", "Cloud", "Data Analysis"], "Lakehouse and data engineering platform."),
    ("Palantir", ["Python", "Java", "SQL", "Machine Learning", "System Design"], "Data analytics and enterprise software for complex operations."),
    ("Thoughtworks", ["Java", "JavaScript", "Python", "Cloud", "Testing", "Agile"], "Consulting and product engineering across multiple domains."),
    ("Accenture", ["Java", "Python", "SQL", "Cloud", "Agile", "Testing"], "Global consulting and enterprise transformation services."),
    ("Deloitte", ["Python", "Java", "SQL", "Cloud", "Agile", "Testing"], "Consulting, data, and enterprise digital transformation."),
    ("Cognizant", ["Java", "Python", "SQL", "Cloud", "REST APIs", "Testing"], "Technology and consulting services for global enterprises."),
    ("Capgemini", ["Java", "Python", "SQL", "Cloud", "Testing", "Agile"], "IT services and digital engineering firm."),
    ("Infosys", ["Java", "Python", "SQL", "Azure", "REST APIs", "Agile"], "Global digital services and enterprise platform consulting."),
    ("TCS", ["Java", "Python", "SQL", "Spring Boot", "REST APIs", "Testing"], "Large-scale enterprise technology and IT services."),
    ("Wipro", ["Java", "Python", "SQL", "Cloud", "Testing", "Agile"], "Enterprise IT services and digital transformation."),
    ("HCLTech", ["Java", "Python", "SQL", "Cloud", "Testing", "Agile"], "Product engineering and digital services company."),
    ("Tech Mahindra", ["Java", "Python", "SQL", "Cloud", "Testing", "AWS"], "Digital transformation and telecom technology services."),
    ("Persistent Systems", ["Java", "Python", "Cloud", "Microservices", "SQL", "Testing"], "Product engineering and digital transformation services."),
    ("Coforge", ["Java", "Python", "SQL", "Cloud", "REST APIs", "Testing"], "Digital engineering and enterprise IT services."),
    ("LTIMindtree", ["Java", "Python", "SQL", "Cloud", "Testing", "Agile"], "Digital engineering and platform modernization."),
    ("Razorpay", ["Java", "Spring Boot", "SQL", "RabbitMQ", "AWS", "Microservices"], "Fintech platform built for scale and payment infrastructure."),
    ("Zoho", ["Java", "JavaScript", "SQL", "REST APIs", "Linux", "System Design"], "Product company with a strong full-stack engineering culture."),
    ("Freshworks", ["JavaScript", "React", "Node.js", "REST APIs", "AWS", "Testing"], "Customer engagement SaaS platform and product engineering."),
    ("Zerodha", ["Python", "Go", "React", "Linux", "System Design", "Data Structures"], "Brokerage platform with a lean and high-scale stack."),
    ("Swiggy", ["Java", "Go", "React", "Microservices", "AWS", "System Design"], "Food delivery scale platform across operations and logistics."),
    ("PhonePe", ["Java", "Spring Boot", "SQL", "Kubernetes", "System Design", "Microservices"], "UPI and fintech infrastructure at scale."),
    ("CRED", ["Go", "Java", "React", "AWS", "Microservices", "System Design"], "Credit and fintech platform with modern engineering."),
    ("Flipkart", ["Java", "Spring Boot", "SQL", "Data Analysis", "AWS", "System Design"], "E-commerce marketplace with complex scale and analytics."),
    ("Paytm", ["Java", "Spring Boot", "SQL", "AWS", "Microservices", "System Design"], "Fintech and commerce ecosystem with large engineering teams."),
    ("Meesho", ["Python", "React", "Node.js", "AWS", "Machine Learning", "SQL"], "Social commerce platform using data and product engineering."),
    ("Groww", ["Java", "Spring Boot", "React", "AWS", "System Design", "SQL"], "Investment platform built around scale and UX."),
    ("Myntra", ["Java", "JavaScript", "React", "Machine Learning", "AWS", "SQL"], "Fashion commerce and recommendation-driven product experience."),
    ("Zomato", ["Java", "Go", "AWS", "Microservices", "System Design", "SQL"], "Food delivery and local commerce platform at scale."),
    ("Navi", ["Java", "Python", "AWS", "Machine Learning", "System Design", "SQL"], "Data-driven fintech product company."),
    ("Dream11", ["Java", "Node.js", "AWS", "System Design", "NoSQL", "Testing"], "Real-time sports platform with internet-scale traffic."),
    ("Postman", ["JavaScript", "Node.js", "React", "AWS", "Microservices", "Testing"], "API platform with developer-first tooling."),
    ("BrowserStack", ["JavaScript", "Testing", "Java", "Docker", "AWS", "Node.js"], "Software testing platform for global developers."),
    ("Ola", ["Go", "Java", "AWS", "Kubernetes", "System Design", "React"], "Mobility platform with cloud and ride-operations engineering."),
    ("Urban Company", ["Java", "Node.js", "React", "AWS", "System Design", "SQL"], "Home services and local commerce marketplace."),
    ("MakeMyTrip", ["Java", "JavaScript", "React", "AWS", "SQL", "System Design"], "Travel booking platform with high-scale consumer products."),
    ("Delhivery", ["Java", "Python", "SQL", "AWS", "System Design", "Data Analysis"], "Logistics and supply chain platform at scale."),
    ("Jio", ["Java", "Python", "AWS", "Kubernetes", "System Design", "Network"], "Telecom and digital ecosystem infrastructure."),
    ("Airtel", ["Java", "Python", "AWS", "System Design", "Networking", "SQL"], "Telecom and digital platform services."),
    ("Upstox", ["Python", "Java", "React", "SQL", "System Design", "Testing"], "Brokerage and fintech product engineering."),
    ("ShareChat", ["Java", "Python", "React", "Machine Learning", "AWS", "SQL"], "Regional social content and recommendation platform."),
    ("Unacademy", ["Python", "JavaScript", "React", "Node.js", "AWS", "Machine Learning"], "Edtech platform and learner-first digital products."),
    ("Byju's", ["Python", "JavaScript", "Node.js", "AWS", "Machine Learning", "React"], "Edtech platform with product engineering and data systems."),
    ("Naukri", ["Java", "Python", "SQL", "Node.js", "AWS", "Testing"], "Recruitment platform and consumer product infrastructure."),
    ("Indeed", ["Java", "Python", "SQL", "Cloud", "System Design", "Testing"], "Global employment marketplace and search platform."),
    ("LinkedIn", ["Java", "Python", "JavaScript", "SQL", "System Design", "Machine Learning"], "Professional network with large-scale data and product systems."),
    ("Reddit", ["Python", "Go", "JavaScript", "SQL", "System Design", "Testing"], "Community platform with content, feed, and scale challenges."),
    ("Shopify", ["Ruby", "JavaScript", "React", "Node.js", "AWS", "SQL"], "Commerce platform and merchant ecosystem."),
    ("Notion", ["TypeScript", "React", "Node.js", "SQL", "AWS", "Testing"], "Productivity and collaboration software."),
    ("Dropbox", ["Python", "Go", "JavaScript", "SQL", "System Design", "AWS"], "Storage, sync, and productivity platform."),
    ("Slack", ["JavaScript", "Node.js", "React", "Java", "Testing", "System Design"], "Real-time collaboration platform."),
    ("Discord", ["Go", "TypeScript", "React", "Node.js", "Engineering", "Testing"], "Real-time communication and gaming platform."),
    ("Figma", ["TypeScript", "React", "Node.js", "JavaScript", "Testing", "System Design"], "Collaborative design and product prototyping platform."),
    ("Canva", ["JavaScript", "TypeScript", "Node.js", "React", "AWS", "Testing"], "Design and publishing platform."),
    ("Pinterest", ["Python", "JavaScript", "Machine Learning", "SQL", "System Design"], "Visual discovery and recommendation platform."),
    ("Twitter", ["Scala", "Java", "Python", "System Design", "Machine Learning", "SQL"], "Social media platform with high-scale content flows."),
    ("Snapchat", ["Java", "Swift", "Kotlin", "Python", "Machine Learning", "AWS"], "Social media and AR product platform."),
    ("ByteDance", ["Java", "Python", "C++", "Machine Learning", "System Design", "SQL"], "Global short-form media and AI ecosystem."),
    ("Nubank", ["Java", "Python", "React", "SQL", "AWS", "System Design"], "Digital banking and fintech platform."),
    ("Plaid", ["Python", "JavaScript", "SQL", "REST APIs", "Testing", "Cloud"], "Financial data and infrastructure platform."),
    ("Robinhood", ["Python", "Java", "JavaScript", "SQL", "Machine Learning", "System Design"], "Trading and finance consumer platform."),
    ("Coinbase", ["JavaScript", "Python", "Go", "SQL", "System Design", "AWS"], "Crypto trading and digital wallet platform."),
    ("Square", ["Java", "JavaScript", "Python", "SQL", "System Design", "Cloud"], "Payments and business tools platform."),
    ("ShopUp", ["Python", "JavaScript", "Node.js", "AWS", "SQL", "REST APIs"], "Commerce and SMB platform in emerging markets."),
    ("Gojek", ["Java", "Go", "Python", "AWS", "System Design", "SQL"], "Super app with mobility, payments, and services."),
    ("Grab", ["Java", "Python", "Go", "AWS", "System Design", "SQL"], "Super app and mobility marketplace."),
    ("Practo", ["Python", "JavaScript", "Node.js", "SQL", "AWS", "Testing"], "Healthcare platform and digital workflow products."),
    ("HealthifyMe", ["Python", "JavaScript", "Node.js", "Machine Learning", "SQL"], "Health-tech platform with data and recommendation products."),
    ("Myntra", ["Java", "JavaScript", "React", "Machine Learning", "AWS", "SQL"], "Fashion commerce experience with recommendations and scale."),
    ("Cult.fit", ["Python", "JavaScript", "Node.js", "AWS", "Machine Learning", "SQL"], "Fitness and wellness platform with consumer product scale."),
    ("Spinny", ["Java", "Python", "React", "Node.js", "AWS", "SQL"], "Auto marketplace and commerce platform."),
    ("CarDekho", ["Java", "Python", "JavaScript", "AWS", "SQL", "Machine Learning"], "Auto marketplace and recommendation platform."),
    ("OYO", ["Java", "Python", "Node.js", "React", "AWS", "System Design"], "Hospitality and marketplace platform."),
    ("NoBroker", ["Java", "Python", "Node.js", "AWS", "SQL", "System Design"], "Real estate marketplace and platform engineering."),
    ("HackerRank", ["Python", "JavaScript", "Node.js", "SQL", "Testing", "Machine Learning"], "Developer assessment and hiring platform."),
    ("CodeChef", ["Python", "JavaScript", "Node.js", "SQL", "Testing", "Machine Learning"], "Coding platform and developer community."),
    ("GeeksforGeeks", ["JavaScript", "Python", "Node.js", "SQL", "Machine Learning"], "Learning platform and technical content ecosystem."),
    ("NVIDIA", ["C++", "Python", "Machine Learning", "Linux", "Data Structures", "CUDA"], "Accelerated computing and AI platform."),
    ("OpenAI", ["Python", "C++", "Machine Learning", "System Design", "Data Structures"], "Foundation model and AI platform research."),
    ("Anthropic", ["Python", "C++", "Machine Learning", "Data Structures", "System Design"], "AI research and model platform company."),
    ("Perplexity", ["Python", "JavaScript", "Machine Learning", "SQL", "System Design"], "AI-powered search and assistant platform."),
    ("Kaggle", ["Python", "SQL", "Machine Learning", "Data Analysis", "Statistics"], "Data science community and ML platform."),
    ("Coursera", ["Python", "JavaScript", "Node.js", "SQL", "Machine Learning"], "Online learning platform and digital education experience."),
    ("Udemy", ["Python", "JavaScript", "Node.js", "AWS", "SQL", "Testing"], "Marketplace for online learning and digital products."),
    ("Akamai", ["Python", "Java", "Linux", "Networking", "System Design", "Cloud"], "CDN and edge platform engineering."),
    ("Cloudflare", ["Go", "Rust", "Python", "Networking", "Linux", "System Design"], "Distributed edge network and security platform."),
    ("Fastly", ["Go", "JavaScript", "Python", "Networking", "Docker", "Cloud"], "Edge delivery and application platform."),
    ("HashiCorp", ["Go", "Python", "Linux", "Docker", "System Design", "Testing"], "Infrastructure automation and cloud platform tools."),
    ("Docker", ["Go", "Python", "Linux", "Docker", "Kubernetes", "Testing"], "Container platform and developer tooling."),
    ("Red Hat", ["Python", "Java", "Linux", "Kubernetes", "Docker", "System Design"], "Enterprise open-source infrastructure platform."),
    ("MongoDB", ["Python", "JavaScript", "NoSQL", "REST APIs", "System Design", "Cloud"], "Document database and app data platform."),
    ("Elastic", ["Java", "Go", "Python", "Search", "System Design", "Cloud"], "Search, observability, and data platform."),
    ("SUSE", ["Python", "Go", "Linux", "Kubernetes", "Docker", "Cloud"], "Enterprise Linux and cloud infrastructure."),
    ("VMware", ["Python", "Go", "Linux", "Cloud", "Docker", "Kubernetes"], "Virtualization and cloud-native enterprise platform."),
    ("Nutanix", ["Python", "Java", "Go", "Linux", "Kubernetes", "Cloud"], "Hyperconverged infrastructure and hybrid cloud."),
    ("Criteo", ["Python", "Java", "SQL", "Machine Learning", "Data Analysis", "System Design"], "Ad-tech and recommendation platform."),
    ("PubMatic", ["Java", "Python", "SQL", "System Design", "Machine Learning"], "Programmatic advertising and ad-tech platform."),
    ("Affle", ["Python", "JavaScript", "Machine Learning", "SQL", "AWS"], "Mobile advertising and consumer tech platform."),
    ("InMobi", ["Java", "Python", "Machine Learning", "AWS", "SQL", "System Design"], "Mobile advertising and app discovery platform."),
    ("OnePlus", ["Java", "Kotlin", "Android", "REST APIs", "Testing", "JavaScript"], "Consumer electronics and mobile platform company."),
    ("Samsung", ["Java", "Kotlin", "Android", "C++", "Linux", "Testing"], "Consumer hardware and mobile platform company."),
    ("Motorola", ["Java", "Kotlin", "Android", "Testing", "REST APIs"], "Mobile hardware and software engineering."),
    ("BharatPe", ["Java", "Python", "SQL", "AWS", "System Design", "REST APIs"], "Fintech platform focused on digital payments and commerce."),
    ("PolicyBazaar", ["Java", "Python", "Node.js", "AWS", "SQL", "Testing"], "Insurtech and digital consumer platform."),
    ("Nykaa", ["Java", "Python", "React", "Node.js", "AWS", "SQL"], "Beauty e-commerce and digital commerce platform."),
    ("PharmEasy", ["Java", "Python", "Node.js", "AWS", "SQL", "REST APIs"], "Healthcare and digital pharmacy platform."),
    ("Gupshup", ["Java", "Python", "Node.js", "REST APIs", "AWS", "SQL"], "Messaging and conversational platform."),
    ("JioMart", ["Java", "Python", "Node.js", "AWS", "SQL", "System Design"], "Retail and ecommerce platform for digital commerce."),
    ("Bharat Matrimony", ["Java", "Python", "SQL", "Node.js", "AWS", "Testing"], "Consumer matchmaking and digital services platform."),
    ("Hexaware", ["Java", "Python", "SQL", "Cloud", "Testing", "Agile"], "Digital transformation and enterprise engineering services."),
    ("Mphasis", ["Java", "Python", "SQL", "Cloud", "Testing", "Agile"], "Application and digital engineering services."),
    ("Sutherland", ["Java", "Python", "SQL", "Cloud", "Testing", "Agile"], "Digital business and customer experience service company."),
    ("EXL", ["Python", "SQL", "Machine Learning", "Data Analysis", "Cloud"], "Analytics and digital operations company."),
    ("Fractal", ["Python", "SQL", "Machine Learning", "Data Analysis", "Cloud"], "AI and analytics transformation services."),
    ("MuSigma", ["Python", "SQL", "Machine Learning", "Data Analysis", "Statistics"], "Analytics and decision intelligence company."),
    ("Tiger Analytics", ["Python", "SQL", "Machine Learning", "Data Analysis", "Statistics"], "Data science and AI consulting company."),
    ("Mindtree", ["Java", "Python", "SQL", "Cloud", "Testing", "Agile"], "Digital engineering and enterprise technology services."),
    ("L&T Technology Services", ["Java", "Python", "SQL", "Cloud", "Testing", "System Design"], "Engineering research and product development services."),
    ("Cybage", ["Java", "Python", "JavaScript", "Cloud", "Testing", "Agile"], "Product engineering services company."),
    ("Zeta", ["Java", "Python", "Node.js", "AWS", "System Design", "SQL"], "Fintech and banking platform technology company."),
    ("FIS", ["Java", "Python", "SQL", "Cloud", "System Design", "Testing"], "Financial technology and payment infrastructure provider."),
    ("Fiserv", ["Java", "Python", "SQL", "REST APIs", "AWS", "Testing"], "Payments and financial software platform."),
    ("Netskope", ["Python", "Go", "Linux", "Security", "Cloud", "Testing"], "Cloud security and network platform."),
    ("Palo Alto Networks", ["Python", "Go", "Linux", "Security", "Networking", "Cloud"], "Cybersecurity platform and threat detection company."),
    ("CrowdStrike", ["Python", "C++", "Linux", "Security", "Cloud", "Testing"], "Cybersecurity and cloud-native endpoint protection."),
    ("Zscaler", ["Python", "Java", "Security", "Cloud", "Linux", "Testing"], "Secure cloud access and zero-trust networking company."),
    ("Verizon", ["Java", "Python", "Cloud", "Networking", "Linux", "SQL"], "Telecom and digital infrastructure company."),
    ("AT&T", ["Java", "Python", "Cloud", "Networking", "Linux", "SQL"], "Telecom and digital connectivity company."),
    ("Comcast", ["Java", "Python", "Cloud", "Networking", "Linux", "Testing"], "Telecom and digital media platform architecture."),
    ("Amdocs", ["Java", "Python", "SQL", "REST APIs", "Cloud", "Testing"], "Telecom and software services company."),
    ("Nokia", ["C++", "Python", "Networking", "Linux", "Cloud", "System Design"], "Telecom and network infrastructure company."),
    ("Ericsson", ["C++", "Python", "Networking", "Linux", "Cloud", "System Design"], "Telecom network, software, and infrastructure company."),
    ("Broadcom", ["C++", "Python", "Linux", "Networking", "System Design", "Testing"], "Semiconductor and infrastructure technology company."),
    ("Intel", ["C++", "Python", "Linux", "System Design", "Cloud", "Testing"], "Semiconductors and platform engineering company."),
    ("AMD", ["C++", "Python", "Linux", "System Design", "Data Structures", "Cloud"], "Semiconductor and high-performance computing company."),
    ("NVIDIA", ["C++", "Python", "Machine Learning", "CUDA", "Linux", "Data Structures"], "AI and accelerated-computing technology platform."),
    ("OpenAI", ["Python", "C++", "Machine Learning", "Data Structures", "System Design"], "AI research and application platform company."),
    ("Anthropic", ["Python", "C++", "Machine Learning", "Data Structures", "System Design"], "AI model development and platform research."),
    ("Perplexity", ["Python", "JavaScript", "Machine Learning", "SQL", "System Design"], "AI-powered search and assistant platform."),
    ("KPMG", ["Python", "SQL", "Machine Learning", "Cloud", "Testing"], "Consulting and analytics transformation firm."),
    ("EY", ["Python", "SQL", "Cloud", "Machine Learning", "Testing"], "Consulting and enterprise digital transformation services."),
    ("PwC", ["Python", "SQL", "Cloud", "Machine Learning", "Testing"], "Professional services and digital transformation consulting."),
    ("Mercari", ["Java", "Python", "Go", "SQL", "System Design", "AWS"], "Marketplace and consumer commerce platform."),
    ("Rakuten", ["Java", "Python", "SQL", "System Design", "Cloud", "Testing"], "E-commerce and digital platform company."),
    ("Bajaj Finserv", ["Java", "Python", "SQL", "System Design", "Cloud", "Testing"], "Financial services and digital platform company."),
    ("Axis Bank", ["Java", "Python", "SQL", "REST APIs", "Cloud", "Testing"], "Banking and financial technology platform."),
    ("HDFC Bank", ["Java", "Python", "SQL", "REST APIs", "Cloud", "Testing"], "Banking technology and digital services platform."),
    ("ICICI Bank", ["Java", "Python", "SQL", "REST APIs", "Cloud", "Testing"], "Banking and digital financial services platform."),
]

_ADDITIONAL_COMPANIES = [
    ("technology", "Alibaba Group|Tencent|Baidu|JD.com|PDD Holdings|Xiaomi|Huawei|Lenovo|ASUS|Acer|Sony|Panasonic|LG Electronics|SK Hynix|Micron Technology|Texas Instruments|Applied Materials|Lam Research|ASML|TSMC|MediaTek|Arm Holdings|Marvell Technology|Analog Devices|NXP Semiconductors|Infineon Technologies|STMicroelectronics|KLA Corporation|Synopsys|Cadence Design Systems|Qualcomm India|Samsung Semiconductor|Foxconn|HP Enterprise|NetApp|Pure Storage|Seagate Technology|Western Digital|Keysight Technologies|Roku|Roblox|Epic Games|Unity Software|Electronic Arts|Take-Two Interactive|Ubisoft|Bandai Namco|Nintendo|Sega|Kakao|Naver|LINE Corporation|Rakuten Mobile|Opera Limited|Yandex|Mercado Libre|Globant|EPAM Systems|ThoughtSpot|Atlassian India|SUSE India|GitHub India"),
    ("ecommerce", "Blinkit|BigBasket|Zepto|Tata Digital|Reliance Retail|Jiomart|Amazon India|Flipkart Wholesale|Myntra Jabong|AJIO|FirstCry|Lenskart|Meesho India|Udaan|OfBusiness|Infra.Market|Moglix|IndiaMART|Snapdeal|Pepperfry|Wakefit|Livspace|Urban Ladder|CaratLane|Titan Company|Croma|DMart|Avenue Supermarts|Trent|Shoppers Stop|Landmark Group|Noon|Namshi|Daraz|Tokopedia|Shopee|Lazada|Coupang|Rakuten Ichiba|Wayfair|Etsy|eBay|Chewy|Instacart|DoorDash|Delivery Hero|Just Eat Takeaway|Ocado Group|Zalando|ASOS|Farfetch|Vinted|Temu|Shein|Wayfair India|Nykaa Fashion|Tata 1mg|Jio Platforms"),
    ("finance", "State Bank of India|Bank of Baroda|Punjab National Bank|Canara Bank|Union Bank of India|Bank of India|Indian Bank|Central Bank of India|IDBI Bank|Yes Bank|Kotak Mahindra Bank|Axis Bank India|IndusInd Bank|Federal Bank|Bandhan Bank|AU Small Finance Bank|IDFC First Bank|RBL Bank|South Indian Bank|Karur Vysya Bank|City Union Bank|Jana Small Finance Bank|Equitas Small Finance Bank|Bajaj Finance|Bajaj Finserv|Shriram Finance|Muthoot Finance|Manappuram Finance|Cholamandalam Investment|HDB Financial Services|Tata Capital|Aditya Birla Capital|L&T Finance|Mahindra Finance|SBI Life Insurance|HDFC Life|ICICI Prudential Life|Max Life Insurance|LIC|New India Assurance|ICICI Lombard|HDFC ERGO|Star Health Insurance|Acko|Policybazaar|PayU|BillDesk|CAMS|CDSL|BSE Limited|National Stock Exchange of India|Angel One|Motilal Oswal|ICICI Securities|HDFC Securities|Dhan|Jupiter Money|Fi Money|Niyo|RazorpayX|Cashfree Payments|Pine Labs|CRED|BharatPe India|PhonePe India|Paytm Payments Bank|Wise|Revolut|Monzo|Starling Bank|Chime|SoFi|Capital One|Wells Fargo|Citigroup|Bank of America|Morgan Stanley|BlackRock|Fidelity Investments|Charles Schwab|American Express|Discover Financial|Synchrony Financial|BNY Mellon|State Street Corporation|HSBC|Barclays|Lloyds Banking Group|NatWest Group|Standard Chartered|UBS|Credit Suisse|Deutsche Bank|Commerzbank|BNP Paribas|Societe Generale|Crédit Agricole|ING Group|ABN AMRO|Santander|BBVA|UniCredit|Intesa Sanpaolo|Nordea|Danske Bank|KBC Group|Mizuho Financial Group|Mitsubishi UFJ Financial Group|Sumitomo Mitsui Financial Group|Nomura|Dai-ichi Life|Japan Post Bank|China Construction Bank|Industrial and Commercial Bank of China|Agricultural Bank of China|Bank of China|China Merchants Bank|Ping An Insurance|Ant Group|KakaoBank|DBS Bank|OCBC Bank|United Overseas Bank|Maybank|CIMB Group|Kasikornbank|Bangkok Bank|Banco do Brasil|Itaú Unibanco|Bancolombia|RBC|TD Bank Group|Scotiabank|BMO Financial Group|Manulife|Sun Life Financial|MetLife|Prudential Financial|AIG|Allianz|AXA|Zurich Insurance Group|Swiss Re|Munich Re"),
    ("automotive", "Tata Motors|Mahindra and Mahindra|Maruti Suzuki|Hyundai Motor India|Kia India|Ashok Leyland|Eicher Motors|Bajaj Auto|TVS Motor Company|Hero MotoCorp|Royal Enfield|Ather Energy|Ola Electric|Bharat Forge|JBM Auto|Force Motors|Sundram Fasteners|Motherson|Bosch India|Continental Automotive|ZF Friedrichshafen|Valeo|Aptiv|Denso|Magna International|Lear Corporation|Rivian|Lucid Motors|Tesla|Ford Motor Company|General Motors|Stellantis|Volkswagen Group|Porsche|Mercedes-Benz Group|BMW Group|Audi|Volvo Cars|Polestar|BYD|Geely|NIO|XPeng|Li Auto|Great Wall Motor|SAIC Motor|FAW Group|Dongfeng Motor|Chery Automobile|Toyota Motor Corporation|Honda Motor Company|Nissan Motor|Subaru Corporation|Mazda Motor|Suzuki Motor Corporation|Mitsubishi Motors|Isuzu Motors|Hyundai Motor Company|Kia Corporation|Renault Group|Peugeot|Ferrari|Yamaha Motor|Kawasaki Motors|BorgWarner|Cummins|PACCAR|Navistar|Oshkosh Corporation|Caterpillar|John Deere|CNH Industrial|Kubota|JCB|Hitachi Construction Machinery|Komatsu|Volvo Group|Scania|MAN Truck and Bus|Daimler Truck|Traton|Uber Freight|Rivian Automotive|Lucid Group"),
    ("energy", "Reliance Industries|Adani Enterprises|Adani Ports|Adani Green Energy|Adani Energy Solutions|Tata Power|NTPC|Power Grid Corporation of India|Power Finance Corporation|REC Limited|NHPC|Coal India|ONGC|Oil India|Indian Oil Corporation|Bharat Petroleum|Hindustan Petroleum|GAIL India|Petronet LNG|JSW Energy|Torrent Power|CESC Limited|Suzlon Energy|Inox Wind|Waaree Energies|Tata Chemicals|Larsen and Toubro|BHEL|Siemens India|ABB India|Schneider Electric India|Honeywell Automation India|GE Vernova|General Electric|Siemens Energy|Schneider Electric|Eaton|Emerson Electric|Rockwell Automation|Johnson Controls|Carrier Global|Trane Technologies|3M|Honeywell International|DuPont|Dow Chemical|BASF|Bayer|Linde|Air Liquide|Air Products|Airbus|Boeing|Lockheed Martin|RTX Corporation|Northrop Grumman|General Dynamics|BAE Systems|Thales Group|Safran|Leonardo S.p.A.|Rolls-Royce Holdings|GE Aerospace|Parker Hannifin|Illinois Tool Works|Deere and Company|Stanley Black and Decker|Emerson India|Cochin Shipyard|Mazagon Dock Shipbuilders|Garden Reach Shipbuilders|HAL India|Bharat Dynamics|BEL India|ISRO|Blue Origin|SpaceX|Rocket Lab|Relativity Space|A.P. Moller Maersk|Schlumberger|Halliburton|Baker Hughes|Weatherford International|ExxonMobil|Chevron|ConocoPhillips|Occidental Petroleum|Marathon Petroleum|Phillips 66|Valero Energy|Shell|BP|TotalEnergies|Eni|Equinor|Petrobras|Saudi Aramco|ADNOC|QatarEnergy|PetroChina|Sinopec|CNOOC|Petronas|PTT Public Company|Neste|Vestas|Orsted|Iberdrola|Enel|RWE|E.ON|EDF|Engie|NextEra Energy|Duke Energy|Southern Company|Dominion Energy|American Electric Power|Constellation Energy|Vistra|First Solar|Enphase Energy|SolarEdge Technologies|Sungrow|LONGi Green Energy|Trina Solar|Canadian Solar|Bloom Energy|Plug Power|Schlumberger India"),
    ("healthcare", "Apollo Hospitals|Fortis Healthcare|Max Healthcare|Manipal Hospitals|Narayana Health|Aster DM Healthcare|Dr Lal PathLabs|Metropolis Healthcare|Thyrocare|Dr Reddy's Laboratories|Sun Pharmaceutical|Cipla|Lupin|Zydus Lifesciences|Torrent Pharmaceuticals|Biocon|Serum Institute of India|Bharat Biotech|Divi's Laboratories|Glenmark Pharmaceuticals|Aurobindo Pharma|Mankind Pharma|Alkem Laboratories|Abbott India|Piramal Pharma|Syngene International|Strides Pharma Science|IQVIA|Medtronic|Johnson and Johnson|Pfizer|Moderna|Eli Lilly|Novo Nordisk|Roche|Novartis|Sanofi|GSK|AstraZeneca|Merck and Co|Bristol Myers Squibb|Amgen|Gilead Sciences|Regeneron Pharmaceuticals|Vertex Pharmaceuticals|Thermo Fisher Scientific|Danaher|Becton Dickinson|Stryker Corporation|Boston Scientific|Intuitive Surgical|GE HealthCare|Siemens Healthineers|Philips Healthcare|ResMed|UnitedHealth Group|CVS Health|Cigna|Elevance Health|Humana|HCA Healthcare|Tenet Healthcare|Labcorp|Quest Diagnostics|Oscar Health|Zocdoc|Practo Technologies|PharmEasy India|Netmeds|Tata 1mg Health|Innovaccer|Health Catalyst|Tempus AI|Veeva Systems|Cerner|Epic Systems|Dexcom|Hims and Hers Health|GoodRx|Align Technology|EssilorLuxottica|Coloplast|Fresenius Medical Care|Baxter International|Cardinal Health|McKesson|Cencora|Henry Schein|ResMed India|Dr Agarwal's Health Care"),
    ("consumer", "Hindustan Unilever|ITC Limited|Nestlé India|Britannia Industries|Varun Beverages|Tata Consumer Products|Godrej Consumer Products|Dabur India|Marico|United Spirits|Radico Khaitan|Asian Paints|Berger Paints|Pidilite Industries|Havells India|Voltas|Blue Star|Crompton Greaves Consumer Electricals|Whirlpool India|LG Electronics India|Procter and Gamble|Coca-Cola|PepsiCo|Mondelez International|Mars Incorporated|Kraft Heinz|General Mills|Kellogg Company|Danone|Unilever|L'Oreal|Estée Lauder Companies|Colgate-Palmolive|Reckitt|Kimberly-Clark|Procter and Gamble India|Coty|Kenvue|Church and Dwight|Clorox|Walmart|Costco|Home Depot|Lowe's|Kroger|Target Corporation|Carrefour|Tesco|Aldi|Lidl|Auchan|IKEA|Inditex|H&M Group|Fast Retailing|Nike|Adidas|Puma|Under Armour|VF Corporation|Levi Strauss and Co|Deckers Brands|Tapestry|Ralph Lauren|Hermes|LVMH|Kering|Richemont|Swatch Group|Rolex|Pandora|Chanel|Prada|Burberry|Ferragamo|Tata International|D-Mart India|Reliance Brands|Future Retail|Vishal Mega Mart|Sapphire Foods|Jubilant FoodWorks|Westlife Foodworld|Devyani International|Varun Beverages India|Emami|Colgate India|Godrej Industries|Tata Steel Consumer Products"),
    ("telecom", "Bharti Airtel|Vodafone Idea|BSNL|MTNL|T-Mobile|Verizon Communications|AT&T Inc|Deutsche Telekom|Orange S.A.|Telefonica|Vodafone Group|BT Group|Swisscom|Telstra|Optus|KDDI|NTT Data|SoftBank Group|China Mobile|China Telecom|China Unicom|SK Telecom|KT Corporation|Singtel|Reliance Jio|Comcast|Charter Communications|Rogers Communications|Bell Canada|Telus|Walt Disney Company|Warner Bros Discovery|NBCUniversal|Paramount Global|Sony Pictures|Netflix Studios|Spotify|Warner Music Group|Universal Music Group|Sony Music Entertainment|Nintendo of America|Fox Corporation|News Corp|Thomson Reuters|Bloomberg LP|The New York Times Company|The Guardian|Financial Times|Zee Entertainment|Sony Pictures Networks India|JioStar|Sun TV Network|Network18|Times Internet|ShareChat India|Dailyhunt|Inshorts|Pocket FM|JioSaavn|Gaana|Audible|iHeartMedia|Sirius XM|Live Nation Entertainment|Bilibili|iQIYI|Weibo|Kuaishou|Tripledot Studios"),
    ("transport", "Indian Railways|IRCTC|Delhi Metro Rail Corporation|Bangalore Metro Rail Corporation|Adani Airports|GMR Airports|GMR Group|Air India|IndiGo|SpiceJet|Akasa Air|Air India Express|Vistara|Emirates|Qatar Airways|Etihad Airways|Singapore Airlines|Cathay Pacific|Japan Airlines|All Nippon Airways|Korean Air|Lufthansa|Air France-KLM|British Airways|easyJet|Ryanair|Turkish Airlines|Qantas|Air Canada|United Airlines|Delta Air Lines|American Airlines|Southwest Airlines|FedEx|UPS|DHL Group|Blue Dart Express|Ecom Express|Shadowfax|XpressBees|Amazon Transportation Services|Delhivery India|Safexpress|DTDC|Gati Limited|BlackBuck|Porter|Rapido|Ola Cabs|BlaBlaCar|Lyft|Grab Holdings|Bolt Technology|DiDi Global|Cabify|Rappi|Yandex Go|Booking Holdings|Expedia Group|Airbnb Experiences|MakeMyTrip India|Cleartrip|EaseMyTrip|Yatra Online|OYO Rooms|Marriott International|Hilton Worldwide|Hyatt Hotels|Accor|IHG Hotels and Resorts|Wyndham Hotels|TUI Group|Trip.com Group|Amadeus IT Group|Sabre Corporation|A.P. Moller Maersk India|Hapag-Lloyd|CMA CGM|COSCO Shipping|DP World|PSA International|DHL Supply Chain|XPO Logistics|C.H. Robinson|Kuehne and Nagel|DSV|DB Schenker|Ryder System|J.B. Hunt Transport|Union Pacific|BNSF Railway|Canadian National Railway|Canadian Pacific Kansas City|Deutsche Bahn|SNCF|Japan Railways Group|Uber India|Ola Electric Mobility"),
    ("food", "Zomato Limited|Blinkit India|Swiggy Instamart|Eternal Limited|Haldiram's|Amul|Mother Dairy|Hatsun Agro Product|Dodla Dairy|Parag Milk Foods|Heritage Foods|Cargill|Archer Daniels Midland|Bunge|JBS S.A.|Tyson Foods|Hormel Foods|Pilgrim's Pride|McDonald's|Yum! Brands|Restaurant Brands International|Starbucks|Chipotle Mexican Grill|Domino's Pizza|Papa John's|Darden Restaurants|Yum China|Luckin Coffee|Tim Hortons|Restaurant Brands Asia|Barbeque Nation|Wow! Momo|Rebel Foods|FreshToHome|Licious|Country Delight|EatSure|Swiggy Dineout|CloudKitchens|Compass Group|Sodexo|Aramark|Sysco|US Foods|Performance Food Group|HelloFresh|Blue Apron|Deliveroo|Gopuff|Getir|Grocery Outlet|Sprouts Farmers Market|Whole Foods Market|The Hershey Company|Lindt and Sprungli|Ferrero Group|Barry Callebaut|Keurig Dr Pepper|JDE Peet's|Carlsberg Group|Heineken|AB InBev|Diageo India|Pernod Ricard|Brown-Forman|Molson Coors|Constellation Brands|Treasury Wine Estates|Remy Cointreau"),
    ("enterprise", "Tata Consultancy Services|Infosys Limited|Wipro Limited|HCL Technologies|Tech Mahindra Limited|LTIMindtree Limited|Mphasis Limited|Coforge Limited|Hexaware Technologies|Birlasoft|KPIT Technologies|Sonata Software|Zensar Technologies|Cyient|L&T Technology Services|Tata Elxsi|GlobalLogic|Virtusa|UST|Nagarro|N-iX|Luxoft|DXC Technology|Kyndryl|CGI Inc|Booz Allen Hamilton|Leidos|SAIC|KBR Inc|Jacobs Solutions|Fluor Corporation|AECOM|Bechtel|Accenture Federal Services|Genpact|EXL Service|WNS Global Services|Concentrix|Teleperformance|TaskUs|Foundever|Sopra Steria|Atos|Capgemini Invent|Publicis Sapient|Slalom|Bain and Company|McKinsey and Company|Boston Consulting Group|Oliver Wyman|Kearney|Roland Berger|Grant Thornton|BDO International|RSM International|Protiviti|Alvarez and Marsal|WTW|Aon|Marsh McLennan|Deloitte India|KPMG India|EY India|PwC India|Tata Projects|Shapoorji Pallonji|Adani Group|JSW Group|Vedanta Resources|Hindalco Industries|Tata Steel|JSW Steel|Steel Authority of India|Jindal Steel and Power|Jindal Stainless|ArcelorMittal|Nucor|Cleveland-Cliffs|POSCO|Hyundai Steel|Nippon Steel|China Baowu Steel Group|Tata International Limited|Grasim Industries|UltraTech Cement|Shree Cement|Ambuja Cements|Dalmia Bharat|ACC Limited|Cemex|Holcim|Heidelberg Materials|Saint-Gobain|Corning Incorporated|Owens Corning|PPG Industries|Sherwin-Williams|Ecolab|International Paper|Smurfit Westrock|Crown Holdings|Ball Corporation|Amcor|Packaging Corporation of America|Avery Dennison|Xerox|Canon|Ricoh|Brother Industries|Konica Minolta|Dixon Technologies|Amber Enterprises|Kaynes Technology|Syrma SGS Technology|Havells India Limited|Polycab India|KEI Industries|Finolex Cables|CG Power|Thermax|KSB Limited|Kirloskar Brothers|AIA Engineering|SKF India|Timken India|Atlas Copco|Kone|Otis Worldwide|Schindler Group|TK Elevator|Daikin Industries|Mitsubishi Electric|Mitsubishi Heavy Industries|Toshiba|Fujitsu|NEC Corporation|Hitachi|Mitsui and Co|Mitsubishi Corporation|Itochu Corporation|Sumitomo Corporation|Marubeni|Toyota Tsusho|Berkshire Hathaway|Honeywell India|Siemens Limited|ABB Limited|Bharat Electronics Limited|Bharat Heavy Electricals Limited|Tata Communications|Indus Towers|Crown Castle|American Tower Corporation|Equinix|Digital Realty|Prologis|CBRE Group|JLL|Cushman and Wakefield|DLF Limited|Godrej Properties|Prestige Estates Projects|Oberoi Realty|Phoenix Mills|Embassy Office Parks|Brookfield India Real Estate Trust|Lodha Developers|Brigade Enterprises|Sunteck Realty|Tata Realty and Infrastructure|Hindustan Construction Company|NCC Limited|IRB Infrastructure Developers|KNR Constructions|Larsen and Toubro Construction|Afcons Infrastructure|KEC International|Kalpataru Projects International|Rail Vikas Nigam|IRCON International|RITES Limited|Container Corporation of India|Adani Wilmar|AWL Agri Business|Patanjali Foods|Godrej Agrovet|Coromandel International|PI Industries|UPL Limited|Bayer Crop Science India|FMC Corporation|Corteva Agriscience|Deere India|Kubota India|Mahindra and Mahindra Financial Services"),
]

_COMPANY_PROFILES = {
    "technology": (["Python", "Java", "SQL", "Cloud", "System Design", "Data Structures"], "technology and software products"),
    "ecommerce": (["Java", "Python", "SQL", "AWS", "Data Analysis", "System Design"], "commerce and marketplace products"),
    "finance": (["Java", "Python", "SQL", "REST APIs", "Cloud", "Security"], "financial services and payment technology"),
    "automotive": (["C++", "Python", "Embedded", "Linux", "Cloud", "System Design"], "automotive engineering and mobility products"),
    "energy": (["Python", "SQL", "Cloud", "Data Analysis", "Linux", "Security"], "energy, infrastructure, and industrial technology"),
    "healthcare": (["Python", "SQL", "Machine Learning", "Cloud", "Data Analysis", "Security"], "healthcare, medical products, and digital health"),
    "consumer": (["Java", "Python", "SQL", "Cloud", "Data Analysis", "Testing"], "consumer products and retail operations"),
    "telecom": (["Java", "Python", "Networking", "Cloud", "Linux", "System Design"], "telecommunications and media platforms"),
    "transport": (["Java", "Python", "SQL", "Cloud", "Data Analysis", "System Design"], "transportation, travel, and logistics systems"),
    "food": (["Python", "SQL", "Data Analysis", "Cloud", "Java", "Operations"], "food, grocery, and hospitality services"),
    "enterprise": (["Java", "Python", "SQL", "Cloud", "REST APIs", "System Design"], "enterprise, engineering, and professional services"),
}


def _expand_company_catalog() -> list[tuple[str, list[str], str]]:
    companies = []
    seen = set()
    for name, skills, about in _SEED_COMPANIES:
        key = name.casefold()
        if key not in seen:
            companies.append((name, skills, about))
            seen.add(key)
    for sector, names in _ADDITIONAL_COMPANIES:
        skills, description = _COMPANY_PROFILES[sector]
        for name in names.split("|"):
            key = name.casefold()
            if key in seen:
                continue
            companies.append((name, skills, f"Major company in {description}."))
            seen.add(key)
            if len(companies) == 500:
                return companies
    raise RuntimeError(f"Company catalog contains only {len(companies)} unique profiles; expected 500.")


_SEED_COMPANIES = _expand_company_catalog()

_SEED_TITLES = [
    "Software Engineer", "Senior Software Engineer", "Backend Developer",
    "Frontend Developer", "Full Stack Developer", "Data Analyst",
    "Machine Learning Engineer", "DevOps Engineer", "SDE I", "SDE II",
    "QA Automation Engineer", "Product Engineer",
]

_SEED_LOCATIONS = ["Bengaluru", "Bengaluru", "Hyderabad", "Pune", "Chennai", "NCR", "Remote (India)", "Mumbai"]


def _seed_jobs(query: Optional[str], limit: int) -> list[dict]:
    rng = random.Random(42)  # deterministic-ish demo data
    jobs = []
    for i, (company, skills, blurb) in enumerate(_SEED_COMPANIES):
        if query:
            q = query.lower()
            hay = f"{company} {' '.join(skills)} {blurb}".lower()
            if q not in hay and not any(q in s.lower() for s in skills):
                continue
        jobs.append({
            "id": f"seed-{i}",
            "title": rng.choice(_SEED_TITLES),
            "company": company,
            "location": rng.choice(_SEED_LOCATIONS),
            "url": None,
            "type": "full_time",
            "published": f"2026-09-{rng.randint(10, 23):02d}",
            "salary": f"₹{rng.randint(6, 45)} – ₹{rng.randint(46, 90)} LPA",
            "tags": skills[:4],
            "description": f"{company}: {blurb} Core stack: {', '.join(skills)}.",
            "required_skills": skills,
            "source": "seed",
        })
    return jobs[:limit]


def get_companies() -> list[dict]:
    """Company profiles with required skills — used by the matching engine."""
    return [
        {"name": name, "required_skills": skills, "about": blurb}
        for name, skills, blurb in _SEED_COMPANIES
    ]


# ---------------------------------------------------------------- public API

def get_jobs(query: Optional[str] = None, limit: int = 100, live_first: bool = True) -> dict:
    """Return {'jobs': [...], 'source': 'live-remotive'|'live-adzuna'|'cache'|'seed', 'fetched_at': ts}.

    Tries live sources; on any failure falls back to cache then seed data.
    Never raises — the product must always show something.
    """
    errors = []
    if live_first:
        try:
            jobs = _fetch_remotive(query, limit)
            if jobs:
                if len(jobs) < limit:
                    seed_jobs = _seed_jobs(query, max(limit - len(jobs), 0))
                    seen = {job["id"] for job in jobs}
                    for job in seed_jobs:
                        if job["id"] not in seen:
                            jobs.append(job)
                            seen.add(job["id"])
                            if len(jobs) >= limit:
                                break
                with _lock:
                    _cache["ts"] = time.time()
                    _cache["jobs"] = jobs
                return {"jobs": jobs, "source": "live-remotive", "fetched_at": _cache["ts"]}
        except Exception as e:  # noqa: BLE001
            errors.append(f"remotive: {type(e).__name__}")

        try:
            jobs = _fetch_adzuna(query, limit)
            if jobs:
                if len(jobs) < limit:
                    seed_jobs = _seed_jobs(query, max(limit - len(jobs), 0))
                    seen = {job["id"] for job in jobs}
                    for job in seed_jobs:
                        if job["id"] not in seen:
                            jobs.append(job)
                            seen.add(job["id"])
                            if len(jobs) >= limit:
                                break
                with _lock:
                    _cache["ts"] = time.time()
                    _cache["jobs"] = jobs
                return {"jobs": jobs, "source": "live-adzuna", "fetched_at": _cache["ts"]}
        except Exception as e:  # noqa: BLE001
            errors.append(f"adzuna: {type(e).__name__}")

        # fresh cache?
        with _lock:
            if _cache["jobs"] and time.time() - _cache["ts"] < CACHE_TTL_SECONDS:
                jobs = _filter_seed(_cache["jobs"], query, limit)
                return {"jobs": jobs, "source": "cache", "fetched_at": _cache["ts"], "notes": errors}

    seed_jobs = _seed_jobs(query, limit)
    return {
        "jobs": seed_jobs,
        "source": "seed",
        "fetched_at": time.time(),
        "notes": errors or ["live sources unreachable"],
    }


def _filter_seed(jobs: list[dict], query: Optional[str], limit: int) -> list[dict]:
    if not query:
        return jobs[:limit]
    q = query.lower()
    out = [j for j in jobs if q in j["title"].lower() or q in j["company"].lower()
           or any(q in s.lower() for s in j.get("required_skills", []))]
    return out[:limit] or jobs[:limit]
