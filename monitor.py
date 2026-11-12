"""Authored fixture: this is a preview, not actual packet forwarding."""
import json
from router import select_route

ROUTES = [
    {"id": "default", "cidr": "0.0.0.0/0", "metric": 1, "egress": "internet-edge"},
    {"id": "office", "cidr": "10.42.0.0/16", "metric": 50, "egress": "private-core"},
    {"id": "service", "cidr": "10.42.7.0/24", "metric": 100, "egress": "service-net"},
]

def main():
    actual = select_route("10.42.7.19", ROUTES)
    egress = {r["id"]: r["egress"] for r in ROUTES}
    result = {"kind": "authored offline route preview", "destination": "10.42.7.19",
              "observed_route": actual, "observed_egress": egress.get(actual),
              "expected_route": "service", "expected_egress": "service-net",
              "status": "PASS" if actual == "service" else "FAIL: preview mismatch"}
    print(json.dumps(result, indent=2))
    return 0 if actual == "service" else 1

if __name__ == "__main__":
    raise SystemExit(main())
