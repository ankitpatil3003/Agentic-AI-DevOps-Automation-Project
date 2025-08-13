# Agentic AI DevOps Automation 🚀

An intelligent FastAPI microservice that processes free-form IT service requests, creates and updates ServiceNow incidents, and executes agentic remediation flows using modular GPT agents.

---

## 📌 Features

- 🔁 End-to-end flow from request → diagnosis → automation → ServiceNow update
- 🧠 GPT-based agents: Diagnosis, Automation (PowerShell/Bash), Writer
- 📊 LangGraph-compatible modular flows
- 🔒 Approval workflow before executing high-risk operations
- 🔗 Full ServiceNow Table API integration (Incident table)

---

## 📁 Project Structure

project-root/
├── app/
│ ├── api/ # FastAPI routes
│ ├── agents/ # Modular agents (diagnosis, automation, writer)
│ ├── workflows/ # Orchestration flows (expandable)
│ ├── integrations/ # OpenAI & ServiceNow clients
│ ├── core/ # Shared models and task store
│ └── utils/ # Logger & helpers
│
├── tests/ # Pytest test suite
├── postman/ # Postman API collection
├── requirements.txt
├── .env # Local secrets (OPENAI_API_KEY, SN creds)
└── README.md

---

## ⚙️ Setup Instructions

1. **Clone repo & install dependencies**

```bash
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
```

2. Create .env file

```ini
OPENAI_API_KEY=sk-...
SERVICENOW_INSTANCE_URL=https://dev-xxxx.service-now.com
SERVICENOW_USERNAME=admin
SERVICENOW_PASSWORD=yourpassword
```

3. Run the API

```bash
uvicorn app.api.main:app --reload
```

Visit: http://127.0.0.1:8000/api/v1/docs

🚀 API Endpoints
POST /api/v1/execute
Submit a request. If require_approval=false, agents are executed immediately. Otherwise, it pauses for approval.

POST /api/v1/plans/{incident_sys_id}/approve
Trigger agents for a pending request.

POST /api/v1/plans/{incident_sys_id}/reject
Reject automation. Marks incident for manual handling.

GET /api/v1/tasks/{incident_sys_id}
Check task status & updates.

✅ Examples
🔹 Example A – Auto Execution
```bash
http
POST /api/v1/execute
{
  "request": "Diagnose high CPU usage on VM-node1 and generate a script.",
  "require_approval": false
}
```
Response:
```bash
{
  "incident_sys_id": "abc123",
  "status": "resolved",
  "diagnosis": { ... },
  "script": { ... },
  "email_draft": "...",
  "servicenow_updated": true
}
```
🔹 Example B – With Approval
```bash
POST /api/v1/execute
{
  "request": "Limit RDP on prod VMs to 10.0.0.0/24",
  "require_approval": true
}
```
Response:
```bash
{
  "incident_sys_id": "xyz456",
  "status": "awaiting_approval",
  "message": "Awaiting approval before initiating automation."
}
```
Then:
```bash
curl -X POST /api/v1/plans/xyz456/approve
```
🧪 Running Tests

pytest

Covers:

✅ Happy path execution
⏳ Approval + execution flow
❌ Rejection path
🔁 Automation retry
✔️ Lint validation of scripts

📬 Postman Collection
Import this:

postman/agentic_ai_collection.json

Run the full flow via Postman or newman.

🖼 Architecture Diagram
Included in architecture_diagram.png — see LangGraph-based orchestration and API flow.

🔒 Security Notes
No private database used — relies on memory (task_store) and ServiceNow

Replace in-memory store with Redis for multi-instance deployment

🧠 Authors & Credits
Built by Ankit Patil
Powered by FastAPI, LangGraph, OpenAI GPT, and ServiceNow PDI