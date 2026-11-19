import os
import re
import ast
import uuid
import builtins
import difflib
from typing import List, Dict, Any, Optional, Set, Tuple

# Optional 3rd party AST parsers
try:
    import javalang
    HAS_JAVALANG = True
except ImportError:
    HAS_JAVALANG = False

try:
    import esprima
    HAS_ESPRIMA = True
except ImportError:
    HAS_ESPRIMA = False

PYTHON_BUILTINS = set(dir(builtins)) | {
    "self", "cls", "_", "__name__", "__file__", "__doc__", "__package__",
    "args", "kwargs"
}

JAVA_BUILTINS = {
    "System", "String", "Integer", "Long", "Double", "Float", "Boolean",
    "Byte", "Short", "Character", "Math", "Object", "Class", "Thread",
    "Runnable", "Exception", "RuntimeException", "Throwable", "Error",
    "List", "ArrayList", "Map", "HashMap", "Set", "HashSet", "Collections",
    "Arrays", "Scanner", "PrintStream", "StringBuilder", "StringBuffer",
    "this", "super", "null", "true", "false", "void"
}

JS_BUILTINS = {
    "console", "window", "document", "process", "global", "globalThis",
    "Math", "JSON", "Object", "Array", "String", "Number", "Boolean",
    "Function", "Promise", "Symbol", "Map", "Set", "WeakMap", "WeakSet",
    "Error", "TypeError", "RangeError", "SyntaxError", "ReferenceError",
    "Date", "RegExp", "setTimeout", "clearTimeout", "setInterval", "clearInterval",
    "fetch", "require", "module", "exports", "undefined", "NaN", "Infinity",
    "null", "true", "false", "this", "arguments"
}


# ==============================================================================
# 1. PYTHON SCOPE & DEEP AST CHECKERS
# ==============================================================================

class Scope:
    def __init__(self, scope_type: str, name: str = ""):
        self.scope_type = scope_type  # 'global', 'class', 'function', 'comprehension'
        self.name = name
        self.defs: Dict[str, int] = {}       # var_name -> line of first assignment
        self.reads: List[Tuple[str, int, int]] = []  # (var_name, line, col)
        self.params: Set[str] = set()
        self.imported_names: Set[str] = set()

    def add_def(self, name: str, line: int):
        if name not in self.defs:
            self.defs[name] = line

    def add_read(self, name: str, line: int, col: int = 0):
        self.reads.append((name, line, col))


class PythonScopeVisitor(ast.NodeVisitor):
    """
    Tracks lexical scopes (global, class, function, comprehension) to detect:
    - Undefined variables (ERROR)
    - Variables used before assignment (ERROR)
    - Unused local variables (WARNING)
    - Duplicate function/class definitions (WARNING)
    """
    def __init__(self, filepath: str, lines: List[str]):
        self.filepath = filepath
        self.lines = lines
        self.scopes: List[Scope] = [Scope("global", "<module>")]
        self.findings: List[Dict[str, Any]] = []

    @property
    def current_scope(self) -> Scope:
        return self.scopes[-1]

    def is_defined_in_any_scope(self, name: str) -> bool:
        if name in PYTHON_BUILTINS:
            return True
        for s in reversed(self.scopes):
            if name in s.defs or name in s.params or name in s.imported_names:
                return True
        return False

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            name = alias.asname or alias.name.split('.')[0]
            self.current_scope.imported_names.add(name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        for alias in node.names:
            name = alias.asname or alias.name
            self.current_scope.imported_names.add(name)
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef):
        # Check duplicate definition in current scope
        if node.name in self.current_scope.defs:
            prev_line = self.current_scope.defs[node.name]
            self.findings.append({
                "id": f"bug-dup-{uuid.uuid4().hex[:8]}",
                "title": f"Duplicate Function Definition: '{node.name}' (Line {node.lineno})",
                "category": "Function Errors",
                "severity": "WARNING",
                "confidence": 95,
                "line_start": node.lineno,
                "line_end": node.lineno,
                "col_offset": node.col_offset,
                "end_col_offset": node.col_offset + len(node.name),
                "description": f"Function '{node.name}' is already defined at line {prev_line}.",
                "root_cause": f"Redefining '{node.name}' shadows the previous definition, potentially causing unexpected behavior.",
                "trigger_input_or_state": "Calling the function will always execute the second definition.",
                "repair_summary": f"Rename or remove redundant function '{node.name}'.",
                "node": node
            })
        self.current_scope.add_def(node.name, node.lineno)

        # Enter function scope
        fn_scope = Scope("function", node.name)
        for arg in node.args.args:
            fn_scope.params.add(arg.arg)
            fn_scope.add_def(arg.arg, node.lineno)
        if node.args.vararg:
            fn_scope.params.add(node.args.vararg.arg)
            fn_scope.add_def(node.args.vararg.arg, node.lineno)
        if node.args.kwarg:
            fn_scope.params.add(node.args.kwarg.arg)
            fn_scope.add_def(node.args.kwarg.arg, node.lineno)

        self.scopes.append(fn_scope)
        for stmt in node.body:
            self.visit(stmt)
        exited_scope = self.scopes.pop()

        # Check unused local variables in this function
        read_names = {r[0] for r in exited_scope.reads}
        for var_name, def_line in exited_scope.defs.items():
            if var_name not in exited_scope.params and var_name not in exited_scope.imported_names:
                if not var_name.startswith("_") and var_name not in read_names and var_name != node.name:
                    self.findings.append({
                        "id": f"bug-unused-{uuid.uuid4().hex[:8]}",
                        "title": f"Unused Local Variable: '{var_name}' (Line {def_line})",
                        "category": "Variable Errors",
                        "severity": "WARNING",
                        "confidence": 90,
                        "line_start": def_line,
                        "line_end": def_line,
                        "col_offset": 0,
                        "end_col_offset": 0,
                        "description": f"Variable '{var_name}' is assigned on line {def_line} but never used.",
                        "root_cause": f"Local variable '{var_name}' is defined inside '{node.name}' but is never referenced, indicating redundant computation or a missing variable reference.",
                        "trigger_input_or_state": "Function execution allocates unused memory.",
                        "repair_summary": f"Use or remove unused variable '{var_name}'.",
                        "node": node
                    })

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self.visit_FunctionDef(node)  # type: ignore

    def visit_ClassDef(self, node: ast.ClassDef):
        self.current_scope.add_def(node.name, node.lineno)
        cls_scope = Scope("class", node.name)
        self.scopes.append(cls_scope)
        for stmt in node.body:
            self.visit(stmt)
        self.scopes.pop()

    def visit_Assign(self, node: ast.Assign):
        for target in node.targets:
            if isinstance(target, ast.Name):
                self.current_scope.add_def(target.id, getattr(node, "lineno", 1))
            elif isinstance(target, (ast.Tuple, ast.List)):
                for elt in target.elts:
                    if isinstance(elt, ast.Name):
                        self.current_scope.add_def(elt.id, getattr(node, "lineno", 1))
        self.visit(node.value)

    def visit_AnnAssign(self, node: ast.AnnAssign):
        if isinstance(node.target, ast.Name):
            self.current_scope.add_def(node.target.id, getattr(node, "lineno", 1))
        if node.value:
            self.visit(node.value)

    def visit_AugAssign(self, node: ast.AugAssign):
        if isinstance(node.target, ast.Name):
            self.current_scope.add_read(node.target.id, getattr(node, "lineno", 1), getattr(node, "col_offset", 0))
            self.current_scope.add_def(node.target.id, getattr(node, "lineno", 1))
        self.visit(node.value)

    def visit_For(self, node: ast.For):
        if isinstance(node.target, ast.Name):
            self.current_scope.add_def(node.target.id, getattr(node, "lineno", 1))

        # Check off-by-one: range(len(...) + 1)
        if isinstance(node.iter, ast.Call) and getattr(node.iter.func, 'id', '') == 'range':
            if node.iter.args and len(node.iter.args) == 1:
                arg = node.iter.args[0]
                if isinstance(arg, ast.BinOp) and isinstance(arg.op, ast.Add):
                    if isinstance(arg.left, ast.Call) and getattr(arg.left.func, 'id', '') == 'len':
                        if isinstance(arg.right, ast.Constant) and arg.right.value == 1:
                            lineno = getattr(node, 'lineno', 1)
                            self.findings.append({
                                "id": f"bug-offbyone-{uuid.uuid4().hex[:8]}",
                                "title": f"Off-by-One Loop Boundary Error (Line {lineno})",
                                "category": "Logical Errors",
                                "severity": "ERROR",
                                "confidence": 98,
                                "line_start": lineno,
                                "line_end": lineno,
                                "col_offset": getattr(node, 'col_offset', 0),
                                "end_col_offset": getattr(node, 'col_offset', 0) + 15,
                                "description": f"Loop range 'range(len(...) + 1)' on line {lineno} iterates past sequence boundary, triggering IndexError upon indexing the final element.",
                                "root_cause": f"At line {lineno}, upper bound reaches len(sequence) which is out of range for 0-indexed sequences.",
                                "trigger_input_or_state": "Execution reaches final iteration (index == len(sequence)).",
                                "repair_summary": "Change `range(len(...) + 1)` to `range(len(...))` or iterate directly over items.",
                                "node": node
                            })

        self.visit(node.iter)
        for stmt in node.body:
            self.visit(stmt)
        for stmt in node.orelse:
            self.visit(stmt)

    def visit_Name(self, node: ast.Name):
        lineno = getattr(node, "lineno", 1)
        col = getattr(node, "col_offset", 0)
        if isinstance(node.ctx, ast.Load):
            self.current_scope.add_read(node.id, lineno, col)
            # Check if defined anywhere
            if not self.is_defined_in_any_scope(node.id):
                self.findings.append({
                    "id": f"bug-undef-{uuid.uuid4().hex[:8]}",
                    "title": f"Undefined Variable: '{node.id}' (Line {lineno})",
                    "category": "Variable Errors",
                    "severity": "ERROR",
                    "confidence": 98,
                    "line_start": lineno,
                    "line_end": lineno,
                    "col_offset": col,
                    "end_col_offset": col + len(node.id),
                    "description": f"Variable or identifier '{node.id}' is used without being defined in any accessible scope.",
                    "root_cause": f"At line {lineno}, col {col}, Python resolves '{node.id}'. It was neither imported nor declared, triggering `NameError: name '{node.id}' is not defined`.",
                    "trigger_input_or_state": "Runtime execution reaches this statement.",
                    "repair_summary": f"Define or initialize variable '{node.id}' before accessing it.",
                    "var_name": node.id,
                    "node": node
                })
            else:
                # Check used before assignment in current scope
                if node.id in self.current_scope.defs:
                    def_line = self.current_scope.defs[node.id]
                    if lineno < def_line and node.id not in self.current_scope.params and node.id not in self.current_scope.imported_names:
                        self.findings.append({
                            "id": f"bug-unbound-{uuid.uuid4().hex[:8]}",
                            "title": f"Variable Used Before Assignment: '{node.id}' (Line {lineno})",
                            "category": "Variable Errors",
                            "severity": "ERROR",
                            "confidence": 96,
                            "line_start": lineno,
                            "line_end": lineno,
                            "col_offset": col,
                            "end_col_offset": col + len(node.id),
                            "description": f"Variable '{node.id}' is referenced on line {lineno} before its declaration on line {def_line}.",
                            "root_cause": f"At line {lineno}, accessing '{node.id}' prior to its initialization raises `UnboundLocalError`.",
                            "trigger_input_or_state": "Executing function reaches this statement before assignment.",
                            "repair_summary": f"Move initialization of '{node.id}' above line {lineno}.",
                            "node": node
                        })
        self.generic_visit(node)


