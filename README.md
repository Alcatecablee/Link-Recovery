Link Recovery — MVP
Lightweight tool to find, prioritize and recommend fixes for broken links across multiple sites using automated scans and AI-powered redirect suggestions.

Overview
This repository contains an MVP for Link Recovery: a FastAPI backend and a React frontend that work together to detect 404s, score/prioritize them, and surface actionable recommendations (AI-generated) to help restore traffic from backlinks. The project is built as a focused, testable prototype with demo login and sample data to validate core product–market fit.

Key Features
Automated 404 detection and tracking
Priority scoring to surface highest-impact issues
AI-generated redirect / recovery recommendations (Emergent LLM / OpenAI GPT-4o-mini)
Multi-site monitoring (manage multiple properties)
Dashboard with real-time metrics and progress tracking
One-click scan with detailed error modals
Demo login (no OAuth required for initial testing)
Sample data included for quick testing
Tech Stack
Backend: FastAPI, async MongoDB driver
Frontend: React 19, Tailwind CSS, shadcn/ui
AI: Emergent LLM / OpenAI GPT-4o-mini (configurable API key)
Database: MongoDB
Repo Status
MVP completed with core features and over 15 REST endpoints implemented and tested.
Frontend implements a minimal login, site management, scanning UI and error detail modals.
Backend exposes dashboard statistics, scan and site management APIs, scoring and status tracking.
Sample data (three example 404s with backlinks and impressions) included for demo/testing.
Quickstart
These are generic steps to run the project locally. Adjust commands to your environment and package manager.

Clone the repo

git clone https://github.com/Alcatecablee/Link-Recovery.git
cd Link-Recovery
Backend

Create a Python virtual environment and install dependencies:
python -m venv .venv
source .venv/bin/activate (or .venv\Scripts\activate on Windows)
pip install -r backend/requirements.txt
Create a .env file (example below) and set required variables
Start the API:
uvicorn backend.main:app --reload --port 8000
Frontend

cd frontend
npm install (or pnpm / yarn)
cp .env.example .env (or configure as needed)
npm run dev
Open http://localhost:3000 (or the port your dev server uses)
.env example (adjust names to match your codebase):

MONGO_URI=mongodb://localhost:27017/link_recovery
MONGO_DB=link_recovery
EMERGENT_API_KEY=<your-emergent-or-openai-key>
OPENAI_API_KEY=<optional-if-using-openai-directly>
NEXT_PUBLIC_API_URL=http://localhost:8000
Note: If your repo uses different filenames or environment variable names, adapt accordingly.

Demo & Sample Data
A demo login flow is available for quick testing (no OAuth required).
Sample 404s and backlink data are included so you can exercise the scan, scoring and AI recommendation flows without external integrations.
API Testing
Most core endpoints are implemented and have been tested. Use the backend’s OpenAPI docs (e.g., http://localhost:8000/docs) to explore endpoints, payloads and sample responses.
Design Goals
Keep the UX simple and focused on core value: find broken links, prioritize them and provide clear remediation recommendations.
Deliver a tested prototype that demonstrates the main value before integrating more complex data sources (GSC, backlinks providers, background jobs).
Next Steps / Roadmap
Planned enhancements to move this MVP toward production readiness:

Google Search Console OAuth integration for live 404 data
Backlink provider integrations (Ahrefs, SEMrush, Moz, etc.)
Background job scheduler (Celery, RQ, or native async workers) for periodic scans
Notifications/alerts (email, Slack)
Advanced multi-site user management and hardened authentication
More robust rate limits, error handling, and monitoring
CI/CD and deploy-ready configuration
Contributing
Contributions, issues and suggestions are welcome. For a smooth collaboration:

Open issues for bugs or feature requests
Submit PRs with descriptive titles and testing notes
Keep changes scoped and document any new environment variables or configuration
Troubleshooting
If the frontend cannot reach the API, verify NEXT_PUBLIC_API_URL and cors configuration on the backend.
For AI features, ensure your EMERGENT_API_KEY / OPENAI_API_KEY is valid and has quota.
If MongoDB connection fails, confirm MONGO_URI and that the database is running and accessible.
License & Contact
License: (add your license here, e.g., MIT)
Author / Maintainer: Alcatecablee
Questions or feedback: open an issue or contact via your preferred channel
If you want, I can:

produce a ready-to-copy README.md file with this content,
add example .env.example and run scripts,
or tailor instructions to exact backend/frontend commands used in this repo — tell me which you prefer.
— GitHub Copilot Chat Assistant

