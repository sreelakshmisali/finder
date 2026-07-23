"""
Mock AI Provider

Deterministic rule-based implementation of `AIProvider` tuned for Indian IT/Software Engineering resumes.
Extracts candidate details, Indian phone numbers, Indian degree titles (B.Tech, M.Tech, MCA, etc.),
skills, experience, and projects from raw PDF text without inventing or fabricating fake data.
"""

import re
import logging
from typing import Dict, Any, List, Optional

from app.ai.base import AIProvider
from app.schemas.resume import ParsedResumeData

logger = logging.getLogger(__name__)

# Expanded list of Indian software engineering technologies & skills
INDIAN_TECH_SKILLS = [
    # Languages
    "Python", "Java", "C++", "C#", "C", "JavaScript", "TypeScript", "Go", "Golang",
    "Rust", "PHP", "Swift", "Kotlin", "SQL", "PL/SQL", "Bash", "Shell", "HTML", "CSS", "R", "Dart",
    # Frameworks & Web Tech
    "React", "React.js", "Node.js", "Express", "Express.js", "Next.js", "Vue.js", "Angular",
    "Django", "FastAPI", "Flask", "Spring", "Spring Boot", "Hibernate", "ASP.NET", ".NET",
    "Laravel", "Redux", "TailwindCSS", "Bootstrap", "jQuery",
    # Mobile
    "Android", "iOS", "Flutter", "React Native",
    # Cloud & DevOps & Tools
    "AWS", "Azure", "GCP", "Google Cloud", "Docker", "Kubernetes", "Terraform", "Jenkins",
    "Git", "GitHub", "GitLab", "CI/CD", "Linux", "Unix", "Nginx", "Ansible", "Jira",
    # Databases & Storage
    "PostgreSQL", "MySQL", "MongoDB", "Redis", "SQLite", "Oracle", "Elasticsearch",
    "DynamoDB", "Firebase", "Cassandra", "MariaDB",
    # Data Science & AI & ML
    "Machine Learning", "Deep Learning", "Data Science", "Artificial Intelligence",
    "Pandas", "NumPy", "Scikit-learn", "TensorFlow", "PyTorch", "OpenCV", "NLP",
    "Data Structures", "Algorithms", "System Design", "OOP", "Object Oriented Programming",
    # APIs & Testing & Architecture
    "REST API", "RESTful APIs", "GraphQL", "Microservices", "Kafka", "RabbitMQ",
    "WebSockets", "Unit Testing", "PyTest", "Jest", "Selenium", "JUnit", "Postman"
]

# Common Indian Degrees (Exact titles preserved, no US conversion)
INDIAN_DEGREE_PATTERNS = [
    r"\bB\.?\s*Tech\b(?:\s+(?:in|of)\s+[^,\n\(\)]+)?",
    r"\bBachelor\s+of\s+Technology\b(?:\s+(?:in|of)\s+[^,\n\(\)]+)?",
    r"\bM\.?\s*Tech\b(?:\s+(?:in|of)\s+[^,\n\(\)]+)?",
    r"\bMaster\s+of\s+Technology\b(?:\s+(?:in|of)\s+[^,\n\(\)]+)?",
    r"\bB\.?\s*E\.?\b(?:\s+(?:in|of)\s+[^,\n\(\)]+)?",
    r"\bBachelor\s+of\s+Engineering\b(?:\s+(?:in|of)\s+[^,\n\(\)]+)?",
    r"\bM\.?\s*E\.?\b(?:\s+(?:in|of)\s+[^,\n\(\)]+)?",
    r"\bMaster\s+of\s+Engineering\b(?:\s+(?:in|of)\s+[^,\n\(\)]+)?",
    r"\bMCA\b|\bMaster\s+of\s+Computer\s+Applications\b",
    r"\bBCA\b|\bBachelor\s+of\s+Computer\s+Applications\b",
    r"\bB\.?\s*Sc\b(?:\s+(?:in|of)\s+[^,\n\(\)]+)?",
    r"\bBachelor\s+of\s+Science\b(?:\s+(?:in|of)\s+[^,\n\(\)]+)?",
    r"\bM\.?\s*Sc\b(?:\s+(?:in|of)\s+[^,\n\(\)]+)?",
    r"\bMaster\s+of\s+Science\b(?:\s+(?:in|of)\s+[^,\n\(\)]+)?",
    r"\bMBA\b|\bMaster\s+of\s+Business\s+Administration\b",
    r"\bDiploma\b(?:\s+(?:in|of)\s+[^,\n\(\)]+)?",
    r"\bPh\.?D\b",
    r"\bHigher\s+Secondary\b|\bHSC\b|\bClass\s+XII?\b|\b12th\b",
    r"\bSSLC\b|\bClass\s+X\b|\b10th\b",
]