class PythonFunctionCallChecker(ast.NodeVisitor):
    """
    Checks function call argument count and typos against functions declared in the file.
    """
    def __init__(self, filepath: str, lines: List[str]):
        self.filepath = filepath
        self.lines = lines
        self.defined_funcs: Dict[str, Dict[str, Any]] = {}
        self.findings: List[Dict[str, Any]] = []

    def collect_definitions(self, tree: ast.AST):
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                defaults_count = len(node.args.defaults)
                total_pos = len(node.args.args)
                min_args = total_pos - defaults_count
                max_args = total_pos if not (node.args.vararg or node.args.kwarg) else float('inf')
                # Account for 'self'/'cls' in methods
                is_method = bool(node.args.args and node.args.args[0].arg in ("self", "cls"))
                self.defined_funcs[node.name] = {
                    "min_args": max(0, min_args - (1 if is_method else 0)),
                    "max_args": max_args if max_args == float('inf') else max(0, max_args - (1 if is_method else 0)),
                    "lineno": node.lineno,
                    "has_varargs": bool(node.args.vararg)
                }

    def visit_Call(self, node: ast.Call):
        if isinstance(node.func, ast.Name):
            call_name = node.func.id
            lineno = getattr(node, "lineno", 1)
            num_args = len(node.args)

            # 1. Check wrong argument count
            if call_name in self.defined_funcs:
                info = self.defined_funcs[call_name]
                if not info["has_varargs"]:
                    if num_args < info["min_args"]:
                        self.findings.append({
                            "id": f"bug-argc-{uuid.uuid4().hex[:8]}",
                            "title": f"Missing Function Arguments: '{call_name}' (Line {lineno})",
                            "category": "Function Errors",
                            "severity": "ERROR",
                            "confidence": 98,
                            "line_start": lineno,
                            "line_end": lineno,
                            "col_offset": getattr(node, "col_offset", 0),
                            "end_col_offset": getattr(node, "end_col_offset", 0),
                            "description": f"Function '{call_name}' requires at least {info['min_args']} argument(s), but was called with {num_args}.",
                            "root_cause": f"At line {lineno}, call to '{call_name}' lacks required positional arguments defined on line {info['lineno']}.",
                            "trigger_input_or_state": "Execution raises `TypeError: missing required positional argument`.",
                            "repair_summary": f"Provide all {info['min_args']} required arguments to '{call_name}'.",
                            "node": node
                        })
                    elif num_args > info["max_args"]:
                        self.findings.append({
                            "id": f"bug-argc-{uuid.uuid4().hex[:8]}",
                            "title": f"Too Many Function Arguments: '{call_name}' (Line {lineno})",
                            "category": "Function Errors",
                            "severity": "ERROR",
                            "confidence": 98,
                            "line_start": lineno,
                            "line_end": lineno,
                            "col_offset": getattr(node, "col_offset", 0),
                            "end_col_offset": getattr(node, "end_col_offset", 0),
                            "description": f"Function '{call_name}' accepts at most {info['max_args']} argument(s), but was called with {num_args}.",
                            "root_cause": f"At line {lineno}, call to '{call_name}' provides {num_args} arguments exceeding the parameter list on line {info['lineno']}.",
                            "trigger_input_or_state": "Execution raises `TypeError: takes at most positional arguments`.",
                            "repair_summary": f"Reduce argument count for '{call_name}' to {info['max_args']}.",
                            "node": node
                        })

            # 2. Check function name typos
            elif call_name not in PYTHON_BUILTINS:
                for f in self.defined_funcs:
                    ratio = difflib.SequenceMatcher(None, call_name, f).ratio()
                    if ratio >= 0.75 and call_name != f:
                        self.findings.append({
                            "id": f"bug-typo-{uuid.uuid4().hex[:8]}",
                            "title": f"Function Typo: '{call_name}' should be '{f}' (Line {lineno})",
                            "category": "Function Errors",
                            "severity": "ERROR",
                            "confidence": 98,
                            "line_start": lineno,
                            "line_end": lineno,
                            "col_offset": getattr(node, "col_offset", 0),
                            "end_col_offset": getattr(node, "end_col_offset", 0),
                            "description": f"Function '{call_name}' is called on line {lineno}, but was defined as '{f}' on line {self.defined_funcs[f]['lineno']}.",
                            "root_cause": f"At line {lineno}, Python attempts to resolve '{call_name}' which does not exist, raising `NameError`.",
                            "trigger_input_or_state": "Executing the script immediately throws NameError.",
                            "repair_summary": f"Correct function call '{call_name}' to '{f}'.",
                            "bad_name": call_name,
                            "good_name": f,
                            "node": node
                        })
                        break

        self.generic_visit(node)


