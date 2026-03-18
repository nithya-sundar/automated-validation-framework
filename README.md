# Automated Validation Framework

## Overview
This project demonstrates how an automated validation framework can be designed to reduce manual verification effort in high‑risk release environments.

The focus of the project is not on a specific product, but on **how validation logic, integrity checks, and reporting can be automated in a structured and reusable way** using public or simulated data.

---

## Problem Statement
Manual verification of structured data and release artifacts is:
- Time‑consuming
- Prone to human error
- Difficult to scale across multiple release cycles

In regulated or customer‑visible systems, missed inconsistencies can lead to late‑stage failures.

---

## Solution Approach
This framework simulates an automation pipeline that:
1. Ingests structured input data (CSV / JSON)
2. Applies rule‑based validation checks
3. Flags missing, inconsistent, or invalid data
4. Generates a clear validation report (pass / fail summary)

The solution is designed to be:
- Reusable
- Auditable
- Easy to extend with additional validation rules

---

## High‑Level Architecture

Input Data  
→ Validation Engine  
→ Integrity Checks  
→ Report Generation  

---

## Key Features
- Configurable validation rules
- Clear error reporting
- Separation of logic and data
- Designed with quality gates in mind

---

## Technologies Used
- Python
- CSV / JSON data handling
- Basic reporting logic

---

## What This Project Demonstrates
- Automation mindset for quality assurance
- Validation‑first thinking
- Structured problem solving
- Clear technical documentation

---

## to Extend (When You’re Ready)

Add more rules like:

- **Type checks**: ensure `id` is an integer
- **Cross-field checks**: if `status == "MISSING"`, then `name` must not be empty
- **Row-level policy**: minimum number of rows, required combinations
- **Schema check**: header must match expected set
- **Threshold rule**: error if more than X% rows are invalid

**Example: type check for integer `id`:**

```python
def field_is_int(field: str, severity: str = "ERROR") -> RuleFunc:
    def _rule(row, idx):
        val = (row.get(field) or "").strip()
        if val == "":
            return []
        try:
            int(val)
            return []
        except ValueError:
            return [ValidationIssue(
                row_index=idx,
                field=field,
                code="NOT_INTEGER",
                severity=severity,
                message=f"Field '{field}' must be an integer, got '{val}'."
            )]
    return _rule

---

## Usage

1. Ensure you have Python 3.10+ installed.
2. From the repository root, run:

```bash
python -m src.run_validation
