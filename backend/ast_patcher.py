import ast
import re
import difflib
from typing import Dict, Any, Tuple, List, Optional

def generate_unified_diff(original: str, patched: str, filepath: str = "snippet.py") -> str:
    """Produces clean unified diff string."""
    orig_lines = original.splitlines(keepends=True)
    patch_lines = patched.splitlines(keepends=True)
    diff = difflib.unified_diff(
        orig_lines,
        patch_lines,
        fromfile=f"a/{filepath}",
        tofile=f"b/{filepath}",
        lineterm=""
    )
    return "".join(diff)


class TargetedMutableDefaultTransformer(ast.NodeTransformer):
    def __init__(self, target_lineno: int, arg_name: Optional[str] = None):
        self.target_lineno = target_lineno
        self.arg_name = arg_name
        self.applied = False

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self.generic_visit(node)
        defaults = node.args.defaults
        args_with_defaults = node.args.args[-len(defaults):] if defaults else []

        for i, (arg, default_node) in enumerate(zip(args_with_defaults, defaults)):
            def_lineno = getattr(default_node, "lineno", node.lineno)
            if def_lineno == self.target_lineno or (self.arg_name and arg.arg == self.arg_name):
                if isinstance(default_node, (ast.List, ast.Dict, ast.Set)):
                    # Replace default with None
                    node.args.defaults[i] = ast.Constant(value=None)
                    
                    # Create empty literal for initialization
                    if isinstance(default_node, ast.Dict):
                        empty_literal = ast.Dict(keys=[], values=[])
                    elif isinstance(default_node, ast.Set):
                        empty_literal = ast.Call(func=ast.Name(id="set", ctx=ast.Load()), args=[], keywords=[])
                    else:
                        empty_literal = ast.List(elts=[], ctx=ast.Load())

                    # Insert: if arg is None: arg = []
                    guard_stmt = ast.If(
                        test=ast.Compare(
                            left=ast.Name(id=arg.arg, ctx=ast.Load()),
                            ops=[ast.Is()],
                            comparators=[ast.Constant(value=None)]
                        ),
                        body=[ast.Assign(targets=[ast.Name(id=arg.arg, ctx=ast.Store())], value=empty_literal)],
                        orelse=[]
                    )
                    node.body.insert(0, guard_stmt)
                    self.applied = True
                    break
        return node


class TargetedZeroDivisionTransformer(ast.NodeTransformer):
    def __init__(self, target_lineno: int):
        self.target_lineno = target_lineno
        self.applied = False

    def visit_BinOp(self, node: ast.BinOp):
        self.generic_visit(node)
        if getattr(node, "lineno", 0) == self.target_lineno and isinstance(node.op, (ast.Div, ast.FloorDiv, ast.Mod)):
            self.applied = True
            # Transform to: (total / len(items)) if len(items) > 0 else 0.0
            condition = ast.Compare(
                left=node.right,
                ops=[ast.Gt()],
                comparators=[ast.Constant(value=0)]
            )
            return ast.IfExp(
                test=condition,
                body=node,
                orelse=ast.Constant(value=0.0)
            )
        return node


class TargetedBooleanLogicTransformer(ast.NodeTransformer):
    def __init__(self, target_lineno: int):
        self.target_lineno = target_lineno
        self.applied = False

    def visit_BoolOp(self, node: ast.BoolOp):
        self.generic_visit(node)
        if getattr(node, "lineno", 0) == self.target_lineno:
            if isinstance(node.op, ast.And):
                node.op = ast.Or()
                self.applied = True
            elif isinstance(node.op, ast.Or):
                node.op = ast.And()
                self.applied = True
        return node


class TargetedBoundaryTransformer(ast.NodeTransformer):
    def __init__(self, target_lineno: int):
        self.target_lineno = target_lineno
        self.applied = False

    def visit_Compare(self, node: ast.Compare):
        self.generic_visit(node)
        if getattr(node, "lineno", 0) == self.target_lineno:
            for i, op in enumerate(node.ops):
                if isinstance(op, ast.Gt):
                    node.ops[i] = ast.GtE()
                    self.applied = True
                elif isinstance(op, ast.Lt):
                    node.ops[i] = ast.LtE()
                    self.applied = True
        return node


