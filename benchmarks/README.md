# 📊 AutoPatch Problem Statement 02 – Comprehensive Benchmark Dataset

This directory contains the official **Ground Truth Evaluation Benchmark Dataset** for **AutoPatch (Problem Statement 02)**.

## 📁 Files Included

| File | Format | Description |
| :--- | :--- | :--- |
| `autopatch_problem_statement_02_comprehensive_dataset.csv` | CSV | Tabular format for spreadsheet analysis (Excel, Google Sheets) and statistical reporting. |
| `autopatch_problem_statement_02_comprehensive_dataset.json` | JSON | Structured JSON array for automated evaluation harnesses, CI/CD runners, and LLM benchmarking. |

---

## 🎯 Dataset Structure & Metrics

- **Total Unique Bugs:** 40 (`AP001` through `AP040`)
- **Total Test Records:** 200 ($40 \text{ bugs} \times 5 \text{ test scenarios}$)
- **Supported Languages:**
  - **Python:** 13 defects (65 test cases)
  - **Java:** 11 defects (55 test cases)
  - **JavaScript:** 11 defects (55 test cases)
  - **C:** 5 defects (25 test cases)
- **Defect Categories Covered:** Input Validation, Boundary Conditions, Null Handling, Memory Safety, Pointer Safety, Concurrency, Async Handling, Resource Management, Security Vulnerabilities, and Arithmetic/Logic Errors.

---

## 🧪 5-Tier Testing Methodology per Bug

Every single defect contains 5 standardized test kinds:
1. `primary_trigger` (T01): The exact minimal input reproducing the defect.
2. `normal_input` (T02): Validates that standard functionality works as intended.
3. `boundary_input` (T03): Tests edge values, upper/lower boundaries, and off-by-one conditions.
4. `edge_case` (T04): Validates robustness against extreme, empty, missing, or unexpected inputs.
5. `regression_check` (T05): Proves that the applied patch introduces zero regressions to existing code.

---

## 🔍 Schema (26 Standard Fields)

Each record specifies:
`test_case_id`, `bug_id`, `language`, `file_name`, `function_name`, `bug_category`, `bug_type`, `severity`, `buggy_code`, `bug_location`, `root_cause`, `trigger_input`, `expected_behavior`, `test_kind`, `test_case`, `expected_output_or_result`, `actual_output`, `test_execution_status`, `suggested_patch`, `patch_explanation`, `regression_test_purpose`, `confidence_label`, `confidence_score`, `source_type`, `human_review_required`, `notes`.
