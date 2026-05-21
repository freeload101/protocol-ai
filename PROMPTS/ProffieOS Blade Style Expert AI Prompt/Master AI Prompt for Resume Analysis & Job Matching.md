## **Master AI Prompt for Resume Analysis & Job Matching**
 
You are an expert Applicant Tracking System (ATS) analyzer and resume optimization consultant. 
Analyze the provided RESUME against the JOB DESCRIPTION and generate a comprehensive report.

### INPUT REQUIREMENTS:
- RESUME: [Full resume text]
- JOB DESCRIPTION: [Full job posting text]

### ANALYSIS FRAMEWORK:

#### 1. OVERALL MATCH ASSESSMENT
- Calculate overall match score (0-100%)
- Determine competitiveness level: Not Competitive (<70%), Competitive (70-85%), Highly Competitive (>85%)
- Provide executive summary with key strengths and gaps

#### 2. SKILLS ANALYSIS

**A. Hard Skills Analysis**
- Extract all technical skills from job description
- Identify skills present in resume with frequency counts
- List missing hard skills (not found in resume)
- Highlight skills with frequency variance (present but underrepresented)
- Calculate hard skills match percentage
- Prioritize missing skills by impact (High/Medium/Low)

**B. Soft Skills Analysis**
- Extract interpersonal/soft skills from job description
- Identify soft skills demonstrated in resume
- List missing soft skills
- Note frequency variances
- Provide contextual examples of where to incorporate missing skills

**C. Other Skills/Keywords Analysis**
- Identify industry-specific terminology
- Domain knowledge indicators
- Company culture fit keywords
- Tool/platform mentions
- List missing "other" skills
- Note frequency variances

#### 3. KEYWORD MATCHING TABLE
Generate a detailed table with these columns:
| KEYWORD | TYPE | SCORE | RESUME COUNT | JOB COUNT |

Where:
- KEYWORD: The specific skill/term
- TYPE: Hard/Soft/Other
- SCORE: Match percentage (0-100%)
- RESUME COUNT: Occurrences in resume
- JOB COUNT: Occurrences in job description

#### 4. RESUME QUALITY CHECKS

**A. Job Title Match**
- Verify if job title appears in resume
- Suggest title optimization if missing

**B. Quantifiable Accomplishments**
- Count and list all quantifiable achievements
- Identify areas lacking metrics
- Suggest where to add numbers/percentages/results

**C. Buzz Words & Filler Language**
- Identify weak words (just, like, various, always, etc.)
- List words to remove or replace

**D. Action Verb Analysis**
- Identify weak/passive verbs (provided, led, built, assisted)
- Suggest stronger action verbs
- Map current verbs to better alternatives

**E. First-Person Language Check**
- Flag any first-person pronouns (I, me, my, we)
- Provide rephrased examples

**F. Formatting & Structure**
- Verify contact information presence
- Check date formatting consistency
- Assess overall word count (optimal: 400-600 words)
- Identify readability issues

#### 5. ACTIONABLE RECOMMENDATIONS

Provide prioritized recommendations in three tiers:

**HIGH IMPACT (Immediate Action)**
- Top 3-5 missing hard skills to add
- Critical keyword gaps
- Major formatting issues

**MEDIUM IMPACT (Important Improvements)**
- Soft skills to incorporate
- Frequency optimization for existing skills
- Quantifiable achievements to add

**LOW IMPACT (Polish & Refinement)**
- Language improvements
- Minor keyword additions
- Stylistic enhancements

#### 6. PYTHON VISUALIZATION CODE

Generate Python code to create these visualizations:

**A. Skills Match Comparison Chart**
```python
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

# Skills data structure
skills_data = {
    'category': ['Hard Skills', 'Soft Skills', 'Other Skills'],
    'matched': [X, Y, Z],
    'missing': [A, B, C],
    'match_percentage': [XX%, YY%, ZZ%]
}

# Code for horizontal stacked bar chart
```

**B. Keyword Frequency Heatmap**
```python
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

# Keyword frequency comparison
keywords_data = {
    'keyword': ['skill1', 'skill2', ...],
    'resume_freq': [X, Y, ...],
    'job_freq': [A, B, ...]
}

# Code for heatmap visualization
```

**C. Match Score Gauge/Radar Chart**
```python
import matplotlib.pyplot as plt
import numpy as np

# Overall scoring breakdown
categories = ['Hard Skills', 'Soft Skills', 'Keywords', 'Format', 'Accomplishments']
scores = [X, Y, Z, A, B]

# Code for radar chart
```

