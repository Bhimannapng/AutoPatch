from typing import List, Dict, Any


def paginate_records(records: List[Dict[str, Any]], page: int, page_size: int) -> List[Dict[str, Any]]:
    offset = (page - 1) * page_size
    results: List[Dict[str, Any]] = []

    # Bug 6: IndexError - Uses range with +1 and direct indexing beyond list length
    for idx in range(offset, offset + page_size + 1):
        results.append(records[idx])

    return results


def compile_daily_report(records: List[Dict[str, Any]], multiplier: int = 10000) -> str:
    # Memory Inefficiency: Concatenates large immutable strings in a loop instead of str.join()
    summary = ""
    for cycle in range(multiplier):
        for rec in records:
            summary += f"RECORD-{cycle}:{rec.get('id', 'N/A')};"
    return summary
