from typing import Generator, List, Dict, Any
import csv
import io

class DataLoader:
    """Streams data lazily using Python generators to maintain O(1) constant memory footprint."""
    
    @staticmethod
    def stream_dataset(raw_csv_text: str) -> Generator[Dict[str, float], None, None]:
        f = io.StringIO(raw_csv_text.strip())
        reader = csv.DictReader(f)
        for row in reader:
            yield {
                "feature_1": float(row.get("feature_1", 0.0)),
                "feature_2": float(row.get("feature_2", 0.0)),
                "target": float(row.get("target", 0.0))
            }