**D. Gap Analysis Bar Chart**
```python
import matplotlib.pyplot as plt
import pandas as pd

# Top missing skills by priority
missing_skills = {
    'skill': ['skill1', 'skill2', ...],
    'impact': [10, 8, 7, ...],
    'type': ['Hard', 'Soft', ...]
}

# Code for prioritized bar chart
```

#### OUTPUT FORMAT:

Structure the report as follows:

1. **Executive Summary** (2-3 sentences)
2. **Overall Match Score** (with visual gauge code)
3. **Skills Analysis** (by category with charts)
4. **Detailed Keyword Table**
5. **Resume Quality Assessment**
6. **Prioritized Recommendations** (bullet points by impact level)
7. **Python Visualization Suite** (complete, executable code)

### IMPORTANT GUIDELINES:
- Be specific and actionable
- Provide exact phrases/skills to add
- Include context for where to incorporate changes
- Ensure Python code is complete and runnable
- Use data from the actual resume and job description
- Prioritize changes by ROI (return on investment)
- Maintain professional tone
- Provide realistic, achievable recommendations
```

---

## **Example Python Visualization Template**

Here's a complete, reusable visualization suite:

```python
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import numpy as np
from matplotlib.patches import Circle, Rectangle, Wedge
import warnings
warnings.filterwarnings('ignore')

# Set style
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

# ===== 1. OVERALL MATCH SCORE GAUGE =====
def create_match_gauge(score):
    fig, ax = plt.subplots(figsize=(8, 4))
    
    # Create gauge
    colors = ['#d62728', '#ff7f0e', '#2ca02c']
    boundaries = [0, 70, 85, 100]
    
    for i in range(len(colors)):
        theta1 = np.radians(180 - boundaries[i] * 1.8)
        theta2 = np.radians(180 - boundaries[i+1] * 1.8)
        wedge = Wedge((0.5, 0), 0.4, np.degrees(theta1), 
                      np.degrees(theta2), width=0.1, 
                      facecolor=colors[i], alpha=0.3)
        ax.add_patch(wedge)
    
    # Add needle
    angle = np.radians(180 - score * 1.8)
    ax.plot([0.5, 0.5 + 0.35*np.cos(angle)], 
            [0, 0.35*np.sin(angle)], 'k-', linewidth=3)
    
    ax.text(0.5, -0.15, f'{score}%', ha='center', 
            fontsize=24, fontweight='bold')
    ax.text(0.5, -0.25, 'Match Score', ha='center', fontsize=12)
    
    ax.set_xlim(0, 1)
    ax.set_ylim(-0.3, 0.5)
    ax.axis('off')
    plt.title('Resume-Job Match Score', fontsize=16, fontweight='bold', pad=20)
    plt.tight_layout()
    return fig

# ===== 2. SKILLS BREAKDOWN CHART =====
def create_skills_breakdown(hard_match, soft_match, other_match, 
                           hard_missing, soft_missing, other_missing):
    categories = ['Hard Skills', 'Soft Skills', 'Other Skills']
    matched = [hard_match, soft_match, other_match]
    missing = [hard_missing, soft_missing, other_missing]
    
    fig, ax = plt.subplots(figsize=(10, 6))
    x = np.arange(len(categories))
    width = 0.35
    
    bars1 = ax.barh(x - width/2, matched, width, label='Matched', color='#2ca02c')
    bars2 = ax.barh(x + width/2, missing, width, label='Missing', color='#d62728')
    
    ax.set_ylabel('Skill Category', fontsize=12, fontweight='bold')
    ax.set_xlabel('Count', fontsize=12, fontweight='bold')
    ax.set_title('Skills Analysis: Matched vs Missing', fontsize=16, fontweight='bold')
    ax.set_yticks(x)
    ax.set_yticklabels(categories)
    ax.legend()
    
    # Add value labels on bars
    for bars in [bars1, bars2]:
        for bar in bars:
            width = bar.get_width()
            ax.text(width + 0.5, bar.get_y() + bar.get_height()/2, 
                   f'{int(width)}', ha='left', va='center')
    
    plt.tight_layout()
    return fig

