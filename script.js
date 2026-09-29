/* =====================================================
   NAVIGATION
===================================================== */

function exploreSkills() {
    const section = document.getElementById("skills");
    if (section) {
        section.scrollIntoView({ behavior: "smooth" });
    }
}

function exploreJobs() {
    const section = document.getElementById("jobs");
    if (section) {
        section.scrollIntoView({ behavior: "smooth" });
    }
}

function filterRecommendedJobs() {
    const input = document.getElementById("skillJobSearch");
    const empty = document.getElementById("recommendationEmpty");
    const query = input ? input.value.trim().toLowerCase() : "";
    const cards = document.querySelectorAll(".skill-job-card");
    let visible = 0;

    cards.forEach(function (card) {
        const matches = !query || card.dataset.search.includes(query);
        card.hidden = !matches;
        if (matches) visible += 1;
    });

    if (empty) empty.hidden = visible !== 0;
}

function openProjectFile(button) {
    const modal = document.getElementById("projectModal");
    const title = document.getElementById("projectModalTitle");
    const status = document.getElementById("projectModalStatus");
    const code = document.getElementById("projectCode");
    const file = button.getAttribute("data-file");

    if (!modal || !title || !status || !code || !file) return;

    title.textContent = file;
    status.textContent = "Loading file...";
    code.textContent = "";
    modal.classList.add("open");
    modal.setAttribute("aria-hidden", "false");
    document.body.classList.add("modal-open");

    fetch(file)
        .then(function (response) {
            if (!response.ok) throw new Error("File could not be loaded");
            return response.text();
        })
        .then(function (contents) {
            code.textContent = contents;
            status.textContent = "Read-only project source";
        })
        .catch(function (error) {
            status.textContent = error.message + ". Start the local server to preview files.";
        });
}

function closeProjectFile() {
    const modal = document.getElementById("projectModal");
    if (!modal) return;
    modal.classList.remove("open");
    modal.setAttribute("aria-hidden", "true");
    document.body.classList.remove("modal-open");
}

document.addEventListener("keydown", function (event) {
    if (event.key === "Escape") closeProjectFile();
});


/* =====================================================
   MOBILE MENU
===================================================== */

function toggleMenu() {
    const navLinks = document.getElementById("navLinks");
    if (navLinks) {
        navLinks.classList.toggle("open");
    }
}


/* =====================================================
   HERO CHART
===================================================== */

function animateChart() {
    const bars = document.querySelectorAll(".chart-bar");

    bars.forEach(function (bar, index) {
        const width = bar.getAttribute("data-width");
        setTimeout(function () {
            bar.style.width = width;
        }, 250 + (index * 150));
    });
}


/* =====================================================
   SKILLS API
===================================================== */

async function loadSkills() {
    const container = document.getElementById("skillsContainer");
    const message = document.getElementById("message");

    if (!container) return;

    try {
        const response = await fetch("http://localhost:8080/api/skills");
        if (!response.ok) throw new Error("Server returned an error");

        const skills = await response.json();
        container.innerHTML = "";

        skills.forEach(function (skill) {
            const card = document.createElement("div");
            card.className = "data-card";
            const info = findSkillInfo(skill.name);
            card.innerHTML = `
                <div class="card-icon">${info.icon}</div>
                <h3>${skill.name}</h3>
                <p>${info.text}</p>
                <span class="tag">${skill.level}</span>
            `;
            container.appendChild(card);
        });

        if (message) {
            message.textContent = "✓ Connected to Java backend";
            message.style.color = "#16803c";
        }
    } catch (error) {
        console.error("Skills error:", error);
        if (message) {
            message.textContent = "⚠ Cannot connect to Java backend. Start index.java first.";
            message.style.color = "#c62828";
        }
    }
}


/* =====================================================
   SKILL INFO
   Short descriptions shown on the skill cards.
===================================================== */

const SKILL_INFO = {
    "python sql": {
        icon: "\uD83D\uDC0D",
        text: "The most requested combination in data and back-end roles \u2014 Python for building logic and automation, SQL for storing and querying data."
    },
    "java full stack": {
        icon: "\u2615",
        text: "Enterprise web development end to end \u2014 Java, Spring Boot and SQL together power large-scale business applications."
    },
    "cloud": {
        icon: "\u2601\uFE0F",
        text: "Deploying and running applications on AWS, Azure and GCP \u2014 the foundation of every modern product team."
    },
    "data analytics": {
        icon: "\uD83D\uDCCA",
        text: "Turning raw business data into decisions using SQL, Excel and visualization tools like Power BI."
    },
    "generative ai": {
        icon: "\u2728",
        text: "Building with large language models \u2014 prompting, LLM APIs and AI-powered features now appear across products."
    },
    "machine learning and generative ai": {
        icon: "\uD83E\uDD16",
        text: "Training models that learn from data \u2014 from classic ML algorithms to modern LLM applications."
    }
};

function findSkillInfo(name) {
    const hit = SKILL_INFO[normalizeKey(name)];
    return hit || { icon: "💻", text: "A core skill tracked by our live industry demand engine." };
}


/* =====================================================
   JOBS API
===================================================== */

let allJobs = [];

async function loadJobs() {
    const container = document.getElementById("jobsContainer");
    if (!container) return;

    try {
        const response = await fetch("http://localhost:8080/api/jobs");
        if (!response.ok) throw new Error("Server returned an error");

        const jobs = await response.json();
        allJobs = jobs;
        container.innerHTML = "";

        jobs.forEach(function (job) {
            const card = document.createElement("div");
            card.className = "data-card";
            const info = findRichDetail("job", job.title);

            card.innerHTML = `
                <div class="card-icon">${info && info.icon ? info.icon : "🚀"}</div>
                <h3>${job.title}</h3>
                <p>Skills required:</p>
                <span class="tag">${job.skills}</span>
                <a class="card-arrow" href="detail.html?type=job&key=${encodeURIComponent(job.title)}" aria-label="View ${job.title} details">→</a>
            `;

            container.appendChild(card);
        });
    } catch (error) {
        console.error("Jobs error:", error);
        container.innerHTML = `
            <div class="data-card">
                <h3>Unable to load jobs</h3>
                <p>Please start the Java backend and refresh the page</p>
            </div>
        `;
    }
}


/* =====================================================
   FIND JOB ROLES (skill filter for the jobs section)
===================================================== */

const JOB_SKILL_ALIASES = {
    "java": ["spring"],
    "python": [],
    "sql": ["database", "data base"],
    "cloud": ["aws", "azure", "docker", "devops"],
    "data analytics": ["data analyst", "data analysis", "database management", "power bi", "excel"],
    "machine learning": ["genai", "llm", "artificial intelligence"],
    "cyber security": ["cyber scurity", "information security", "network security"]
};

function jobMatchesSkill(job, selectedSkill) {
    const haystack = (job.skills + " " + job.title).toLowerCase();
    if (haystack.includes(selectedSkill)) return true;

    const aliases = JOB_SKILL_ALIASES[selectedSkill] || [];
    return aliases.some(function (alias) {
        return haystack.includes(alias);
    });
}