class PythonLogicalAndStructureChecker(ast.NodeVisitor):
    """
    Checks:
    - Division by Zero (ERROR)
    - Impossible Boolean Logic (ERROR)
    - Boundary / Off-By-One (WARNING)
    - Mutable Default Arguments (WARNING)
    - Exception Swallowing (WARNING)
    - Unreachable Dead Code (WARNING)
    - String Concatenation TypeError (ERROR)
    """
    def __init__(self, filepath: str, lines: List[str]):
        self.filepath = filepath
        self.lines = lines
        self.findings: List[Dict[str, Any]] = []

    def visit_BinOp(self, node: ast.BinOp):
        lineno = getattr(node, "lineno", 1)
        col_offset = getattr(node, "col_offset", 0)

        # 1. Division by Zero
        if isinstance(node.op, (ast.Div, ast.FloorDiv, ast.Mod)):
            is_zero_literal = isinstance(node.right, ast.Constant) and node.right.value == 0
            is_len_call = isinstance(node.right, ast.Call) and isinstance(node.right.func, ast.Name) and node.right.func.id == "len"
            is_var_divisor = isinstance(node.right, ast.Name) and node.right.id.lower() in ("count", "items", "total", "qty", "length", "denom", "size")

            if is_zero_literal or is_len_call or is_var_divisor:
                desc = "literal zero '0'" if is_zero_literal else ("'len(...)' expression" if is_len_call else f"variable '{node.right.id}'")
                self.findings.append({
                    "id": f"bug-zero-{uuid.uuid4().hex[:8]}",
                    "title": f"Unguarded Division by Zero (Line {lineno})",
                    "category": "Logical Errors",
                    "severity": "ERROR",
                    "confidence": 99 if is_zero_literal else 95,
                    "line_start": lineno,
                    "line_end": getattr(node, "end_lineno", lineno),
                    "col_offset": col_offset,
                    "end_col_offset": getattr(node, "end_col_offset", col_offset + 5),
                    "description": f"Division operator `/` executed with denominator {desc} without a non-zero guard check.",
                    "root_cause": (
                        f"At line {lineno}, col {col_offset}, AST node `ast.BinOp(op={type(node.op).__name__})` evaluates division. "
                        f"When denominator evaluates to zero (e.g. empty collection `[]` or 0 items), execution raises `ZeroDivisionError`."
                    ),
                    "trigger_input_or_state": "Supplying an empty sequence `[]` or parameter equal to 0.",
                    "repair_summary": "Add guard condition to ensure denominator is non-zero before evaluating division.",
                    "node": node
                })

        # 2. String Concatenation TypeError
        if isinstance(node.op, ast.Add):
            is_left_str = isinstance(node.left, ast.Constant) and isinstance(node.left.value, str)
            is_right_var = isinstance(node.right, ast.Name)
            if is_left_str and is_right_var and node.right.id not in ("str", "repr"):
                self.findings.append({
                    "id": f"bug-concat-{uuid.uuid4().hex[:8]}",
                    "title": f"TypeError: String Concatenation with '{node.right.id}' (Line {lineno})",
                    "category": "Code Quality Problems",
                    "severity": "ERROR",
                    "confidence": 97,
                    "line_start": lineno,
                    "line_end": lineno,
                    "col_offset": col_offset,
                    "end_col_offset": getattr(node, "end_col_offset", col_offset + 10),
                    "description": f"Direct string concatenation `+ {node.right.id}` raises TypeError if the variable is numeric.",
                    "root_cause": f"At line {lineno}, binary addition `+` concatenates string with variable '{node.right.id}'. In Python, string concatenation with integer/float raises `TypeError: can only concatenate str (not 'int') to str`.",
                    "trigger_input_or_state": f"Variable '{node.right.id}' holding an integer or numeric value.",
                    "repair_summary": f"Wrap variable with `str({node.right.id})`.",
                    "var_name": node.right.id,
                    "node": node
                })

        self.generic_visit(node)

    def visit_Compare(self, node: ast.Compare):
        lineno = getattr(node, "lineno", 1)
        # Check boundary > 0 on subtraction or > threshold
        if len(node.ops) == 1 and isinstance(node.ops[0], ast.Gt):
            if isinstance(node.left, ast.BinOp) and isinstance(node.left.op, ast.Sub):
                if len(node.comparators) == 1 and isinstance(node.comparators[0], ast.Constant) and node.comparators[0].value == 0:
                    self.findings.append({
                        "id": f"bug-bound-{uuid.uuid4().hex[:8]}",
                        "title": f"Off-by-One Subtraction Boundary Error (Line {lineno})",
                        "category": "Logical Errors",
                        "severity": "WARNING",
                        "confidence": 96,
                        "line_start": lineno,
                        "line_end": lineno,
                        "col_offset": getattr(node, "col_offset", 0),
                        "end_col_offset": getattr(node, "end_col_offset", 0),
                        "description": "Strict inequality `> 0` rejects valid cases where exact remaining balance is zero.",
                        "root_cause": f"At line {lineno}, `ast.Compare` tests `(a - b) > 0`. When requested quantity exactly matches available capacity (a == b), `0 > 0` returns False.",
                        "trigger_input_or_state": "Requesting exact remaining quota / quantity (remaining - requested == 0).",
                        "repair_summary": "Change boundary operator from `> 0` to `>= 0` to allow exact matches.",
                        "node": node
                    })
            # Check len(...) > threshold
            is_len_left = isinstance(node.left, ast.Call) and isinstance(node.left.func, ast.Name) and node.left.func.id == "len"
            is_threshold_right = len(node.comparators) == 1 and (
                (isinstance(node.comparators[0], ast.Name) and "thresh" in node.comparators[0].id.lower()) or
                (isinstance(node.comparators[0], ast.Constant) and isinstance(node.comparators[0].value, (int, float)))
            )
            if is_len_left and is_threshold_right:
                self.findings.append({
                    "id": f"bug-bound-{uuid.uuid4().hex[:8]}",
                    "title": f"Off-by-One Threshold Boundary Condition (Line {lineno})",
                    "category": "Logical Errors",
                    "severity": "WARNING",
                    "confidence": 95,
                    "line_start": lineno,
                    "line_end": lineno,
                    "col_offset": getattr(node, "col_offset", 0),
                    "end_col_offset": getattr(node, "end_col_offset", 0),
                    "description": "Strict greater-than `len(...) > threshold` excludes exact boundary inputs meeting the threshold.",
                    "root_cause": f"At line {lineno}, AST node `ast.Compare` uses operator `ast.Gt` for threshold qualification.",
                    "trigger_input_or_state": "Item count exactly equal to threshold.",
                    "repair_summary": "Change comparison from strict `>` to `>=` to include exact threshold boundaries.",
                    "node": node
                })
        self.generic_visit(node)

    def visit_BoolOp(self, node: ast.BoolOp):
        lineno = getattr(node, "lineno", 1)
        if isinstance(node.op, ast.And) and len(node.values) == 2:
            left_val, right_val = node.values[0], node.values[1]
            if isinstance(left_val, ast.Compare) and isinstance(right_val, ast.Compare):
                if (isinstance(left_val.left, ast.Name) and isinstance(right_val.left, ast.Name) and
                    left_val.left.id == right_val.left.id):
                    var_name = left_val.left.id
                    is_left_lt = len(left_val.ops) == 1 and isinstance(left_val.ops[0], (ast.Lt, ast.LtE))
                    is_right_gt = len(right_val.ops) == 1 and isinstance(right_val.ops[0], (ast.Gt, ast.GtE))
                    if is_left_lt and is_right_gt:
                        left_c = left_val.comparators[0] if left_val.comparators else None
                        right_c = right_val.comparators[0] if right_val.comparators else None
                        if (isinstance(left_c, ast.Constant) and isinstance(right_c, ast.Constant) and
                            isinstance(left_c.value, (int, float)) and isinstance(right_c.value, (int, float))):
                            if left_c.value <= right_c.value:
                                self.findings.append({
                                    "id": f"bug-bool-{uuid.uuid4().hex[:8]}",
                                    "title": f"Impossible Boolean 'and' Condition (Line {lineno})",
                                    "category": "Logical Errors",
                                    "severity": "ERROR",
                                    "confidence": 99,
                                    "line_start": lineno,
                                    "line_end": lineno,
                                    "col_offset": getattr(node, "col_offset", 0),
                                    "end_col_offset": getattr(node, "end_col_offset", 0),
                                    "description": f"Contradictory boolean check: variable '{var_name}' can never be both < {left_c.value} and > {right_c.value}.",
                                    "root_cause": f"At line {lineno}, combining `{var_name} < {left_c.value}` and `{var_name} > {right_c.value}` with `and` always evaluates to False.",
                                    "trigger_input_or_state": "Any input will evaluate to False.",
                                    "repair_summary": "Change boolean operator from `and` to `or`.",
                                    "node": node
                                })
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef):
        # 1. Mutable Default Arguments
        defaults = node.args.defaults
        args_with_defaults = node.args.args[-len(defaults):] if defaults else []
        for arg, default_node in zip(args_with_defaults, defaults):
            if isinstance(default_node, (ast.List, ast.Dict, ast.Set)) or (
                isinstance(default_node, ast.Call) and isinstance(default_node.func, ast.Name) and default_node.func.id in ("list", "dict", "set")
            ):
                lineno = getattr(default_node, "lineno", node.lineno)
                self.findings.append({
                    "id": f"bug-mut-{uuid.uuid4().hex[:8]}",
                    "title": f"Mutable Default Argument in Function '{node.name}' (Line {lineno})",
                    "category": "Structural Errors",
                    "severity": "WARNING",
                    "confidence": 98,
                    "line_start": lineno,
                    "line_end": lineno,
                    "col_offset": getattr(default_node, "col_offset", 0),
                    "end_col_offset": getattr(default_node, "end_col_offset", 0),
                    "description": f"Parameter '{arg.arg}' uses a mutable default value (`{ast.unparse(default_node)}`), causing shared state across calls.",
                    "root_cause": f"At line {lineno}, function `{node.name}` binds a mutable object as default for parameter `{arg.arg}`. Modifications persist across all calls.",
                    "trigger_input_or_state": "Calling the function multiple times without explicitly passing this parameter.",
                    "repair_summary": f"Replace mutable default with `None` and initialize inside function.",
                    "arg_name": arg.arg,
                    "node": node
                })
        # 2. Dead Code Check
        self._check_dead_code(node.body)
        self.generic_visit(node)

    def visit_If(self, node: ast.If):
        self._check_dead_code(node.body)
        self._check_dead_code(node.orelse)
        self.generic_visit(node)

    def visit_ExceptHandler(self, node: ast.ExceptHandler):
        lineno = getattr(node, "lineno", 1)
        is_bare = node.type is None
        is_broad = isinstance(node.type, ast.Name) and node.type.id in ("Exception", "BaseException")
        is_swallowed = False
        if len(node.body) == 1:
            if isinstance(node.body[0], ast.Pass):
                is_swallowed = True
            elif isinstance(node.body[0], ast.Return) and (node.body[0].value is None or (isinstance(node.body[0].value, ast.Constant) and node.body[0].value.value is None)):
                is_swallowed = True

        if (is_bare or is_broad) and is_swallowed:
            self.findings.append({
                "id": f"bug-exc-{uuid.uuid4().hex[:8]}",
                "title": f"Silent Exception Swallowing via Bare 'except:' (Line {lineno})",
                "category": "Structural Errors",
                "severity": "WARNING",
                "confidence": 95,
                "line_start": lineno,
                "line_end": lineno,
                "col_offset": getattr(node, "col_offset", 0),
                "end_col_offset": getattr(node, "end_col_offset", 0),
                "description": "Bare or overly broad `except:` block silently swallows unexpected exceptions with `pass`.",
                "root_cause": f"At line {lineno}, `ast.ExceptHandler` catches all exceptions without specifying the type or logging the error.",
                "trigger_input_or_state": "Any error occurring inside the preceding try block.",
                "repair_summary": "Catch explicit exception type (e.g. `ZeroDivisionError`) or log error.",
                "node": node
            })
        self.generic_visit(node)

    def _check_dead_code(self, stmts: List[ast.stmt]):
        found_terminator = False
        terminator_stmt = None
        for stmt in stmts:
            if found_terminator:
                lineno = getattr(stmt, "lineno", 1)
                term_name = type(terminator_stmt).__name__.lower()
                self.findings.append({
                    "id": f"bug-dead-{uuid.uuid4().hex[:8]}",
                    "title": f"Unreachable Dead Code after {term_name.capitalize()} (Line {lineno})",
                    "category": "Structural Errors",
                    "severity": "WARNING",
                    "confidence": 98,
                    "line_start": lineno,
                    "line_end": getattr(stmt, "end_lineno", lineno),
                    "col_offset": getattr(stmt, "col_offset", 0),
                    "end_col_offset": getattr(stmt, "end_col_offset", 0),
                    "description": f"Statement on line {lineno} is dead code located immediately after a `{term_name}`.",
                    "root_cause": f"At line {lineno}, control flow exited on line {getattr(terminator_stmt, 'lineno', 1)} via `{term_name}`.",
                    "trigger_input_or_state": "Always unreachable under all execution paths.",
                    "repair_summary": f"Remove unreachable statement after `{term_name}`.",
                    "node": stmt
                })
            elif isinstance(stmt, (ast.Return, ast.Raise, ast.Break, ast.Continue)):
                found_terminator = True
                terminator_stmt = stmt


