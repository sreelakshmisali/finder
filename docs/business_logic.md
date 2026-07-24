# Finder - Business Logic Documentation

This document outlines the core business logic and algorithms applied across the Finder platform. 

## 1. Resume-First Onboarding
Finder relies heavily on a candidate's resume to drive the automation.
- **Active Resume Requirement**: A user must have an active PDF resume uploaded. 
- **Profile Completion Score**: The onboarding completion percentage is calculated based on four 25% pillars:
  1. Account Created (25%)
  2. Resume Uploaded (25%)
  3. Resume Analyzed (Parsed) (25%)
  4. Preferences Configured (Roles, Locations, or Companies set) (25%)

## 2. Job Discovery & Search (`JobService`)
Job searching uses a concurrent scraping and caching mechanism to aggregate jobs from various providers.
- **Candidate-Aware Search**: If a user does not explicitly provide a query keyword, the system generates optimal search queries based on their active resume (parsed skills/roles) and stated preferences.
- **Concurrent Scraping**: Dispatches search queries across enabled providers (e.g., via `asyncio.gather`).
- **Caching & Deduplication**: Avoids rate limits and redundant scraping by utilizing an in-memory or Redis-backed caching layer and saving normalized jobs to the local `JobRepository`. If no new jobs are found online, it falls back to previously cached local database jobs.

## 3. Hybrid Job Matching Engine (`MatchingService`)
Every discovered job is scored against the candidate's profile to measure fit. The final score is a composite of three main pillars (totaling up to 100%, with freshness added on top):

### A. Resume Compatibility (70% Influence)
Extracted via NLP and basic text analysis from the raw resume and parsed data:
- **Skills Match (35%)**: Compares parsed resume skills against the job description.
- **Experience Match (20%)**: Matches seniority indicators (e.g., junior, senior, staff) against the candidate's years of experience.
- **Role Similarity (25%)**: Overlaps candidate's target roles and historical job titles with the target job title.
- **Technology Overlap (20%)**: Checks common tech stacks (React, Python, AWS, etc.) found in the resume against the job post.

### B. Preference Alignment (30% Influence)
Matches user-defined settings against the job metadata:
- **Location Match (30%)**: Compares preferred locations to the job location.
- **Salary Match (25%)**: Checks if the job's minimum salary meets the candidate's expectation.
- **Remote Match (25%)**: Aligns remote/hybrid/onsite preferences.
- **Company Match (20%)**: Checks if the job is at a preferred company.

### C. Freshness Alignment (10% Bonus Influence)
- **Posted Date**: Scores high for recent postings with a linear decay over a max number of days.
- **Verified Date**: Scores based on when the job was last discovered or verified in the system.

### D. AI Explainability
- After calculating the raw hybrid score, the platform passes the resume, job details, and score to an AI Provider to generate human-readable reasoning and identify "missing skills".

## 4. Application Automation & Safety (`AutomationService`)
Finder automates the tedious parts of applying to jobs on platforms like Greenhouse, Lever, and Ashby using Playwright, but it enforces a **Strict Safety Guarantee**.

- **Initialization**: Status shifts to `running` while the system navigates to the job application URL.
- **Form Filling**: Parses candidate data (Full Name, Email, Phone, Skills) from the active resume to fill out standard fields and uploads the PDF resume.
- **Safety Pause**: Automator pauses at the `awaiting_confirmation` status. **Finder NEVER automatically submits a job application without user consent.**
- **User Confirmation**: The user must explicitly review the drafted application and click to submit, which triggers `confirm_and_submit()` to complete the workflow.

## 5. Application State Machine
Applications track candidate progress through defined states:
`saved` ➔ `approved` ➔ `queued` ➔ `running` ➔ `awaiting_input` / `awaiting_confirmation` ➔ `completed` / `failed`
Post-application states include: `interview`, `rejected`, `offer`.
