import os
import json
import time
import zipfile
import tempfile
import shutil
from typing import List, Optional, Dict
from dotenv import load_dotenv

load_dotenv()
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

from schemas import (
    ChangeHistoryEntry,
    BugReport,
    ProjectAnalysisSummary,
    OptimizationFinding,
    SecurityFinding,
    ArchitectureFinding,
    ProjectCapacityMetrics
)

STATE_FILE = os.path.join(os.path.dirname(__file__), "history.json")

class AppState:
    def __init__(self):
        self.current_project_id: Optional[str] = None
        self.current_project_name: Optional[str] = None
        self.current_project_dir: Optional[str] = None
        self.engine_mode: str = os.getenv("AUTOPATCH_ENGINE_MODE", "LLM").upper()
        self.gemini_api_key: Optional[str] = os.getenv("GEMINI_API_KEY", None)
        
        # Files and Original Backups for Safe Rollback
        self.files_dict: Dict[str, str] = {}
        self.original_files_backup: Dict[str, str] = {}
        
        # Multi-Agent and Project-Level Findings
        self.bugs: List[BugReport] = []
        self.optimizations: List[OptimizationFinding] = []
        self.security_findings: List[SecurityFinding] = []
        self.architecture_findings: List[ArchitectureFinding] = []
        self.summary: Optional[ProjectAnalysisSummary] = None
        
        self.history: List[ChangeHistoryEntry] = []
        self.load_history()

    def set_engine_mode(self, mode: str):
        cleaned = mode.upper().strip()
        if cleaned in ("AST", "LLM", "COMBINED", "SANDBOX"):
            self.engine_mode = cleaned

    def set_gemini_api_key(self, key: str):
        self.gemini_api_key = key.strip() if key else None

    def load_history(self):
        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.history = [ChangeHistoryEntry(**item) for item in data]
            except Exception:
                self.history = []

    def save_history(self):
        try:
            with open(STATE_FILE, "w", encoding="utf-8") as f:
                json.dump([item.model_dump() for item in self.history], f, indent=2)
        except Exception:
            pass

    def add_history_entry(self, entry: ChangeHistoryEntry):
        self.history.insert(0, entry)
        self.save_history()

    def clear_history(self):
        self.history = []
        self.save_history()

    def delete_history_entry(self, entry_id: str) -> bool:
        initial_len = len(self.history)
        self.history = [h for h in self.history if h.id != entry_id]
        if len(self.history) != initial_len:
            self.save_history()
            return True
        return False

    def backup_project_files(self):
        """Creates a snapshot of the files before applying any patches for revert safety."""
        self.original_files_backup = dict(self.files_dict)

    def apply_patch_to_project(self, bug: BugReport, comment: Optional[str] = None) -> bool:
        """Applies the accepted patch to the active project files on disk and memory."""
        if not self.current_project_dir:
            return False

        target_file = os.path.join(self.current_project_dir, bug.file_path)
        if not os.path.exists(target_file):
            return False

        # Backup original content if not already backed up
        if bug.file_path not in self.original_files_backup:
            self.original_files_backup[bug.file_path] = bug.original_code

        try:
            with open(target_file, "w", encoding="utf-8") as f:
                f.write(bug.patched_code)

            self.files_dict[bug.file_path] = bug.patched_code
            bug.status = "Accepted"
            bug.review_notes = comment

            history_entry = ChangeHistoryEntry(
                id=f"hist-{int(time.time()*1000)}",
                bug_id=bug.id,
                bug_title=bug.title,
                file_path=bug.file_path,
                action="ACCEPTED",
                timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
                original_code=bug.original_code,
                patched_code=bug.patched_code,
                diff=bug.diff,
                comment=comment or "Patch accepted by engineer."
            )
            self.add_history_entry(history_entry)
            return True
        except Exception:
            return False

    def revert_patch(self, bug_id: str) -> bool:
        """Reverts an applied patch back to original code."""
        target_bug = next((b for b in self.bugs if b.id == bug_id), None)
        if not target_bug or not self.current_project_dir:
            return False

        target_file = os.path.join(self.current_project_dir, target_bug.file_path)
        original = self.original_files_backup.get(target_bug.file_path, target_bug.original_code)

        try:
            with open(target_file, "w", encoding="utf-8") as f:
                f.write(original)

            self.files_dict[target_bug.file_path] = original
            target_bug.status = "Needs Review"
            target_bug.review_notes = "Patch reverted to original version."

            history_entry = ChangeHistoryEntry(
                id=f"hist-{int(time.time()*1000)}",
                bug_id=target_bug.id,
                bug_title=target_bug.title,
                file_path=target_bug.file_path,
                action="REVERTED",
                timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
                original_code=target_bug.patched_code,
                patched_code=original,
                diff="",
                comment="Engineer rolled back this patch."
            )
            self.add_history_entry(history_entry)
            return True
        except Exception:
            return False

    def reject_patch(self, bug: BugReport, comment: Optional[str] = None) -> bool:
        """Marks patch as rejected in state and logs decision."""
        bug.status = "Rejected"
        bug.review_notes = comment

        history_entry = ChangeHistoryEntry(
            id=f"hist-{int(time.time()*1000)}",
            bug_id=bug.id,
            bug_title=bug.title,
            file_path=bug.file_path,
            action="REJECTED",
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
            original_code=bug.original_code,
            patched_code=bug.patched_code,
            diff=bug.diff,
            comment=comment or "Patch rejected during manual review."
        )
        self.add_history_entry(history_entry)
        return True

    def create_project_zip(self, apply_corrections: bool = True) -> str:
        """Creates a downloadable .zip of the project with all corrections/patches applied."""
        if not self.current_project_dir or not os.path.exists(self.current_project_dir):
            raise ValueError("No active project to download")

        temp_export_dir = tempfile.mkdtemp(prefix="autopatch_export_")
        try:
            # 1. Copy entire current project workspace to temp export directory
            for root, dirs, files in os.walk(self.current_project_dir):
                dirs[:] = [d for d in dirs if d not in ("__pycache__", ".pytest_cache", ".git", "venv", "node_modules")]
                rel_dir = os.path.relpath(root, self.current_project_dir)
                dest_dir = os.path.join(temp_export_dir, rel_dir) if rel_dir != "." else temp_export_dir
                os.makedirs(dest_dir, exist_ok=True)
                for file in files:
                    src_f = os.path.join(root, file)
                    dest_f = os.path.join(dest_dir, file)
                    shutil.copy2(src_f, dest_f)

            # 2. If apply_corrections is True, apply all verified and composed patches
            if apply_corrections and self.bugs:
                file_to_bugs: Dict[str, List[BugReport]] = {}
                for bug in self.bugs:
                    file_to_bugs.setdefault(bug.file_path, []).append(bug)

                for file_path, bugs in file_to_bugs.items():
                    # Resolve exact target file in temp_export_dir
                    target_file = os.path.join(temp_export_dir, file_path)
                    if not os.path.exists(target_file):
                        candidates = []
                        for root, _, fs in os.walk(temp_export_dir):
                            for f in fs:
                                full_cand = os.path.join(root, f)
                                rel_cand = os.path.relpath(full_cand, temp_export_dir)
                                if rel_cand.endswith(file_path) or f == os.path.basename(file_path):
                                    candidates.append(full_cand)
                        if candidates:
                            candidates.sort(key=lambda c: len(c))
                            target_file = candidates[0]

                    working_code = ""
                    if os.path.exists(target_file):
                        with open(target_file, "r", encoding="utf-8") as f:
                            working_code = f.read()

                    corrected_code: Optional[str] = None

                    # Priority 1: Composed code that differs from original
                    for b in bugs:
                        if getattr(b, "composed_code", None) and b.composed_code and b.composed_code.strip() and b.composed_code != b.original_code:
                            corrected_code = b.composed_code
                            break

                    # Priority 2: Modified files_dict from session
                    if not corrected_code and file_path in self.files_dict and self.files_dict[file_path] != self.original_files_backup.get(file_path):
                        corrected_code = self.files_dict[file_path]

                    # Priority 3: Successively apply each bug's patched_code or replacement
                    if not corrected_code and working_code:
                        cur_text = working_code
                        for b in bugs:
                            if getattr(b, "patched_code", None) and b.patched_code and b.patched_code != b.original_code:
                                if len(bugs) == 1:
                                    cur_text = b.patched_code
                                else:
                                    prob = getattr(b, "problematic_code", "") or ""
                                    fix = getattr(b, "suggested_fix", "") or ""
                                    if prob and fix and prob in cur_text:
                                        cur_text = cur_text.replace(prob, fix, 1)
                                    else:
                                        cur_text = b.patched_code
                        if cur_text != working_code:
                            corrected_code = cur_text

                    if corrected_code:
                        os.makedirs(os.path.dirname(target_file), exist_ok=True)
                        with open(target_file, "w", encoding="utf-8") as f:
                            f.write(corrected_code)

                # Reconcile cross-file contracts & function call signatures across all patched files
                try:
                    from contract_reconciler import reconcile_project_contracts
                    reconcile_project_contracts(temp_export_dir)
                except Exception:
                    pass

            # 3. Create ZIP archive from temp_export_dir
            temp_zip = tempfile.NamedTemporaryFile(suffix=".zip", delete=False)
            zip_path = temp_zip.name
            temp_zip.close()

            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
                for root, dirs, files in os.walk(temp_export_dir):
                    dirs[:] = [d for d in dirs if d not in ("__pycache__", ".pytest_cache", ".git", "venv", "node_modules")]
                    for file in files:
                        full_p = os.path.join(root, file)
                        rel_p = os.path.relpath(full_p, temp_export_dir)
                        zf.write(full_p, rel_p)

            return zip_path
        finally:
            shutil.rmtree(temp_export_dir, ignore_errors=True)

state = AppState()