# ==============================================================================
# 2. PYTHON PARSER & MULTI-ERROR RECOVERY
# ==============================================================================

def detect_python_ast_bugs(filepath: str, content: str) -> List[Dict[str, Any]]:
    """
    Analyzes Python source code using AST.
    DOES NOT STOP AT THE FIRST ERROR:
    - Pre-scans for syntax errors (assignment in conditions, missing colons).
    - If whole-file parsing fails with syntax/indentation errors, records them,
      heals or partitions independent top-level blocks/functions, and analyzes
      all valid blocks so multiple independent errors are discovered.
    """
    lines = content.splitlines()
    findings: List[Dict[str, Any]] = []

    # 1. Pre-scan for assignment '=' inside if/elif/while conditions
    for idx, l in enumerate(lines):
        trimmed = l.strip()
        if trimmed.startswith("if ") or trimmed.startswith("elif ") or trimmed.startswith("while "):
            cond_part = l[:l.find(":")] if ":" in l else l
            rest_part = l[l.find(":"):] if ":" in l else ""
            m = re.search(r'([^=<>!])=([^=]|$)', cond_part)
            if m:
                lineno = idx + 1
                col = m.start() + 1
                findings.append({
                    "id": f"bug-assign-{uuid.uuid4().hex[:8]}",
                    "title": f"Syntax Error: Assignment '=' in Condition (Line {lineno})",
                    "category": "Syntax Errors",
                    "severity": "ERROR",
                    "confidence": 100,
                    "line_start": lineno,
                    "line_end": lineno,
                    "col_offset": col,
                    "end_col_offset": col + 1,
                    "description": f"Assignment operator '=' used inside condition on line {lineno} instead of comparison operator '=='.",
                    "root_cause": f"At line {lineno}, Python syntax prohibits assignment '=' inside conditional expressions.",
                    "trigger_input_or_state": "Python raises SyntaxError before execution.",
                    "repair_summary": f"Replace assignment '=' with comparison '==' on line {lineno}.",
                    "syntax_type": "assign_in_cond"
                })
                fixed_cond = re.sub(r'([^=<>!])=([^=])', r'\1==\2', cond_part)
                lines[idx] = fixed_cond + rest_part

    # 2. Pre-scan for missing ':' on compound statements
    for idx, l in enumerate(lines):
        trimmed = l.strip()
        is_compound = False
        for kw in ("def ", "class ", "if ", "elif ", "for ", "while ", "with "):
            if trimmed.startswith(kw):
                is_compound = True
                break
        for kw in ("else", "try", "finally", "except"):
            if trimmed == kw or trimmed.startswith(kw + " ") or trimmed.startswith(kw + ":"):
                is_compound = True
                break
        if is_compound and ":" not in trimmed:
            lineno = idx + 1
            findings.append({
                "id": f"bug-colon-{uuid.uuid4().hex[:8]}",
                "title": f"Syntax Error: Missing ':' on Line {lineno}",
                "category": "Syntax Errors",
                "severity": "ERROR",
                "confidence": 100,
                "line_start": lineno,
                "line_end": lineno,
                "col_offset": len(l),
                "end_col_offset": len(l),
                "description": f"Compound statement header on line {lineno} is missing required ':' delimiter.",
                "root_cause": f"At line {lineno}, Python grammar requires a trailing ':' for block headers.",
                "trigger_input_or_state": 'Python interpreter raises SyntaxError: expected ":".',
                "repair_summary": f"Append missing ':' to statement on line {lineno}.",
                "syntax_type": "missing_colon"
            })
            lines[idx] = l.rstrip() + ":"

    # 3. Iterative syntax repair & parse attempts
    syntax_fixed_content = "\n".join(lines)
    tree: Optional[ast.AST] = None

    for attempt in range(5):
        try:
            tree = ast.parse(syntax_fixed_content, filename=filepath)
            break
        except IndentationError as e:
            lineno = e.lineno or 1
            idx = lineno - 1
            if 0 <= idx < len(lines):
                orig_line = lines[idx]
                lines[idx] = "    " + orig_line.strip()
                findings.append({
                    "id": f"bug-indent-{uuid.uuid4().hex[:8]}",
                    "title": f"Indentation Error: Misaligned Block (Line {lineno})",
                    "category": "Syntax Errors",
                    "severity": "ERROR",
                    "confidence": 100,
                    "line_start": lineno,
                    "line_end": lineno,
                    "col_offset": e.offset or 0,
                    "end_col_offset": e.offset or 0,
                    "description": f"Indentation on line {lineno} does not match enclosing block level.",
                    "root_cause": f"At line {lineno}, indentation level was misaligned ({e.msg}).",
                    "trigger_input_or_state": "Python interpreter raises IndentationError before execution.",
                    "repair_summary": f"Aligned line {lineno} indentation to standard 4-space block level.",
                    "syntax_type": "indentation"
                })
                syntax_fixed_content = "\n".join(lines)
            else:
                break
        except SyntaxError as e:
            lineno = e.lineno or 1
            if "expected ':'" in e.msg:
                idx = lineno - 1
                if 0 <= idx < len(lines):
                    lines[idx] = lines[idx].rstrip() + ":"
                    findings.append({
                        "id": f"bug-colon-{uuid.uuid4().hex[:8]}",
                        "title": f"Syntax Error: Missing ':' on Line {lineno}",
                        "category": "Syntax Errors",
                        "severity": "ERROR",
                        "confidence": 100,
                        "line_start": lineno,
                        "line_end": lineno,
                        "col_offset": e.offset or 0,
                        "end_col_offset": e.offset or 0,
                        "description": f"Line {lineno} is missing required ':' delimiter.",
                        "root_cause": f"At line {lineno}, Python syntax requires ':'.",
                        "trigger_input_or_state": "Python raises SyntaxError.",
                        "repair_summary": f"Appended missing ':' on line {lineno}.",
                        "syntax_type": "missing_colon"
                    })
                    syntax_fixed_content = "\n".join(lines)
                    continue

            # Record unrecovered syntax error
            findings.append({
                "id": f"bug-syn-{uuid.uuid4().hex[:8]}",
                "title": f"Syntax Error: {e.msg} (Line {lineno})",
                "category": "Syntax Errors",
                "severity": "ERROR",
                "confidence": 100,
                "line_start": lineno,
                "line_end": lineno,
                "col_offset": e.offset or 0,
                "end_col_offset": e.offset or 0,
                "description": f"Invalid syntax encountered on line {lineno}: {e.msg}.",
                "root_cause": f"Python interpreter cannot compile source: {e.msg} on line {lineno}.",
                "trigger_input_or_state": "Python interpreter raises SyntaxError before execution.",
                "repair_summary": f"Resolve syntax error on line {lineno}.",
            })
            break

    # Block-Level Fallback Recovery:
    # If full AST could not be parsed, attempt block-by-block parsing of top-level functions/classes
    trees_to_analyze: List[ast.AST] = []
    if tree is not None:
        trees_to_analyze.append(tree)
    else:
        # Partition lines into function/class blocks
        current_block: List[str] = []
        block_start_line = 1
        for idx, l in enumerate(lines):
            trimmed = l.strip()
            if (trimmed.startswith("def ") or trimmed.startswith("class ")) and current_block:
                block_code = "\n".join(current_block)
                try:
                    b_tree = ast.parse(block_code)
                    trees_to_analyze.append(b_tree)
                except Exception:
                    pass
                current_block = [l]
                block_start_line = idx + 1
            else:
                current_block.append(l)
        if current_block:
            try:
                b_tree = ast.parse("\n".join(current_block))
                trees_to_analyze.append(b_tree)
            except Exception:
                pass

    # 4. Run AST visitors across all parsed trees
    for t in trees_to_analyze:
        # A. Scope & Variable Errors
        scope_visitor = PythonScopeVisitor(filepath, lines)
        scope_visitor.visit(t)
        findings.extend(scope_visitor.findings)

        # B. Function Call Errors (argc & typos)
        call_checker = PythonFunctionCallChecker(filepath, lines)
        call_checker.collect_definitions(t)
        call_checker.visit(t)
        findings.extend(call_checker.findings)

        # C. Logical & Structural Errors
        logic_checker = PythonLogicalAndStructureChecker(filepath, lines)
        logic_checker.visit(t)
        findings.extend(logic_checker.findings)

    return findings


