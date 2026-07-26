# Secure Device Posture Tracker

A dashboard for small organizations without dedicated IT staff to see which
of their devices have known vulnerabilities — with an AI layer that
translates raw CVE data into plain-English, prioritized guidance instead of
a wall of jargon.

Built on top of the CVE-lookup logic from an earlier project,
[port-scanner](https://github.com/EmberP06/port-scanner), extended into a
full-stack application with AI-assisted analysis and cloud deployment.

## Live demo

https://device-tracker.mangodesert-45af2103.eastus2.azurecontainerapps.io

## Video walkthrough

https://github.com/EmberP06/secure-device-tracker/raw/main/demo.mp4

## Features

| Feature | Description |
|---|---|
| Flask + Jinja dashboard | Full-stack web application with device inventory and risk views |
| NVD CVE lookup per device/software | Cross-references each device's OS and installed software against the National Vulnerability Database, including a fallback search strategy for partial matches |
| OpenAI-powered summarization | Converts raw CVE findings into a short, prioritized, plain-English action summary for non-technical readers |
| Containerized deployment | Built with Docker, hosted on Azure Container Apps, image built and pushed via Azure Container Registry |
| Infrastructure as Code | Azure infrastructure (App Service, Key Vault, logging, managed-identity role assignments) defined in Bicep (`infra/main.bicep`) |

## Architecture

```
Browser -> Azure Container App (Flask, containerized via Docker)
              |
              +-- NVD CVE API (vulnerability data)
              +-- OpenAI API (summarization)
```

## Tech stack

Python, Flask, Docker, NVD CVE API, OpenAI API, Azure Container Apps, Azure
Container Registry, Bicep (IaC)

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

## Deployment

The live demo runs on **Azure Container Apps**. The image is built and
pushed to Azure Container Registry, then deployed to the Container App:

```powershell
az acr build --registry <your-registry> --resource-group <your-rg> --image device-tracker:latest .
```

The Container App is then pointed at that image, with API keys supplied as
environment variables at the container level.

### Infrastructure as Code

`infra/main.bicep` defines a complete Azure App Service deployment
(App Service Plan, Key Vault for secrets via managed identity, a Log
Analytics workspace, and the role assignment linking them) as a
repeatable, one-command deployment path:

```powershell
az group create --name device-tracker-rg --location eastus2

az deployment group create \
  --resource-group device-tracker-rg \
  --template-file infra/main.bicep \
  --parameters nvdApiKey="YOUR_NVD_KEY" openaiApiKey="YOUR_OPENAI_KEY"
```

The live demo above runs on Container Apps rather than this App Service
path, after the App Service deployment was blocked by a regional compute
quota restriction on a new Azure subscription. Container Apps uses a
different underlying compute pool and wasn't subject to the same
restriction, so it became the deployment target for the live version.
Both paths are kept in the repo: the Bicep template represents the
original infrastructure design (including Key Vault-based secret
management), and the manual ACR build/Container Apps path is what's
actually serving the live demo.

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