function renderJobCards(jobs) {
    const container = document.getElementById("jobsContainer");
    container.innerHTML = "";

    if (jobs.length === 0) {
        container.innerHTML = `
            <div class="data-card">
                <h3>No matching job roles</h3>
                <p>No current job roles require this skill. Try selecting another skill.</p>
            </div>
        `;
        return;
    }

    jobs.forEach(function (job) {
        const card = document.createElement("div");
        card.className = "data-card";
        const info = findRichDetail("job", job.title);

        card.innerHTML = `
            <div class="card-icon">${info && info.icon ? info.icon : "\u{1F680}"}</div>
            <h3>${job.title}</h3>
            <p>Skills required:</p>
            <span class="tag">${job.skills}</span>
            <a class="card-arrow" href="detail.html?type=job&key=${encodeURIComponent(job.title)}" aria-label="View ${job.title} details">\u2192</a>
        `;

        container.appendChild(card);
    });
}

function findSkills() {
    const select = document.getElementById("skillSelect");
    if (!select) return;

    const selectedSkill = select.value;

    if (selectedSkill === "") {
        renderJobCards(allJobs);
        return;
    }

    const filteredJobs = allJobs.filter(function (job) {
        return jobMatchesSkill(job, selectedSkill);
    });

    renderJobCards(filteredJobs);
}

/* =====================================================
   PROGRAMS API
===================================================== */

let allPrograms = [];

async function loadPrograms() {
    const container = document.getElementById("programsContainer");
    if (!container) return;

    try {
        const response = await fetch("http://localhost:8080/api/programs");
        if (!response.ok) throw new Error("Server returned an error");

        allPrograms = await response.json();
        displayPrograms(allPrograms);
    } catch (error) {
        console.error("Programs error:", error);
        container.innerHTML = `
            <div class="data-card">
                <h3>Unable to load programs</h3>
                <p>Please start the Java backend.</p>
            </div>
        `;
    }
}

function displayPrograms(programs) {
    const container = document.getElementById("programsContainer");
    if (!container) return;

    container.innerHTML = "";

    if (programs.length === 0) {
        container.innerHTML = `
            <div class="data-card">
                <h3>No matching program</h3>
                <p>Try selecting another skill.</p>
            </div>
        `;
        return;
    }

    programs.forEach(function (program) {
        const card = document.createElement("div");
        card.className = "data-card";
        const info = findRichDetail("program", program.name);
        card.innerHTML = `
            <div class="card-icon">${info && info.icon ? info.icon : "🎓"}</div>
            <h3>${program.name}</h3>
            <p>Skill: ${program.skill}</p>
            <span class="tag">${program.duration}</span>
            <a class="card-arrow" href="detail.html?type=program&key=${encodeURIComponent(program.name)}" aria-label="View ${program.name} details">→</a>
        `;
        container.appendChild(card);
    });
}

function findPrograms() {
    const select = document.getElementById("skillSelect");
    const result = document.getElementById("result");

    if (!select || !result) return;

    const selectedSkill = select.value.toLowerCase().trim();

    if (selectedSkill === "") {
        result.textContent = "Please select a skill first.";
        displayPrograms(allPrograms);
        return;
    }

    const filteredPrograms = allPrograms.filter(function (program) {
        return programMatchesSkill(program, selectedSkill);
    });

    if (filteredPrograms.length > 0) {
        result.textContent = filteredPrograms.length + " program(s) found for " + select.options[select.selectedIndex].text;
    } else {
        result.textContent = "No program found for this skill.";
    }

    displayPrograms(filteredPrograms);
}

/* =====================================================
   RICH DETAIL CONTENT
   Add a new entry here (key = normalized name) and the
   detail page will automatically show rich content for
   that job role / program. If an entry is missing, the
   page falls back to the simple basic card.
===================================================== */

/* Turns "Cyber Scurity" / "AI & ML Engineer" etc. into
   one canonical key so backend typos still match. */
function normalizeKey(text) {
    return String(text || "")
        .toLowerCase()
        .replace(/scurity/g, "security")
        .replace(/sequrity/g, "security")
        .replace(/genrative/g, "generative")
        .replace(/oparting/g, "operating")
        .replace(/prating/g, "prating")
        .replace(/data base/g, "database")
        .replace(/&/g, "and")
        .replace(/[^a-z0-9]+/g, " ")
        .trim();
}

