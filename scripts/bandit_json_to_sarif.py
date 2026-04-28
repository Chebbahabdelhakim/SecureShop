import json
import sys
from pathlib import Path


RULE_METADATA = {
    "B105": {
        "name": "hardcoded-password-string",
        "help_uri": "https://bandit.readthedocs.io/en/latest/plugins/b105_hardcoded_password_string.html",
    },
    "B608": {
        "name": "hardcoded-sql-expressions",
        "help_uri": "https://bandit.readthedocs.io/en/latest/plugins/b608_hardcoded_sql_expressions.html",
    },
}


def level_from_severity(severity: str) -> str:
    severity = (severity or "").upper()
    if severity == "HIGH":
        return "error"
    if severity == "MEDIUM":
        return "warning"
    return "note"


def load_bandit_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def build_rule_descriptors(results: list[dict]) -> list[dict]:
    seen = {}
    for issue in results:
        test_id = issue.get("test_id", "BANDIT")
        if test_id in seen:
            continue
        meta = RULE_METADATA.get(test_id, {})
        seen[test_id] = {
            "id": test_id,
            "name": meta.get("name", issue.get("test_name", test_id)),
            "shortDescription": {"text": issue.get("issue_text", test_id)},
            "helpUri": meta.get("help_uri", issue.get("more_info", "")),
            "properties": {
                "tags": [
                    "security",
                    "sast",
                    f"severity:{(issue.get('issue_severity') or 'LOW').lower()}",
                    f"confidence:{(issue.get('issue_confidence') or 'LOW').lower()}",
                ]
            },
        }
    return list(seen.values())


def build_results(results: list[dict], repo_root: Path) -> list[dict]:
    sarif_results = []
    for issue in results:
        filename = issue.get("filename", "")
        try:
            uri = str(Path(filename).resolve().relative_to(repo_root.resolve())).replace("\\", "/")
        except ValueError:
            uri = filename.replace("\\", "/")

        message_bits = [
            issue.get("issue_text", "Bandit issue"),
            f"Severity: {issue.get('issue_severity', 'LOW')}",
            f"Confidence: {issue.get('issue_confidence', 'LOW')}",
        ]
        if issue.get("more_info"):
            message_bits.append(f"More info: {issue['more_info']}")

        sarif_results.append(
            {
                "ruleId": issue.get("test_id", "BANDIT"),
                "level": level_from_severity(issue.get("issue_severity", "LOW")),
                "message": {"text": " | ".join(message_bits)},
                "locations": [
                    {
                        "physicalLocation": {
                            "artifactLocation": {"uri": uri},
                            "region": {
                                "startLine": issue.get("line_number", 1),
                                "startColumn": 1,
                            },
                        }
                    }
                ],
                "properties": {
                    "issue_confidence": issue.get("issue_confidence", "LOW"),
                    "issue_severity": issue.get("issue_severity", "LOW"),
                    "test_name": issue.get("test_name", ""),
                    "test_id": issue.get("test_id", ""),
                    "cwe": issue.get("issue_cwe", {}),
                },
            }
        )
    return sarif_results


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: python scripts/bandit_json_to_sarif.py <input.json> <output.sarif>")
        return 1

    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])
    repo_root = Path.cwd()

    bandit_report = load_bandit_json(input_path)
    issues = bandit_report.get("results", [])

    sarif = {
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "version": "2.1.0",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "Bandit",
                        "informationUri": "https://bandit.readthedocs.io/",
                        "rules": build_rule_descriptors(issues),
                    }
                },
                "results": build_results(issues, repo_root),
            }
        ],
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(sarif, handle, indent=2)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