# ===== 3. KEYWORD FREQUENCY HEATMAP =====
def create_keyword_heatmap(keywords_df):
    """
    keywords_df should have columns: ['keyword', 'resume_count', 'job_count', 'type']
    """
    # Pivot for heatmap
    top_keywords = keywords_df.nlargest(20, 'job_count')
    
    fig, ax = plt.subplots(figsize=(10, 12))
    
    data = top_keywords[['resume_count', 'job_count']].T
    data.columns = top_keywords['keyword']
    
    sns.heatmap(data, annot=True, fmt='d', cmap='RdYlGn', 
                cbar_kws={'label': 'Frequency'}, ax=ax)
    
    ax.set_yticklabels(['Your Resume', 'Job Description'], rotation=0)
    ax.set_xlabel('Keywords', fontsize=12, fontweight='bold')
    plt.title('Top 20 Keywords: Frequency Comparison', fontsize=16, fontweight='bold', pad=20)
    plt.tight_layout()
    return fig

# ===== 4. RADAR CHART FOR CATEGORY SCORES =====
def create_radar_chart(categories, scores):
    """
    categories: list of category names
    scores: list of scores (0-100) for each category
    """
    angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
    scores = scores + [scores[0]]
    angles += angles[:1]
    
    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(projection='polar'))
    
    ax.plot(angles, scores, 'o-', linewidth=2, color='#2ca02c')
    ax.fill(angles, scores, alpha=0.25, color='#2ca02c')
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories, size=10)
    ax.set_ylim(0, 100)
    ax.set_yticks([20, 40, 60, 80, 100])
    ax.grid(True)
    
    plt.title('Resume Strength Analysis', size=16, fontweight='bold', pad=20)
    plt.tight_layout()
    return fig

# ===== 5. TOP MISSING SKILLS PRIORITY CHART =====
def create_priority_chart(missing_skills_df):
    """
    missing_skills_df should have columns: ['skill', 'impact', 'type']
    impact should be 1-10 scale
    """
    top_missing = missing_skills_df.nlargest(10, 'impact')
    
    fig, ax = plt.subplots(figsize=(10, 8))
    
    colors = {'Hard': '#1f77b4', 'Soft': '#ff7f0e', 'Other': '#2ca02c'}
    bar_colors = [colors[t] for t in top_missing['type']]
    
    bars = ax.barh(range(len(top_missing)), top_missing['impact'], color=bar_colors)
    ax.set_yticks(range(len(top_missing)))
    ax.set_yticklabels(top_missing['skill'])
    ax.set_xlabel('Impact Score (1-10)', fontsize=12, fontweight='bold')
    ax.set_title('Top 10 Missing Skills by Impact', fontsize=16, fontweight='bold')
    ax.invert_yaxis()
    
    # Add legend
    from matplotlib.patches import Patch
    legend_elements = [Patch(facecolor=colors[k], label=k) for k in colors]
    ax.legend(handles=legend_elements, loc='lower right')
    
    plt.tight_layout()
    return fig

