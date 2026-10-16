
from investigation import get_investigation
import json

report = get_investigation()

if report is None:
    print("No matching investigation found.")
    raise SystemExit(0)

print(json.dumps(report, indent=2))