const JOB_DETAILS = {
    "full stack developer": {
        icon: "💻",
        description: "A Full Stack Developer builds complete web applications end to end — the user-facing front end, the server-side logic behind it, and the database that stores the data. It is one of the most in-demand roles in the Indian tech market because startups and enterprises alike need engineers who can own a feature from UI to deployment.",
        salary: "Indicative salary (India, 2025): ₹3.5–6 LPA for freshers (0–1 year), ₹6–15 LPA with 3+ years of experience, and ₹12–25 LPA for 5+ years — product-based companies pay at the top of each band.",
        highlights: [
            "Build responsive, interactive user interfaces with HTML, CSS and JavaScript",
            "Design and consume REST APIs using Java and Spring Boot",
            "Model, query and manage relational databases with SQL",
            "Connect the front end to the back end and handle authentication, validation and errors",
            "Use Git for version control and collaborate in a team workflow",
            "Deploy and maintain applications on servers or the cloud"
        ],
        skills: ["HTML & CSS", "JavaScript", "Java", "Spring Boot", "SQL", "REST APIs", "Git"],
        roadmap: [
            { title: "Front-end basics", text: "HTML, CSS, responsive layout, and core JavaScript (DOM, events, fetch). Build 3\u20134 small UI projects." },
            { title: "Core Java", text: "OOP, collections, exception handling, and clean coding practices." },
            { title: "Back-end with Spring Boot", text: "REST controllers, services, Spring Data JPA, validation and security basics." },
            { title: "Databases", text: "SQL queries, joins, normalization, and connecting MySQL/PostgreSQL to your app." },
            { title: "Build & ship projects", text: "Combine everything into 2\u20133 full projects (e.g. job portal, e-commerce) and deploy them." }
        ],
        research: [
            { label: "Full Stack Developer Roadmap", url: "https://roadmap.sh/full-stack" },
            { label: "MDN Web Docs (HTML/CSS/JS)", url: "https://developer.mozilla.org" },
            { label: "Spring Boot official guides", url: "https://spring.io/projects/spring-boot" },
            { label: "NPTEL programming courses", url: "https://nptel.ac.in" },
            { label: "COMPUTER SCIENCE WITH PYTHON book by Sumita Arora (for Basics of SQL)", url:"https://www.ssgopalganj.in/online/Class%20XII/Comp/Computer%20science%20PYTHON%20book%20pdf%20for%20class%2012.pdf" },
        ],
        youtube: [
            { label: "Java Full Stack Development course", url: "https://youtube.com/playlist?list=PLsyeobzWxl7pe_IiTfNyr55kwJPWbgxB5&si=gCUzN99WNEG1hfyA" },
            { label: "Spring Boot tutorial for beginners", url: "https://youtube.com/playlist?list=PLsyeobzWxl7qbKoSgR5ub6jolI8-ocxCF&si=yu2ECcWpZWIf1zy4" },
            { label: "HTML CSS JavaScript full course", url: "https://youtube.com/playlist?list=PLu0W_9lII9agiCUZYRsvtGTXdxkzPyItg&si=WEIKH6kyCpnZ_4Ji" },
            { label: "SQL full course", url: "https://youtu.be/7S_tz1z_5bA?si=-JKbX7P2ZwfReP1A" }
        ]
    },

    "python developer": {
        icon: "🐍",
        description: "Python Developers write the server-side logic, scripts, data pipelines and APIs that power modern applications. Python's simplicity and huge ecosystem (FastAPI, Django, pandas, and AI libraries) make it the most flexible first language — and one of the most requested skills in Indian job postings.",
        salary: "Indicative salary (India, 2025): ₹3–6 LPA for freshers (0–1 year), ₹6–12 LPA with 3+ years of experience, and ₹12–25 LPA for 5+ years, with Django, data and cloud skills pushing pay toward the higher end.",
        highlights: [
            "Write clean, well-tested Python code following OOP and functional patterns",
            "Build and document REST APIs with FastAPI or Django",
            "Query and manage databases using SQL and Python ORMs",
            "Automate repetitive tasks: file handling, web scraping, report generation",
            "Work with data using pandas and NumPy",
            "Integrate third-party APIs and deploy Python services"
        ],
        skills: ["Python", "SQL", "FastAPI", "REST APIs", "Git", "Pandas / NumPy basics"],
        roadmap: [
            { title: "Python fundamentals", text: "Syntax, data structures, functions, OOP, error handling and virtual environments." },
            { title: "SQL & databases", text: "SELECT/JOIN/aggregate queries, indexes, and connecting Python to MySQL or PostgreSQL." },
            { title: "Build APIs with FastAPI", text: "Routes, request validation, authentication, and automatic docs." },
            { title: "Practical tooling", text: "Git/GitHub, unit testing with pytest, logging, and project structure." },
            { title: "Portfolio projects", text: "Build 2\u20133 back-end projects (e.g. URL shortener, expense API) and host them." }
        ],
        research: [
            { label: "Introduction with Python programming (harvard course)", url: "https://pll.harvard.edu/course/cs50s-introduction-programming-python" },
            { label: "Official Python documentation", url: "https://docs.python.org/3/" },
            { label: "Python Developer Roadmap", url: "https://roadmap.sh/python" },
            { label: "FastAPI official docs", url: "https://fastapi.tiangolo.com" },
            { label: "Real Python tutorials", url: "https://realpython.com" },
            { label: "COMPUTER SCIENCE WITH PYTHON book by Sumita Arora (for Basics of SQL)", url:"https://www.ssgopalganj.in/online/Class%20XII/Comp/Computer%20science%20PYTHON%20book%20pdf%20for%20class%2012.pdf" },
        ],
        youtube: [
            { label: "Python fundamentals", url: "https://www.youtube.com/watch?v=rfscVS0vtbw" },
            { label: "Python full course for beginners", url: "https://www.youtube.com/results?search_query=python+full+course+for+beginners" },
            { label: "FastAPI tutorial", url: "https://www.youtube.com/results?search_query=fastapi+tutorial" },
            { label: "SQL full course with python", url: "https://youtu.be/7S_tz1z_5bA?si=-JKbX7P2ZwfReP1A" },
            { label: "Python projects with source code", url: "https://www.youtube.com/results?search_query=python+projects+with+source+code" },
            { label: "Fast API", url: "https://youtu.be/Lu8lXXlstvM?si=cNvGv_5MY_6hrCpF" }
        ]
    },

    "data analyst": {
        icon: "📊",
        description: "Data Analysts turn raw business data into decisions. They collect and clean data, explore it with SQL and Python, build dashboards, and present insights that help companies understand customers, operations and trends. It is the most common entry point into the wider data careers (data science, analytics engineering, BI leadership).",
        salary: "Indicative salary (India, 2025): ₹3.5–6 LPA for freshers (0–1 year), ₹5–12 LPA with 3+ years of experience, and ₹10–20 LPA for 5+ years — strong SQL, Python and Power BI/Tableau skills move you up each band.",
        highlights: [
            "Write SQL queries to extract, join and aggregate data from databases",
            "Clean and explore datasets with Python (pandas) or Excel",
            "Build interactive dashboards in Power BI or Excel",
            "Apply statistics: averages, distributions, correlation, A/B test basics",
            "Tell a clear story with data visualizations and presentations",
            "Work with stakeholders to define metrics and KPIs"
        ],
        skills: ["SQL", "Python", "Excel", "Power BI", "Statistics", "Data Visualization"],
        roadmap: [
            { title: "Excel & statistics foundation", text: "Pivot tables, lookup functions, descriptive statistics and chart types." },
            { title: "SQL deep dive", text: "Joins, GROUP BY, window functions on real datasets (practice on SQLBolt / PGExercises)." },
            { title: "Python for analysis", text: "pandas and matplotlib to clean, explore and visualize data." },
            { title: "Dashboards", text: "Build 2\u20133 Power BI or Excel dashboards on public datasets." },
            { title: "Portfolio & communication", text: "Publish case studies (Kaggle notebooks / GitHub) explaining the business insight, not just the code." }
        ],
        research: [
            { label: "Data Analyst Roadmap", url: "https://roadmap.sh/data-analyst" },
            { label: "Data science with python (Harvard course)", url: "https://pll.harvard.edu/course/introduction-data-science-python/2026-05" },
            { label: "Kaggle Learn (free micro-courses)", url: "https://www.kaggle.com/learn" },
            { label: "SQLBolt (interactive SQL)", url: "https://sqlbolt.com" },
            { label: "NPTEL data analytics courses", url: "https://nptel.ac.in" },
            { label: "Power Bi usecases", url: "https://www.microsoft.com/en-in/power-platform/products/power-bi#Use-cases" }
        ],
        youtube: [
            { label: "Excel ", url: "https://www.youtube.com/watch?v=Vl0H-qTclOg" },
            { label: "Data Analyst full course", url: "https://www.youtube.com/results?search_query=data+analyst+full+course" },
            { label: "SQL full course", url: "https://www.youtube.com/results?search_query=sql+full+course" },
            { label: "Power BI tutorial for beginners", url: "https://www.youtube.com/watch?v=VaOhNqNtGGE" },
            { label: "Pandas Python tutorial", url: "https://www.youtube.com/watch?v=gtjxAH8uaP0    " },
            { label: "Statistics", url: "https://www.youtube.com/watch?v=Vfo5le26IhY" }
        ]
    },

    "cyber security": {
        icon: "🛡️",
        description: "Cyber Security professionals protect systems, networks and data from attacks. The field spans network security, web application security, operating system hardening, and incident response. With India's digital economy expanding and CERT-In reporting lakhs of security incidents every year, demand for entry-level security analysts, SOC analysts and penetration testers keeps rising.",
        salary: "Indicative salary (India, 2025): ₹3.5–6 LPA for freshers (0–1 year), ₹6–12 LPA with 3+ years of experience, and ₹12–25 LPA for 5+ years — certifications like CompTIA Security+ and CEH add ₹1–3 LPA to starting packages.",
        highlights: [
            "Understand networking fundamentals: TCP/IP, DNS, routing, firewalls, VPNs",
            "Harden and monitor operating systems, especially Linux",
            "Test web applications against the OWASP Top 10 (injection, XSS, broken access control and more)",
            "Run network security scans and analyse traffic with tools like Nmap, Wireshark and Burp Suite",
            "Detect, respond to and document security incidents",
            "Automate security checks and log analysis with Python"
        ],
        skills: ["Networking", "Linux", "Operating Systems", "Web Application Security", "Network Security", "Python", "SIEM tools"],
        roadmap: [
            { title: "Networking fundamentals", text: "OSI/TCP-IP model, subnetting, common ports and protocols. Practice with Wireshark and Cisco Packet Tracer." },
            { title: "Operating systems & Linux", text: "File permissions, processes, users, logs and hardening basics on Linux." },
            { title: "Web & application security", text: "OWASP Top 10, SQL injection, XSS, authentication flaws. Practice legally on PortSwigger Web Security Academy and TryHackMe." },
            { title: "Network security & tools", text: "Nmap scanning, firewall rules, IDS/IPS concepts, SIEM dashboards." },
            { title: "Certify & specialize", text: "CompTIA Security+ or CEH, then choose a track: SOC analyst, penetration testing, or security engineering." }
        ],
        research: [
            { label: "Introduction to Cybersecurity (HARVARD COURSE)", url: "https://pll.harvard.edu/course/cs50s-introduction-cybersecurity" },
            { label: "Cyber Security Roadmap", url: "https://roadmap.sh/cybersecurity" },
            { label: "OWASP (Top 10 & standards)", url: "https://owasp.org" },
            { label: "TryHackMe (hands-on labs)", url: "https://tryhackme.com" },
            { label: "PortSwigger Web Security Academy", url: "https://portswigger.net/web-security" },
            { label: "CERT-In (Govt. of India)", url: "https://www.cert-in.org.in" }
        ],
        youtube: [
            { label: "Cyber-security channel :- Network chuck", url: "https://youtube.com/@networkchuck?si=U9s0C6HhjJt6mbL7" },
            { label: "Cyber Security full course", url: "https://www.youtube.com/results?search_query=cyber+security+full+course+for+beginners" },
            { label: "Complete networking course ", url: "https://youtu.be/fQbBPa0ADvs?si=bn6STQTE8KZ3LHMY" },
            { label: "Linux and O.S. for ethical hackers", url: "https://youtu.be/1hvVcEhcbLM?si=2FeEU1PjkzWPO6Qe" },
            { label: "OWASP Top 10 explained", url: "https://www.youtube.com/watch?v=Jzr0Jdnq_EI" },
            { label: "Complete Ethical hacking course", url: "https://youtube.com/playlist?list=PLIhvC56v63IIJZRa3lzK6IeBQOH_VFjUQ&si=iBeza2hWavgiGu7g" },
         
        ]
    },

    "ai and ml engineer": {
        icon: "🤖",
        description: "AI & ML Engineers build systems that learn from data — from classic machine-learning models to modern LLM-powered applications. The role combines strong Python skills, understanding of ML algorithms, and increasingly, working with large language models, prompt engineering and AI APIs. It is currently the fastest-growing and highest-paying entry-level tech role in India.",
        salary: "Indicative salary (India, 2025): ₹5–10 LPA for freshers (0–1 year) — the highest starting package among these roles — ₹10–20 LPA with 3+ years of experience, and ₹20–35 LPA for 5+ years, with GenAI/LLM specialists commanding a significant premium.",
        highlights: [
            "Train and evaluate machine learning models (regression, classification, clustering)",
            "Handle real datasets: cleaning, feature engineering, validation",
            "Build applications on top of large language models (LLMs) via APIs",
            "Use prompt engineering and RAG (retrieval-augmented generation) patterns",
            "Deploy models as REST APIs so other applications can use them",
            "Evaluate model quality, bias and safety"
        ],
        skills: ["Python", "Machine Learning", "SQL", "LLMs", "Prompt Engineering", "REST APIs", "NumPy / pandas / scikit-learn"],
        roadmap: [
            { title: "Python + data skills", text: "Solid Python, then NumPy, pandas and matplotlib for data handling." },
            { title: "Core machine learning", text: "Supervised/unsupervised algorithms, evaluation metrics, scikit-learn projects." },
            { title: "SQL & data pipelines", text: "Pull and prepare training data from databases." },
            { title: "LLMs & GenAI", text: "Prompt engineering, embeddings, RAG, and calling LLM APIs from Python." },
            { title: "Deploy & showcase", text: "Wrap a model behind a FastAPI endpoint and publish 2\u20133 end-to-end projects." }
        ],
        research: [
            { label: "AI / Data Scientist Roadmap", url: "https://roadmap.sh/ai-data-scientist" },
            { label: "Kaggle Learn & competitions", url: "https://www.kaggle.com/learn" },
            { label: "Hugging Face courses (LLMs)", url: "https://huggingface.co/learn" },
            { label: "AI / ML with python (INTRODUCTION)-(Harvard course)", url: "https://pll.harvard.edu/course/cs50s-introduction-artificial-intelligence-python" },
            { label: "AI / ML with python (Harvard course) ", url: "https://pll.harvard.edu/course/machine-learning-and-ai-python1" },
            { label: "Machine Learning Specialization (Andrew Ng)", url: "https://www.coursera.org/specializations/machine-learning-introduction" }
        ],
        youtube: [
            { label: "Machine Learning full course", url: "https://youtu.be/i_LwzRVP7bg?si=DmjCxe7yibllA_w2" },
            { label: "LLMs and Generative AI course", url: "https://www.youtube.com/watch?v=d4yCWBGFCEs" },
            { label: "Prompt engineering tutorial", url: "https://youtube.com/playlist?list=PLYio3GBcDKsPP2_zuxEp8eCulgFjI5a3g&si=d8_dgWVSbyPdOsmK" },
            { label: "AI projects with Python", url: "https://youtu.be/XZdY15sHUa8?si=4q3dDKE4Xr0m_Odl" },
            { label: "ML in python", url: "https://youtu.be/hDKCxebp88A?si=FNn282GNz71DGQj4" },
        ]
    },

    "cloud engineer": {
        icon: "☁️",
        description: "Cloud Engineers design, deploy and operate applications on platforms like AWS, Azure and Google Cloud. Almost every modern product runs in the cloud, making this one of the fastest-growing infrastructure roles in India \u2014 and a natural next step for anyone comfortable with Linux and networking.",
        salary: "Indicative salary (India, 2025): ₹4–7 LPA for freshers (0–1 year), ₹8–18 LPA with 3+ years of experience, and ₹20–35 LPA for 5+ years — AWS/Azure certifications typically add 20–35% to offers.",
        highlights: [
            "Provision compute, storage and networking on AWS, Azure or GCP",
            "Administer Linux servers, permissions and services",
            "Package and deploy applications in containers with Docker",
            "Automate infrastructure with scripts and infrastructure-as-code",
            "Build basic CI/CD pipelines for automated deployments",
            "Monitor systems, control cloud costs and apply security best practices"
        ],
        skills: ["Cloud (AWS / Azure / GCP)", "Linux", "Networking", "Docker", "CI/CD", "Scripting"],
        roadmap: [
            { title: "Linux & networking", text: "Command line, users, permissions, TCP/IP and DNS \u2014 the base everything sits on." },
            { title: "One cloud provider", text: "Pick AWS or Azure and work through core services \u2014 compute, storage, IAM, VPC \u2014 on the free tier." },
            { title: "Containers", text: "Build and run Docker images; deploy a small app in a container." },
            { title: "Automation", text: "Shell scripting, Terraform basics and a simple CI/CD pipeline." },
            { title: "Certify & ship", text: "AWS Solutions Architect Associate or Azure AZ-104, plus a deployed capstone project." }
        ],
        research: [
            { label: "DevOps / Cloud Roadmap", url: "https://roadmap.sh/devops" },
            { label: "AWS Training (free courses)", url: "https://aws.amazon.com/training" },
            { label: "Microsoft Azure training", url: "https://learn.microsoft.com/training/" },
            { label: "Google Cloud training", url: "https://cloud.google.com/learn/training" }
        ],
        youtube: [
            { label: "Cloud Computing full course", url: "https://www.youtube.com/results?search_query=cloud+computing+full+course" },
            { label: "AWS tutorial for beginners", url: "https://www.youtube.com/watch?v=SOTamWNgDKc    " },
            { label: "Docker tutorial", url: "https://youtu.be/pg19Z8LL06w?si=iOlti-Ldud362HC4" },
            { label: "Linux command line course", url: "https://www.youtube.com/results?search_query=linux+command+line+full+course" }
        ]
    }
};