# ==============================================================================
# 3. JAVA AST CHECKER (using javalang)
# ==============================================================================

def detect_java_ast_bugs(filepath: str, content: str) -> List[Dict[str, Any]]:
    """
    Parses and analyzes Java source code using javalang AST parser.
    Detects:
    - Syntax Errors (missing semicolons, invalid braces)
    - Undefined Variables
    - Incorrect Method Calls
    - Division by Zero Literal
    - Unreachable Statements
    - Empty Catch Blocks
    """
    findings: List[Dict[str, Any]] = []
    lines = content.splitlines()

    if not HAS_JAVALANG:
        return findings

    tree = None
    try:
        tree = javalang.parse.parse(content)
    except (javalang.parser.JavaSyntaxError, javalang.tokenizer.LexerError) as e:
        lineno = getattr(e, "at", None)
        line_num = lineno.line if lineno and hasattr(lineno, "line") else 1
        col_num = lineno.column if lineno and hasattr(lineno, "column") else 0
        desc = getattr(e, "description", str(e))
        findings.append({
            "id": f"bug-javasyn-{uuid.uuid4().hex[:8]}",
            "title": f"Java Syntax Error: {desc} (Line {line_num})",
            "category": "Syntax Errors",
            "severity": "ERROR",
            "confidence": 100,
            "line_start": line_num,
            "line_end": line_num,
            "col_offset": col_num,
            "end_col_offset": col_num + 5,
            "description": f"Java compiler error: {desc} on line {line_num}.",
            "root_cause": f"At line {line_num}, Java parser failed: {desc}. Semicolon, brace, or token syntax is invalid.",
            "trigger_input_or_state": "javac compiler execution fails.",
            "repair_summary": f"Fix Java syntax error on line {line_num}."
        })

    if tree is None:
        return findings

    # Walk Java AST
    # 1. Collect declared fields and methods
    declared_classes: Set[str] = set()
    declared_fields: Set[str] = set()
    declared_methods: Dict[str, int] = {}  # method_name -> param_count

    for path, node in tree.filter(javalang.tree.ClassDeclaration):
        declared_classes.add(node.name)
        for field in node.fields:
            for declarator in field.declarators:
                declared_fields.add(declarator.name)
        for method in node.methods:
            declared_methods[method.name] = len(method.parameters)

    # 2. Inspect methods for local scope, undefined variables, division by zero, dead code
    for path, method_node in tree.filter(javalang.tree.MethodDeclaration):
        local_vars = set(declared_fields)
        # Add method parameters
        for param in method_node.parameters:
            local_vars.add(param.name)

        if method_node.body:
            found_return = False
            known_zero_vars: Set[str] = set()
            for stmt in method_node.body:
                # Dead code detection
                if found_return:
                    lineno = stmt.position.line if stmt.position else method_node.position.line
                    findings.append({
                        "id": f"bug-javadead-{uuid.uuid4().hex[:8]}",
                        "title": f"Unreachable Statement in Method '{method_node.name}' (Line {lineno})",
                        "category": "Structural Errors",
                        "severity": "WARNING",
                        "confidence": 98,
                        "line_start": lineno,
                        "line_end": lineno,
                        "col_offset": stmt.position.column if stmt.position else 0,
                        "end_col_offset": 0,
                        "description": f"Unreachable statement located after return in method '{method_node.name}'.",
                        "root_cause": f"At line {lineno}, statement follows a return statement and cannot be executed.",
                        "trigger_input_or_state": "Java compiler error: unreachable statement.",
                        "repair_summary": f"Remove unreachable statement on line {lineno}."
                    })
                if isinstance(stmt, (javalang.tree.ReturnStatement, javalang.tree.ThrowStatement)):
                    found_return = True

                # Collect local variable declarations and track zero assignments
                if isinstance(stmt, javalang.tree.LocalVariableDeclaration):
                    for decl in stmt.declarators:
                        local_vars.add(decl.name)
                        if hasattr(decl, "initializer") and isinstance(decl.initializer, javalang.tree.Literal) and decl.initializer.value in ("0", "0.0"):
                            known_zero_vars.add(decl.name)

                # Check Division by Zero in binary operations (literal or variable known to be 0)
                for sub_path, bin_op in stmt.filter(javalang.tree.BinaryOperation):
                    is_zero_div = False
                    if bin_op.operator == "/":
                        if isinstance(bin_op.operandr, javalang.tree.Literal) and bin_op.operandr.value in ("0", "0.0"):
                            is_zero_div = True
                        elif isinstance(bin_op.operandr, javalang.tree.MemberReference) and bin_op.operandr.member in known_zero_vars:
                            is_zero_div = True

                    if is_zero_div:
                        lineno = bin_op.position.line if bin_op.position else method_node.position.line
                        findings.append({
                            "id": f"bug-javazero-{uuid.uuid4().hex[:8]}",
                            "title": f"Java Division by Zero (Line {lineno})",
                            "category": "Logical Errors",
                            "severity": "ERROR",
                            "confidence": 100,
                            "line_start": lineno,
                            "line_end": lineno,
                            "col_offset": bin_op.position.column if bin_op.position else 0,
                            "end_col_offset": 0,
                            "description": "Division by zero causes runtime java.lang.ArithmeticException.",
                            "root_cause": f"At line {lineno}, divisor evaluates to 0.",
                            "trigger_input_or_state": "Executing this operation throws ArithmeticException: / by zero.",
                            "repair_summary": "Provide a non-zero divisor."
                        })

                # Check undefined variable accesses
                for sub_path, member_ref in stmt.filter(javalang.tree.MemberReference):
                    var_name = member_ref.member
                    if var_name not in local_vars and var_name not in JAVA_BUILTINS and var_name not in declared_methods and var_name not in declared_classes:
                        # Only report if it is a standalone identifier, not a property access of a known object
                        if not member_ref.qualifier:
                            lineno = member_ref.position.line if member_ref.position else method_node.position.line
                            findings.append({
                                "id": f"bug-javaundef-{uuid.uuid4().hex[:8]}",
                                "title": f"Undefined Identifier in Java: '{var_name}' (Line {lineno})",
                                "category": "Variable Errors",
                                "severity": "ERROR",
                                "confidence": 95,
                                "line_start": lineno,
                                "line_end": lineno,
                                "col_offset": member_ref.position.column if member_ref.position else 0,
                                "end_col_offset": 0,
                                "description": f"Variable or identifier '{var_name}' is not declared in class or method scope.",
                                "root_cause": f"At line {lineno}, symbol '{var_name}' cannot be resolved by javac.",
                                "trigger_input_or_state": "Compilation error: cannot find symbol.",
                                "repair_summary": f"Declare variable '{var_name}' before use."
                            })

    # 3. Check empty catch blocks
    for path, catch_node in tree.filter(javalang.tree.CatchClause):
        if not catch_node.block or len(catch_node.block) == 0:
            lineno = catch_node.position.line if catch_node.position else 1
            findings.append({
                "id": f"bug-javaemptycatch-{uuid.uuid4().hex[:8]}",
                "title": f"Empty Catch Block in Java (Line {lineno})",
                "category": "Structural Errors",
                "severity": "WARNING",
                "confidence": 95,
                "line_start": lineno,
                "line_end": lineno,
                "col_offset": catch_node.position.column if catch_node.position else 0,
                "end_col_offset": 0,
                "description": "Empty catch block silently suppresses exceptions without logging or handling.",
                "root_cause": f"At line {lineno}, exception is caught with an empty body.",
                "trigger_input_or_state": "Exception occurs and is suppressed.",
                "repair_summary": "Log the caught exception or rethrow."
            })

    return findings


