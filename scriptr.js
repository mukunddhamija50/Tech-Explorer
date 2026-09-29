const API = location.port === '8000' ? '' : 'http://127.0.0.1:8000';
let mySkills = [];
let currentTest = null;
let companyMatchResults = null;

// ---------------- navigation ----------------
function go(tab){
  document.querySelectorAll('nav button').forEach(b=>b.classList.toggle('active',b.dataset.tab===tab));
  document.querySelectorAll('section').forEach(s=>s.classList.toggle('active',s.id===tab));
  if(location.hash !== `#${tab}`) history.replaceState(null,'',`#${tab}`);
  if(tab==='tests' && !document.querySelector('#t_list .q')) loadTestList();
}
function toast(msg){const t=document.getElementById('toast');t.textContent=msg;t.classList.add('show');setTimeout(()=>t.classList.remove('show'),2600);}
function esc(s){return (s??'').toString().replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
async function api(path,opts={}){
  try{
    const r = await fetch(API+path,{headers:{'Content-Type':'application/json'},...opts});
    const j = await r.json().catch(()=>({detail:'network error'}));
    if(!r.ok) throw new Error(j.detail||r.statusText);
    return j;
  }catch(error){
    return offlineApi(path,opts);
  }
}
function requestBody(opts){
  try{return JSON.parse(opts.body||'{}');}catch(error){return {};}
}
function offlineApi(path,opts){
  const body=requestBody(opts);
  if(path==='/api/resume/scan') return offlineScan(body.text||'');
  if(path==='/api/resume/generate') return offlineResume(body);
  if(path==='/api/tests') return {tests:offlineTests.map(t=>({skill:t.skill,questions:t.questions.length,mcq:t.questions.length,code:0}))};
  if(path.match(/^\/api\/tests\/[^/]+\/submit$/)) return offlineGrade(path.split('/')[3],body.answers||[]);
  if(path.match(/^\/api\/tests\/[^/]+$/)) return offlineTest(decodeURIComponent(path.split('/')[3]));
  if(path==='/api/match/companies') return offlineMatch(body.skills||[]);
  if(path==='/api/match/gap') return offlineGap(body.skills||[],body.company||'');
  if(path.startsWith('/api/jobs')) {
    const queryString = path.includes('?') ? path.split('?')[1] : '';
    const params = new URLSearchParams(queryString);
    const query = (params.get('query') || '').trim().toLowerCase();
    const limit = Math.min(Number(params.get('limit') || 500), 500);
    const terms = query ? query.split(/[\n,]+/).map(term => term.trim()).filter(Boolean) : [];
    const filtered = offlineJobs.filter(job => {
      const text = `${job.title} ${job.company} ${(job.required_skills || job.skills || []).join(' ')}`.toLowerCase();
      return terms.length === 0 || terms.some(term => text.includes(term));
    });
    return {jobs: (filtered.length ? filtered : offlineJobs).slice(0, limit), source: 'seed'};
  }
  throw new Error('The SkillMatch server is unavailable. Start SkillMatch.bat from the project folder.');
}
const offlineSkillNames=['Python','Java','JavaScript','SQL','REST APIs','Docker','Git','Linux','React','Spring Boot','AWS','Data Structures'];
function offlineScan(text){
  const lower=text.toLowerCase();
  const names=offlineSkillNames.filter(skill=>lower.includes(skill.toLowerCase()));
  const emails=text.match(/[\w.+-]+@[\w.-]+\.[a-z]{2,}/ig)||[];
  const phones=text.match(/(?:\+?\d[\d\s-]{8,}\d)/g)||[];
  const score=Math.min(100,Math.max(25,names.length*8+(text.length>250?25:0)+(emails.length?10:0)));
  return {detected_skills:names.map(skill=>({skill,category:'Skills',evidence:[skill]})),skill_count:names.length,ats_score:score,
    seniority:/senior|lead|manager/i.test(text)?'Senior (5+ yrs)':'Entry-level (0-2 yrs)',education:[],contact:{emails,phones},
    findings:[{severity:'warn',issue:'Offline scan completed. Start the API server for deeper ATS analysis.'}]};
}
function offlineResume(payload){
  const skills=(payload.skills||[]).map(skill=>skill.trim()).filter(Boolean);
  const categorized={Skills:skills};
  const resume={header:{name:payload.name||'',email:payload.email||'',phone:payload.phone||'',target_role:payload.target_role||''},
    professional_summary:`${payload.name||'Candidate'} is a ${payload.target_role||'technology'} professional with experience in ${skills.join(', ')||'technology'}.`,
    skills:{categorized,flat:skills},experience:payload.experience||[],projects:payload.projects||[],education:payload.education||[],
    suggestions:['Add measurable outcomes and links to projects for a stronger ATS score.']};
  return {resume,download:{plain_text:`${resume.header.name}\n${resume.header.email}\n${resume.header.target_role}\nSkills: ${skills.join(', ')}`}};
}
const offlineTests=[{skill:'Python',questions:[{question:'Which keyword defines a function?',options:['func','def','function'],answer:1},{question:'What type is [1, 2]?',options:['list','tuple','set'],answer:0}]},{skill:'Java',questions:[{question:'Which keyword creates an object?',options:['new','make','create'],answer:0}]},{skill:'SQL',questions:[{question:'Which clause filters rows?',options:['WHERE','ORDER','GROUP'],answer:0}]}];
function offlineTest(skill){
  const test=offlineTests.find(item=>item.skill.toLowerCase()===skill.toLowerCase())||offlineTests[0];
  return {skill:test.skill,total:test.questions.length,questions:test.questions.map((q,index)=>({index,question:q.question,options:q.options}))};
}
function offlineGrade(skill,answers){
  const test=offlineTests.find(item=>item.skill.toLowerCase()===skill.toLowerCase())||offlineTests[0];
  const per_question=test.questions.map((q,index)=>{const correct=answers[index]===q.answer;return {question:q.question,correct,your_answer:q.options[answers[index]]||'Skipped',correct_answer:q.options[q.answer],explanation:correct?'Correct.':'Review this topic.'};});
  const correct=per_question.filter(q=>q.correct).length, percent=correct/test.questions.length*100;
  return {skill:test.skill,correct,total:test.questions.length,percent,band:percent>=75?'Strong':percent>=50?'Developing':'Beginner',advice:'Use the explanations to guide your next practice session.',per_question};
}
function offlineMatch(skills){
  const normalized=skills.map(skill=>skill.toLowerCase());
  const all=offlineJobs.map(job=>{const matched=job.skills.filter(skill=>normalized.includes(skill.toLowerCase()));const missing=job.skills.filter(skill=>!normalized.includes(skill.toLowerCase()));return {company:job.company,about:`${job.company} technology team`,fit_percent:Math.round(matched.length/job.skills.length*100),matched_skills:matched,missing_skills:missing};});
  return {all,ready_now:all.filter(job=>job.fit_percent>=60),close:all.filter(job=>job.fit_percent>=35&&job.fit_percent<60),stretch:all.filter(job=>job.fit_percent<35)};
}
function offlineGap(skills,company){
  const match=offlineMatch(skills).all.find(job=>job.company.toLowerCase()===company.toLowerCase())||offlineMatch(skills).all[0];
  return {company:match.company,current_fit_percent:match.fit_percent,projected_fit_percent_after_roadmap:Math.min(100,match.fit_percent+25),total_weeks:4,message:'Offline roadmap generated from the curated company profile.',roadmap:match.missing_skills.map((skill,index)=>({skill,start_week:index+1,duration_weeks:1,resource:'https://developer.mozilla.org/',verify_with_test:`Take the ${skill} test after studying.`}))};
}
function renderSkills(){
  const el=document.getElementById('myskills');
  el.innerHTML = mySkills.length ? mySkills.map(s=>`<span class="chip ok">${esc(s)}</span>`).join(' ')
    : '<i>none yet — scan your resume or add manually</i>';
}
function setSkills(list, silent){
  mySkills=[...new Set(list)];renderSkills();
  if(!silent) toast(`Skills updated (${mySkills.length})`);
}
function showSkillPicker(){
  const v = prompt('Comma-separated skills:', mySkills.join(', '));
  if(v!==null){ setSkills(v.split(',').map(s=>s.trim()).filter(Boolean), true); }
}

// ---------------- resume maker ----------------
function addExp(){
  const d=document.createElement('div');d.className='card';d.style.background='var(--bg2)';
  d.innerHTML=`<div class="row"><div><input placeholder="Role" class="e_role"></div><div><input placeholder="Company" class="e_co"></div><div><input placeholder="Duration (2023–2025)" class="e_dur"></div></div>
  <label>Highlights (one per line)</label><textarea class="e_hl" placeholder="Built REST APIs in Python serving 10k users/day
responsible for database design"></textarea>
  <br><button class="btn small ghost" onclick="this.parentElement.remove()">Remove</button>`;
  document.getElementById('m_exp').appendChild(d);
}
function addProj(){
  const d=document.createElement('div');d.className='card';d.style.background='var(--bg2)';
  d.innerHTML=`<div class="row"><div><input placeholder="Project name" class="p_name"></div></div>
  <label>Description</label><textarea class="p_desc" placeholder="News aggregator using Python + Django; deployed on AWS; 500 users."></textarea>
  <br><button class="btn small ghost" onclick="this.parentElement.remove()">Remove</button>`;
  document.getElementById('m_proj').appendChild(d);
}
function addEdu(){
  const d=document.createElement('div');d.className='card';d.style.background='var(--bg2)';
  d.innerHTML=`<div class="row"><div><input placeholder="Degree (B.Tech CSE)" class="d_deg"></div><div><input placeholder="Institute" class="d_ins"></div><div><input placeholder="Year" class="d_yr"></div></div>
  <br><button class="btn small ghost" onclick="this.parentElement.remove()">Remove</button>`;
  document.getElementById('m_edu').appendChild(d);
}
async function makeResume(){
  const payload={
    name:v('m_name'),email:v('m_email'),phone:v('m_phone'),target_role:v('m_role'),
    skills:v('m_skills').split(',').map(s=>s.trim()).filter(Boolean),
    experience:[...document.querySelectorAll('#m_exp > div')].map(d=>({
      role:d.querySelector('.e_role').value,company:d.querySelector('.e_co').value,duration:d.querySelector('.e_dur').value,
      highlights:d.querySelector('.e_hl').value.split('\n').map(x=>x.trim()).filter(Boolean)})),
    projects:[...document.querySelectorAll('#m_proj > div')].map(d=>({name:d.querySelector('.p_name').value,description:d.querySelector('.p_desc').value})),
    education:[...document.querySelectorAll('#m_edu > div')].map(d=>({degree:d.querySelector('.d_deg').value,institute:d.querySelector('.d_ins').value,year:d.querySelector('.d_yr').value})),
    extra_text:v('m_extra')
  };
  if(!payload.name) return toast('Name is required');
  try{
    const r=await api('/api/resume/generate',{method:'POST',body:JSON.stringify(payload)});
    renderResume(r);
    const found=r.resume.skills.flat; if(found.length) setSkills(found,true);
  }catch(e){
    toast(e instanceof TypeError ? 'Scanner API unavailable. Start SkillMatch.bat from the project folder.' : e.message);
  }
}
function v(id){return document.getElementById(id).value.trim();}
function renderResume(r){
  const res=r.resume,h=res.header;
  let skills='<div>'+Object.entries(res.skills.categorized).map(([c,ss])=>`<b>${esc(c)}:</b> ${ss.map(esc).join(', ')}`).join('<br>')+'</div>';
  let exp=res.experience.length?res.experience.map(e=>`<b>${esc(e.role||'')} — ${esc(e.company||'')}</b> (${esc(e.duration||'')})<ul>${(e.highlights||[]).map(h=>`<li>${esc(h)}</li>`).join('')}</ul>`).join(''):'';
  let proj=res.projects.length?`<ul>${res.projects.map(p=>`<li><b>${esc(p.name)}:</b> ${esc(p.description)}</li>`).join('')}</ul>`:'';
  let edu=res.education.length?`<ul>${res.education.map(d=>`<li>${esc(d.degree)}, ${esc(d.institute)} (${esc(d.year)})</li>`).join('')}</ul>`:'';
  document.getElementById('m_out').innerHTML=`
  <div class="card"><h2>Your resume</h2>
  <div class="resume-sheet">
    <h1>${esc(h.name)}</h1><div class="rh">${esc(h.email)} ${h.phone?' • '+esc(h.phone):''}</div>
    ${h.target_role?`<div class="rh"><b>Target:</b> ${esc(h.target_role)}</div>`:''}
    <h4>Summary</h4><p>${esc(res.professional_summary)}</p>
    <h4>Skills</h4>${skills}
    ${exp?`<h4>Experience</h4>${exp}`:''}
    ${proj?`<h4>Projects</h4>${proj}`:''}
    ${edu?`<h4>Education</h4>${edu}`:''}
  </div>
  <h3>💡 Suggestions</h3>
  ${res.suggestions.map(s=>`<div class="finding warn">${esc(s)}</div>`).join('')||'<span class="muted">No issues found.</span>'}
  <br><button class="btn alt" onclick="downloadResume()">⬇ Download as .txt</button>
  </div>`;
  window._lastResumeTxt=r.download.plain_text;
  window._lastResumePayload=r;
}
function downloadResume(){
  const b=new Blob([window._lastResumeTxt||''],{type:'text/plain'});
  const a=document.createElement('a');a.href=URL.createObjectURL(b);a.download='resume.txt';a.click();
}

// ---------------- scanner ----------------
function showSelectedPdf(){
  const file=document.getElementById('s_file').files[0];
  document.getElementById('s_file_name').textContent=file ? `${file.name} (${Math.ceil(file.size/1024)} KB)` : 'No PDF selected.';
}
async function scanResume(){
  const file=document.getElementById('s_file').files[0];
  if(!file) return toast('Choose a PDF resume first');
  if(file.type!=='application/pdf' && !file.name.toLowerCase().endsWith('.pdf')) return toast('Please choose a PDF file');
  const form=new FormData();
  form.append('file',file);
  try{
    const response=await fetch(API+'/api/resume/scan/file',{method:'POST',body:form});
    const r=await response.json().catch(()=>({detail:'network error'}));
    if(!response.ok) throw new Error(r.detail||response.statusText);
    const names=r.detected_skills.map(s=>s.skill);
    document.getElementById('s_out').innerHTML=`
    <div class="card">
      <h2>AI analysis results</h2>
      <p class="muted">${esc(r.filename||file.name)}</p>
      <div class="row" style="align-items:center">
        <div class="ring" style="--p:${r.ats_score}"><div>${r.ats_score}%</div></div>
        <div style="flex:1">
          <h3>Detected skills (${r.skill_count})</h3>
          ${names.map(s=>`<span class="chip ok">${esc(s)}</span>`).join(' ')}
          <h3>Seniority estimate</h3><span class="chip">${esc(r.seniority)}</span>
          ${r.education.length?`<h3>Education</h3>${r.education.map(esc).join(', ')}`:''}
          <h3>Contact</h3><span class="muted">${r.contact.emails.join(', ')||'—'} ${r.contact.phones.join(', ')||''}</span>
        </div>
      </div>
      <h3>ATS findings</h3>
      ${r.findings.map(f=>`<div class="finding ${f.severity}">${esc(f.issue)}</div>`).join('')}
      <br><button class="btn" onclick="go('match');matchCompanies()">Use these skills → match companies</button>
    </div>`;
    setSkills(names);
  }catch(e){
    toast(e instanceof TypeError ? 'Scanner API unavailable. Start SkillMatch.bat from the project folder.' : e.message);
  }
}

// ---------------- jobs ----------------
function buildOfflineJobs(){
  const companyCatalog = [
    {company:'Google', skills:['Python','SQL','Cloud','System Design']},
    {company:'Microsoft', skills:['Java','JavaScript','Azure','REST APIs']},
    {company:'Amazon', skills:['Python','SQL','AWS','ETL']},
    {company:'Meta', skills:['Python','JavaScript','System Design','Machine Learning']}, 
    {company:'Apple', skills:['Swift','iOS','Testing','Objective-C']},
    {company:'Netflix', skills:['Java','AWS','Microservices','Testing']},
    {company:'Uber', skills:['Go','Java','Kubernetes','System Design']},
    {company:'Airbnb', skills:['JavaScript','React','Node.js','AWS']},
    {company:'Stripe', skills:['Python','SQL','REST APIs','Testing']},
    {company:'Atlassian', skills:['JavaScript','TypeScript','React','Node.js']},
    {company:'GitHub', skills:['Go','Git','Docker','Linux']},
    {company:'GitLab', skills:['Ruby','Go','Linux','Docker']},
    {company:'Adobe', skills:['Python','SQL','Machine Learning','Testing']},
    {company:'Salesforce', skills:['Java','AWS','REST APIs','SQL']},
    {company:'ServiceNow', skills:['JavaScript','Java','REST APIs','SQL']},
    {company:'Oracle', skills:['Java','SQL','Python','Linux']},
    {company:'SAP', skills:['Java','SQL','Python','Cloud']},
    {company:'Intuit', skills:['Python','SQL','Machine Learning','REST APIs']},
    {company:'NVIDIA', skills:['C++','Python','CUDA','Machine Learning']},
    {company:'Qualcomm', skills:['C++','Python','Embedded','Linux']},
    {company:'IBM', skills:['Python','Java','SQL','Cloud']},
    {company:'PayPal', skills:['Java','Python','SQL','System Design']},
    {company:'Visa', skills:['Java','Python','SQL','REST APIs']},
    {company:'Mastercard', skills:['Java','Python','SQL','System Design']},
    {company:'JPMorgan Chase', skills:['Python','Java','SQL','Cloud']},
    {company:'Goldman Sachs', skills:['Python','Java','SQL','Machine Learning']},
    {company:'Walmart Global Tech', skills:['Java','Python','SQL','AWS']},
    {company:'Target', skills:['Java','Python','JavaScript','Cloud']},
    {company:'Dell Technologies', skills:['Python','Java','Linux','Cloud']},
    {company:'HP', skills:['Java','Python','Linux','REST APIs']},
    {company:'Cisco', skills:['Python','Java','Linux','Networking']},
    {company:'VMware', skills:['Python','Go','Linux','Kubernetes']},
    {company:'Datadog', skills:['Python','Go','AWS','Docker']},
    {company:'New Relic', skills:['Python','JavaScript','Go','Cloud']},
    {company:'Confluent', skills:['Java','Go','Kafka','System Design']},
    {company:'MongoDB', skills:['Python','JavaScript','NoSQL','System Design']},
    {company:'Snowflake', skills:['Python','SQL','Cloud','Data Analysis']},
    {company:'Databricks', skills:['Python','SQL','Spark','Machine Learning']},
    {company:'Palantir', skills:['Python','Java','SQL','Machine Learning']},
    {company:'Thoughtworks', skills:['Java','JavaScript','Python','Cloud']},
    {company:'Accenture', skills:['Java','Python','SQL','Cloud']},
    {company:'Deloitte', skills:['Python','SQL','Cloud','Machine Learning']},
    {company:'Cognizant', skills:['Java','Python','SQL','REST APIs']},
    {company:'Capgemini', skills:['Java','Python','SQL','Cloud']},
    {company:'Infosys', skills:['Java','Python','SQL','Azure']},
    {company:'TCS', skills:['Java','Python','SQL','Spring Boot']},
    {company:'Wipro', skills:['Java','Python','SQL','Cloud']},
    {company:'HCLTech', skills:['Java','Python','Cloud','Testing']},
    {company:'Tech Mahindra', skills:['Java','Python','SQL','AWS']},
    {company:'Persistent Systems', skills:['Java','Python','Microservices','Cloud']},
    {company:'Coforge', skills:['Java','Python','REST APIs','Cloud']},
    {company:'LTIMindtree', skills:['Java','Python','SQL','Cloud']},
    {company:'Razorpay', skills:['Java','Spring Boot','SQL','AWS']},
    {company:'Zoho', skills:['Java','JavaScript','SQL','Linux']},
    {company:'Freshworks', skills:['JavaScript','React','Node.js','AWS']},
    {company:'Zerodha', skills:['Python','Go','React','Linux']},
    {company:'Swiggy', skills:['Java','Go','React','Microservices']},
    {company:'PhonePe', skills:['Java','Spring Boot','SQL','Kubernetes']},
    {company:'CRED', skills:['Go','Java','React','AWS']},
    {company:'Flipkart', skills:['Java','Spring Boot','SQL','System Design']},
    {company:'Paytm', skills:['Java','Spring Boot','SQL','AWS']},
    {company:'Meesho', skills:['Python','React','AWS','Machine Learning']},
    {company:'Groww', skills:['Java','Spring Boot','React','AWS']},
    {company:'Myntra', skills:['Java','JavaScript','React','Machine Learning']},
    {company:'Zomato', skills:['Java','Go','AWS','System Design']},
    {company:'Navi', skills:['Java','Python','AWS','Machine Learning']},
    {company:'Dream11', skills:['Java','Node.js','AWS','System Design']},
    {company:'Postman', skills:['JavaScript','Node.js','React','AWS']},
    {company:'BrowserStack', skills:['JavaScript','Testing','Java','Docker']},
    {company:'Ola', skills:['Go','Java','AWS','Kubernetes']},
    {company:'Urban Company', skills:['Java','Node.js','React','System Design']},
    {company:'MakeMyTrip', skills:['Java','JavaScript','React','AWS']},
    {company:'Delhivery', skills:['Java','Python','SQL','AWS']},
    {company:'Jio', skills:['Java','Python','AWS','Networking']},
    {company:'Airtel', skills:['Java','Python','AWS','System Design']},
    {company:'Upstox', skills:['Python','Java','React','SQL']},
    {company:'ShareChat', skills:['Java','Python','React','Machine Learning']},
    {company:'Unacademy', skills:['Python','JavaScript','React','AWS']},
    {company:'Byju\'s', skills:['Python','JavaScript','Node.js','AWS']},
    {company:'Naukri', skills:['Java','Python','SQL','Node.js']},
    {company:'Indeed', skills:['Java','Python','SQL','Cloud']},
    {company:'LinkedIn', skills:['Java','Python','SQL','Machine Learning']},
    {company:'Reddit', skills:['Python','Go','JavaScript','SQL']},
    {company:'Shopify', skills:['Ruby','JavaScript','React','AWS']},
    {company:'Notion', skills:['TypeScript','React','Node.js','SQL']},
    {company:'Dropbox', skills:['Python','Go','JavaScript','System Design']},
    {company:'Slack', skills:['JavaScript','Node.js','React','Java']},
    {company:'Discord', skills:['Go','TypeScript','React','Node.js']},
    {company:'Figma', skills:['TypeScript','React','Node.js','Testing']},
    {company:'Canva', skills:['JavaScript','TypeScript','Node.js','AWS']},
    {company:'Pinterest', skills:['Python','JavaScript','Machine Learning','SQL']},
    {company:'Twitter', skills:['Scala','Java','Python','System Design']},
    {company:'Snapchat', skills:['Java','Python','Machine Learning','AWS']},
    {company:'ByteDance', skills:['Java','Python','C++','Machine Learning']},
    {company:'Nubank', skills:['Java','Python','React','SQL']},
    {company:'Plaid', skills:['Python','JavaScript','SQL','REST APIs']},
    {company:'Robinhood', skills:['Python','Java','JavaScript','SQL']},
    {company:'Coinbase', skills:['JavaScript','Python','Go','System Design']},
    {company:'Square', skills:['Java','JavaScript','Python','System Design']},
    {company:'ShopUp', skills:['Python','JavaScript','Node.js','AWS']},
    {company:'Gojek', skills:['Java','Go','Python','AWS']},
    {company:'Grab', skills:['Java','Python','Go','System Design']},
    {company:'Practo', skills:['Python','JavaScript','Node.js','AWS']},
    {company:'HealthifyMe', skills:['Python','JavaScript','Node.js','Machine Learning']},
    {company:'Cult.fit', skills:['Python','JavaScript','Node.js','AWS']},
    {company:'Spinny', skills:['Java','Python','React','Node.js']},
    {company:'CarDekho', skills:['Java','Python','JavaScript','Machine Learning']},
    {company:'OYO', skills:['Java','Python','Node.js','AWS']},
    {company:'NoBroker', skills:['Java','Python','Node.js','System Design']},
    {company:'HackerRank', skills:['Python','JavaScript','Node.js','Testing']},
    {company:'CodeChef', skills:['Python','JavaScript','Node.js','SQL']},
    {company:'GeeksforGeeks', skills:['JavaScript','Python','Node.js','Machine Learning']},
    {company:'OpenAI', skills:['Python','C++','Machine Learning','System Design']},
    {company:'Anthropic', skills:['Python','C++','Machine Learning','System Design']},
    {company:'Perplexity', skills:['Python','JavaScript','Machine Learning','SQL']},
    {company:'Kaggle', skills:['Python','SQL','Machine Learning','Data Analysis']},
    {company:'Coursera', skills:['Python','JavaScript','Node.js','SQL']},
    {company:'Udemy', skills:['Python','JavaScript','Node.js','AWS']},
    {company:'Akamai', skills:['Python','Java','Linux','Networking']},
    {company:'Cloudflare', skills:['Go','Rust','Python','Linux']},
    {company:'Fastly', skills:['Go','JavaScript','Python','Cloud']},
    {company:'HashiCorp', skills:['Go','Python','Linux','Docker']},
    {company:'Docker', skills:['Go','Python','Linux','Kubernetes']},
    {company:'Red Hat', skills:['Python','Java','Linux','Kubernetes']},
    {company:'Elastic', skills:['Java','Go','Python','Search']},
    {company:'SUSE', skills:['Python','Go','Linux','Cloud']},
    {company:'Nutanix', skills:['Python','Java','Go','Kubernetes']},
    {company:'Criteo', skills:['Python','Java','SQL','Machine Learning']},
    {company:'PubMatic', skills:['Java','Python','SQL','System Design']},
    {company:'Affle', skills:['Python','JavaScript','Machine Learning','SQL']},
    {company:'InMobi', skills:['Java','Python','Machine Learning','AWS']},
    {company:'OnePlus', skills:['Java','Kotlin','Android','Testing']},
    {company:'Samsung', skills:['Java','Kotlin','Android','C++']},
    {company:'Motorola', skills:['Java','Kotlin','Android','Testing']},
    {company:'BharatPe', skills:['Java','Python','SQL','REST APIs']},
    {company:'PolicyBazaar', skills:['Java','Python','Node.js','AWS']},
    {company:'Nykaa', skills:['Java','Python','React','Node.js']},
    {company:'PharmEasy', skills:['Java','Python','Node.js','REST APIs']},
    {company:'Gupshup', skills:['Java','Python','Node.js','REST APIs']},
    {company:'JioMart', skills:['Java','Python','Node.js','AWS']},
    {company:'Bharat Matrimony', skills:['Java','Python','SQL','Node.js']},
    {company:'Hexaware', skills:['Java','Python','SQL','Cloud']},
    {company:'Mphasis', skills:['Java','Python','SQL','Cloud']},
    {company:'Sutherland', skills:['Java','Python','SQL','Cloud']},
    {company:'EXL', skills:['Python','SQL','Machine Learning','Cloud']},
    {company:'Fractal', skills:['Python','SQL','Machine Learning','Cloud']},
    {company:'MuSigma', skills:['Python','SQL','Machine Learning','Statistics']},
    {company:'Tiger Analytics', skills:['Python','SQL','Machine Learning','Data Analysis']},
    {company:'Mindtree', skills:['Java','Python','SQL','Cloud']},
    {company:'L&T Technology Services', skills:['Java','Python','SQL','Cloud']},
    {company:'Cybage', skills:['Java','Python','JavaScript','Cloud']},
    {company:'Zeta', skills:['Java','Python','Node.js','AWS']},
    {company:'FIS', skills:['Java','Python','SQL','System Design']},
    {company:'Fiserv', skills:['Java','Python','REST APIs','AWS']},
    {company:'Netskope', skills:['Python','Go','Linux','Security']},
    {company:'Palo Alto Networks', skills:['Python','Go','Linux','Security']},
    {company:'CrowdStrike', skills:['Python','C++','Linux','Security']},
    {company:'Zscaler', skills:['Python','Java','Security','Cloud']},
    {company:'Verizon', skills:['Java','Python','Cloud','Networking']},
    {company:'AT&T', skills:['Java','Python','Cloud','Networking']},
    {company:'Comcast', skills:['Java','Python','Cloud','Linux']},
    {company:'Amdocs', skills:['Java','Python','REST APIs','Cloud']},
    {company:'Nokia', skills:['C++','Python','Networking','Linux']},
    {company:'Ericsson', skills:['C++','Python','Networking','Cloud']},
    {company:'Broadcom', skills:['C++','Python','Linux','System Design']},
    {company:'Intel', skills:['C++','Python','Linux','Cloud']},
    {company:'AMD', skills:['C++','Python','Linux','Data Structures']},
    {company:'KPMG', skills:['Python','SQL','Machine Learning','Cloud']},
    {company:'EY', skills:['Python','SQL','Cloud','Machine Learning']},
    {company:'PwC', skills:['Python','SQL','Cloud','Machine Learning']},
    {company:'Mercari', skills:['Java','Python','Go','System Design']},
    {company:'Rakuten', skills:['Java','Python','SQL','Cloud']},
    {company:'Bajaj Finserv', skills:['Java','Python','SQL','System Design']},
    {company:'Axis Bank', skills:['Java','Python','REST APIs','Cloud']},
    {company:'HDFC Bank', skills:['Java','Python','SQL','Cloud']},
    {company:'ICICI Bank', skills:['Java','Python','SQL','REST APIs']}
  ];

  const titles = ['Software Engineer','Backend Developer','Full Stack Engineer','Platform Engineer','Data Engineer','AI Engineer','DevOps Engineer','Product Engineer','Machine Learning Engineer','Cloud Engineer'];
  const cities = ['Bengaluru','Hyderabad','Pune','Chennai','Remote (India)','Mumbai','NCR'];
  const jobs = [];

  for(let i = 0; i < 100; i++){
    const company = companyCatalog[i % companyCatalog.length];
    const title = titles[(i + company.company.length) % titles.length];
    const location = cities[i % cities.length];
    jobs.push({
      id: `offline-${i}`,
      title,
      company: company.company,
      location,
      salary: `₹${(6 + ((i * 7) % 25))} - ₹${(24 + ((i * 13) % 55))} LPA`,
      published: `2026-09-${String((i % 20) + 10).padStart(2,'0')}`,
      required_skills: company.skills,
      skills: company.skills,
      url: null,
      source: 'seed'
    });
  }

  return jobs;
}

const offlineJobs = buildOfflineJobs();
function renderJobs(jobs){
  return jobs.length?jobs.map(j=>`
      <div class="job">
        <div class="t">${esc(j.title)}</div>
        <div class="c">${esc(j.company)} ${j.source==='seed'?'<span class="chip seed">Sample role</span>':''}</div>
        <div class="meta">📍 ${esc(j.location||'—')} ${j.salary?' • 💰 '+esc(j.salary):''} ${j.published?' • 📅 '+esc(j.published):''}</div>
        ${(j.required_skills||j.skills||[]).slice(0,8).map(s=>`<span class="chip">${esc(s)}</span>`).join(' ')}
        ${j.url?`<br><a href="${esc(j.url)}" target="_blank">View listing ↗</a>`:''}
      </div>`).join(''):'<div class="gate">No jobs found.</div>';
}
function jobMatchesQuery(job,terms){
  if(!terms.length) return true;
  const text=[job.title,job.company,job.location,...(job.required_skills||job.skills||[]).slice(0,8)].join(' ').toLowerCase();
  return terms.some(term=>text.includes(term.toLowerCase()));
}
async function loadJobs(){
  const q=document.getElementById('j_q').value.trim();
  const out=document.getElementById('j_out');out.innerHTML='<div class="gate">Fetching…</div>';
  try{
    const queries=(q?q.split(/[,\n]+/):['']).map(term=>term.trim()).filter(Boolean);
    const responses=await Promise.all((queries.length?queries:['']).map(term=>api('/api/jobs?query='+encodeURIComponent(term)+'&limit=500')));
    const jobs=[...new Map(responses.flatMap(response=>response.jobs).map(job=>[job.id||`${job.company}-${job.title}`,job])).values()].slice(0,500);
    const r={jobs,source:responses.some(response=>response.source&&response.source.indexOf('live-')===0)?'live-remotive':'seed'};
    const badge=document.getElementById('src_badge');
    badge.textContent=r.source==='seed'?'sample roles from 500-company catalog':(jobs.some(job=>job.source==='seed')?'live listings + sample roles':'live listings ✓');
    badge.className='chip '+(r.source==='seed'?'seed':'live');
    out.innerHTML=renderJobs(r.jobs.filter(job=>jobMatchesQuery(job,queries)));
  }catch(e){
    const queries=(q?q.split(/[,\n]+/):['']).map(term=>term.trim().toLowerCase()).filter(Boolean);
    const matches=offlineJobs.filter(job=>jobMatchesQuery(job,queries)).slice(0,100);
    document.getElementById('src_badge').textContent='offline curated dataset';
    document.getElementById('src_badge').className='chip seed';
    out.innerHTML=renderJobs(matches);
  }
}

// ---------------- matching ----------------
async function matchCompanies(){
  if(!mySkills.length) return toast('Add skills first — scan your resume or use the picker');
  const out=document.getElementById('mt_out');out.innerHTML='<div class="gate">Matching…</div>';
  try{
    companyMatchResults=await api('/api/match/companies',{method:'POST',body:JSON.stringify({skills:mySkills, limit:500})});
    renderCompanyMatches();
  }catch(e){out.innerHTML=`<div class="gate">${esc(e.message)}</div>`;}
}
function renderCompanyMatches(){
  if(!companyMatchResults) return;
  const query=document.getElementById('mt_q').value.trim().toLowerCase();
  const matches=company=>`${company.company} ${company.about} ${company.matched_skills.join(' ')} ${company.missing_skills.join(' ')}`.toLowerCase().includes(query);
  const groups=[
    {title:'✅ Ready now — 60%+ fit',companies:companyMatchResults.ready_now,ready:true},
    {title:'🟡 Close — small gaps',companies:companyMatchResults.close},
    {title:'🔴 Stretch — significant gaps',companies:companyMatchResults.stretch}
  ].map(group=>({...group,visible:group.companies.filter(matches)}));
  const count=groups.reduce((total,group)=>total+group.visible.length,0);
  const out=document.getElementById('mt_out');
  out.innerHTML=`<div class="card"><h3>Your skills</h3>${mySkills.map(skill=>`<span class="chip ok">${esc(skill)}</span>`).join(' ')}<div class="muted" style="margin-top:8px">Showing ${count} of ${companyMatchResults.all.length} ranked companies</div></div>`+
    (count?groups.filter(group=>group.visible.length).map(group=>`<div class="card"><h3>${group.title}</h3>${group.visible.map(company=>companyCard(company,group.ready)).join('')}</div>`).join(''):`<div class="gate">No companies match "${esc(query)}". Try another name or skill.</div>`);
}
function companyCard(c,ready){
  const requiredCount=c.matched_skills.length+c.missing_skills.length;
  return `<div class="gapcard">
    <div class="row" style="align-items:center">
      <div style="flex:1"><b>${esc(c.company)}</b><div class="muted">${esc(c.about)}</div></div>
      <div class="barline"><div class="bar"><div style="width:${c.fit_percent}%"></div></div><span class="pct">${c.fit_percent}%</span></div>
    </div>
    <div><b>Required skills (${requiredCount})</b></div>
    <div>${c.matched_skills.map(s=>`<span class="chip ok">${esc(s)} · you have</span>`).join(' ')}${c.missing_skills.map(s=>`<span class="chip miss">${esc(s)} · learn next</span>`).join(' ')}</div>
    ${ready?`<br><span class="chip live">Ready — apply now</span>`:`<br><button class="btn small" onclick="gapAnalysis('${esc(c.company)}')">📚 What do I need to develop?</button>`}
  </div>`;
}
async function gapAnalysis(company){
  const out=document.getElementById('mt_out');
  try{
    const r=await api('/api/match/gap',{method:'POST',body:JSON.stringify({skills:mySkills,company})});
    out.insertAdjacentHTML('beforeend',`
    <div class="card" id="gapcard">
      <h2>Roadmap for ${esc(r.company)} <button class="btn small ghost" style="float:right" onclick="document.getElementById('gapcard').remove()">✕</button></h2>
      <p class="sub">${esc(r.message)}</p>
      <div class="row" style="align-items:center;margin:10px 0">
        <span class="muted">Now</span><div class="bar"><div style="width:${r.current_fit_percent}%"></div></div><b>${r.current_fit_percent}%</b>
      </div>
      <div class="row" style="align-items:center;margin:10px 0">
        <span class="muted">After roadmap (~${r.total_weeks} wks)</span><div class="bar"><div style="width:${r.projected_fit_percent_after_roadmap}%"></div></div><b>${r.projected_fit_percent_after_roadmap}%</b>
      </div>
      ${r.roadmap.length?`<h3>Learning roadmap</h3>${r.roadmap.map(s=>`
        <div class="week"><span class="wk">Week ${s.start_week}+ (${s.duration_weeks}w)</span>
          <div><b>${esc(s.skill)}</b> — <a class="link" href="${esc(s.resource)}" target="_blank">free resource ↗</a><br>
          <span class="muted">${esc(s.verify_with_test)}</span></div></div>`).join('')}`:'<div class="chip live">No gaps — every required skill is already in your profile!</div>'}
    </div>`);
    out.lastElementChild.scrollIntoView({behavior:'smooth'});
  }catch(e){toast(e.message);}
}

// ---------------- tests ----------------
async function loadTestList(){
  try{
    const r=await api('/api/tests');
    document.getElementById('t_list').innerHTML=r.tests.map(t=>`
      <div class="gapcard" style="display:flex;gap:14px;align-items:center;flex-wrap:wrap">
        <div style="flex:1"><b>${esc(t.skill)}</b><div class="muted">${t.questions} questions — ${t.mcq} MCQ + ${t.code} code-output</div></div>
        <button class="btn small" onclick="startTest('${esc(t.skill)}')">Start test</button>
      </div>`).join('');
  }catch(e){toast(e.message);}
}
async function startTest(skill){
  try{
    currentTest=await api('/api/tests/'+encodeURIComponent(skill));
    currentTest.answers=new Array(currentTest.total).fill(null);
    renderQuiz();
  }catch(e){toast(e.message);}
}
function renderQuiz(){
  const t=currentTest;
  document.getElementById('t_out').innerHTML=`
  <div class="card"><h2>${esc(t.skill)} test</h2>
  ${t.questions.map(q=>`
    <div class="q">
      <div class="qt">Q${q.index+1}. ${esc(q.question)}</div>
      ${q.code?`<pre>${esc(q.code)}</pre>`:''}
      ${q.options.map((o,i)=>`<label class="opt" id="opt_${q.index}_${i}" onclick="pick(${q.index},${i})">${esc(o)}</label>`).join('')}
    </div>`).join('')}
  <button class="btn" onclick="submitTest()">Submit test</button>
  <button class="btn ghost" onclick="cancelTest()">Cancel</button></div>`;
  go('tests');
  document.getElementById('t_out').scrollIntoView({behavior:'smooth'});
}
function pick(qi,oi){
  currentTest.answers[qi]=oi;
  for(let i=0;i<currentTest.questions[qi].options.length;i++)
    document.getElementById(`opt_${qi}_${i}`).classList.toggle('sel',i===oi);
}
function cancelTest(){currentTest=null;document.getElementById('t_out').innerHTML='';}
async function submitTest(){
  if(currentTest.answers.includes(null) && !confirm('Some questions are skipped. Submit anyway?')) return;
  try{
    const r=await api(`/api/tests/${encodeURIComponent(currentTest.skill)}/submit`,{method:'POST',body:JSON.stringify({answers:currentTest.answers})});
    const band=r.percent>=75?'ok':(r.percent>=50?'':'miss');
    document.getElementById('t_out').innerHTML=`
    <div class="card">
      <h2>${esc(r.skill)} test result</h2>
      <div class="row" style="align-items:center">
        <div class="ring" style="--p:${r.percent}"><div>${r.percent}%</div></div>
        <div style="flex:1">
          <span class="chip ${band||''}">${esc(r.band)}</span>
          <p class="muted" style="margin-top:8px">${esc(r.advice)}</p>
          <p class="muted">${r.correct} / ${r.total} correct</p>
        </div>
      </div>
      <h3>Review</h3>
      ${r.per_question.map((q,i)=>`
        <div class="q">
          <div class="qt">Q${i+1}. ${esc(q.question)} ${q.correct?'<span class="chip ok">✓</span>':'<span class="chip miss">✗</span>'}</div>
          <div class="muted">Your answer: <b>${esc(q.your_answer)}</b>${q.correct?'':` &nbsp;→&nbsp; Correct: <b style="color:var(--ok)">${esc(q.correct_answer)}</b>`}</div>
          <div class="muted" style="margin-top:4px">💡 ${esc(q.explanation)}</div>
        </div>`).join('')}
      <button class="btn alt" onclick="addVerified('${esc(r.skill)}',${r.percent})">Add ${esc(r.skill)} ${r.percent>=75?'✓ ':''}to my skills</button>
      <button class="btn ghost" onclick="cancelTest()">Back to tests</button>
    </div>`;
    document.getElementById('t_out').scrollIntoView({behavior:'smooth'});
    window._lastResult=r;
  }catch(e){toast(e.message);}
}
function addVerified(skill,pct){
  if(pct>=75){ if(!mySkills.includes(skill)) setSkills([...mySkills,skill]); else toast(skill+' already in your skills'); }
  else toast(`You scored ${pct}% — study first, 75%+ adds it as a verified skill`);
}

renderSkills();
document.getElementById('mt_q').addEventListener('input',renderCompanyMatches);
document.getElementById('j_q').addEventListener('keydown',event=>{
  if(event.key==='Enter') loadJobs();
});
const initialTab = location.hash.slice(1);
if(document.getElementById(initialTab) && document.querySelector(`nav button[data-tab="${initialTab}"]`)) go(initialTab);