const PROGRAM_DETAILS = {
    "full stack java development bootcamp": {
        icon: "☕",
        description: "A 6-month bootcamp that takes you from web fundamentals to a complete, deployable full-stack application using Java. You will learn the front end (HTML, CSS, JavaScript), the back end (Java, Spring Boot) and the database layer (SQL), finishing with a capstone project you can show to recruiters.",
        highlights: [
            "Build structured, responsive web pages with HTML5 and CSS3",
            "Add interactivity with core JavaScript",
            "Write object-oriented Java and use collections, streams and exception handling",
            "Create production-style REST APIs with Spring Boot and Spring Data JPA",
            "Design and query relational databases with SQL",
            "Complete a capstone full-stack project with Git version control"
        ],
        skills: ["HTML & CSS", "JavaScript", "Java", "Spring Boot", "SQL", "Git"],
        roadmap: [
            { title: "Month 1\u20132: Front-end foundations", text: "HTML, CSS layout (flexbox/grid), JavaScript basics and DOM manipulation." },
            { title: "Month 3: Core Java", text: "OOP, collections, generics, exception handling and clean code practices." },
            { title: "Month 4: Spring Boot", text: "REST controllers, services, repositories, validation and Spring Data JPA." },
            { title: "Month 5: Databases", text: "SQL schema design, joins, indexing and connecting MySQL/PostgreSQL." },
            { title: "Month 6: Capstone project", text: "Plan, build, test and deploy a complete full-stack application." }
        ],
        research: [
            { label: "Spring Boot guides", url: "https://spring.io/projects/spring-boot" },
            { label: "MDN Web Docs", url: "https://developer.mozilla.org" },
            { label: "Full Stack Roadmap", url: "https://roadmap.sh/full-stack" },
            { label: "NPTEL Java courses", url: "https://nptel.ac.in" }
        ],
        youtube: [
            { label: "Java Full Stack course", url: "https://www.youtube.com/results?search_query=java+full+stack+development+full+course" },
            { label: "Spring Boot for beginners", url: "https://www.youtube.com/results?search_query=spring+boot+tutorial+for+beginners" },
            { label: "JavaScript crash course", url: "https://www.youtube.com/results?search_query=javascript+crash+course" }
        ]
    },

    "python programming and database management": {
        icon: "🗄️",
        description: "A 4-month program focused on the two most reusable skills in tech: Python programming and database management with SQL. Ideal for roles like Python Developer, Data Analyst or as a foundation before moving into data science or AI.",
        highlights: [
            "Master Python syntax, data structures, functions and OOP",
            "Read, write and automate file and data processing tasks",
            "Design normalized relational databases",
            "Write SQL queries: joins, aggregations, subqueries and indexes",
            "Connect Python to MySQL/PostgreSQL and build small data apps",
            "Use Git and virtual environments like a professional developer"
        ],
        skills: ["Python", "SQL", "Database Design", "MySQL / PostgreSQL", "Git"],
        roadmap: [
            { title: "Month 1: Python core", text: "Variables, loops, functions, data structures and error handling." },
            { title: "Month 2: Python deep dive", text: "OOP, modules, file handling, standard library and testing basics." },
            { title: "Month 3: SQL & databases", text: "Schema design, joins, aggregation and practice on SQLBolt / PGExercises." },
            { title: "Month 4: Python + database projects", text: "Build data-driven apps (CRUD apps, report generators) connecting Python to a database." }
        ],
        research: [
            { label: "Official Python docs", url: "https://docs.python.org/3/" },
            { label: "SQLBolt (interactive SQL)", url: "https://sqlbolt.com" },
            { label: "PGExercises (PostgreSQL practice)", url: "https://pgexercises.com" },
            { label: "Real Python tutorials", url: "https://realpython.com" }
        ],
        youtube: [
            { label: "Python full course", url: "https://www.youtube.com/results?search_query=python+full+course+for+beginners" },
            { label: "SQL full course", url: "https://www.youtube.com/results?search_query=sql+full+course" },
            { label: "Python database projects", url: "https://www.youtube.com/results?search_query=python+mysql+project" }
        ]
    },

    "cloud engineering with aws and azure": {
        icon: "☁️",
        description: "A 5-month program on designing, deploying and operating applications in the cloud, with hands-on practice on both AWS and Azure. You will work with at least one major provider (AWS, Azure or GCP), learn Linux and networking basics, containers, and infrastructure-as-code — the skills behind Cloud Engineer and DevOps roles.",
        highlights: [
            "Understand cloud service models: IaaS, PaaS, SaaS",
            "Configure compute, storage, networking and identity services",
            "Work confidently on the Linux command line",
            "Deploy applications in containers with Docker",
            "Automate infrastructure with scripts and infrastructure-as-code",
            "Monitor, secure and control cloud costs"
        ],
        skills: ["Cloud (AWS / Azure / GCP)", "Linux", "Networking basics", "Docker", "CI/CD basics", "Scripting"],
        roadmap: [
            { title: "Month 1: Cloud fundamentals", text: "Shared responsibility model, global infrastructure, core services and free-tier accounts." },
            { title: "Month 2: Linux & networking", text: "Shell commands, users, permissions, DNS, TCP/IP and load balancers." },
            { title: "Month 3: Core cloud services", text: "Virtual machines, object storage, VPCs, IAM roles — on AWS or Azure." },
            { title: "Month 4: Containers & automation", text: "Docker images, containers, and a basic CI/CD pipeline." },
            { title: "Month 5: Capstone deployment", text: "Deploy a real application to the cloud with monitoring and security configured." }
        ],
        research: [
            { label: "AWS Training (free courses)", url: "https://aws.amazon.com/training" },
            { label: "Microsoft Azure training", url: "https://learn.microsoft.com/training/" },
            { label: "Google Cloud training", url: "https://cloud.google.com/learn/training" },
            { label: "DevOps / Cloud Roadmap", url: "https://roadmap.sh/devops" }
        ],
        youtube: [
            { label: "Cloud Computing full course", url: "https://www.youtube.com/results?search_query=cloud+computing+full+course" },
            { label: "AWS tutorial for beginners", url: "https://www.youtube.com/results?search_query=aws+tutorial+for+beginners" },
            { label: "Docker tutorial", url: "https://www.youtube.com/results?search_query=docker+tutorial+for+beginners" },
            { label: "Linux command line course", url: "https://www.youtube.com/results?search_query=linux+command+line+full+course" }
        ]
    },

    "applied data analytics": {
        icon: "📈",
        description: "A 5-month applied program that teaches you to clean, analyze and present data — the full workflow from raw dataset to business decision. You will use Excel, SQL, Python (pandas) and a dashboarding tool like Power BI, and graduate with portfolio case studies.",
        highlights: [
            "Perform analysis and reporting in Excel (pivot tables, lookups)",
            "Extract and join data from databases with SQL",
            "Clean and explore datasets with Python and pandas",
            "Apply descriptive statistics and spot misleading metrics",
            "Design interactive dashboards in Power BI",
            "Present findings as clear, actionable business recommendations"
        ],
        skills: ["Excel", "SQL", "Python", "pandas", "Power BI", "Statistics", "Data Visualization"],
        roadmap: [
            { title: "Month 1: Excel & statistics", text: "Pivot tables, charts, averages, distributions and correlation." },
            { title: "Month 2: SQL", text: "Joins, GROUP BY, window functions and practice datasets." },
            { title: "Month 3: Python for data", text: "pandas dataframes, cleaning missing values, grouping and visualization." },
            { title: "Month 4: Dashboards", text: "Power BI data models, DAX basics and publishing reports." },
            { title: "Month 5: Case studies", text: "Analyze 2\u20133 public datasets end to end and document your insights." }
        ],
        research: [
            { label: "Data Analyst Roadmap", url: "https://roadmap.sh/data-analyst" },
            { label: "Kaggle Learn", url: "https://www.kaggle.com/learn" },
            { label: "SQLBolt", url: "https://sqlbolt.com" },
            { label: "NPTEL analytics courses", url: "https://nptel.ac.in" }
        ],
        youtube: [
            { label: "Data Analytics full course", url: "https://www.youtube.com/results?search_query=data+analytics+full+course" },
            { label: "Power BI tutorial", url: "https://www.youtube.com/results?search_query=power+bi+tutorial+for+beginners" },
            { label: "Excel for data analysis", url: "https://www.youtube.com/results?search_query=excel+for+data+analysis" },
            { label: "pandas tutorial", url: "https://www.youtube.com/results?search_query=pandas+python+tutorial" }
        ]
    },

    "machine learning and generative ai specialization": {
        icon: "🧠",
        description: "A 5-month specialization covering machine learning fundamentals through to modern generative AI. You will train and evaluate classic ML models with Python, work with real datasets and SQL, and finish with LLMs — prompt engineering, APIs and retrieval-augmented applications.",
        highlights: [
            "Use Python, NumPy, pandas and matplotlib for ML workloads",
            "Train regression, classification and clustering models with scikit-learn",
            "Evaluate models with the right metrics and avoid overfitting",
            "Prepare data with SQL for training pipelines",
            "Work with large language models: prompting, embeddings and RAG",
            "Deploy a model as a REST API"
        ],
        skills: ["Python", "Machine Learning", "scikit-learn", "SQL", "LLMs", "Prompt Engineering", "REST APIs"],
        roadmap: [
            { title: "Month 1: Python for ML", text: "NumPy, pandas, matplotlib and data cleaning workflows." },
            { title: "Month 2: Machine learning core", text: "Supervised learning, model evaluation and scikit-learn projects." },
            { title: "Month 3: Advanced ML + SQL", text: "Unsupervised learning, feature engineering and pulling training data from databases." },
            { title: "Month 4: LLMs & GenAI", text: "Prompt engineering, LLM APIs, embeddings and building a RAG application." },
            { title: "Month 5: Capstone", text: "Build and deploy an end-to-end AI application (API + front-end)." }
        ],
        research: [
            { label: "Kaggle Learn", url: "https://www.kaggle.com/learn" },
            { label: "Hugging Face courses", url: "https://huggingface.co/learn" },
            { label: "ML Specialization (Andrew Ng)", url: "https://www.coursera.org/specializations/machine-learning-introduction" },
            { label: "AI / Data Scientist Roadmap", url: "https://roadmap.sh/ai-data-scientist" }
        ],
        youtube: [
            { label: "Machine Learning full course", url: "https://www.youtube.com/results?search_query=machine+learning+full+course" },
            { label: "Generative AI course", url: "https://www.youtube.com/results?search_query=generative+ai+course" },
            { label: "Prompt engineering", url: "https://www.youtube.com/results?search_query=prompt+engineering+tutorial" },
            { label: "scikit-learn tutorial", url: "https://www.youtube.com/results?search_query=scikit-learn+tutorial" }
        ]
    },

    "cyber security analyst track": {
        icon: "🔐",
        description: "A 10-month, in-depth program covering the full security stack: networking, operating systems, web & application security, and network security. The longer duration reflects how much foundation cyber security requires — by the end you will be prepared for entry-level SOC analyst and security testing roles and ready for certifications like CompTIA Security+.",
        highlights: [
            "Networking: TCP/IP, routing, switching, DNS, VPNs and firewalls",
            "Operating systems: Linux administration, permissions, processes and log analysis",
            "Web & application security: the OWASP Top 10, injection, XSS, broken authentication",
            "Network security: vulnerability scanning, IDS/IPS and traffic analysis with Wireshark and Nmap",
            "Hands-on practice in safe lab environments (TryHackMe, PortSwigger Academy)",
            "Incident response basics and security documentation"
        ],
        skills: ["Networking", "Linux", "Operating Systems", "Web Application Security", "Network Security", "Wireshark / Nmap / Burp Suite", "Python"],
        roadmap: [
            { title: "Months 1\u20133: Networking", text: "OSI and TCP/IP models, subnetting, protocols, and practice with Cisco Packet Tracer and Wireshark." },
            { title: "Months 4\u20135: Operating systems", text: "Linux command line, users and permissions, services, and reading system logs." },
            { title: "Months 6\u20137: Web & application security", text: "OWASP Top 10 vulnerabilities, exploitation in legal labs, and secure coding basics." },
            { title: "Months 8\u20139: Network security", text: "Scanning with Nmap, firewall configuration, SIEM concepts and incident handling." },
            { title: "Month 10: Capstone & certification prep", text: "Complete a security audit project and prepare for CompTIA Security+ or CEH." }
        ],
        research: [
            { label: "Cyber Security Roadmap", url: "https://roadmap.sh/cybersecurity" },
            { label: "OWASP Top 10", url: "https://owasp.org" },
            { label: "TryHackMe labs", url: "https://tryhackme.com" },
            { label: "PortSwigger Web Security Academy", url: "https://portswigger.net/web-security" },
            { label: "CERT-In (Govt. of India)", url: "https://www.cert-in.org.in" },
            { label: "NIELIT / FutureSkills Prime", url: "https://www.futureskillsprime.in" }
        ],
        youtube: [
            { label: "Cyber Security full course", url: "https://www.youtube.com/results?search_query=cyber+security+full+course+for+beginners" },
            { label: "Complete networking course", url: "https://www.youtube.com/results?search_query=complete+computer+networking+course" },
            { label: "Linux for security", url: "https://www.youtube.com/results?search_query=linux+for+ethical+hackers" },
            { label: "OWASP Top 10", url: "https://www.youtube.com/results?search_query=owasp+top+10+explained" },
            { label: "Nmap and Wireshark tutorials", url: "https://www.youtube.com/results?search_query=nmap+wireshark+tutorial" }
        ]
    }
};

