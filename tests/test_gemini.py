
from investigation import get_investigation
from ai_investigator import generate_ai_analysis
import json


investigation = get_investigation()

if investigation is None:
    print("No investigation found in FalkorDB.")
    raise SystemExit(1)

print("Sending investigation data to Gemini...\n")

try:
    analysis = generate_ai_analysis(investigation)
    print(json.dumps(analysis, indent=2, ensure_ascii=False))

except Exception as error:
    print(f"Gemini test failed: {error}")