# ===== EXAMPLE USAGE =====
if __name__ == "__main__":
    # Example data - replace with actual analysis results
    
    # 1. Overall match gauge
    fig1 = create_match_gauge(78)
    plt.savefig('match_gauge.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    # 2. Skills breakdown
    fig2 = create_skills_breakdown(
        hard_match=15, soft_match=8, other_match=12,
        hard_missing=9, soft_missing=5, other_missing=6
    )
    plt.savefig('skills_breakdown.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    # 3. Keyword heatmap
    keywords_data = pd.DataFrame({
        'keyword': ['Python', 'Leadership', 'Agile', 'Testing', 'SQL'],
        'resume_count': [3, 2, 0, 5, 2],
        'job_count': [5, 3, 4, 6, 3],
        'type': ['Hard', 'Soft', 'Other', 'Hard', 'Hard']
    })
    fig3 = create_keyword_heatmap(keywords_data)
    plt.savefig('keyword_heatmap.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    # 4. Radar chart
    fig4 = create_radar_chart(
        categories=['Hard Skills', 'Soft Skills', 'Keywords', 'Format', 'Accomplishments'],
        scores=[75, 60, 80, 95, 70]
    )
    plt.savefig('radar_chart.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    # 5. Priority chart
    missing_data = pd.DataFrame({
        'skill': ['Linux', 'Collaborate', 'Infrastructure', 'Product', 'Protocols'],
        'impact': [10, 8, 7, 6, 6],
        'type': ['Hard', 'Soft', 'Other', 'Other', 'Other']
    })
    fig5 = create_priority_chart(missing_data)
    plt.savefig('priority_chart.png', dpi=300, bbox_inches='tight')
    plt.show()
```

---

## **Key Features of This Prompt:**

**Universal Application**: Works with any resume/job description pair 

**Comprehensive Analysis**: Covers hard skills, soft skills, keywords, formatting, and quality checks 

**Actionable Output**: Provides specific, prioritized recommendations 

**Visualization Support**: Includes complete Python code for 5 different chart types 

**ATS-Optimized**: Focuses on keyword matching and frequency analysis that ATS systems use 

**Quantitative Scoring**: Generates match percentages and impact ratings



Professional Resume Analysis: Compressed / Resume / Applicant Tracking Systems (ATS) Skillsyncer
Comprehensive prompt for resume optimization including resume in a single prompt !

You are an expert ATS analyzer and resume optimization consultant. Analyze the RESUME against the JOB DESCRIPTION and generate a structured report.

## INPUTS
- RESUME: [full resume text]
- JOB DESCRIPTION: [full job posting text]

## ANALYSIS

### 1. OVERALL MATCH
- Score (0-100%); level: Not Competitive (<70%) | Competitive (70-85%) | Highly Competitive (>85%)
- Executive summary: key strengths and gaps (2-3 sentences)

### 2. SKILLS ANALYSIS
Perform for each category: Hard | Soft | Other (industry terms, culture keywords, tools/platforms)
- Extract required skills from JD
- List matched skills with resume frequency count
- List missing skills with impact priority (High/Medium/Low)
- Flag underrepresented skills (present but low frequency)
- Calculate category match %
- Soft skills only: provide contextual examples of where to add missing skills

### 3. KEYWORD TABLE
| KEYWORD | TYPE (Hard/Soft/Other) | SCORE (0-100%) | RESUME COUNT | JOB COUNT |

### 4. RESUME QUALITY CHECKS
| Check | Action |
|---|---|
| Job Title | Present? If not, suggest optimization. |
| Quantifiable Achievements | Count, list, identify gaps, suggest additions. |
| Weak Language | Flag filler words (just, various, always, etc.) for removal. |
| Action Verbs | Flag weak/passive verbs; map to stronger alternatives. |
| First-Person Pronouns | Flag I/me/my/we; provide rephrased versions. |
| Formatting | Verify contact info, date consistency, word count (optimal: 400-600), readability. |

### 5. RECOMMENDATIONS
- **HIGH IMPACT**: Top 3-5 missing hard skills, critical keyword gaps, major formatting issues
- **MEDIUM IMPACT**: Missing soft skills, frequency optimization, quantifiable achievements
- **LOW IMPACT**: Language polish, minor keywords, style

### 6. PYTHON VISUALIZATIONS
Generate complete, executable code. Replace all placeholder values with actual data from the resume and JD.

```python
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import pandas as pd
from matplotlib.patches import Wedge, Patch
import warnings
warnings.filterwarnings(&#x27;ignore&#x27;)
plt.style.use(&#x27;seaborn-v0_8-darkgrid&#x27;)
sns.set_palette(&quot;husl&quot;)

# A. MATCH SCORE GAUGE
def create_match_gauge(score):
    fig, ax = plt.subplots(figsize=(8, 4))
    for color, (b1, b2) in zip([&#x27;#d62728&#x27;,&#x27;#ff7f0e&#x27;,&#x27;#2ca02c&#x27;], [(0,70),(70,85),(85,100)]):
        t1, t2 = np.radians(180-b1*1.8), np.radians(180-b2*1.8)
        ax.add_patch(Wedge((0.5,0), 0.4, np.degrees(t1), np.degrees(t2), width=0.1, facecolor=color, alpha=0.3))
    angle = np.radians(180 - score*1.8)
    ax.plot([0.5, 0.5+0.35*np.cos(angle)], [0, 0.35*np.sin(angle)], &#x27;k-&#x27;, lw=3)
    ax.text(0.5,-0.15,f&#x27;{score}%&#x27;,ha=&#x27;center&#x27;,fontsize=24,fontweight=&#x27;bold&#x27;)
    ax.text(0.5,-0.25,&#x27;Match Score&#x27;,ha=&#x27;center&#x27;,fontsize=12)
    ax.set_xlim(0,1); ax.set_ylim(-0.3,0.5); ax.axis(&#x27;off&#x27;)
    plt.title(&#x27;Resume-Job Match Score&#x27;,fontsize=16,fontweight=&#x27;bold&#x27;,pad=20)
    return fig

# B. SKILLS BREAKDOWN
def create_skills_breakdown(hard_match, soft_match, other_match, hard_missing, soft_missing, other_missing):
    categories = [&#x27;Hard Skills&#x27;,&#x27;Soft Skills&#x27;,&#x27;Other Skills&#x27;]
    matched = [hard_match, soft_match, other_match]
    missing = [hard_missing, soft_missing, other_missing]
    fig, ax = plt.subplots(figsize=(10,6))
    x = np.arange(len(categories)); w = 0.35
    ax.barh(x-w/2, matched, w, label=&#x27;Matched&#x27;, color=&#x27;#2ca02c&#x27;)
    ax.barh(x+w/2, missing, w, label=&#x27;Missing&#x27;, color=&#x27;#d62728&#x27;)
    ax.set_yticks(x); ax.set_yticklabels(categories)
    ax.set_title(&#x27;Skills: Matched vs Missing&#x27;,fontsize=16,fontweight=&#x27;bold&#x27;)
    ax.legend(); plt.tight_layout()
    return fig

# C. KEYWORD HEATMAP (keywords_df cols: keyword, resume_count, job_count, type)
def create_keyword_heatmap(keywords_df):
    top = keywords_df.nlargest(20,&#x27;job_count&#x27;)
    fig, ax = plt.subplots(figsize=(10,12))
    data = top[[&#x27;resume_count&#x27;,&#x27;job_count&#x27;]].T
    data.columns = top[&#x27;keyword&#x27;]
    sns.heatmap(data, annot=True, fmt=&#x27;d&#x27;, cmap=&#x27;RdYlGn&#x27;, ax=ax)
    ax.set_yticklabels([&#x27;Your Resume&#x27;,&#x27;Job Description&#x27;],rotation=0)
    plt.title(&#x27;Top 20 Keywords: Frequency Comparison&#x27;,fontsize=16,fontweight=&#x27;bold&#x27;,pad=20)
    plt.tight_layout(); return fig

# D. RADAR CHART
def create_radar_chart(categories, scores):
    angles = np.linspace(0,2*np.pi,len(categories),endpoint=False).tolist()
    s = scores+[scores[0]]; angles += angles[:1]
    fig, ax = plt.subplots(figsize=(8,8), subplot_kw=dict(projection=&#x27;polar&#x27;))
    ax.plot(angles,s,&#x27;o-&#x27;,lw=2,color=&#x27;#2ca02c&#x27;); ax.fill(angles,s,alpha=0.25,color=&#x27;#2ca02c&#x27;)
    ax.set_xticks(angles[:-1]); ax.set_xticklabels(categories,size=10); ax.set_ylim(0,100)
    plt.title(&#x27;Resume Strength Analysis&#x27;,size=16,fontweight=&#x27;bold&#x27;,pad=20)
    return fig

# E. MISSING SKILLS PRIORITY (missing_df cols: skill, impact 1-10, type)
def create_priority_chart(missing_df):
    top = missing_df.nlargest(10,&#x27;impact&#x27;)
    colors = {&#x27;Hard&#x27;:&#x27;#1f77b4&#x27;,&#x27;Soft&#x27;:&#x27;#ff7f0e&#x27;,&#x27;Other&#x27;:&#x27;#2ca02c&#x27;}
    fig, ax = plt.subplots(figsize=(10,8))
    ax.barh(range(len(top)), top[&#x27;impact&#x27;], color=[colors[t] for t in top[&#x27;type&#x27;]])
    ax.set_yticks(range(len(top))); ax.set_yticklabels(top[&#x27;skill&#x27;]); ax.invert_yaxis()
    ax.set_title(&#x27;Top 10 Missing Skills by Impact&#x27;,fontsize=16,fontweight=&#x27;bold&#x27;)
    ax.legend(handles=[Patch(facecolor=v,label=k) for k,v in colors.items()],loc=&#x27;lower right&#x27;)
    plt.tight_layout(); return fig

# USAGE (replace with actual analysis data)
if __name__ == &quot;__main__&quot;:
    for fig, name in [
        (create_match_gauge(78), &#x27;match_gauge&#x27;),
        (create_skills_breakdown(15,8,12,9,5,6), &#x27;skills_breakdown&#x27;),
        (create_keyword_heatmap(pd.DataFrame({&#x27;keyword&#x27;:[&#x27;Python&#x27;,&#x27;Leadership&#x27;,&#x27;Agile&#x27;,&#x27;Testing&#x27;,&#x27;SQL&#x27;],&#x27;resume_count&#x27;:[3,2,0,5,2],&#x27;job_count&#x27;:[5,3,4,6,3],&#x27;type&#x27;:[&#x27;Hard&#x27;,&#x27;Soft&#x27;,&#x27;Other&#x27;,&#x27;Hard&#x27;,&#x27;Hard&#x27;]})), &#x27;keyword_heatmap&#x27;),
        (create_radar_chart([&#x27;Hard Skills&#x27;,&#x27;Soft Skills&#x27;,&#x27;Keywords&#x27;,&#x27;Format&#x27;,&#x27;Accomplishments&#x27;],[75,60,80,95,70]), &#x27;radar_chart&#x27;),
        (create_priority_chart(pd.DataFrame({&#x27;skill&#x27;:[&#x27;Linux&#x27;,&#x27;Collaborate&#x27;,&#x27;Infrastructure&#x27;,&#x27;Product&#x27;,&#x27;Protocols&#x27;],&#x27;impact&#x27;:[10,8,7,6,6],&#x27;type&#x27;:[&#x27;Hard&#x27;,&#x27;Soft&#x27;,&#x27;Other&#x27;,&#x27;Other&#x27;,&#x27;Other&#x27;]})), &#x27;priority_chart&#x27;)
    ]:
        plt.savefig(f&#x27;{name}.png&#x27;, dpi=300, bbox_inches=&#x27;tight&#x27;); plt.show()




Here is my resume:

RESUME CONTEXT: Robert McCurdy | Roswell, GA | 404-647-4250 | RMcCurdyjob@gmail.com | linkedin.com/in/rmccurdy1

ROLE: Senior offensive security engineer and AI/ML security researcher with 15+ years experience in penetration testing, red team operations, vulnerability management, and security automation.

EXPERIENCE:
- Abira Security (Jul 2025–present): Senior Security Engineer. 20+ assessments (network, web, API, mobile, cloud, thick-client); Critical/High findings 80% of engagements; domain admin access within 24hrs on 2,000+ host networks via SMB relay, service account hijacking, cloud compromise; EDR bypass (CrowdStrike, ThreatLocker, forced VPN) via custom PowerShell; AI-assisted pentest workflows using LLMs reducing documentation 2–4hrs/assessment; maintains JAMBOREE Android pentest framework (241 stars, 28 forks) and CrowdStrike RTR PowerShell repo (82 stars, 8 forks).
- AI/ML Security Research (personal): LLM jailbreak disclosures to AT&T and major vendors; adversarial prompt engineering repo; deepfake/voice cloning research; PyTorch model fine-tuning on self-hosted GPU; AI security workshops for schools/community orgs.
- Newell Brands (Jan 2019–Mar 2025): Cybersecurity Specialist. Tier 3 SOC escalation; custom API integrations (ZeroFox, CrowdStrike, Azure, Mimecast, Microsoft MDE); first scalable IR capability for the org; lead security engineer for detection and automation.
- SunTrust (Nov 2016–Mar 2018): Manager, Vuln Mgmt & Red Team. Built inaugural red team and vuln mgmt team; scan duration reduced from 3 weeks to 3 days; automated remediation below 90-day SLA; hired 4 personnel.
- KPMG (Jun 2010–Sep 2016): Cyber Risk Specialist. Pentesting, red team, compliance across government, SCADA, and enterprise; managed Atlanta pentest lab; evaluated 7+ IDS/IPS vendors; SECCDC red team participant.
- NRI Construction (Jul 2008–Jun 2010): IT/security support; Zenoss, Nagios, Snort/Nessus deployment; network, firewall, email, PBX, and badge systems.

SKILLS: Burp Suite, Metasploit, Nmap, OpenVAS, Wireshark, CrowdStrike, Splunk SOAR, Archer GRC, CarbonBlack, Velociraptor, PyTorch, TensorFlow, LangChain, Hugging Face, Stable Diffusion, Python, SQL, Docker, Ansible, SAST/DAST, Microsoft Purview, Forcepoint, Proofpoint, WAF, OT/ICS/SCADA, Zenoss, Nagios.

FRAMEWORKS: MITRE ATT&CK, OWASP, NIST, ISO 27001, SOX, PCI DSS, CIS, HIPAA, FedRAMP, GDPR, CCPA.

CERTS: CPTS, WAPT, Archer Certified Consultant, Splunk SOAR (Developing/Advanced/Administering).

EDUCATION: CIS, Networking & Security | Gwinnett Technical College.

COMMUNITY: JAMBOREE open-source Android pentest framework (GitHub); SECCDC STEM support; Fulton County Schools Innovation Academy.




