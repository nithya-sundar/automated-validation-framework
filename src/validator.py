"""
Validator module for the automated validation framework.

Design goals:
- Read structured input (CSV)
- Apply a set of reusable validation rules
- Emit a human-readable report and a pass/fail summary
- Keep logic decoupled and easy to extend
"""

from dataclasses import dataclass
from typing import Callable, List, Dict, Any, Tuple
import csv
from pathlib import Path


# ---------------------------
# Data structures
# ---------------------------

@dataclass
class ValidationIssue:
    row_index: int  # 1-based index for readability in reports
    field: str
    code: str
    severity: str  # "ERROR" or "WARN"
    message: str


@dataclass
class ValidationResult:
    passed: bool
    total_rows: int
    errors: List[ValidationIssue]
    warnings: List[ValidationIssue]


# ---------------------------
# Rule engine
# ---------------------------

RuleFunc = Callable[[Dict[str, Any], int], List[ValidationIssue]]
# A rule takes (row_dict, row_index) and returns zero or more issues.


class Validator:
    def __init__(self, rules: List[RuleFunc]) -> None:
        self.rules = rules

    def validate_rows(self, rows: List[Dict[str, Any]]) -> ValidationResult:
        errors: List[ValidationIssue] = []
        warnings: List[ValidationIssue] = []

        for idx, row in enumerate(rows, start=1):
            for rule in self.rules:
                issues = rule(row, idx)
                for issue in issues:
                    if issue.severity.upper() == "ERROR":
                        errors.append(issue)
                    else:
                        warnings.append(issue)

        passed = len(errors) == 0
        return ValidationResult(
            passed=passed,
            total_rows=len(rows),
            errors=errors,
            warnings=warnings,
        )


# ---------------------------
# Utility: CSV loader
# ---------------------------

def load_csv(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")
    with path.open("r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return list(reader)


# ---------------------------
# Built-in example rules
# ---------------------------

def require_fields(fields: List[str]) -> RuleFunc:
    """Ensure required fields are present and non-empty."""
    def _rule(row: Dict[str, Any], idx: int) -> List[ValidationIssue]:
        issues: List[ValidationIssue] = []
        for field in fields:
            value = (row.get(field) or "").strip()
            if value == "":
                issues.append(
                    ValidationIssue(
                        row_index=idx,
                        field=field,
                        code="REQUIRED_MISSING",
                        severity="ERROR",
                        message=f"Required field '{field}' is empty or missing.",
                    )
                )
        return issues
    return _rule


def field_in_set(field: str, allowed: List[str], severity: str = "ERROR") -> RuleFunc:
    """Ensure the field value is one of the allowed values."""
    allowed_set = {a.strip() for a in allowed}
    def _rule(row: Dict[str, Any], idx: int) -> List[ValidationIssue]:
        value = (row.get(field) or "").strip()
        if value and value not in allowed_set:
            return [
                ValidationIssue(
                    row_index=idx,
                    field=field,
                    code="VALUE_NOT_ALLOWED",
                    severity=severity,
                    message=f"Value '{value}' not in allowed set {sorted(allowed_set)}.",
                )
            ]
        return []
    return _rule


def unique_field(field: str) -> RuleFunc:
    """Ensure the field value is unique across all rows."""
    seen: Dict[str, int] = {}
    def _rule(row: Dict[str, Any], idx: int) -> List[ValidationIssue]:
        value = (row.get(field) or "").strip()
        if value == "":
            return []
        if value in seen:
            first_idx = seen[value]
            return [
                ValidationIssue(
                    row_index=idx,
                    field=field,
                    code="DUPLICATE_VALUE",
                    severity="ERROR",
                    message=f"Duplicate '{field}'='{value}' (first seen at row {first_idx}).",
                )
            ]
        seen[value] = idx
        return []
    return _rule


def no_placeholder_text(fields: List[str], placeholders: List[str] = None, severity: str = "WARN") -> RuleFunc:
    """
    Warn if fields contain placeholder text like 'TBD', 'N/A', '-', etc.
    """
    if placeholders is None:
        placeholders = ["TBD", "N/A", "-", "NA", "null", "None"]
    placeholders_norm = {p.lower() for p in placeholders}

    def _rule(row: Dict[str, Any], idx: int) -> List[ValidationIssue]:
        issues: List[ValidationIssue] = []
        for f in fields:
            val = (row.get(f) or "").strip()
            if val.lower() in placeholders_norm:
                issues.append(
                    ValidationIssue(
                        row_index=idx,
                        field=f,
                        code="PLACEHOLDER_VALUE",
                        severity=severity,
                        message=f"Field '{f}' contains placeholder value '{val}'.",
                    )
                )
        return issues
    return _rule


# ---------------------------
# Report writer
# ---------------------------

def write_report(result: ValidationResult, report_path: Path) -> None:
    report_lines: List[str] = []
    report_lines.append("Validation Report")
    report_lines.append("-----------------")
    report_lines.append(f"Total rows: {result.total_rows}")
    report_lines.append(f"Errors    : {len(result.errors)}")
    report_lines.append(f"Warnings  : {len(result.warnings)}")
    report_lines.append("")
    if result.errors:
        report_lines.append("Errors:")
        for e in result.errors:
            report_lines.append(
                f"  [Row {e.row_index}] {e.severity} {e.code} - {e.field}: {e.message}"
            )
        report_lines.append("")
    if result.warnings:
        report_lines.append("Warnings:")
        for w in result.warnings:
            report_lines.append(
                f"  [Row {w.row_index}] {w.severity} {w.code} - {w.field}: {w.message}"
            )
        report_lines.append("")
    report_lines.append(f"Overall Status: {'PASS' if result.passed else 'FAIL'}")

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(report_lines), encoding="utf-8")
