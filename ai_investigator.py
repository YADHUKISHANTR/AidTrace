
import os
import json

from dotenv import load_dotenv
from google import genai


load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise RuntimeError(
        "GEMINI_API_KEY is missing. Check your .env file."
    )

client = genai.Client(api_key=API_KEY)


def generate_ai_analysis(investigation):
    """
    Generate an evidence-grounded analysis of an AidTrace investigation.

    The AI explains the available evidence and suggests verification steps.
    It must not invent facts or determine guilt.
    """

    prompt = f"""
You are the evidence-analysis assistant for AidTrace,
a graph-based relief-supply investigation project.

Analyze the supplied investigation data and return valid JSON only.
Do not include Markdown fences or text outside the JSON object.

EVIDENCE RULES — FOLLOW STRICTLY:

1. SOURCE OF TRUTH
- Use only the supplied investigation data.
- Treat the supplied data as the available graph-query results,
  not as proof that every reported event physically occurred.
- Never invent records, relationships, people, events, or quantities.
- If a field is missing, null, or unknown, say it is unknown.

2. REPORTED VS CONFIRMED
- Keep reported quantities separate from receipt-confirmed quantities.
- A delivery marked "reported" or "reported delivered" is a record
  of a claim, not independent proof of physical delivery.
- A receipt-confirmed quantity establishes only what the supplied
  receipt record says was confirmed.
- Calculate the unconfirmed quantity only when the supplied numbers
  support the calculation. Explain the arithmetic.
- An unconfirmed quantity does not prove loss, theft, fraud,
  diversion, or non-delivery.

3. SIMULATED AND SYNTHETIC DATA
- Check incident descriptions and statuses for words such as
  "SIMULATED", "SYNTHETIC", or "DEMO".
- Treat those records strictly as demonstration data.
- Never describe a simulated incident as a verified real-world event.
- Never use a simulated incident to claim it caused a discrepancy.
- If simulation status is unclear, state that its real-world
  status cannot be established from the supplied data.

4. FACTS VS HYPOTHESES
- Clearly separate recorded facts, evidence gaps, and hypotheses.
- A connected graph relationship does not by itself prove causation.
- Do not claim a route disruption affected a delivery unless
  the supplied evidence directly establishes that connection.
- Possible explanations must be labelled as unverified possibilities.
- Do not present a hypothesis as a finding.
- Never suggest that a simulated event reflects, represents, or hints
  at a real-world event unless separate, independent evidence is supplied.
- Do not use simulated incidents as possible explanations for real-world
  discrepancies, even with words such as "might" or "possibly".
- If an incident is simulated, exclude it from causal explanations.
  You may mention it only to explain why it cannot establish causation.
- Base possible explanations on general evidence gaps, such as missing
  receipts or recordkeeping errors, and clearly label them unverified.

5. RECOMMENDATIONS
- Suggest specific, practical steps a human investigator can verify.
- Prioritize checking original delivery records, receipts,
  recipient confirmation, timestamps, and relevant source documents.
- Recommend checking route status or warehouse stock only when
  relevant, and do not assume either explains the discrepancy.
- Do not claim an action has already been performed unless the
  supplied data explicitly establishes that it was performed.

6. CONFIDENCE AND LIMITATIONS
- Confidence describes how strongly the available records support
  the stated assessment, not whether wrongdoing occurred.
- Use "High" only for conclusions directly supported by consistent
  records. Use "Medium" for partially supported conclusions.
  Use "Low" when important evidence is missing or ambiguous.
- Explain important evidence limitations explicitly.

Return exactly this JSON structure:
{{
  "summary": "Concise summary of the evidence and discrepancy",
  "evidence_assessment": "What the records establish and what remains unknown",
  "possible_explanations": [
    "Clearly labelled, unverified possibility"
  ],
  "recommended_actions": [
    "Specific human-reviewable verification step"
  ],
  "confidence": "Low, Medium, or High",
  "limitations": [
    "Important evidence limitation"
  ]
}}

Investigation data:
{json.dumps(investigation, indent=2, default=str)}
"""

    interaction = client.interactions.create(
        model="gemini-3.5-flash-lite",
        input=prompt,
    )

    try:
        result = json.loads(interaction.output_text)

    except (json.JSONDecodeError, TypeError) as exc:
        raise ValueError(
            "Gemini returned a response that was not valid JSON."
        ) from exc

    if not isinstance(result, dict):
        raise ValueError(
            "Gemini response must be a JSON object."
        )

    required_fields = [
        "summary",
        "evidence_assessment",
        "possible_explanations",
        "recommended_actions",
        "confidence",
        "limitations",
    ]

    for field in required_fields:
        if field not in result:
            raise ValueError(
                f"Gemini response is missing the '{field}' field."
            )

    for field in ["summary", "evidence_assessment"]:
        if not isinstance(result[field], str):
            raise ValueError(
                f"Gemini field '{field}' must be a string."
            )

    for field in [
        "possible_explanations",
        "recommended_actions",
        "limitations",
    ]:
        if not isinstance(result[field], list) or not all(
            isinstance(item, str) for item in result[field]
        ):
            raise ValueError(
                f"Gemini field '{field}' must be a list of strings."
            )

    if result["confidence"] not in ["Low", "Medium", "High"]:
        raise ValueError(
            "Gemini confidence must be Low, Medium, or High."
        )

    if investigation.get("gap", 0) > 0:
        if result["confidence"] == "High":
            result["confidence"] = "Medium"

    if investigation.get("incident_is_simulated"):
        incident_terms = [
            "simulated incident caused",
            "simulated disruption caused",
            "real-world transit delays",
            "real world transit delays",
        ]

        result["possible_explanations"] = [
            explanation
            for explanation in result["possible_explanations"]
            if not any(
                term in explanation.lower()
                for term in incident_terms
            )
        ]

    return result
