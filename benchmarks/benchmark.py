"""Reproducible synthetic benchmark; timings are environment-specific."""
import json
from pathlib import Path
import statistics
import tempfile
import time
from reqcontext import RequirementContext


def run():
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        for i in range(500):
            (root / f"module_{i:04}.py").write_text("\n".join(f"def process_{i}_{j}(item):\n    return str(item)\n" for j in range(12)))
        (root / "uploader.py").write_text("def upload_document(client, data):\n    return client.upload(data)\n")
        with RequirementContext(root) as context:
            start = time.perf_counter()
            cold = context.analyze("Add retries to upload_document")
            cold_time = time.perf_counter() - start
            warm_times = []
            for _ in range(7):
                start = time.perf_counter()
                warm = context.analyze("Add retries to upload_document")
                warm_times.append(time.perf_counter() - start)
            (root / "uploader.py").write_text("def upload_document(client, data):\n    return client.upload(data, timeout=5)\n")
            start = time.perf_counter()
            changed = context.analyze("Add retries to upload_document")
            changed_time = time.perf_counter() - start
            assert cold.evidence == warm.evidence
            assert warm.index_stats["indexed"] == 0
            assert changed.index_stats["indexed"] == 1
            assert cold.evidence[0]["path"] == "uploader.py"
            return {"files": 501, "python_functions": 6001, "cold_seconds": cold_time,
                    "warm_median_seconds": statistics.median(warm_times),
                    "warm_speedup_vs_cold": cold_time / statistics.median(warm_times),
                    "one_file_change_seconds": changed_time,
                    "cold_stats": cold.index_stats, "warm_stats": warm.index_stats,
                    "one_file_change_stats": changed.index_stats,
                    "same_results_on_warm": True, "expected_target_rank": 1,
                    "limitations": "Synthetic local workload; warm filesystem caches; not an LLM quality benchmark. Refresh still reads and hashes every eligible file."}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
