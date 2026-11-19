import pytest
from six_bug_15_lines import process_data

def test_1_mutable_default_argument_isolation():
    """Bug 1: Calling process_data twice should not leak cache between independent calls."""
    res1 = process_data([10] * 10, threshold=10)
    assert res1 == 10.0
    # Second call with empty items should not retain previous cache
    res2 = process_data([], threshold=10)
    assert res2 == 0.0

def test_2_empty_items_zero_division():
    """Bug 2 & 3: Empty items should safely return 0.0 without triggering internal ZeroDivisionError."""
    res = process_data([], threshold=5)
    assert res == 0.0

def test_3_threshold_out_of_bounds_negative():
    """Bug 4: Negative threshold (< 0) should return -1 (failed because of 'and' instead of 'or')."""
    res = process_data([5, 5], threshold=-5)
    assert res == -1

def test_4_threshold_out_of_bounds_excessive():
    """Bug 4: Threshold over 100 should return -1 (failed because of 'and' instead of 'or')."""
    res = process_data([5, 5], threshold=150)
    assert res == -1

def test_5_exact_boundary_threshold():
    """Bug 5: Exactly meeting the threshold (len == threshold) should qualify (fails due to > instead of >=)."""
    items = [2.0] * 10  # len = 10, threshold = 10
    res = process_data(items, threshold=10)
    assert res == 2.0

def test_6_normal_processing():
    """Standard valid input processing."""
    items = [10.0, 20.0, 30.0, 40.0, 50.0]
    res = process_data(items, threshold=3)
    assert res == 30.0