class TargetedBareExceptTransformer(ast.NodeTransformer):
    def __init__(self, target_lineno: int):
        self.target_lineno = target_lineno
        self.applied = False

    def visit_ExceptHandler(self, node: ast.ExceptHandler):
        self.generic_visit(node)
        if getattr(node, "lineno", 0) == self.target_lineno:
            # Replace bare except with explicit ZeroDivisionError
            node.type = ast.Name(id="ZeroDivisionError", ctx=ast.Load())
            self.applied = True
        return node


class TargetedDeadCodeTransformer(ast.NodeTransformer):
    def __init__(self, target_lineno: int):
        self.target_lineno = target_lineno
        self.applied = False

    def _strip_dead_code(self, stmts: List[ast.stmt]) -> List[ast.stmt]:
        new_stmts = []
        has_returned = False
        for s in stmts:
            if has_returned and getattr(s, "lineno", 0) == self.target_lineno:
                self.applied = True
                continue
            new_stmts.append(s)
            if isinstance(s, (ast.Return, ast.Raise)):
                has_returned = True
        return new_stmts

    def visit_FunctionDef(self, node: ast.FunctionDef):
        self.generic_visit(node)
        node.body = self._strip_dead_code(node.body)
        return node

    def visit_If(self, node: ast.If):
        self.generic_visit(node)
        node.body = self._strip_dead_code(node.body)
        node.orelse = self._strip_dead_code(node.orelse)
        return node


class TargetedFunctionTypoTransformer(ast.NodeTransformer):
    def __init__(self, bad_name: str, good_name: str, target_lineno: int):
        self.bad_name = bad_name
        self.good_name = good_name
        self.target_lineno = target_lineno
        self.applied = False

    def visit_Call(self, node: ast.Call):
        self.generic_visit(node)
        if getattr(node, "lineno", 0) == self.target_lineno or not self.target_lineno:
            if isinstance(node.func, ast.Name) and node.func.id == self.bad_name:
                node.func.id = self.good_name
                self.applied = True
        return node


class TargetedConcatTransformer(ast.NodeTransformer):
    def __init__(self, var_name: str, target_lineno: int):
        self.var_name = var_name
        self.target_lineno = target_lineno
        self.applied = False

    def visit_BinOp(self, node: ast.BinOp):
        self.generic_visit(node)
        if getattr(node, "lineno", 0) == self.target_lineno and isinstance(node.op, ast.Add):
            if isinstance(node.left, ast.Constant) and isinstance(node.left.value, str):
                if isinstance(node.right, ast.Name) and (not self.var_name or node.right.id == self.var_name):
                    node.right = ast.Call(
                        func=ast.Name(id="str", ctx=ast.Load()),
                        args=[node.right],
                        keywords=[]
                    )
                    self.applied = True
            elif isinstance(node.right, ast.Constant) and isinstance(node.right.value, str):
                if isinstance(node.left, ast.Name) and (not self.var_name or node.left.id == self.var_name):
                    node.left = ast.Call(
                        func=ast.Name(id="str", ctx=ast.Load()),
                        args=[node.left],
                        keywords=[]
                    )
                    self.applied = True
        return node


def apply_syntax_line_fix(content: str, bug: Dict[str, Any]) -> str:
    """Applies a targeted line-level syntax fix (missing colon, assignment in condition, or indentation)."""
    lines = content.splitlines()
    target_idx = bug.get("line_start", 1) - 1
    syntax_type = bug.get("syntax_type", "")

    if 0 <= target_idx < len(lines):
        line = lines[target_idx]
        if syntax_type == "assign_in_cond":
            if ":" in line:
                cond_part = line[:line.find(":")]
                rest_part = line[line.find(":"):]
            else:
                cond_part = line
                rest_part = ""
            fixed_cond = re.sub(r'([^=<>!])=([^=])', r'\1==\2', cond_part)
            lines[target_idx] = fixed_cond + rest_part
        elif syntax_type == "missing_colon":
            lines[target_idx] = line.rstrip() + ":"
        elif syntax_type == "indentation":
            lines[target_idx] = "    " + line.strip()
        else:
            # Fallback for general syntax
            if not line.strip().endswith(":") and any(line.strip().startswith(kw) for kw in ("def ", "if ", "for ", "while ")):
                lines[target_idx] = line.rstrip() + ":"
            elif re.search(r'[^=<>!]=([^=]|$)', line):
                lines[target_idx] = re.sub(r'([^=<>!])=([^=])', r'\1==\2', line)

    return "\n".join(lines)


