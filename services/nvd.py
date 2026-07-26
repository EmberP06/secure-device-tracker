"""
NVD CVE lookup service.
Reused/adapted from the original port-scanner project's CVE lookup logic,
now applied to (software name + version) instead of (port -> service name).
"""

import logging
import time
import requests

logger = logging.getLogger("device-tracker")

NVD_BASE_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"

# Simple severity ranking so we can sort/prioritize results later.
SEVERITY_ORDER = {"CRITICAL": 4, "HIGH": 3, "MEDIUM": 2, "LOW": 1, "UNKNOWN": 0}

# Cache results per keyword so the same OS/software string (e.g. two
# devices both running "Windows 10") only hits NVD once, not once per
# device. Also cuts total request volume well under NVD's rate limit.
_cve_cache: dict[str, list] = {}

# Small delay between NVD calls. Cheap insurance against bursting past
# the rate limit when scanning several devices back-to-back on one
# dashboard load.
_REQUEST_DELAY_SECONDS = 0.4


def lookup_cves(keyword: str, api_key: str | None, limit: int = 5):
    """Query NVD for CVEs matching a keyword (e.g. 'Windows Server 2016',
    'OpenSSL 1.0.1'). Returns a list of dicts with id, description, severity.

    NVD's keyword search only matches text that appears verbatim in a CVE's
    description, so overly specific strings (build numbers, edition names)
    often return zero results even for well-known software. If the exact
    keyword returns nothing, we retry with a broadened version (drop the
    last word) once before giving up.
    """
    if keyword in _cve_cache:
        return _cve_cache[keyword]

    time.sleep(_REQUEST_DELAY_SECONDS)

    headers = {"apiKey": api_key} if api_key else {}
    params = {"keywordSearch": keyword, "resultsPerPage": limit}

    try:
        resp = requests.get(NVD_BASE_URL, headers=headers, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as e:
        logger.warning("NVD lookup failed for '%s': %s", keyword, e)
        return [{"error": f"CVE lookup temporarily unavailable for {keyword}"}]

    vulnerabilities = data.get("vulnerabilities", [])

    # Fallback: broaden the search by dropping the last token (usually a
    # build number/version/edition) and try once more.
    if not vulnerabilities and " " in keyword:
        broadened = " ".join(keyword.split(" ")[:-1])
        if broadened and broadened != keyword:
            logger.info("No results for '%s', retrying with '%s'", keyword, broadened)
            params["keywordSearch"] = broadened
            try:
                resp = requests.get(NVD_BASE_URL, headers=headers, params=params, timeout=10)
                resp.raise_for_status()
                data = resp.json()
                vulnerabilities = data.get("vulnerabilities", [])
            except requests.RequestException as e:
                logger.warning("NVD fallback lookup failed for '%s': %s", broadened, e)

    results = []
    for item in vulnerabilities:
        cve = item["cve"]
        severity = "UNKNOWN"
        try:
            metrics = cve.get("metrics", {})
            for key in ("cvssMetricV31", "cvssMetricV30"):
                if key in metrics:
                    # CVSS v3: baseSeverity lives inside cvssData
                    severity = metrics[key][0]["cvssData"].get(
                        "baseSeverity", "UNKNOWN"
                    ).upper()
                    break
            else:
                if "cvssMetricV2" in metrics:
                    # CVSS v2: baseSeverity is a sibling of cvssData, not
                    # nested inside it - the v2 spec has no severity field
                    # in the score data itself, so NVD adds it alongside.
                    severity = metrics["cvssMetricV2"][0].get(
                        "baseSeverity", "UNKNOWN"
                    ).upper()
        except (KeyError, IndexError):
            pass

        results.append({
            "id": cve["id"],
            "description": cve["descriptions"][0]["value"][:250],
            "severity": severity,
        })

    results.sort(key=lambda r: SEVERITY_ORDER.get(r["severity"], 0), reverse=True)
    _cve_cache[keyword] = results
    return results


def scan_device(device: dict, api_key: str | None):
    """Run CVE lookups for a device's OS and each piece of software.
    Returns the device dict enriched with a 'findings' list and a
    computed overall risk level."""
    findings = []

    # Search on the OS name alone first (e.g. "Windows 10") rather than
    # including the specific build/edition, since that matches real CVE
    # description text far more reliably. The fallback in lookup_cves
    # handles software strings that are too specific the same way.
    os_keyword = device["os"]
    findings.append({
        "component": f"{device['os']} {device['os_version']}",
        "cves": lookup_cves(os_keyword, api_key),
    })

    for sw in device["software"]:
        findings.append({"component": sw, "cves": lookup_cves(sw, api_key)})

    # Compute overall risk = highest severity found across all components
    highest = 0
    for f in findings:
        for cve in f["cves"]:
            sev = cve.get("severity", "UNKNOWN")
            highest = max(highest, SEVERITY_ORDER.get(sev, 0))

    risk_level = {4: "critical", 3: "high", 2: "medium", 1: "low", 0: "unknown"}[highest]

    return {**device, "findings": findings, "risk_level": risk_level}
