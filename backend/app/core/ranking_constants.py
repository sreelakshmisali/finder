"""
Ranking & Matching Constants

Centralized configuration for matching weights, thresholds, and freshness decay parameters.
This allows tuning the ranking algorithm without modifying core business logic.
"""

# Overall Weight Distributions
WEIGHT_RESUME = 0.70        # 70% influence for Resume Compatibility
WEIGHT_PREFERENCE = 0.20    # 20% influence for Preference Alignment
WEIGHT_FRESHNESS = 0.10     # 10% influence for Job Freshness

# Resume Sub-Weights (Total = 1.0)
RESUME_SKILLS_WEIGHT = 0.35
RESUME_EXP_WEIGHT = 0.20
RESUME_ROLE_WEIGHT = 0.25
RESUME_TECH_WEIGHT = 0.20

# Preference Sub-Weights (Total = 1.0)
PREF_LOCATION_WEIGHT = 0.30
PREF_SALARY_WEIGHT = 0.25
PREF_REMOTE_WEIGHT = 0.25
PREF_COMPANY_WEIGHT = 0.20

# Freshness Sub-Weights (Total = 1.0)
FRESH_POSTED_WEIGHT = 0.60
FRESH_VERIFIED_WEIGHT = 0.40

# Freshness Decay Parameters
DECAY_POSTED_DAYS_MAX = 45.0      # Days until posted_date score drops to 0
DECAY_VERIFIED_DAYS_MAX = 14.0    # Days until last_verified_date score drops to 0
