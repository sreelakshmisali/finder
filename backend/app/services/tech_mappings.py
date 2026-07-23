"""
Technology & Domain Mappings

Configurable taxonomy maps for categorizing tech stack components (Languages, Frameworks,
Databases, Infrastructure) and mapping them to domain expertise without hardcoded logic.
"""

from typing import Dict, List, Set

# Known Primary Programming Languages
PROGRAMMING_LANGUAGES: Set[str] = {
    "python", "javascript", "typescript", "java", "golang", "go", "c++", "c#",
    "rust", "ruby", "php", "swift", "kotlin", "scala", "elixir", "r", "c", "dart"
}

# Frameworks and Libraries
FRAMEWORKS: Set[str] = {
    "django", "fastapi", "flask", "react", "vue", "angular", "next.js", "nuxt",
    "express", "node.js", "nodejs", "spring", "spring boot", "rails", "laravel",
    "asp.net", ".net", "flutter", "react native", "pytorch", "tensorflow", "pandas",
    "numpy", "scikit-learn", "tailwind", "bootstrap", "graphql", "grpc"
}

# Databases & Storage Systems
DATABASES: Set[str] = {
    "postgresql", "postgres", "mysql", "mongodb", "redis", "elasticsearch",
    "sqlite", "dynamodb", "cassandra", "snowflake", "bigquery", "oracle", "mariadb"
}

# Domain Expertise Mapping Rules based on Skills and Keywords
DOMAIN_KEYWORD_MAP: Dict[str, List[str]] = {
    "Backend": [
        "backend", "django", "fastapi", "flask", "express", "node", "spring",
        "api", "rest", "graphql", "grpc", "postgresql", "postgres", "mysql",
        "mongodb", "redis", "microservices", "sql"
    ],
    "Frontend": [
        "frontend", "react", "vue", "angular", "next.js", "typescript",
        "css", "html", "tailwind", "redux", "web"
    ],
    "Full Stack": [
        "full stack", "fullstack", "full-stack"
    ],
    "Data": [
        "data engineer", "data science", "spark", "hadoop", "snowflake",
        "bigquery", "pandas", "airflow", "etl", "sql", "data pipeline"
    ],
    "DevOps": [
        "devops", "aws", "docker", "kubernetes", "k8s", "terraform",
        "ci/cd", "cloud", "azure", "gcp", "ansible", "jenkins"
    ],
    "Mobile": [
        "ios", "android", "swift", "kotlin", "flutter", "react native", "mobile"
    ],
    "AI/ML": [
        "machine learning", "deep learning", "pytorch", "tensorflow", "ai",
        "llm", "nlp", "computer vision"
    ]
}

# Seniority level keyword triggers
SENIORITY_KEYWORDS: Dict[str, str] = {
    "lead": "Lead",
    "principal": "Lead",
    "staff": "Senior",
    "senior": "Senior",
    "sr": "Senior",
    "mid": "Mid",
    "junior": "Junior",
    "jr": "Junior",
    "intern": "Junior",
    "entry": "Junior"
}