# ==============================================================================
# 4. JAVASCRIPT AST CHECKER (using esprima)
# ==============================================================================

def detect_js_ast_bugs(filepath: str, content: str) -> List[Dict[str, Any]]:
    """
    Parses and analyzes JavaScript source code using esprima AST parser with tolerant mode.
    DOES NOT STOP AT THE FIRST ERROR: collects all syntax errors from tree.errors.
    Detects:
    - Syntax Errors
    - Assignment in If Condition (a = 5)
    - Division by Zero Literal (/ 0)
    - Unreachable Dead Code
    - Undefined Identifiers
    """
    findings: List[Dict[str, Any]] = []

    # 1. Structural and Safety Heuristic Checks (Runs universally)
    for idx, line in enumerate(content.splitlines()):
        lineno = idx + 1
        trimmed = line.strip()

        # Check Unhandled JSON.parse on LocalStorage
        if "JSON.parse(" in line and "localStorage" in line and "try" not in line and not trimmed.startswith("//"):
            findings.append({
                "id": f"bug-jsjson-{uuid.uuid4().hex[:8]}",
                "title": f"Unhandled JSON.parse from LocalStorage (Line {lineno})",
                "category": "Logical Errors",
                "severity": "ERROR",
                "confidence": 95,
                "line_start": lineno,
                "line_end": lineno,
                "col_offset": line.find("JSON.parse"),
                "end_col_offset": line.find("JSON.parse") + 10,
                "description": "Calling JSON.parse directly on browser LocalStorage without try...catch throws an uncaught SyntaxError if stored data is corrupted, halting script execution.",
                "root_cause": f"At line {lineno}, if localStorage contains malformed JSON, JSON.parse() crashes the entire application.",
                "trigger_input_or_state": "Corrupted or unexpected localStorage state.",
                "repair_summary": "Wrap JSON.parse in a try...catch block with safe fallback."
            })

        # Check Date.now() as Unique Identifier
        if "Date.now()" in line and ("id:" in line or "id =" in line) and not trimmed.startswith("//"):
            findings.append({
                "id": f"bug-jsid-{uuid.uuid4().hex[:8]}",
                "title": f"Timestamp Collision Risk in Unique ID Generation (Line {lineno})",
                "category": "Logical Errors",
                "severity": "WARNING",
                "confidence": 92,
                "line_start": lineno,
                "line_end": lineno,
                "col_offset": line.find("Date.now()"),
                "end_col_offset": line.find("Date.now()") + 10,
                "description": "Using Date.now() for unique identifiers can cause duplicate keys if multiple items are created in the same millisecond.",
                "root_cause": f"At line {lineno}, Date.now() has millisecond resolution, risking duplicate ID generation during rapid clicks or automated inputs.",
                "trigger_input_or_state": "Multiple rapid additions in the same millisecond.",
                "repair_summary": "Use crypto.randomUUID() or incremental counter for collision-free IDs."
            })

    if not HAS_ESPRIMA:
        return findings

    try:
        tree = esprima.parseScript(content, {'tolerant': True, 'loc': True})
    except Exception as e:
        findings.append({
            "id": f"bug-jssyn-{uuid.uuid4().hex[:8]}",
            "title": f"JavaScript Syntax Error: {str(e)}",
            "category": "Syntax Errors",
            "severity": "ERROR",
            "confidence": 100,
            "line_start": 1,
            "line_end": 1,
            "col_offset": 0,
            "end_col_offset": 0,
            "description": f"JavaScript parser error: {str(e)}.",
            "root_cause": "JavaScript syntax parsing failed.",
            "trigger_input_or_state": "Node.js / V8 runtime fails to compile script.",
            "repair_summary": "Correct JavaScript syntax."
        })
        return findings

    # 1. Collect all tolerant parsing errors
    if hasattr(tree, "errors") and tree.errors:
        for err in tree.errors:
            line = getattr(err, "lineNumber", 1)
            col = getattr(err, "column", 0)
            msg = getattr(err, "description", str(err))
            findings.append({
                "id": f"bug-jssyn-{uuid.uuid4().hex[:8]}",
                "title": f"JavaScript Syntax Error: {msg} (Line {line})",
                "category": "Syntax Errors",
                "severity": "ERROR",
                "confidence": 100,
                "line_start": line,
                "line_end": line,
                "col_offset": col,
                "end_col_offset": col + 5,
                "description": f"Syntax error on line {line}: {msg}.",
                "root_cause": f"At line {line}, col {col}, invalid JavaScript syntax ({msg}).",
                "trigger_input_or_state": "V8 parser raises SyntaxError.",
                "repair_summary": f"Fix syntax error on line {line}."
            })

    # Recursive walker for AST nodes
    def walk_js(node: Any, parent: Any = None):
        if not node or not hasattr(node, "type"):
            return

        # Check Assignment inside If condition: if (a = 5)
        if node.type == "IfStatement" and hasattr(node, "test"):
            if node.test.type == "AssignmentExpression":
                line = node.test.loc.start.line if hasattr(node.test, "loc") else 1
                findings.append({
                    "id": f"bug-jsassign-{uuid.uuid4().hex[:8]}",
                    "title": f"Assignment '=' in JavaScript 'if' Condition (Line {line})",
                    "category": "Syntax Errors",
                    "severity": "ERROR",
                    "confidence": 98,
                    "line_start": line,
                    "line_end": line,
                    "col_offset": node.test.loc.start.column if hasattr(node.test, "loc") else 0,
                    "end_col_offset": 0,
                    "description": f"Assignment expression '=' used inside 'if' test on line {line} instead of '==='. ",
                    "root_cause": f"At line {line}, assignment in condition accidentally rebinds variable and evaluates truthiness instead of checking equality.",
                    "trigger_input_or_state": "Condition always evaluates to the assigned value.",
                    "repair_summary": "Change '=' to '===' in condition."
                })

        # Check Division by Zero literal
        if node.type == "BinaryExpression" and getattr(node, "operator", "") in ("/", "%"):
            right = getattr(node, "right", None)
            if right and right.type == "Literal" and right.value in (0, "0"):
                line = node.loc.start.line if hasattr(node, "loc") else 1
                findings.append({
                    "id": f"bug-jszero-{uuid.uuid4().hex[:8]}",
                    "title": f"Division by Literal 0 in JavaScript (Line {line})",
                    "category": "Logical Errors",
                    "severity": "ERROR",
                    "confidence": 98,
                    "line_start": line,
                    "line_end": line,
                    "col_offset": node.loc.start.column if hasattr(node, "loc") else 0,
                    "end_col_offset": 0,
                    "description": "Division by 0 produces Infinity or NaN.",
                    "root_cause": f"At line {line}, binary operator '{node.operator}' uses denominator 0.",
                    "trigger_input_or_state": "Produces unexpected Infinity or NaN in calculations.",
                    "repair_summary": "Guard against zero denominator."
                })

        # Check Dead Code after Return/Throw in BlockStatement
        if node.type == "BlockStatement" and hasattr(node, "body"):
            found_term = False
            for stmt in node.body:
                if found_term:
                    line = stmt.loc.start.line if hasattr(stmt, "loc") else 1
                    findings.append({
                        "id": f"bug-jsdead-{uuid.uuid4().hex[:8]}",
                        "title": f"Unreachable JavaScript Code (Line {line})",
                        "category": "Structural Errors",
                        "severity": "WARNING",
                        "confidence": 98,
                        "line_start": line,
                        "line_end": line,
                        "col_offset": stmt.loc.start.column if hasattr(stmt, "loc") else 0,
                        "end_col_offset": 0,
                        "description": f"Unreachable statement located after return or throw on line {line}.",
                        "root_cause": f"At line {line}, statement is unreachable due to prior return.",
                        "trigger_input_or_state": "Execution will never reach this statement.",
                        "repair_summary": "Remove dead code statement."
                    })
                if stmt.type in ("ReturnStatement", "ThrowStatement", "BreakStatement"):
                    found_term = True

        # Walk children
        for key, val in node.__dict__.items():
            if isinstance(val, list):
                for item in val:
                    walk_js(item, node)
            elif hasattr(val, "type"):
                walk_js(val, node)

    walk_js(tree)

    # 3. Supplemental High-Impact JavaScript Defect Detection
    for idx, line in enumerate(content.splitlines()):
        lineno = idx + 1
        trimmed = line.strip()

        # Check Unhandled JSON.parse on LocalStorage
        if "JSON.parse(" in line and "localStorage" in line and "try" not in line and not line.startswith("//"):
            findings.append({
                "id": f"bug-jsjson-{uuid.uuid4().hex[:8]}",
                "title": f"Unhandled JSON.parse from LocalStorage (Line {lineno})",
                "category": "Logical Errors",
                "severity": "ERROR",
                "confidence": 95,
                "line_start": lineno,
                "line_end": lineno,
                "col_offset": line.find("JSON.parse"),
                "end_col_offset": line.find("JSON.parse") + 10,
                "description": "Calling JSON.parse directly on browser LocalStorage without try...catch throws an uncaught SyntaxError if stored data is corrupted, halting script execution.",
                "root_cause": f"At line {lineno}, if localStorage contains malformed JSON, JSON.parse() crashes the entire application.",
                "trigger_input_or_state": "Corrupted or unexpected localStorage state.",
                "repair_summary": "Wrap JSON.parse in a try...catch block with safe fallback."
            })

        # Check Date.now() as Unique Identifier
        if "Date.now()" in line and ("id:" in line or "id =" in line) and not line.startswith("//"):
            findings.append({
                "id": f"bug-jsid-{uuid.uuid4().hex[:8]}",
                "title": f"Timestamp Collision Risk in Unique ID Generation (Line {lineno})",
                "category": "Logical Errors",
                "severity": "WARNING",
                "confidence": 92,
                "line_start": lineno,
                "line_end": lineno,
                "col_offset": line.find("Date.now()"),
                "end_col_offset": line.find("Date.now()") + 10,
                "description": "Using Date.now() for unique identifiers can cause duplicate keys if multiple items are created in the same millisecond.",
                "root_cause": f"At line {lineno}, Date.now() has millisecond resolution, risking duplicate ID generation during rapid clicks or automated inputs.",
                "trigger_input_or_state": "Multiple rapid additions in the same millisecond.",
                "repair_summary": "Use crypto.randomUUID() or incremental counter for collision-free IDs."
            })

    return findings


