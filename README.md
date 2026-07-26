# Secure Device Posture Tracker

A dashboard for small organizations without dedicated IT staff to see which
of their devices have known vulnerabilities — with an AI layer that
translates raw CVE data into plain-English, prioritized guidance instead of
a wall of jargon.

Built on top of the CVE-lookup logic from an earlier project,
[port-scanner](https://github.com/EmberP06/port-scanner), extended into a
full-stack application with AI-assisted analysis and secure cloud
deployment.

## Demo


https://github.com/user-attachments/assets/a8c60804-10d4-484c-92d9-2838fde16bf1





## Features

| Feature | Description |
|---|---|
| Flask + Jinja dashboard | Full-stack web application with device inventory and risk views |
| NVD CVE lookup per device/software | Cross-references each device's OS and installed software against the National Vulnerability Database, including a fallback search strategy for partial matches |
| OpenAI-powered summarization | Converts raw CVE findings into a short, prioritized, plain-English action summary for non-technical readers |
| Azure Key Vault | API keys and secrets are never hardcoded; retrieved at runtime via managed identity |
| Entra ID authentication | Access control via Azure App Service Easy Auth, no custom auth code required |
| Azure Monitor / Log Analytics | Application activity is logged and queryable for auditing |
| Infrastructure as Code | Full Azure infrastructure (compute, Key Vault, logging, identity/role assignments) defined in Bicep for repeatable deployment |

## Architecture

```
Browser -> Container App (Flask)
              |
              +-- Azure Key Vault (secrets, via managed identity)
              +-- Azure Monitor / Log Analytics (logging)
              +-- NVD CVE API (vulnerability data)
              +-- OpenAI API (summarization)
```

## Tech stack

Python, Flask, NVD CVE API, OpenAI API, Azure Container Apps, Azure Key
Vault, Microsoft Entra ID, Azure Monitor, Bicep (IaC)

## Running locally

**Requirements:** Python 3.9+

```powershell
git clone https://github.com/EmberP06/secure-device-tracker.git
cd secure-device-tracker
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Create a `.env` file in the project root:
```
NVD_API_KEY=your_nvd_key_here
OPENAI_API_KEY=your_openai_key_here
USE_KEY_VAULT=false
PORT=8000
```

- Free NVD API key: https://nvd.nist.gov/developers/request-an-api-key
- OpenAI API key: https://platform.openai.com/api-keys

Run the app:
```powershell
python app.py
```

Visit `http://localhost:8000`.

## Deploying to Azure

Infrastructure is defined in `infra/main.bicep` and provisions an App
Service/Container App, Key Vault (with both API keys stored as secrets),
a Log Analytics workspace, and the managed-identity role assignment
linking them together.

```powershell
az group create --name device-tracker-rg --location eastus2

az deployment group create \
  --resource-group device-tracker-rg \
  --template-file infra/main.bicep \
  --parameters nvdApiKey="YOUR_NVD_KEY" openaiApiKey="YOUR_OPENAI_KEY"
```

Entra ID authentication is enabled via Azure Portal -> your app ->
**Authentication** -> **Add identity provider** -> **Microsoft**.

## Design notes

The demo data (`data/devices.py`) is a seeded inventory representing a
small organization's device fleet. In a production version, this would be
populated via a device inventory integration (e.g., Intune, a CMDB, or
network discovery) rather than hardcoded.

The CVE lookup includes a fallback strategy: an overly specific search
(e.g. including an OS build number) that returns no results is retried
with a broadened query, since NVD's keyword search only matches text
appearing verbatim in a CVE description.

Severity parsing handles both CVSS v3 (severity nested within score data)
and CVSS v2 (severity stored separately from score data) response formats,
since older CVEs frequently only have v2 scoring available.