def apply_single_ast_patch(content: str, bug: Dict[str, Any], filepath: str = "snippet.py") -> Tuple[str, str]:
    """
    Applies an isolated AST transformation or syntax fix for a specific bug finding.
    Returns (patched_code, diff).
    """
    category = bug.get("category", "")
    target_lineno = bug.get("line_start", 1)

    # 1. Handle syntax line fix directly
    if bug.get("syntax_type") or "Syntax Error" in category or "Indentation" in category:
        patched_code = apply_syntax_line_fix(content, bug)
        diff = generate_unified_diff(content, patched_code, filepath)
        return patched_code, diff

    # 2. Handle function typo line fix
    if "NameError" in category or "Typo" in category:
        bad_name = bug.get("bad_name")
        good_name = bug.get("good_name")
        if bad_name and good_name:
            lines = content.splitlines()
            target_idx = target_lineno - 1
            if 0 <= target_idx < len(lines):
                lines[target_idx] = lines[target_idx].replace(bad_name, good_name)
                patched_code = "\n".join(lines)
                diff = generate_unified_diff(content, patched_code, filepath)
                return patched_code, diff

    # 3. Handle string concatenation Type Error line fix
    if "Type Error" in category or "Concatenation" in category:
        var_name = bug.get("var_name", "")
        lines = content.splitlines()
        target_idx = target_lineno - 1
        if 0 <= target_idx < len(lines):
            line = lines[target_idx]
            # Replace `+ var_name` with `+ str(var_name)` or `var_name +` with `str(var_name) +`
            if var_name:
                pattern = re.compile(rf'(\+\s*){re.escape(var_name)}(\b|\))')
                line = pattern.sub(rf'\1str({var_name})\2', line)
                lines[target_idx] = line
                patched_code = "\n".join(lines)
                diff = generate_unified_diff(content, patched_code, filepath)
                return patched_code, diff

    # 4. AST-based transformation
    try:
        tree = ast.parse(content, filename=filepath)
    except SyntaxError:
        # If syntax error in original, heal syntax first to get tree
        healed_lines = content.splitlines()
        for idx, l in enumerate(healed_lines):
            if re.search(r'([^=<>!])=([^=]|$)', l) and any(l.strip().startswith(kw) for kw in ("if ", "elif ", "while ")):
                healed_lines[idx] = re.sub(r'([^=<>!])=([^=])', r'\1==\2', l)
            if any(l.strip().startswith(kw) for kw in ("def ", "if ", "for ", "while ")) and not l.strip().endswith(":"):
                healed_lines[idx] = l.rstrip() + ":"
        try:
            tree = ast.parse("\n".join(healed_lines), filename=filepath)
        except Exception:
            return content, ""

    transformer = None
    if "Mutable Default" in category:
        transformer = TargetedMutableDefaultTransformer(target_lineno, bug.get("arg_name"))
    elif "Zero Division" in category:
        transformer = TargetedZeroDivisionTransformer(target_lineno)
    elif "Boolean Logic" in category:
        transformer = TargetedBooleanLogicTransformer(target_lineno)
    elif "Boundary" in category or "Off-by-One" in category:
        transformer = TargetedBoundaryTransformer(target_lineno)
    elif "Exception" in category:
        transformer = TargetedBareExceptTransformer(target_lineno)
    elif "Dead Code" in category or "Unreachable" in category:
        transformer = TargetedDeadCodeTransformer(target_lineno)

    if transformer:
        try:
            tree = transformer.visit(tree)
            ast.fix_missing_locations(tree)
            compile(tree, filename="<ast>", mode="exec")
            patched_code = ast.unparse(tree)
            diff = generate_unified_diff(content, patched_code, filepath)
            return patched_code, diff
        except Exception:
            pass

    return content, ""