function findRichDetail(type, name) {
    const key = normalizeKey(name);
    const map = type === "job" ? JOB_DETAILS : PROGRAM_DETAILS;
    return map[key] || null;
}

function buildRichDetailHTML(type, match, rich) {
    const isJob = type === "job";
    const icon = rich.icon || (isJob ? "\uD83D\uDE80" : "\uD83C\uDF93");

    document.title = (isJob ? match.title : match.name) + " \u2013 Tech Explorer";

    const subtitle = isJob
        ? "Skills from the industry dataset: " + match.skills
        : "Core skills: " + match.skill + " \u2022 Duration: " + match.duration;

    const skillChips = (rich.skills || [])
        .map(function (s) { return `<span class="tag detail-chip">${s}</span>`; })
        .join("");

    const highlights = (rich.highlights || [])
        .map(function (h) { return `<li>${h}</li>`; })
        .join("");

    const roadmap = (rich.roadmap || [])
        .map(function (r, i) {
            return `<div class="roadmap-step">
                <div class="roadmap-number">${i + 1}</div>
                <div class="roadmap-text"><strong>${r.title}</strong><p>${r.text}</p></div>
            </div>`;
        })
        .join("");

    const research = (rich.research || [])
        .map(function (r) {
            return `<a class="resource-link" href="${r.url}" target="_blank" rel="noopener">${r.label} \u2197</a>`;
        })
        .join("");

    const youtube = (rich.youtube || [])
        .map(function (y) {
            return `<a class="resource-link youtube" href="${y.url}" target="_blank" rel="noopener">\u25B6 ${y.label}</a>`;
        })
        .join("");

    const salary = rich.salary ? `
        <div class="detail-callout"><strong>Indicative salary:</strong> ${rich.salary}</div>` : "";

    return `
        <div class="detail-card rich">
            <div class="detail-hero">
                <div class="card-icon">${icon}</div>
                <div>
                    <span class="detail-type">${isJob ? "JOB ROLE" : "LEARNING PROGRAM"}</span>
                    <h2>${isJob ? match.title : match.name}</h2>
                    <p>${subtitle}</p>
                </div>
            </div>

            <div class="detail-columns">
                <div class="detail-col">
                    <h3 class="detail-heading">About</h3>
                    <p class="detail-desc">${rich.description}</p>
                    ${salary}

                    <h3 class="detail-heading">${isJob ? "What this role involves" : "What you will learn"}</h3>
                    <ul class="detail-list">${highlights}</ul>
                </div>

                <div class="detail-col">
                    <h3 class="detail-heading">Key skills</h3>
                    <div class="chip-row">${skillChips}</div>

                    <h3 class="detail-heading">${isJob ? "How to become one" : "Learning roadmap"}</h3>
                    <div class="roadmap">${roadmap}</div>
                </div>
            </div>

            <h3 class="detail-heading">Research & reading</h3>
            <div class="resource-grid">${research}</div>

            <h3 class="detail-heading">YouTube courses</h3>
            <div class="resource-grid">${youtube}</div>
        </div>
    `;
}


