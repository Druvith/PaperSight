from __future__ import annotations

import json
import os
import warnings
from pathlib import Path
from typing import Any


class TriageEngine:
    """Evaluate extracted patient data against configurable triage rules."""

    PRIORITY_RANK = {"red": 3, "yellow": 2, "green": 1, "blue": 0}
    ESCALATION_ORDER = ["blue", "green", "yellow", "red"]

    def __init__(self, rules_path: Path | None = None) -> None:
        if rules_path is None:
            rules_path = self._resolve_rules_path()
        self.rules_path = rules_path
        self.raw = json.loads(rules_path.read_text(encoding="utf-8"))
        self.rules = self.raw["rules"]
        self.escalation = self.raw.get("escalation", {})

    @staticmethod
    def _resolve_rules_path() -> Path:
        """Locate triage_rules.json via env var, package root, or CWD fallback."""
        env_path = os.environ.get("TRIAGE_RULES_PATH")
        if env_path:
            path = Path(env_path)
            if path.exists():
                return path
        # Project root when running from source
        path = Path(__file__).resolve().parent.parent.parent / "triage_rules.json"
        if path.exists():
            return path
        # CWD fallback
        path = Path.cwd() / "triage_rules.json"
        if path.exists():
            return path
        raise FileNotFoundError(
            "triage_rules.json not found. Set TRIAGE_RULES_PATH or run from project root."
        )

    def _matches(self, text: str, keywords: list[str]) -> bool:
        text_lower = text.strip().lower().replace("-", " ")
        for kw in keywords:
            if kw.lower() in text_lower:
                return True
        return False

    # Whitelisted comparison operators for rule conditions.
    _CONDITION_OPS = {"<": lambda a, b: a < b, ">": lambda a, b: a > b, "==": lambda a, b: a == b}

    def _check_condition(self, condition: str | None, data: dict[str, Any]) -> bool:
        """Evaluate a numeric comparison condition like 'age < 5'.

        Returns True when the condition is absent, malformed, or the referenced
        field is missing — this keeps the engine permissive and avoids locking
        patients out of triage due to a broken rule file.
        """
        if not condition:
            return True

        parts = condition.split()
        if len(parts) != 3:
            warnings.warn(f"Malformed condition (expected 3 parts): {condition!r}")
            return True

        field, op, value_str = parts
        if op not in self._CONDITION_OPS:
            warnings.warn(f"Unsupported operator in condition: {condition!r}")
            return True

        try:
            value = int(value_str)
            actual = int(data.get(field, "0") or "0")
        except (ValueError, TypeError):
            warnings.warn(f"Non-numeric value in condition: {condition!r}")
            return True

        return self._CONDITION_OPS[op](actual, value)

    def evaluate(self, data: dict[str, Any]) -> dict[str, Any]:
        chief = str(data.get("chief_complaint", ""))
        age = int(data.get("age", "0") or "0")

        # Step 1: Find highest priority rule match
        best_priority = "blue"
        matched_rules = []

        for rule in self.rules:
            if not self._matches(chief, rule["keywords"]):
                continue
            if not self._check_condition(rule.get("condition"), data):
                continue
            matched_rules.append(rule)
            p = rule["priority"]
            if self.PRIORITY_RANK[p] > self.PRIORITY_RANK[best_priority]:
                best_priority = p

        # Step 2: Age escalation
        escalated = False
        escalation_reason = None
        if best_priority != "red":
            if age < 5 and self.escalation.get("pediatric"):
                old = best_priority
                idx = self.ESCALATION_ORDER.index(best_priority)
                best_priority = self.ESCALATION_ORDER[min(idx + 1, 3)]
                if best_priority != old:
                    escalated = True
                    escalation_reason = f"Pediatric escalation (age {age} < 5)"
            elif age > 60 and self.escalation.get("elderly"):
                old = best_priority
                idx = self.ESCALATION_ORDER.index(best_priority)
                best_priority = self.ESCALATION_ORDER[min(idx + 1, 3)]
                if best_priority != old:
                    escalated = True
                    escalation_reason = f"Elderly escalation (age {age} > 60)"

        priority_info = self.raw["priority_levels"][best_priority]

        return {
            "priority": best_priority,
            "priority_label": priority_info["label"],
            "wait_time": priority_info["wait"],
            "action": priority_info["action"],
            "matched_rules": [r["id"] for r in matched_rules],
            "matched_descriptions": [r.get("description", r["id"]) for r in matched_rules],
            "escalated": escalated,
            "escalation_reason": escalation_reason,
            "input": data,
        }
