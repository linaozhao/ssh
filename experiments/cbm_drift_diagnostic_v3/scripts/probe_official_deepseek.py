"""Check an official DeepSeek credential supplied through hidden terminal input."""
from __future__ import annotations

import argparse
import getpass
import json
from pathlib import Path
import sys
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from cbm_drift_v3.common import write_json


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    key = getpass.getpass("Official DeepSeek API key (hidden): ")
    request = urllib.request.Request("https://api.deepseek.com/models", headers={"Authorization": "Bearer " + key})
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    result = {"base_url": "https://api.deepseek.com", "operation": "GET /models", "credential_source": "hidden_interactive_input", "secrets_persisted": False}
    try:
        with opener.open(request, timeout=45) as response:
            body = json.load(response)
        ids = [r["id"] for r in body["data"]]
        result.update(status="verified" if "deepseek-flash" in ids else "requested_model_not_listed", models=ids,
                      requested_model="DeepSeek-V4.1-Flash", api_model="deepseek-flash",
                      mapping_source="https://api-docs.deepseek.com/updates/")
    except urllib.error.HTTPError as exc:
        result.update(status="authentication_failed" if exc.code in (401, 403) else "http_error", http_status=exc.code)
    except (urllib.error.URLError, TimeoutError, ValueError, KeyError) as exc:
        result.update(status="connection_or_response_failure", error_type=type(exc).__name__)
    key = ""
    write_json(args.output, result)
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["status"] == "verified" else 2


if __name__ == "__main__":
    raise SystemExit(main())