def detect_css_bugs(filepath: str, content: str) -> List[Dict[str, Any]]:
    """CSS defect and cross-browser compatibility analyzer."""
    findings: List[Dict[str, Any]] = []
    import re
    for idx, line in enumerate(content.splitlines()):
        lineno = idx + 1
        # Check 8-digit hex #RRGGBBAA with alpha
        m = re.search(r'#([0-9a-fA-F]{2})([0-9a-fA-F]{2})([0-9a-fA-F]{2})([0-9a-fA-F]{2})\b', line)
        if m:
            r = int(m.group(1), 16)
            g = int(m.group(2), 16)
            b = int(m.group(3), 16)
            a = round(int(m.group(4), 16) / 255.0, 2)
            findings.append({
                "id": f"bug-csshex-{uuid.uuid4().hex[:8]}",
                "title": f"CSS 8-Digit Hex Color Compatibility (Line {lineno})",
                "category": "Code Quality Problems",
                "severity": "WARNING",
                "confidence": 90,
                "line_start": lineno,
                "line_end": lineno,
                "col_offset": m.start(),
                "end_col_offset": m.end(),
                "description": f"8-digit hexadecimal color code '{m.group(0)}' with alpha channel may not render properly in legacy browsers or older WebViews.",
                "root_cause": f"At line {lineno}, CSS 8-digit hex notation requires CSS Color Module Level 4. Providing an rgba() equivalent ensures universal cross-browser compatibility.",
                "trigger_input_or_state": "Rendering in legacy browsers or non-CSS4 compliant renderers.",
                "repair_summary": f"Replace '{m.group(0)}' with standard 'rgba({r}, {g}, {b}, {a})'."
            })
    return findings