# Section headers map
SECTION_TITLES = {
    "education": ["education", "academic qualification", "academic background", "qualifications"],
    "experience": ["experience", "work experience", "employment history", "professional experience", "work history", "career summary"],
    "projects": ["projects", "personal projects", "academic projects", "key projects"],
    "skills": ["skills", "technical skills", "skills & expertise", "core competencies", "technologies"]
}


class MockProvider(AIProvider):
    """
    Mock AI Provider performing deterministic rule-based parsing.
    Extracted data strictly reflects raw resume contents without hardcoded US placeholders.
    """

    @property
    def provider_name(self) -> str:
        return "mock"

    def _extract_full_name(self, lines: List[str]) -> Optional[str]:
        """
        Extracts candidate's full name from top lines of the resume text.
        """
        ignore_keywords = [
            "resume", "curriculum", "vitae", "cv", "page", "contact",
            "email", "phone", "profile", "summary", "address", "github", "linkedin"
        ]

        for line in lines[:8]:
            clean_line = re.sub(r"[^\w\s\.-]", "", line).strip()
            if not clean_line or len(clean_line) < 2 or len(clean_line) > 50:
                continue

            line_lower = clean_line.lower()

            # Skip if line contains email or numbers
            if "@" in line_lower or re.search(r"\d", clean_line):
                continue

            # Skip common header labels or section titles
            if any(kw in line_lower for kw in ignore_keywords):
                continue

            words = clean_line.split()
            if 1 <= len(words) <= 4 and all(w.isalpha() or "." in w for w in words):
                return clean_line

        return None

    def _extract_email(self, raw_text: str) -> Optional[str]:
        """
        Extracts valid email address via regex pattern.
        """
        match = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", raw_text)
        return match.group(0).lower() if match else None

    def _extract_phone(self, raw_text: str) -> Optional[str]:
        """
        Extracts Indian phone number formats (+91, 10-digit starting with 6-9, etc.).
        """
        patterns = [
            r"\+91[\s-]?\d{5}[\s-]?\d{5}",
            r"\+91[\s-]?\d{10}",
            r"\+91[\s-]?\d{4}[\s-]?\d{6}",
            r"\b[6-9]\d{9}\b",
            r"\b[6-9]\d{4}[\s-]\d{5}\b",
            r"\b0[6-9]\d{9}\b"
        ]

        for pattern in patterns:
            match = re.search(pattern, raw_text)
            if match:
                phone_str = match.group(0).strip()
                if not re.search(r"(19|20)\d{2}", phone_str):
                    return phone_str

        match = re.search(r"\(?\+?\d{1,3}\)?[\s-]?\d{3,5}[\s-]?\d{4,5}", raw_text)
        if match:
            phone_str = match.group(0).strip()
            if len(re.sub(r"\D", "", phone_str)) >= 10:
                return phone_str

        return None

    def _extract_skills(self, raw_text: str) -> List[str]:
        """
        Extracts technical skills matching Indian software engineering tech stack keywords.
        """
        matched_skills: List[str] = []
        text_lower = raw_text.lower()

        for skill in INDIAN_TECH_SKILLS:
            escaped_skill = re.escape(skill)
            pattern = rf"\b{escaped_skill}\b"
            if re.search(pattern, text_lower, re.IGNORECASE):
                matched_skills.append(skill)

        # Deduplicate while preserving original order
        unique_skills = []
        seen = set()
        for s in matched_skills:
            if s.lower() not in seen:
                seen.add(s.lower())
                unique_skills.append(s)

        return unique_skills

    def _extract_education(self, lines: List[str], raw_text: str) -> List[Dict[str, Any]]:
        """
        Extracts Indian degree titles (B.Tech, M.Tech, MCA, etc.), institution, and graduation year.
        Preserves original degree title exactly as written in resume.
        """
        education_entries: List[Dict[str, Any]] = []

        in_edu_section = False
        edu_lines: List[str] = []

        for line in lines:
            line_clean = line.strip()
            line_lower = line_clean.lower()

            if any(title in line_lower for title in SECTION_TITLES["education"]):
                in_edu_section = True
                continue
            elif in_edu_section and any(
                title in line_lower
                for sec in ["experience", "projects", "skills"]
                for title in SECTION_TITLES[sec]
            ):
                in_edu_section = False

            if in_edu_section:
                edu_lines.append(line_clean)

        target_lines = edu_lines if edu_lines else lines

        for i, line in enumerate(target_lines):
            for pattern in INDIAN_DEGREE_PATTERNS:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    degree_str = match.group(0).strip()

                    institution = None
                    inst_keywords = ["university", "institute", "college", "iit", "nit", "iiit", "bits", "academy", "vtu", "anna"]

                    search_block = " ".join(target_lines[max(0, i-1):min(len(target_lines), i+2)])
                    for word in search_block.split(","):
                        if any(ik in word.lower() for ik in inst_keywords):
                            institution = word.strip()
                            break

                    year_match = re.search(r"\b(19\d{2}|20\d{2})\b", search_block)
                    year = year_match.group(0) if year_match else None

                    if not any(e["degree"].lower() == degree_str.lower() for e in education_entries):
                        education_entries.append({
                            "degree": degree_str,
                            "institution": institution or "Institution Not Specified",
                            "year": year
                        })

        return education_entries

    def _extract_experience(self, lines: List[str], raw_text: str) -> List[Dict[str, Any]]:
        """
        Extracts work experience entries from Experience section.
        Returns empty list if no experience section is present.
        """
        experience_entries: List[Dict[str, Any]] = []

        in_exp_section = False
        exp_lines: List[str] = []

        for line in lines:
            line_clean = line.strip()
            line_lower = line_clean.lower()

            if any(title in line_lower for title in SECTION_TITLES["experience"]):
                in_exp_section = True
                continue
            elif in_exp_section and any(
                title in line_lower
                for sec in ["education", "projects", "skills"]
                for title in SECTION_TITLES[sec]
            ):
                in_exp_section = False

            if in_exp_section and line_clean:
                exp_lines.append(line_clean)

        if not exp_lines:
            return []

        current_entry: Dict[str, Any] = {}
        for line in exp_lines:
            date_match = re.search(
                r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|19\d{2}|20\d{2})\b.*?(?:Present|\b(?:19\d{2}|20\d{2})\b)",
                line,
                re.IGNORECASE
            )

            if date_match or (len(current_entry) == 0 and not line.startswith("-") and not line.startswith("•")):
                if current_entry and ("title" in current_entry or "company" in current_entry):
                    experience_entries.append(current_entry)
                    current_entry = {}

                current_entry["duration"] = date_match.group(0) if date_match else "N/A"
                header_text = line.replace(current_entry.get("duration", ""), "").strip(" |-:,")

                parts = [p.strip() for p in re.split(r"\||-|at|,", header_text) if p.strip()]
                if len(parts) >= 2:
                    current_entry["title"] = parts[0]
                    current_entry["company"] = parts[1]
                elif len(parts) == 1:
                    current_entry["title"] = parts[0]
                    current_entry["company"] = "Company Not Specified"
                else:
                    current_entry["title"] = header_text or "Software Role"
                    current_entry["company"] = "Company Not Specified"

                current_entry["description"] = ""
            else:
                if "description" in current_entry:
                    current_entry["description"] += (" " + line).strip()
                elif current_entry:
                    current_entry["description"] = line

        if current_entry and ("title" in current_entry or "company" in current_entry):
            experience_entries.append(current_entry)

        return experience_entries

    def _extract_projects(self, lines: List[str], raw_text: str) -> List[Dict[str, Any]]:
        """
        Extracts project entries from Projects section.
        Returns empty list if no projects section is present.
        """
        project_entries: List[Dict[str, Any]] = []

        in_proj_section = False
        proj_lines: List[str] = []

        for line in lines:
            line_clean = line.strip()
            line_lower = line_clean.lower()

            if any(title in line_lower for title in SECTION_TITLES["projects"]):
                in_proj_section = True
                continue
            elif in_proj_section and any(
                title in line_lower
                for sec in ["education", "experience", "skills"]
                for title in SECTION_TITLES[sec]
            ):
                in_proj_section = False

            if in_proj_section and line_clean:
                proj_lines.append(line_clean)

        if not proj_lines:
            return []

        current_proj: Dict[str, Any] = {}
        for line in proj_lines:
            if not line.startswith("-") and not line.startswith("•") and len(line.split()) < 8:
                if current_proj and "title" in current_proj:
                    project_entries.append(current_proj)
                current_proj = {"title": line, "description": ""}
            else:
                if "description" in current_proj:
                    current_proj["description"] += (" " + line).strip()
                elif current_proj:
                    current_proj["description"] = line

        if current_proj and "title" in current_proj:
            project_entries.append(current_proj)

        return project_entries

    async def parse_resume(self, raw_text: str) -> ParsedResumeData:
        """
        Parses resume text using modular rule-based extraction tailored for Indian IT resumes.
        """
        logger.info("Executing Mock AI rule-based resume parser")
        lines = [line.strip() for line in raw_text.splitlines() if line.strip()]

        full_name = self._extract_full_name(lines)
        email = self._extract_email(raw_text)
        phone = self._extract_phone(raw_text)
        skills = self._extract_skills(raw_text)
        education = self._extract_education(lines, raw_text)
        experience = self._extract_experience(lines, raw_text)
        projects = self._extract_projects(lines, raw_text)

        return ParsedResumeData(
            full_name=full_name,
            email=email,
            phone=phone,
            skills=skills,
            experience=experience,
            education=education,
            projects=projects
        )

    async def explain_match(
        self,
        resume_data: Dict[str, Any],
        job_title: str,
        company: str,
        job_description: str,
        score: float
    ) -> Dict[str, Any]:
        """
        Generates rule-based match explanation.
        """
        resume_skills = set(s.lower() for s in resume_data.get("skills", []))
        desc_lower = job_description.lower()

        reasons: List[str] = []
        missing: List[str] = []

        for skill in INDIAN_TECH_SKILLS:
            if skill.lower() in desc_lower:
                if skill.lower() in resume_skills:
                    reasons.append(f"✓ Strong proficiency in {skill}")
                else:
                    missing.append(skill)

        if not reasons:
            reasons = ["✓ Relevant engineering background", "✓ Technical skills overlap"]

        rec = f"Strong Match ({round(score)}%) — candidate demonstrates key technical requirements." if score >= 70 else f"Moderate Fit ({round(score)}%) — candidate has foundational skills."

        return {
            "reasons": reasons[:4],
            "missing_skills": missing[:3],
            "recommendation": rec
        }

    async def analyze_resume_quality(
        self,
        raw_text: str,
        parsed_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyzes general resume quality, identifying missing skills, weak descriptions, and ATS issues.
        """
        skills = parsed_data.get("skills", [])
        skills_set = set(s.lower() for s in skills)
        email = parsed_data.get("email")
        phone = parsed_data.get("phone")
        experience = parsed_data.get("experience", [])

        # 1. Identify missing industry standard skills
        essential_tech = ["Git", "Docker", "Unit Testing", "CI/CD", "REST API", "SQL", "Agile"]
        missing_skills = [tech for tech in essential_tech if tech.lower() not in skills_set]

        # 2. Identify weak descriptions
        weak_descriptions: List[str] = []
        passive_words = ["worked on", "responsible for", "helped", "assisted", "did", "handled"]

        text_lower = raw_text.lower()
        for phrase in passive_words:
            if phrase in text_lower:
                weak_descriptions.append(
                    f"Replace passive phrase '{phrase}' with strong action verbs (e.g. 'Architected', 'Engineered', 'Optimized', 'Spearheaded')."
                )

        # Check for metrics / numbers in experience
        has_metrics = bool(re.search(r"\b\d+%\b|\b\d+\s*ms\b|\b\d+k\b|\$\d+", raw_text))
        if not has_metrics:
            weak_descriptions.append(
                "Work experience lacks quantifiable impact metrics. Add numbers like 'reduced latency by 35%', 'handled 50k daily active users', or 'increased coverage to 90%'."
            )

        # 3. ATS Issues
        ats_issues: List[str] = []
        if not email:
            ats_issues.append("ATS Alert: Candidate email address is missing from header.")
        if not phone:
            ats_issues.append("ATS Alert: Phone number is missing from header.")
        if len(skills) < 5:
            ats_issues.append("ATS Alert: Fewer than 5 technical skills detected. Group skills into clear categories (Languages, Frameworks, Databases).")
        if not experience:
            ats_issues.append("ATS Alert: Work experience section heading not clearly parsed. Use standard headers like 'Professional Experience' or 'Work History'.")

        # 4. Quality Score calculation
        quality_score = 100.0
        if missing_skills:
            quality_score -= len(missing_skills) * 3
        if weak_descriptions:
            quality_score -= len(weak_descriptions) * 6
        if ats_issues:
            quality_score -= len(ats_issues) * 8
        quality_score = max(35.0, min(100.0, quality_score))

        summary = f"Resume quality score is {round(quality_score)}%. " + (
            "Excellent structure and formatting." if quality_score >= 85 else
            "Good foundation with minor ATS formatting and metric improvements needed." if quality_score >= 70 else
            "Requires action verb enhancements and key technical skills additions."
        )

        return {
            "quality_score": round(quality_score, 1),
            "missing_skills": missing_skills[:4],
            "weak_descriptions": weak_descriptions[:3],
            "ats_issues": ats_issues,
            "summary": summary
        }

    async def suggest_job_specific_improvements(
        self,
        raw_text: str,
        parsed_data: Dict[str, Any],
        job_title: str,
        job_description: str
    ) -> Dict[str, Any]:
        """
        Provides tailored recommendations to customize resume for a target job posting.
        """
        skills = parsed_data.get("skills", [])
        skills_set = set(s.lower() for s in skills)
        desc_lower = job_description.lower()

        matching_skills: List[str] = []
        missing_job_skills: List[str] = []

        for skill in INDIAN_TECH_SKILLS:
            if skill.lower() in desc_lower:
                if skill.lower() in skills_set:
                    matching_skills.append(skill)
                else:
                    missing_job_skills.append(skill)

        suggested_changes: List[str] = []

        if missing_job_skills:
            top_missing = ", ".join(missing_job_skills[:3])
            suggested_changes.append(
                f"Add target keywords '{top_missing}' into your Skills section as emphasized in the {job_title} position description."
            )

        suggested_changes.append(
            f"Tailor summary header to explicitly highlight experience relevant to '{job_title}' role."
        )

        if "microservices" in desc_lower and "microservices" not in raw_text.lower():
            suggested_changes.append(
                "Emphasize experience with API design, microservices architecture, and distributed services in bullet points."
            )

        if "cloud" in desc_lower or "aws" in desc_lower or "azure" in desc_lower:
            if not any(c in skills_set for c in ["aws", "azure", "gcp", "cloud"]):
                suggested_changes.append(
                    "Highlight cloud deployment experience (AWS, Azure, Docker, or Kubernetes) in project descriptions."
                )

        tailored_summary = (
            f"Resume aligns well with {len(matching_skills)} core skills required for '{job_title}'. "
            f"Incorporate {len(missing_job_skills)} missing keywords to maximize ATS keyword matching score."
        )

        return {
            "matching_skills": matching_skills,
            "missing_job_skills": missing_job_skills,
            "suggested_changes": suggested_changes,
            "tailored_summary": tailored_summary
        }

