import re

# Canonical skill name -> list of lowercase aliases/variations
SKILL_ALIASES: dict[str, list[str]] = {
    # Programming Languages
    "Python": ["python", "python3", "py"],
    "Java": ["java", "core java", "java 8", "java 11", "java 17"],
    "JavaScript": ["javascript", "js", "es6", "ecmascript"],
    "TypeScript": ["typescript", "ts"],
    "C++": ["c++", "cpp"],
    "C": ["c language", "c programming"],
    "C#": ["c#", "csharp", "c sharp"],
    "Go": ["golang", "go lang"],
    "SQL": ["sql", "structured query language"],
    "HTML": ["html", "html5"],
    "CSS": ["css", "css3"],

    # Web & Backend Frameworks
    "Django": ["django", "django rest framework", "drf"],
    "Flask": ["flask"],
    "FastAPI": ["fastapi", "fast api"],
    "React": ["react", "reactjs", "react.js"],
    "Node.js": ["node", "nodejs", "node.js"],
    "Express.js": ["express", "expressjs", "express.js"],
    "Spring Boot": ["spring boot", "springboot", "spring"],
    "Angular": ["angular", "angularjs"],
    "Next.js": ["next.js", "nextjs"],
    "Bootstrap": ["bootstrap"],
    "Tailwind CSS": ["tailwind", "tailwindcss", "tailwind css"],

    # Databases
    "PostgreSQL": ["postgresql", "postgres", "psql"],
    "MySQL": ["mysql"],
    "MongoDB": ["mongodb", "mongo"],
    "SQLite": ["sqlite", "sqlite3"],
    "Redis": ["redis"],

    # Data, AI & Machine Learning
    "Machine Learning": ["machine learning", "ml"],
    "Deep Learning": ["deep learning", "dl"],
    "NLP": ["nlp", "natural language processing"],
    "spaCy": ["spacy"],
    "Pandas": ["pandas"],
    "NumPy": ["numpy"],
    "Scikit-learn": ["scikit-learn", "sklearn", "scikit learn"],
    "TensorFlow": ["tensorflow", "tf"],
    "PyTorch": ["pytorch"],
    "LLMs": ["llm", "llms", "large language models", "generative ai", "genai"],

    # DevOps, Cloud & Tools
    "Git": ["git", "github", "gitlab"],
    "Docker": ["docker", "containerization"],
    "Kubernetes": ["kubernetes", "k8s"],
    "AWS": ["aws", "amazon web services"],
    "Azure": ["azure", "microsoft azure"],
    "GCP": ["gcp", "google cloud", "google cloud platform"],
    "Linux": ["linux", "ubuntu", "bash", "shell scripting"],
    "REST API": ["rest api", "restful api", "rest apis", "restful services"],
    "CI/CD": ["ci/cd", "cicd", "github actions", "jenkins"],

    # Soft Skills (used with soft-skill inflation guard in ats_score.py)
    "Communication": ["communication", "verbal communication", "written communication"],
    "Teamwork": ["teamwork", "team player", "collaboration", "collaborative"],
    "Problem Solving": ["problem solving", "problem-solving", "analytical thinking"],
    "Critical Thinking": ["critical thinking", "decision making"],
}


def extract_skills(text: str) -> list[str]:
    """
    Scans text for canonical skills and their aliases using word-boundary matching.
    Returns a sorted list of unique canonical skill names.
    """
    if not text:
        return []

    text_lower = text.lower()
    found_skills: set[str] = set()

    for canonical, aliases in SKILL_ALIASES.items():
        for alias in aliases:
            escaped = re.escape(alias)
            pattern = rf"(?<![a-z0-9]){escaped}(?![a-z0-9])"
            if re.search(pattern, text_lower):
                found_skills.add(canonical)
                break

    return sorted(found_skills)


def get_skill_aliases(canonical_skill: str) -> list[str]:
    """
    Returns all lowercase aliases for a canonical skill name so
    ats_score.py can verify where the skill appears across resume sections.
    """
    for canonical, aliases in SKILL_ALIASES.items():
        if canonical.lower() == canonical_skill.strip().lower():
            return aliases
    return [canonical_skill.strip().lower()]