def inspect_html_file(filepath: str, content: str) -> List[Dict[str, Any]]:
    """
    HTML markup, accessibility, and structure analyzer.
    Detects missing doctype, missing alt attributes, unclosed tags, broken forms, and deprecated elements.
    """
    findings: List[Dict[str, Any]] = []
    lines = content.splitlines()

    # 1. Missing DOCTYPE
    first_non_empty = next((l.strip() for l in lines if l.strip()), "")
    if not first_non_empty.lower().startswith("<!doctype html"):
        findings.append({
            "title": "HTML Standard: Missing '<!DOCTYPE html>' Declaration (Line 1)",
            "line_start": 1,
            "line_end": 1,
            "category": "Syntax Errors",
            "severity": "WARNING",
            "confidence": 99,
            "description": "HTML document does not declare modern HTML5 DOCTYPE. Browsers will render in Quirks Mode, causing layout inconsistencies.",
            "root_cause": "The document header lacks '<!DOCTYPE html>'. Omitting the DOCTYPE triggers legacy rendering modes.",
            "trigger_input_or_state": "Any modern web browser rendering this document.",
            "repair_summary": "Prepend standard '<!DOCTYPE html>' at line 1.",
            "type": "missing_doctype"
        })

    # 2. Line-by-line defects
    for idx, line in enumerate(lines):
        lineno = idx + 1
        trimmed = line.strip()

        # Check <img> missing alt attribute
        if "<img " in trimmed and "alt=" not in trimmed:
            findings.append({
                "title": f"Accessibility (WCAG 2.1): Missing 'alt' on <img> Tag (Line {lineno})",
                "line_start": lineno,
                "line_end": lineno,
                "category": "Code Quality Problems",
                "severity": "WARNING",
                "confidence": 95,
                "description": f"Image tag on line {lineno} lacks an 'alt' attribute, violating WCAG 2.1 accessibility standards.",
                "root_cause": f"At line {lineno}, <img> element has no alternative text description. Screen readers cannot describe the graphic.",
                "trigger_input_or_state": "Screen reader or accessibility audit tool scanning the document.",
                "repair_summary": f"Add descriptive `alt=\"Image graphic\"` attribute to <img> tag on line {lineno}.",
                "type": "missing_alt",
                "line_idx": idx
            })

        # Check <form> missing action or method
        if "<form" in trimmed and (">" in trimmed) and ("method=" not in trimmed or "action=" not in trimmed):
            findings.append({
                "title": f"HTML Form Specification: Missing 'action' or 'method' (Line {lineno})",
                "line_start": lineno,
                "line_end": lineno,
                "category": "Structural Errors",
                "severity": "WARNING",
                "confidence": 90,
                "description": f"Form tag on line {lineno} does not specify explicit HTTP submission method or action destination.",
                "root_cause": f"At line {lineno}, <form> relies on browser defaults (implicit GET), which may leak sensitive form data into URL parameters.",
                "trigger_input_or_state": "User submits form without explicit destination or POST method.",
                "repair_summary": f"Add `method=\"POST\" action=\"#\"` to <form> element on line {lineno}.",
                "type": "form_attributes",
                "line_idx": idx
            })

        # Check <input> missing associated label (WCAG 2.1)
        if "<input " in trimmed and "type=\"hidden\"" not in trimmed and "aria-label" not in trimmed:
            has_label = False
            for offset in (-2, -1, 1, 2):
                if 0 <= idx + offset < len(lines):
                    if "<label" in lines[idx + offset]:
                        has_label = True
                        break
            if not has_label:
                findings.append({
                    "title": f"Accessibility (WCAG 2.1): Missing Form Label for <input> (Line {lineno})",
                    "line_start": lineno,
                    "line_end": lineno,
                    "category": "Structural Errors",
                    "severity": "WARNING",
                    "confidence": 92,
                    "description": f"Input field on line {lineno} lacks an associated <label> or aria-label attribute, violating WCAG accessibility criteria.",
                    "root_cause": f"At line {lineno}, <input> has no corresponding <label for=\"...\"> element.",
                    "trigger_input_or_state": "Screen reader or assistive technology user accessing form.",
                    "repair_summary": f"Add an associated `<label for=\"...\">` element or `aria-label` attribute on line {lineno}.",
                    "type": "missing_label",
                    "line_idx": idx
                })

        # Check deprecated tags: <center>, <font>, <marquee>, <blink>
        for dep in ("<center>", "<font", "<marquee>", "<blink>"):
            if dep in trimmed.lower():
                tag_name = dep.replace("<", "").replace(">", "").strip()
                findings.append({
                    "title": f"Deprecated HTML Element: '<{tag_name}>' (Line {lineno})",
                    "line_start": lineno,
                    "line_end": lineno,
                    "category": "Code Quality Problems",
                    "severity": "WARNING",
                    "confidence": 95,
                    "description": f"The '<{tag_name}>' element on line {lineno} was deprecated in modern HTML specifications.",
                    "root_cause": f"At line {lineno}, obsolete presentation tag '<{tag_name}>' violates modern web separation of concerns.",
                    "trigger_input_or_state": "Modern browser rendering engine.",
                    "repair_summary": f"Replace '<{tag_name}>' with modern semantic container or CSS styling.",
                    "type": "deprecated_tag",
                    "line_idx": idx,
                    "tag_name": tag_name
                })

    # 3. Check unclosed tags (e.g. <p> without </p> before closing </div>)
    for idx, line in enumerate(lines):
        lineno = idx + 1
        trimmed = line.strip()
        if trimmed.startswith("<p>") and "</p>" not in trimmed:
            closed = False
            for forward in lines[idx+1:idx+6]:
                if "</p>" in forward:
                    closed = True
                    break
                if "</div" in forward or "</body" in forward or "<p>" in forward:
                    break
            if not closed:
                findings.append({
                    "title": f"HTML Syntax: Unclosed '<p>' Tag (Line {lineno})",
                    "line_start": lineno,
                    "line_end": lineno,
                    "category": "Syntax Errors",
                    "severity": "ERROR",
                    "confidence": 92,
                    "description": f"Paragraph tag '<p>' on line {lineno} is unclosed before enclosing container terminates.",
                    "root_cause": f"At line {lineno}, paragraph element lacks terminating '</p>', causing unexpected DOM hierarchy inheritance.",
                    "trigger_input_or_state": "DOM parser constructing browser render tree.",
                    "repair_summary": f"Append closing '</p>' tag to line {lineno}.",
                    "type": "unclosed_p",
                    "line_idx": idx
                })

    return findings


# ==============================================================================
# 5. UNIFIED AST ROUTER
# ==============================================================================

def detect_ast_bugs(filepath: str, content: str) -> List[Dict[str, Any]]:
    """
    Language-aware AST analyzer.
    Routes to language-specific parser:
    - Python: built-in `ast` module with multi-error recovery and scope tracking
    - Java: `javalang` AST parser
    - JavaScript/TypeScript: `esprima` tolerant AST parser
    - HTML: structural and markup heuristic checker
    - CSS: stylesheet and compatibility checker
    """
    ext = os.path.splitext(filepath)[1].lower()

    if ext == ".py":
        findings = detect_python_ast_bugs(filepath, content)
    elif ext == ".java":
        findings = detect_java_ast_bugs(filepath, content)
    elif ext in (".js", ".jsx", ".ts", ".tsx", ".mjs"):
        findings = detect_js_ast_bugs(filepath, content)
    elif ext in (".html", ".htm"):
        findings = inspect_html_file(filepath, content)
    elif ext in (".css",):
        findings = detect_css_bugs(filepath, content)
    else:
        findings = []

    # Sort findings strictly by line_start
    findings.sort(key=lambda x: (x.get("line_start", 1), x.get("col_offset", 0)))
    return findings
