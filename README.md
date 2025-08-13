# Agentic AI DevOps Automation 🚀

An intelligent FastAPI microservice that processes free-form IT service requests, creates/updates ServiceNow incidents, and executes agentic remediation flows using modular agents (Diagnosis, Automation, Writer).

---

## 📌 Features

- 🔁 Request → plan → diagnosis → automation → summary → ServiceNow update
- 🧠 Modular agents (LLM-backed): Diagnostic, Automation (PowerShell/Bash), Writer
- 🧭 Coordinator plans steps from the request (diagnose/script/email)
- 🔒 Optional approval workflow for higher-risk changes
- 🔗 ServiceNow Table API integration (create, PATCH by `sys_id`)
- 🧪 Pytest suite (happy path, approval, reject, agent retry, script lint)

---

## 🧰 Prerequisites

- Python **3.10+**
- **PowerShell**: `pwsh` (PowerShell 7+) preferred, or `powershell.exe` on Windows (used for syntax-only lint via the PowerShell parser)
- *(Optional)* **Bash** (for `bash -n` syntax checks on Bash snippets)

> FastAPI’s dev server uses **Uvicorn**; you can run it with `uvicorn app.api.main:app --reload`. :contentReference[oaicite:0]{index=0}

---

## 📁 Project Structure

```bash
project-root/
├── app/
│ ├── api/ # FastAPI routes (/execute, /plans/.../approve, /plans/.../reject, /tasks/{id})
│ ├── agents/ # DiagnosticAgent, AutomationAgent, WriterAgent, IncidentReportAgent, CoordinatorAgent
│ ├── workflows/ # Orchestration entrypoints
│ ├── integrations/ # ServiceNow client, LLM client(s)
│ ├── core/ # task_store, models, constants
│ └── utils/ # logging/helpers
├── tests/ # pytest cases
├── postman/ # Postman collection
├── requirements.txt
├── .env # OPENAI + ServiceNow creds
└── README.md
```
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
SERVICENOW_USERNAME=integration.incidentuser
SERVICENOW_PASSWORD=yourpassword
```

3. Run the API

```bash
uvicorn app.api.main:app --reload
```

Visit: http://127.0.0.1:8000/api/v1/docs

🔌 API Endpoints

POST /api/v1/execute

Submit a request.

• If require_approval=false, the agents run immediately and the incident is resolved.

• If require_approval=true, the flow pauses and returns a status waiting_approval.

Request

```json
{
  "request": "Diagnose high CPU usage on VM-node1 and generate a mitigation script.",
  "require_approval": false
}
```

Response (auto-execute)

```json
{
  "incident_sys_id": "abc123",
  "status": "resolved",
  "diagnosis": { "...": "..." },
  "script": { "language": "powershell", "lint_passed": true, "...": "..." },
  "email_draft": "Hello team, ...",
  "servicenow_updated": true
}
```
Request (approval)

```json
{
  "request": "Limit inbound RDP on prod VMs to 10.0.0.0/24",
  "require_approval": true
}
```

Response (awaiting approval)

```json
{
  "incident_sys_id": "xyz456",
  "status": "waiting_approval",
  "plan": { "steps": ["script", "email"], "summary": "..." }
}
```

---

POST /api/v1/plans/{incident_sys_id}/approve

Resume a pending plan → executes agents and resolves the incident.

Response

```json
{
  "incident_sys_id": "xyz456",
  "status": "resolved",
  "diagnosis": { "...": "..." },
  "script": { "lint_passed": true, "...": "..." },
  "email_draft": "Hello team, ...",
  "servicenow_updated": true
}
```

---

POST /api/v1/plans/{incident_sys_id}/reject

Rejects automation, posts a work note, and leaves the incident for manual handling.

Response

```json
{
  "id": "xyz456",
  "status": "manual_intervention_required",
  "message": "Plan rejected. Incident flagged for manual investigation."
}
```

---

GET /api/v1/tasks/{incident_sys_id}

Returns current ServiceNow state, derived status (active | waiting_approval | completed) and a timeline of work notes/comments.

Response

```json
{
  "incident_sys_id": "abc123",
  "number": "INC0010023",
  "state": "6",
  "state_label": "Resolved",
  "status": "completed",
  "updates": [
    { "timestamp": "...", "author": "integration.incidentuser", "type": "work_notes", "text": "..." }
  ]
}
```
Under the hood this uses the ServiceNow Table API (create/read/patch by sys_id), and for PATCH you can include parameters like sysparm_input_display_value.

---

🧪 Tests
Use pytest with FastAPI’s TestClient pattern.

```bash
# run everything
python -m pytest -q

# or individual files
python -m pytest -q tests/test_happy_path.py
python -m pytest -q tests/test_approval_flow.py
python -m pytest -q tests/test_agent_retry.py
python -m pytest -q tests/test_script_compiles.py
```

FastAPI’s TestClient lets you call the app without a real HTTP socket, which is the recommended way to test endpoints.

---

🧩 Notes on Incident Updates
• Creating and updating incidents is done via ServiceNow Table API using POST/PATCH with the incident’s sys_id.

• Many instances enforce data policies: moving an incident to Resolved (state=6) may require close_code/close_notes (sometimes also a “Resolution code” field). Your service sets these when resolving. (Policies vary per instance.)

• sysparm_input_display_value=true lets you send display values, but using sys_id is the safest way to set reference fields.

---

📬 Postman
Import: postman/agentic_ai_collection.json and run Example A/B flows.

---

🖼 Architecture
See architecture_diagram.png for routing/orchestration at a glance.

---

🔒 Security
• No external DB by default — uses in-memory task_store + ServiceNow as the system of record.

• For multi-instance/production, replace task_store with Redis and add proper auth.

---

🙌 Credits
Built by Ankit Patil.
Powered by FastAPI, Uvicorn, OpenAI, and ServiceNow (Table API).