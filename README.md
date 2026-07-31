# 🚀 JobPulse

> **Your Personal Job Assistant for Freshers**  
> Automatically discover, rank, and track the best software engineering jobs every day.

---

## 📌 Problem

As a fresher, finding jobs is repetitive:

- Visit multiple job portals every day
- Search the same keywords repeatedly
- Read duplicate job descriptions
- Check if jobs are still active
- Track applications manually
- Miss new opportunities

JobPulse solves this by doing the repetitive work automatically.

---

# ✨ Features (V1)

- Resume upload (PDF)
- Resume parsing (No LLM)
- User preferences
- Daily scheduled job fetching
- Multiple free job sources
- Job deduplication
- Match score & ranking
- Top 20 daily jobs
- Dashboard
- Save / Applied / Rejected
- Browser notifications
- Direct company apply links
- Expired job detection

---

# 🛠 Tech Stack

## Frontend
- HTML5
- CSS3
- Vanilla JavaScript

## Backend
- FastAPI
- SQLAlchemy
- APScheduler

## Database
- PostgreSQL

## Resume Parsing
- PyMuPDF

## Matching
- TF-IDF / Sentence Embeddings (non-generative)
- Cosine Similarity

---

# 📂 Project Structure

```text
JobPulse/
├── backend/
├── frontend/
├── docs/
├── prompts/
├── assets/
├── README.md
└── CLAUDE.md
```

---

# ⚙️ Development Workflow

1. Read `CLAUDE.md`
2. Read the current Phase document
3. Implement one phase only
4. Update documentation
5. Commit changes
6. Review
7. Move to the next phase

---

# 🗺 Roadmap

- [x] Documentation
- [ ] Phase 1 – Project Setup
- [ ] Phase 2 – User Profile
- [ ] Phase 3 – Resume Parser
- [ ] Phase 4 – Job Fetchers
- [ ] Phase 5 – Database & APIs
- [ ] Phase 6 – Dashboard
- [ ] Phase 7 – Matching Engine
- [ ] Phase 8 – Scheduler
- [ ] Phase 9 – Browser Notifications
- [ ] Phase 10 – Application Tracker
- [ ] Phase 11 – Final Refactor

---

# 📸 Screenshots

> Screenshots will be added as the project progresses.

---

# 🚀 Getting Started

```bash
git clone <repository-url>
cd JobPulse
```

Backend (planned):

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

---

# 📖 Documentation

Project documentation is available in the `docs/` directory.

---

# 📌 Current Status

Version: **0.1.0**

Current milestone:
- Documentation complete
- Ready to begin Phase 1

---

# 🔮 Future Ideas

- Email notifications
- Telegram bot
- Company insights
- Referral tracker
- Resume optimization
- Mobile application

These are intentionally out of scope for V1.

---

# 📄 License

This project is developed for learning and portfolio purposes.
