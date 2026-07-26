"""
AI summary service.
Takes a device's raw CVE findings and produces a short, plain-English,
prioritized action summary for a non-technical reader (e.g. a small
business owner who has no IT staff).

Uses the OpenAI API. The API key is retrieved the same way as the NVD
key - from Key Vault in production, from an env var locally.
"""

import logging
from openai import OpenAI

logger = logging.getLogger("device-tracker")

SYSTEM_PROMPT = """You are a security assistant helping a small business owner
who has no dedicated IT staff understand vulnerabilities on their company
devices. You will be given a device name and a list of found CVEs with
severities. Write a short (3-5 sentence) plain-English summary:
1. State the overall risk level in one sentence, in plain language.
2. Name the 1-3 most important issues to fix first, in order.
3. Give one concrete, actionable next step (e.g. "update to the latest
   version" or "replace this device - it can no longer be patched").
Avoid jargon. Do not just restate the CVE IDs - explain what they mean
in practical terms."""


def summarize_findings(device_name: str, findings: list, api_key: str | None) -> str:
    if not api_key:
        return "AI summary unavailable: API key not configured."

    # Build a compact text representation of the findings for the prompt.
    lines = []
    for f in findings:
        cve_list = f.get("cves", [])
        if not cve_list or "error" in cve_list[0]:
            continue
        for cve in cve_list[:3]:
            lines.append(f"- {f['component']}: {cve['id']} ({cve['severity']}) - {cve['description'][:150]}")

    if not lines:
        return f"No significant vulnerabilities found for {device_name}. This device appears current."

    findings_text = "\n".join(lines)
    user_prompt = f"Device: {device_name}\n\nFindings:\n{findings_text}"

    try:
        client = OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=300,
            temperature=0.3,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.warning("AI summary failed for %s: %s", device_name, e)
        return "AI summary temporarily unavailable. See raw CVE findings below."
