
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
    The AI explains evidence; it does not determine guilt or invent facts.
    """

    prompt = f"""
You are the AI investigation assistant for AidTrace,
a relief-supply evidence investigation project.

Analyze the supplied investigation data and return valid JSON only.

Rules:
- Use only the supplied data.
- Clearly distinguish confirmed facts from unverified leads.
- Never claim theft, fraud, or wrongdoing without evidence.
- Do not invent events, people, quantities, or sources.
- Treat simulated or synthetic records as demonstrations, not real-world facts.
- Explain quantity discrepancies with simple arithmetic.
- Recommend practical, human-reviewable next steps.
- If the evidence is insufficient, explicitly say so.

Return this JSON structure:
{{
  "summary": "Short investigation summary",
  "evidence_assessment": "What the records establish and what remains unknown",
  "possible_explanations": [
    "Possible explanation that still needs verification"
  ],
  "recommended_actions": [
    "Specific next step"
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

    return result