/* =====================================================
   SKILL ALIASES (handles backend spellings so the
   program finder still matches, e.g. "Cyber Scurity")
===================================================== */

const SKILL_ALIASES = {
    "cyber security": ["cyber scurity", "networking", "web & application security", "network security", "operating systems", "oparting systems"]
};

function programMatchesSkill(program, selectedSkill) {
    const haystack = (program.skill + " " + program.name).toLowerCase();
    if (haystack.includes(selectedSkill)) return true;

    const aliases = SKILL_ALIASES[selectedSkill] || [];
    return aliases.some(function (alias) {
        return haystack.includes(alias);
    });
}

async function loadDetailPage() {
    const container = document.getElementById("detailContainer");
    if (!container) return;

    const params = new URLSearchParams(window.location.search);
    const type = params.get("type");
    const key = params.get("key");

    if (!type || !key) {
        container.innerHTML = `
            <div class="detail-card">
                <h2>Item not found</h2>
                <p>This link is missing information about what to show.</p>
            </div>
        `;
        return;
    }

    const endpoint = type === "job" ? "jobs" : "programs";

    try {
        const response = await fetch(`http://localhost:8080/api/${endpoint}`);
        if (!response.ok) throw new Error("Server returned an error");

        const items = await response.json();
        const match = items.find(function (item) {
            const name = type === "job" ? item.title : item.name;
            return name === key;
        });

        if (!match) {
            container.innerHTML = `
                <div class="detail-card">
                    <h2>Not found</h2>
                    <p>We couldn't find that ${type === "job" ? "job role" : "program"}.</p>
                </div>
            `;
            return;
        }

        const rich = findRichDetail(type, type === "job" ? match.title : match.name);
        if (rich) {
            container.innerHTML = buildRichDetailHTML(type, match, rich);
        } else if (type === "job") {
            container.innerHTML = `
                <div class="detail-card">
                    <div class="card-icon">🚀</div>
                    <h2>${match.title}</h2>
                    <p>Skills required for this role:</p>
                    <span class="tag">${match.skills}</span>
                </div>
            `;
        } else {
            container.innerHTML = `
                <div class="detail-card">
                    <div class="card-icon">🎓</div>
                    <h2>${match.name}</h2>
                    <p>Core skill(s) covered: ${match.skill}</p>
                    <span class="tag">${match.duration}</span>
                </div>
            `;
        }
    } catch (error) {
        console.error("Detail error:", error);
        container.innerHTML = `
            <div class="detail-card">
                <h2>Unable to load details</h2>
                <p>Please start the Java backend and refresh the page.</p>
            </div>
        `;
    }
}






