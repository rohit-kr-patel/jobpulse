# System Flow

```text
User
 |
 v
Frontend
 |
 v
FastAPI
 |
 +--> Resume Parser
 |
 +--> Scheduler
 |      |
 |      v
 |  Job Fetchers
 |      |
 |      v
 | Matching Engine
 |      |
 +----> PostgreSQL
 |
 v
Dashboard
```
