import pytest
from ast_detector import detect_ast_bugs

def test_correct_python_program():
    code = """
def add(a: int, b: int) -> int:
    result = a + b
    return result

class MathService:
    def __init__(self, multiplier: int):
        self.multiplier = multiplier

    def multiply(self, val: int) -> int:
        return val * self.multiplier

if __name__ == "__main__":
    service = MathService(2)
    print(add(10, service.multiply(5)))
"""
    bugs = detect_ast_bugs("clean.py", code)
    assert len(bugs) == 0, f"Expected 0 bugs in clean code, got: {bugs}"


def test_missing_colons_and_brackets():
    code = """
def calculate(x)
    if x > 10
        return x
    return 0
"""
    bugs = detect_ast_bugs("syntax_issue.py", code)
    colon_bugs = [b for b in bugs if b["category"] == "Syntax Errors"]
    assert len(colon_bugs) >= 2


def test_undefined_variable():
    code = """
def get_user_data():
    return active_user_session
"""
    bugs = detect_ast_bugs("undef.py", code)
    undef_bugs = [b for b in bugs if b["category"] == "Variable Errors" and "active_user_session" in b["title"]]
    assert len(undef_bugs) == 1
    assert undef_bugs[0]["severity"] == "ERROR"


def test_bad_indentation():
    code = """
def do_work():
x = 10
    return x
"""
    bugs = detect_ast_bugs("indent.py", code)
    assert any("Indentation" in b["title"] or b["category"] == "Syntax Errors" for b in bugs)


def test_wrong_function_argument_count():
    code = """
def compute(a, b, c):
    return a + b + c

val = compute(1, 2)
"""
    bugs = detect_ast_bugs("argc.py", code)
    argc_bugs = [b for b in bugs if b["category"] == "Function Errors" and "compute" in b["title"]]
    assert len(argc_bugs) >= 1
    assert argc_bugs[0]["severity"] == "ERROR"


def test_multiple_independent_errors_in_one_file():
    code = """
def first_bad(x)
    if x = 5:
        return x

def second_bad(y):
    if y < 0 and y > 100:
        return -1
    return y / 0
"""
    bugs = detect_ast_bugs("multi_bad.py", code)
    # Must detect syntax errors and logical errors together
    categories = {b["category"] for b in bugs}
    assert "Syntax Errors" in categories
    assert "Logical Errors" in categories
    assert len(bugs) >= 3


def test_nested_functions():
    code = """
def outer(x):
    def inner(y):
        return y / 0
    return inner(x)
"""
    bugs = detect_ast_bugs("nested.py", code)
    zero_bugs = [b for b in bugs if b["category"] == "Logical Errors"]
    assert len(zero_bugs) >= 1


def test_multiple_classes():
    code = """
class WorkerA:
    def run(self, val=[]):
        return sum(val)

class WorkerB:
    def compute(self, a, b):
        return a / 0
"""
    bugs = detect_ast_bugs("classes.py", code)
    assert any("WorkerA" in b["title"] or "Mutable" in b["title"] for b in bugs)
    assert any("Zero" in b["title"] for b in bugs)


def test_loops_and_conditions():
    code = """
def loop_test(items):
    total = 0
    for it in items:
        if it < 0 and it > 50:
            total += 1
    return total
"""
    bugs = detect_ast_bugs("loop.py", code)
    bool_bugs = [b for b in bugs if b["category"] == "Logical Errors"]
    assert len(bool_bugs) >= 1


def test_java_syntax_errors():
    code = """
public class BrokenJava {
    public void brokenMethod( {
        int x = 10;
    }
}
"""
    bugs = detect_ast_bugs("BrokenJava.java", code)
    assert any(b["category"] == "Syntax Errors" for b in bugs)


def test_java_undefined_variable():
    code = """
public class JavaVars {
    public int calc() {
        int a = 5;
        int b = a + nonexistentVar;
        return b;
    }
}
"""
    bugs = detect_ast_bugs("JavaVars.java", code)
    undef_bugs = [b for b in bugs if b["category"] == "Variable Errors" and "nonexistentVar" in b["title"]]
    assert len(undef_bugs) >= 1


def test_java_multiple_methods():
    code = """
public class MultiMethod {
    public int methodOne() {
        return 10 / 0;
    }
    public int methodTwo() {
        int val = unknownField * 2;
        return val;
        int dead = 99;
    }
}
"""
    bugs = detect_ast_bugs("MultiMethod.java", code)
    categories = {b["category"] for b in bugs}
    assert "Logical Errors" in categories
    assert "Variable Errors" in categories
    assert "Structural Errors" in categories


def test_large_python_file():
    lines = ["# Large python file simulation"]
    for i in range(1, 100):
        lines.append(f"def func_{i}(x: int) -> int:\n    return x + {i}")
    lines.append("def faulty_func(items, cache=[]):\n    return items / 0")
    code = "\n".join(lines)
    assert len(code.splitlines()) > 200

    bugs = detect_ast_bugs("large.py", code)
    assert len(bugs) >= 2


def test_large_java_file():
    lines = ["public class LargeJavaService {"]
    for i in range(1, 220):
        lines.append(f"    public int method{i}(int x) {{ return x + {i}; }}")
    lines.append("    public int faultyMethod() { return 100 / 0; }")
    lines.append("}")
    code = "\n".join(lines)
    assert len(code.splitlines()) > 200

    bugs = detect_ast_bugs("LargeJavaService.java", code)
    assert any("Division by Zero" in b["title"] for b in bugs)


def test_clean_large_program_zero_false_positives():
    lines = ["# Clean large program"]
    for i in range(1, 120):
        lines.append(f"def pure_op_{i}(a: int, b: int) -> int:\n    return a + b + {i}")
    code = "\n".join(lines)
    bugs = detect_ast_bugs("clean_large.py", code)
    assert len(bugs) == 0, f"Expected 0 bugs, found: {bugs}"
