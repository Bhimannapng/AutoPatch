import os
import sys
import time
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from analyzer import run_analysis, run_complete_project_analysis
from llm_engine import run_llm_analysis

def test_pure_gemini_llm_library_system():
    catalog_code = '''from typing import List

class Book:
    def __init__(self, isbn: str, title: str, daily_fine: float):
        self.isbn = isbn
        self.title = title
        self.daily_fine = daily_fine

    def format_entry(self) -> str
        return f"[{self.isbn}] {self.title}"
'''
    app_code = '''from catalog import Book

def print_catalog(books):
    for i in range(len(books) + 1):
        print(books[i].format_entry())
'''
    circulation_code = '''from typing import List
from catalog import Book

def calculate_overdue_fines(books: List[Book], overdue_days: int) -> float:
    total_fine = 0.0
    for book in books:
        total_fine += book.daily_fine / overdue_days
    return total_fine
'''
    files = {
        "catalog.py": catalog_code,
        "app.py": app_code,
        "circulation.py": circulation_code
    }

    t0 = time.time()
    bugs, model_used = run_analysis(files, engine_mode="LLM")
    elapsed = time.time() - t0

    assert "Google Gemini LLM Engine" in model_used or "Model Temporarily Unavailable" in model_used
    if "Google Gemini LLM Engine" in model_used:
        assert elapsed < 35.0
        assert len(bugs) >= 2
        # Ensure catalog.py syntax error is found
        assert any(b.file_path == "catalog.py" for b in bugs)
        # Ensure app.py index error is found
        assert any(b.file_path == "app.py" for b in bugs)
        # Ensure circulation.py logic/zero-div error is found
        assert any(b.file_path == "circulation.py" for b in bugs)

def test_pure_llm_error_transparency_on_invalid_key():
    files = {"test.py": "def add(a, b): return a + b"}
    bugs, status = run_analysis(files, engine_mode="LLM", api_key="INVALID_API_KEY_999")
    assert "Model Temporarily Unavailable" in status or "API Key" in status
    assert len(bugs) == 0
