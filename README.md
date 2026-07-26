# Secure Device Posture Tracker

A dashboard for small organizations without IT staff to see which of
their devices have known vulnerabilities — with an AI layer that turns
raw CVE data into plain-English, prioritized guidance instead of a wall
of jargon.

Built on top of the CVE-lookup logic from the original
[port-scanner](https://github.com/EmberP06/port-scanner) project,
extended into a full-stack app with AI, deployed securely on Azure.

| Feature | What it demonstrates |
|---|---|
| Flask + Jinja dashboard | Full-stack SWE fundamentals |
| NVD CVE lookup per device/software | Security analysis, reused/extended from prior project |
| OpenAI API prioritization summary | Practical AI integration (not a gimmick chatbot) |
| Azure Key Vault (2 secrets) | Secrets never hardcoded; managed-identity access |
| Entra ID auth (Easy Auth) | Access control with zero custom auth code |
| Azure Monitor / Log Analytics | Every view is logged and auditable |

---

## Part 1 — Run it locally (Windows)

### 1. Confirm Python is installed
Open **PowerShell** and run:
```powershell
python --version
```
Need 3.9+. If it's missing, install from python.org (check "Add to PATH" during install).

### 2. Get the project onto your Windows desktop
Save all files, keeping this exact folder structure:
```
secure-device-tracker/
├── app.py
├── requirements.txt
├── data/
│   └── devices.py
├── services/
│   ├── nvd.py
│   └── ai.py
├── templates/
│   ├── dashboard.html
│   └── device_detail.html
└── infra/
    └── main.bicep
```

### 3. Open PowerShell in that folder
```powershell
cd C:\Users\<you>\Desktop\secure-device-tracker
```

### 4. Create a virtual environment
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```
If PowerShell blocks the script with an execution-policy error, run this once:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```
then re-run the activate command. Your prompt should show `(.venv)`.

### 5. Install dependencies
```powershell
pip install -r requirements.txt
```

### 6. Get your API keys
- **NVD API key** (free): https://nvd.nist.gov/developers/request-an-api-key
- **OpenAI API key**: https://platform.openai.com/api-keys (requires a small prepaid balance, a few dollars covers this whole project — not part of your Azure $200)

### 7. Create your `.env` file
PowerShell doesn't have the same `cat >> EOF` trick as Mac/Linux, so create it like this:
```powershell
@"
NVD_API_KEY=your_nvd_key_here
OPENAI_API_KEY=your_openai_key_here
USE_KEY_VAULT=false
PORT=8000
"@ | Out-File -FilePath .env -Encoding utf8
```
Then open it to double check the values pasted correctly:
```powershell
notepad .env
```

### 8. Run the app
```powershell
python app.py
```
Visit **http://localhost:8000** — you should see the dashboard with 8 demo devices, color-coded by risk. Click into any device to see the AI-generated summary and raw CVE findings.

**If a device shows an error or "unavailable"** — that's usually the NVD API rate limit (5 requests per 30 seconds without a key, more with one). Wait a few seconds and refresh.

---

## Part 2 — Deploy to Azure

### 1. Install Azure CLI (if not already)
https://learn.microsoft.com/cli/azure/install-azure-cli-windows

### 2. Log in
```powershell
az login
```
This opens a browser window — sign in with the account tied to your $200 credit.

### 3. Deploy infrastructure
```powershell
az group create --name device-tracker-rg --location eastus

az deployment group create `
  --resource-group device-tracker-rg `
  --template-file infra/main.bicep `
  --parameters nvdApiKey="YOUR_NVD_KEY" openaiApiKey="YOUR_OPENAI_KEY"
```
(Note: the backtick `` ` `` is PowerShell's line-continuation character — keep it if you're pasting multi-line, or put it all on one line without the backticks.)

Note the `webAppUrl` in the output when it finishes.

### 4. Deploy the app code
```powershell
Compress-Archive -Path app.py, requirements.txt, data, services, templates -DestinationPath app.zip -Force

az webapp deploy `
  --resource-group device-tracker-rg `
  --name <baseName-from-step-3-output> `
  --src-path app.zip `
  --type zip
```

### 5. Turn on Entra ID login
In the Azure Portal → your Web App → **Authentication** → **Add identity provider** → **Microsoft** → keep defaults → **Add**. Set **Restrict access** to "Require authentication."

### 6. Verify
Visit the `webAppUrl`, sign in with Microsoft, confirm the dashboard loads with real data.

### 7. Check logs are flowing
Portal → your Log Analytics workspace → **Logs**, run:
```kusto
AppServiceConsoleLogs
| order by TimeGenerated desc
| take 20
```

---

## Cleanup / end of credit

```powershell
az group delete --name device-tracker-rg --yes --no-wait
```
Since your $200 credit expires on the 27th regardless, decide by day 4 whether to add a payment method to keep it live for interviews, or take screenshots/a short demo video before it goes offline.

---

## Resume bullet

> Built and deployed a full-stack device vulnerability-tracking dashboard on Azure, integrating the NVD CVE database with an OpenAI-powered summarization layer to translate technical findings into prioritized, plain-English guidance for non-technical users; secured with Key Vault-managed secrets and Entra ID authentication.

## For your GitHub README / portfolio
Include an architecture diagram (App Service → Key Vault via managed identity, App Service → Log Analytics, App Service → NVD API + OpenAI API), a couple of dashboard screenshots, and a screenshot of the Log Analytics query results.
