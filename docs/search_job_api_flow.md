# Search Job API Execution Flow

This document details the minimal baseline execution flow for the Job Search API in Finder.

---

## 1. Overview & Architecture Diagram

The Job Search Engine follows a decoupled, provider-agnostic baseline architecture designed for high readability, fault tolerance, and ease of debugging.

```
                          User Search Request 
                        (GET /api/v1/jobs/search)
                                   │
                                   ▼
                      app/api/v1/jobs.py: search_jobs()
                                   │
                                   ▼
                 app/services/job_service.py: JobService
                                   │
                  ┌────────────────┴────────────────┐
                  │  registry.get_enabled_providers() │
                  └────────────────┬────────────────┘
                                   │
         ┌─────────────────────────┼─────────────────────────┐
         ▼                         ▼                         ▼
  GreenhouseProvider         LeverProvider             AshbyProvider
     .discover()              .discover()               .discover()
         │                         │                         │
         └─────────────────────────┼─────────────────────────┘
                                   │
                                   ▼
                       SearchDiscoveryProvider
                             .discover()
                                   │
             ┌─────────────────────┴─────────────────────┐
             │ 1. search_term = query + location         │
             │ 2. aggregator.aggregate_search()          │
             │ 3. extract_from_url() via asyncio.gather  │
             └─────────────────────┬─────────────────────┘
                                   │
                                   ▼
                 Merge NormalizedJob list from all providers
                                   │
                                   ▼
                JobRepository.save_normalized_job() (DB save)
                                   │
                                   ▼
                     Return JobListResponse API response
```

---

## 2. Step-by-Step Execution Detail

### Step 1: HTTP API Request Entry
- **Endpoint**: `GET /api/v1/jobs/search`
- **File**: [`backend/app/api/v1/jobs.py`](file:///c:/Users/codel/Downloads/sree/finder/backend/app/api/v1/jobs.py)
- **Parameters**: `q` (keywords), `location`, `remote_only`, `search_mode`, `min_salary`, `limit`.
- **Action**: Constructs a strongly-typed `JobSearchQuery` object and calls `JobService(db).search_jobs(query, user_id)`.

### Step 2: Orchestration Layer (`JobService`)
- **File**: [`backend/app/services/job_service.py`](file:///c:/Users/codel/Downloads/sree/finder/backend/app/services/job_service.py)
- **Action**:
  1. Logs search start time and parameters.
  2. Queries `registry.get_enabled_providers()` to obtain all active discovery sources.
  3. Constructs a `DiscoveryContext(query=query, user_id=user_id)`.

### Step 3: Concurrent Provider Discovery
- **File**: [`backend/app/providers/registry.py`](file:///c:/Users/codel/Downloads/sree/finder/backend/app/providers/registry.py)
- **Action**: Executes `provider.discover(context)` concurrently across all enabled providers using `asyncio.gather(*tasks, return_exceptions=True)`.

#### Registered Discovery Providers:
1. **GreenhouseProvider** ([`greenhouse.py`](file:///c:/Users/codel/Downloads/sree/finder/backend/app/providers/greenhouse.py)): Queries public Greenhouse board APIs for popular tech boards.
2. **LeverProvider** ([`lever.py`](file:///c:/Users/codel/Downloads/sree/finder/backend/app/providers/lever.py)): Queries public Lever posting APIs.
3. **AshbyProvider** ([`ashby.py`](file:///c:/Users/codel/Downloads/sree/finder/backend/app/providers/ashby.py)): Queries public Ashby HQ posting APIs.
4. **SearchDiscoveryProvider** ([`search_discovery.py`](file:///c:/Users/codel/Downloads/sree/finder/backend/app/providers/search_engine/search_discovery.py)): Executes web search queries via `SearchAggregator.aggregate_search()` (defaulting to `DuckDuckGoSearchProvider`), then classifies, drills down, and extracts job details via `JobExtractor.extract_from_url()`.

### Step 4: Provider Failure Isolation & Results Collection
- **Action**:
  - Each provider returns a `List[NormalizedJob]`.
  - If a specific provider encounters a network error or timeout, `asyncio.gather()` captures the exception without stopping other providers.
  - `JobService` logs provider errors and collects all successfully returned jobs into a single list.

### Step 5: Database Persistence & Normalization
- **File**: [`backend/app/repositories/job_repository.py`](file:///c:/Users/codel/Downloads/sree/finder/backend/app/repositories/job_repository.py)
- **Action**:
  - Iterates over each `NormalizedJob` and calls `self.repo.save_normalized_job(norm_job)`.
  - Computes content hashes, detects exact URL or title/company duplicates, merges missing metadata (e.g. salary or remote flags), and persists new entries to PostgreSQL.

### Step 6: API Response Generation
- **Schema**: `JobListResponse` ([`backend/app/schemas/job.py`](file:///c:/Users/codel/Downloads/sree/finder/backend/app/schemas/job.py))
- **Action**: Maps saved database `Job` records into `JobResponse` items and returns the HTTP JSON response to the client.

---

## 3. Key Design Properties

1. **Fault Isolation**: Provider exceptions are isolated; one provider failing does not halt overall job search execution.
2. **Concurrency**: All provider requests and page extraction calls run concurrently using `asyncio.gather()`.
3. **Zero Caching Overhead**: Always fetches live data directly from enabled providers for instant baseline verification.
4. **Clean Data Contracts**: `NormalizedJob` acts as the uniform contract across all providers.