/* =====================================================
   ROLE BAR ANIMATION & COUNTER
===================================================== */

function animateDemandBars() {
    const items = document.querySelectorAll(".demand-item");

    items.forEach(function (item, index) {
        const fill = item.querySelector(".demand-fill");
        const counter = item.querySelector(".counter");

        if (!fill || !counter) return;

        const value = Number(item.getAttribute("data-value"));
        const width = fill.getAttribute("data-width");

        setTimeout(function () {
            fill.style.width = width;
            animateCounter(counter, value, 1000);
        }, 250 + (index * 120));
    });
}

function animateCounter(element, target, duration) {
    const startTime = performance.now();

    function update(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3);
        const value = Math.round(target * eased);

        element.textContent = value;

        if (progress < 1) {
            requestAnimationFrame(update);
        }
    }

    requestAnimationFrame(update);
}


/* =====================================================
   2D CIRCLE ANIMATION CHART
   (data mirrors "Most Requested Technology Skills")
===================================================== */

const SKILL_DISTRIBUTION = [
  { label: 'Python + SQL', percent: 26, color: '#635bff' },
  { label: 'Gen AI / LLM + ML', percent: 24, color: '#8b5cf6' },
  { label: 'Java Full Stack', percent: 22, color: '#0ea5e9' },
  { label: 'Data Analytics', percent: 12, color: '#10b981' },
  { label: 'Cyber Security', percent: 10, color: '#f59e0b' },
  { label: 'Cloud', percent: 6, color: '#f43f5e' }
];

let chartProgress = 0;
let hoveredIndex = -1;