def compose_multi_ast_patches(content: str, bugs: List[Dict[str, Any]], filepath: str = "snippet.py") -> Tuple[str, str]:
    """
    Composes all detected patches (syntax line fixes + AST NodeTransformers)
    into a single valid, working output.
    Returns (fully_patched_code, cumulative_diff).
    """
    working_code = content

    # 1. Apply all syntax fixes first
    for bug in bugs:
        if bug.get("syntax_type") or "Syntax Error" in bug.get("category", "") or "Indentation" in bug.get("category", ""):
            working_code = apply_syntax_line_fix(working_code, bug)

    # 2. Parse healed code into AST
    try:
        tree = ast.parse(working_code, filename=filepath)
    except SyntaxError:
        # Fallback line-by-line syntax heal
        lines = working_code.splitlines()
        for idx, l in enumerate(lines):
            if re.search(r'([^=<>!])=([^=]|$)', l) and any(l.strip().startswith(kw) for kw in ("if ", "elif ", "while ")):
                lines[idx] = re.sub(r'([^=<>!])=([^=])', r'\1==\2', l)
            if any(l.strip().startswith(kw) for kw in ("def ", "if ", "for ", "while ")) and not l.strip().endswith(":"):
                lines[idx] = l.rstrip() + ":"
        working_code = "\n".join(lines)
        try:
            tree = ast.parse(working_code, filename=filepath)
        except Exception:
            tree = None

    # 3. Apply AST NodeTransformers if tree parsed successfully
    if tree is not None:
        for bug in bugs:
            category = bug.get("category", "")
            target_lineno = bug.get("line_start", 1)

            transformer = None
            if "Mutable Default" in category:
                transformer = TargetedMutableDefaultTransformer(target_lineno, bug.get("arg_name"))
            elif "Zero Division" in category:
                transformer = TargetedZeroDivisionTransformer(target_lineno)
            elif "Boolean Logic" in category:
                transformer = TargetedBooleanLogicTransformer(target_lineno)
            elif "Boundary" in category or "Off-by-One" in category:
                transformer = TargetedBoundaryTransformer(target_lineno)
            elif "Exception" in category:
                transformer = TargetedBareExceptTransformer(target_lineno)
            elif "Dead Code" in category or "Unreachable" in category:
                transformer = TargetedDeadCodeTransformer(target_lineno)
            elif "NameError" in category or "Typo" in category:
                bad_name = bug.get("bad_name", "")
                good_name = bug.get("good_name", "")
                if bad_name and good_name:
                    transformer = TargetedFunctionTypoTransformer(bad_name, good_name, target_lineno)
            elif "Type Error" in category or "Concatenation" in category:
                var_name = bug.get("var_name", "")
                transformer = TargetedConcatTransformer(var_name, target_lineno)

            if transformer:
                tree = transformer.visit(tree)

        try:
            ast.fix_missing_locations(tree)
            compile(tree, filename="<ast>", mode="exec")
            patched_code = ast.unparse(tree)
            diff = generate_unified_diff(content, patched_code, filepath)
            return patched_code, diff
        except Exception:
            pass

    # 4. Fallback line-level repair across all bugs if AST compilation fails
    lines = working_code.splitlines()
    for bug in bugs:
        category = bug.get("category", "")
        target_lineno = bug.get("line_start", 1)
        target_idx = target_lineno - 1
        if 0 <= target_idx < len(lines):
            if "NameError" in category or "Typo" in category:
                bad_name = bug.get("bad_name")
                good_name = bug.get("good_name")
                if bad_name and good_name:
                    lines[target_idx] = lines[target_idx].replace(bad_name, good_name)
            elif "Type Error" in category or "Concatenation" in category:
                var_name = bug.get("var_name", "")
                if var_name:
                    pattern = re.compile(rf'(\+\s*){re.escape(var_name)}(\b|\))')
                    lines[target_idx] = pattern.sub(rf'\1str({var_name})\2', lines[target_idx])

    patched_code = "\n".join(lines)
    diff = generate_unified_diff(content, patched_code, filepath)
    return patched_code, diff
