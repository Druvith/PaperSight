from __future__ import annotations

import json
import os
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

    def _check_condition(self, condition: str | None, data: dict[str, Any]) -> bool:
        if not condition:
            return True
        # Simple condition parser: "age < 5" or "age > 60"
        try:
            parts = condition.split()
            field = parts[0]
            op = parts[1]
            value = int(parts[2])
            actual = int(data.get(field, "0"))
            if op == "<":
                return actual < value
            elif op == ">":
                return actual > value
            elif op == "==":
                return actual == value
        except Exception:
            return True
        return True

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


def main() -> None:
    import time
    
    engine = TriageEngine()
    run_id = time.strftime("%Y%m%d-%H%M%S")
    out_dir = Path("artifacts/test_02_triage_engine/final") / run_id
    out_dir.mkdir(parents=True, exist_ok=True)

    test_cases = [
        {"patient_name": "Ramesh", "age": "67", "gender": "Male", "chief_complaint": "Chest pain", "duration": "45 minutes", "allergies": "Sulfa", "medications": "Aspirin", "referred_by": "Primary clinic"},
        {"patient_name": "Maya", "age": "43", "gender": "Female", "chief_complaint": "Fever and chills", "duration": "3 days", "allergies": "Penicillin", "medications": "Metformin", "referred_by": "ASHA worker"},
        {"patient_name": "Sara", "age": "8", "gender": "Female", "chief_complaint": "Vomiting", "duration": "Since morning", "allergies": "Peanuts", "medications": "ORS", "referred_by": "School nurse"},
        {"patient_name": "Leela", "age": "29", "gender": "Female", "chief_complaint": "Follow up for diabetes", "duration": "2 weeks", "allergies": "None", "medications": "Iron tablets", "referred_by": "Self"},
        {"patient_name": "Anil", "age": "54", "gender": "Male", "chief_complaint": "Prescription refill", "duration": "N/A", "allergies": "Ibuprofen", "medications": "Lisinopril", "referred_by": "Dr. Sen"},
        {"patient_name": "Baby", "age": "3", "gender": "Male", "chief_complaint": "Cough", "duration": "2 days", "allergies": "None", "medications": "None", "referred_by": "Mother"},
        {"patient_name": "Old Man", "age": "78", "gender": "Male", "chief_complaint": "Minor cut on finger", "duration": "1 day", "allergies": "None", "medications": "None", "referred_by": "Self"},
        {"patient_name": "Test", "age": "35", "gender": "Female", "chief_complaint": "Certificate needed", "duration": "N/A", "allergies": "None", "medications": "None", "referred_by": "Office"},
    ]

    results = []
    lines = ["Triage Scoring Engine — Mock Validation\n"]
    lines.append(f"{'Name':<12} {'Age':>4} {'Complaint':<30} {'Priority':<10} {'Wait':<10} {'Escalated':<10}")
    lines.append("-" * 80)

    passed = 0
    failed = 0
    expectations = {
        "Ramesh": "red",
        "Maya": "yellow",
        "Sara": "yellow",
        "Leela": "green",
        "Anil": "green",
        "Baby": "red",
        "Old Man": "yellow",
        "Test": "blue",
    }

    for case in test_cases:
        result = engine.evaluate(case)
        name = case["patient_name"]
        expected = expectations.get(name, "unknown")
        ok = result["priority"] == expected

        status = "PASS" if ok else "FAIL"
        if ok:
            passed += 1
        else:
            failed += 1

        esc = result["escalation_reason"] or "—"
        line = f"{name:<12} {case['age']:>4} {case['chief_complaint']:<30} {result['priority']:<10} {result['wait_time']:<10} {esc:<20} [{status}]"
        lines.append(line)
        
        result["expected"] = expected
        result["status"] = status
        results.append(result)

    lines.append("-" * 80)
    lines.append(f"\nResults: {passed}/{passed+failed} passed")
    if failed > 0:
        lines.append(f"Failed: {failed}")

    summary = "\n".join(lines)
    print(summary)

    # Save artifacts
    (out_dir / "summary.md").write_text("# Test 02 Result: Triage Engine\n\n" + summary + "\n", encoding="utf-8")
    (out_dir / "results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    (out_dir / "test_cases.json").write_text(json.dumps(test_cases, indent=2), encoding="utf-8")
    
    print(f"\nEvidence: {out_dir}")


if __name__ == "__main__":
    main()