function initCircleChart() {
  const canvas = document.getElementById('skillsChart');
  if (!canvas) return;

  const ctx = canvas.getContext('2d');
  const size = 400;

  // render crisp on high-DPI screens
  const dpr = window.devicePixelRatio || 1;
  canvas.width = size * dpr;
  canvas.height = size * dpr;
  canvas.style.width = size + 'px';
  canvas.style.height = size + 'px';
  ctx.scale(dpr, dpr);

  const centerX = size / 2;
  const centerY = size / 2;
  const outerRadius = 140;
  const innerRadius = 92;

  // build the legend under the chart
  const legend = document.getElementById('gaugeLegend');
  if (legend) {
    legend.innerHTML = SKILL_DISTRIBUTION.map(function (item, i) {
      return `<button type="button" class="legend-item" data-index="${i}">
        <span class="legend-dot" style="background:${item.color}"></span>
        <span class="legend-label">${item.label}</span>
        <span class="legend-value">${item.percent}%</span>
      </button>`;
    }).join('');

    legend.querySelectorAll('.legend-item').forEach(function (el) {
      el.addEventListener('mouseenter', function () {
        hoveredIndex = Number(el.getAttribute('data-index'));
        updateLegendHighlight();
        drawChart(1);
      });
      el.addEventListener('mouseleave', function () {
        hoveredIndex = -1;
        updateLegendHighlight();
        drawChart(1);
      });
    });
  }

  function updateLegendHighlight() {
    if (!legend) return;
    legend.querySelectorAll('.legend-item').forEach(function (el) {
      el.classList.toggle('active', Number(el.getAttribute('data-index')) === hoveredIndex);
    });
  }

  function easeOutCubic(t) {
    return 1 - Math.pow(1 - t, 3);
  }

  function drawChart(progress) {
    ctx.clearRect(0, 0, size, size);

    let startAngle = -Math.PI / 2;

    SKILL_DISTRIBUTION.forEach(function (item, index) {
      const sliceAngle = (item.percent / 100) * (Math.PI * 2) * easeOutCubic(progress);
      const endAngle = startAngle + sliceAngle;

      const isHovered = index === hoveredIndex;
      const currentOuterRadius = isHovered ? outerRadius + 7 : outerRadius;

      // draw arc segment
      ctx.save();
      if (isHovered) {
        ctx.shadowColor = 'rgba(30, 30, 70, 0.25)';
        ctx.shadowBlur = 18;
        ctx.shadowOffsetY = 4;
      }
      ctx.beginPath();
      ctx.arc(centerX, centerY, currentOuterRadius, startAngle, endAngle);
      ctx.arc(centerX, centerY, innerRadius, endAngle, startAngle, true);
      ctx.closePath();
      ctx.fillStyle = item.color;
      ctx.fill();

      // clean white separator between slices
      ctx.shadowColor = 'transparent';
      ctx.lineWidth = 3;
      ctx.strokeStyle = '#ffffff';
      ctx.stroke();
      ctx.restore();

      startAngle = endAngle;
    });

    // draw center hole
    ctx.beginPath();
    ctx.arc(centerX, centerY, innerRadius - 2, 0, Math.PI * 2);
    ctx.fillStyle = '#ffffff';
    ctx.fill();

    // subtle ring outline around the hole
    ctx.beginPath();
    ctx.arc(centerX, centerY, innerRadius - 2, 0, Math.PI * 2);
    ctx.lineWidth = 1;
    ctx.strokeStyle = '#eeeeF7';
    ctx.stroke();

    // center text
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';

    if (hoveredIndex !== -1) {
      ctx.fillStyle = SKILL_DISTRIBUTION[hoveredIndex].color;
      ctx.font = 'bold 38px Arial';
      ctx.fillText(SKILL_DISTRIBUTION[hoveredIndex].percent + '%', centerX, centerY - 12);

      ctx.fillStyle = '#66667a';
      ctx.font = 'bold 13px Arial';
      ctx.fillText(SKILL_DISTRIBUTION[hoveredIndex].label, centerX, centerY + 20);
    } else {
      ctx.fillStyle = '#17172b';
      ctx.font = 'bold 36px Arial';
      ctx.fillText('100%', centerX, centerY - 10);

      ctx.fillStyle = '#77778a';
      ctx.font = '600 13px Arial';
      ctx.fillText('Skill Demand', centerX, centerY + 20);
    }
  }

  function animate() {
    if (chartProgress < 1) {
      chartProgress += 0.02;
      drawChart(chartProgress);
      requestAnimationFrame(animate);
    } else {
      drawChart(1);
    }
  }

  canvas.addEventListener('mousemove', function (e) {
    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left - centerX;
    const y = e.clientY - rect.top - centerY;
    const distanceFromCenter = Math.sqrt(x * x + y * y);

    if (distanceFromCenter >= innerRadius && distanceFromCenter <= outerRadius + 10) {
      let angle = Math.atan2(y, x) + Math.PI / 2;
      if (angle < 0) angle += Math.PI * 2;

      let accumulatedAngle = 0;
      let found = -1;

      for (let i = 0; i < SKILL_DISTRIBUTION.length; i++) {
        const sliceAngle = (SKILL_DISTRIBUTION[i].percent / 100) * (Math.PI * 2);
        if (angle >= accumulatedAngle && angle <= accumulatedAngle + sliceAngle) {
          found = i;
          break;
        }
        accumulatedAngle += sliceAngle;
      }

      if (hoveredIndex !== found) {
        hoveredIndex = found;
        updateLegendHighlight();
        drawChart(1);
      }
    } else if (hoveredIndex !== -1) {
      hoveredIndex = -1;
      updateLegendHighlight();
      drawChart(1);
    }
  });

  canvas.addEventListener('mouseleave', function () {
    if (hoveredIndex !== -1) {
      hoveredIndex = -1;
      updateLegendHighlight();
      drawChart(1);
    }
  });

  animate();
}


/* =====================================================
   SCROLL INTERSECTION OBSERVER
===================================================== */

function setupInsightAnimation() {
  // Circle chart now lives in the hero - animate it as soon as it is visible
  const gaugeCard = document.querySelector(".skill-gauge-card");
  if (gaugeCard) {
    let chartAnimated = false;
    const chartObserver = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting && !chartAnimated) {
          chartAnimated = true;
          initCircleChart();
          chartObserver.disconnect();
        }
      });
    }, { threshold: 0.2 });

    chartObserver.observe(gaugeCard);
  }

  // Role demand bars still animate when the insights section is scrolled to
  const insights = document.querySelector(".insights-section");
  if (insights) {
    let barsAnimated = false;
    const barObserver = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting && !barsAnimated) {
          barsAnimated = true;
          animateDemandBars();
          barObserver.disconnect();
        }
      });
    }, { threshold: 0.25 });

    barObserver.observe(insights);
  }
}

function setupMenuLinks() {
    const links = document.querySelectorAll(".nav-links a");

    links.forEach(function (link) {
        link.addEventListener("click", function () {
            const navLinks = document.getElementById("navLinks");
            if (navLinks) {
                navLinks.classList.remove("open");
            }
        });
    });
}


/* =====================================================
   START EVERYTHING
===================================================== */

document.addEventListener("DOMContentLoaded", function () {
    animateChart();
    loadSkills();
    loadJobs();
    loadPrograms();
    loadDetailPage();
    setupInsightAnimation();
    setupMenuLinks();
    setupUIEffects();
});

/* =====================================================
   UI POLISH — navbar shadow + scroll reveal
===================================================== */

function setupUIEffects() {
    const navbar = document.querySelector(".navbar");
    if (navbar) {
        window.addEventListener("scroll", function () {
            navbar.classList.toggle("scrolled", window.scrollY > 10);
        }, { passive: true });
    }

    const revealItems = document.querySelectorAll(".reveal");
    if (!("IntersectionObserver" in window) || revealItems.length === 0) return;

    const observer = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
            if (entry.isIntersecting) {
                entry.target.classList.add("reveal-in");
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.1 });

    revealItems.forEach(function (el) {
        observer.observe(el);
    });
}