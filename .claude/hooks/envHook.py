import sys
import json

d = json.load(sys.stdin)
if "docker-local.env" in d.get("tool_input", {}).get("file_path", ""):
    print("BLOCKED: Access to 'docker-local.env' is not allowed — this file contains secrets and is excluded from Claude's read permissions.", file=sys.stderr)
    sys.exit(2)
sys.exit(0)
