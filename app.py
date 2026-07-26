"""
Secure Device Posture Tracker
-------------------------------
A dashboard for small organizations with no dedicated IT staff to see,
at a glance, which of their devices have known vulnerabilities and what
to fix first - explained in plain English by an AI summary, not raw
CVE IDs.

Security features:
  1. NVD API key + OpenAI API key pulled from Azure Key Vault at runtime
     via managed identity - never hardcoded, never in source control.
  2. Authentication via Azure App Service Easy Auth (Entra ID).
  3. Structured logging that flows to Azure Monitor / Log Analytics.

Run locally (Windows PowerShell):
    python -m venv .venv
    .venv\\Scripts\\Activate.ps1
    pip install -r requirements.txt
    # create .env with NVD_API_KEY, OPENAI_API_KEY, USE_KEY_VAULT=false
    python app.py
"""

import os
import logging
from flask import Flask, render_template, request, abort
from dotenv import load_dotenv

load_dotenv()  # loads .env automatically - no manual export needed

from data.devices import DEVICES, get_device
from services.nvd import scan_device
from services.ai import summarize_findings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("device-tracker")

app = Flask(__name__)

_secrets_cache = {}


def get_secret(name: str, keyvault_secret_name: str) -> str | None:
    """Fetch a secret from env var (local) or Key Vault (Azure)."""
    if name in _secrets_cache:
        return _secrets_cache[name]

    use_key_vault = os.environ.get("USE_KEY_VAULT", "false").lower() == "true"

    if not use_key_vault:
        value = os.environ.get(name)
    else:
        from azure.identity import DefaultAzureCredential
        from azure.keyvault.secrets import SecretClient

        vault_name = os.environ["KEY_VAULT_NAME"]
        vault_url = f"https://{vault_name}.vault.azure.net"
        credential = DefaultAzureCredential()
        client = SecretClient(vault_url=vault_url, credential=credential)
        value = client.get_secret(keyvault_secret_name).value
        logger.info("Retrieved %s from Key Vault", keyvault_secret_name)

    _secrets_cache[name] = value
    return value


def nvd_key():
    return get_secret("NVD_API_KEY", "nvd-api-key")


def openai_key():
    return get_secret("OPENAI_API_KEY", "openai-api-key")


def current_user():
    """App Service Easy Auth injects this header once Entra ID auth is
    enabled. Falls back to 'local-dev' when running locally."""
    return request.headers.get("X-MS-CLIENT-PRINCIPAL-NAME", "local-dev")


@app.route("/")
def dashboard():
    user = current_user()
    logger.info("Dashboard viewed by %s", user)

    summary_rows = []
    for device in DEVICES:
        scanned = scan_device(device, nvd_key())
        summary_rows.append({
            "id": scanned["id"],
            "name": scanned["name"],
            "os": f"{scanned['os']} {scanned['os_version']}",
            "risk_level": scanned["risk_level"],
        })

    # Sort riskiest devices to the top
    order = {"critical": 4, "high": 3, "medium": 2, "low": 1, "unknown": 0}
    summary_rows.sort(key=lambda r: order.get(r["risk_level"], 0), reverse=True)

    return render_template("dashboard.html", devices=summary_rows, user=user)


@app.route("/device/<int:device_id>")
def device_detail(device_id):
    user = current_user()
    device = get_device(device_id)
    if not device:
        abort(404)

    logger.info("Device %s viewed by %s", device_id, user)

    scanned = scan_device(device, nvd_key())
    ai_summary = summarize_findings(scanned["name"], scanned["findings"], openai_key())

    return render_template(
        "device_detail.html",
        device=scanned,
        ai_summary=ai_summary,
        user=user,
    )


@app.route("/healthz")
def healthz():
    return {"status": "ok"}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port, debug=True)
