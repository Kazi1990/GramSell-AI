from typing import Any

REQUIRED_KEYS = {"facts", "recommendations", "uncertainties", "actions", "evidence"}


def normalize_agent_output(name: str, output: Any, available_evidence: dict) -> dict:
    if not isinstance(output, dict):
        raise ValueError(f"{name} agent returned an invalid object")

    normalized = dict(output)
    for key in REQUIRED_KEYS:
        value = normalized.get(key)
        if value is None:
            normalized[key] = []
        elif not isinstance(value, list):
            normalized[key] = [value]

    if name == "action":
        status = normalized.get("action_status", "proposed")
        if status not in {"proposed", "approved", "executed", "failed"}:
            status = "proposed"
        if status == "executed":
            normalized["action_status"] = "proposed"
            normalized["execution_guard"] = "application_execution_required"
        else:
            normalized["action_status"] = status

    normalized["evidence_policy"] = "grounded_or_recorded_only"
    normalized["available_evidence"] = sorted(available_evidence.keys())
    return normalized


def grounding_summary(grounded: dict) -> dict:
    summary = {}
    for name, result in grounded.items():
        if not isinstance(result, dict):
            summary[name] = {"available": False, "reason": "invalid_tool_result"}
            continue
        summary[name] = {
            "available": bool(result.get("available")),
            "tool": result.get("tool"),
            "has_data": bool(result.get("data")),
        }
    return summary
