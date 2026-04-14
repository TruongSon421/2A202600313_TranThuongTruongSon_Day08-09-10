"""
compare_with_day09.py — So sánh Day 08 (Single Agent) vs Day 09 (Multi-Agent)
==============================================================================
Script này tạo bảng so sánh metrics giữa Day 08 và Day 09.

Chạy:
    python compare_with_day09.py
    python compare_with_day09.py --output comparison_report.md
"""

import json
import os
import argparse
from pathlib import Path
from typing import Dict, Any, Optional


def load_day08_metrics(metrics_file: str = "results/day08_metrics.json") -> Optional[Dict[str, Any]]:
    """Load Day 08 metrics từ file."""
    if not os.path.exists(metrics_file):
        print(f"⚠️  Day 08 metrics not found: {metrics_file}")
        print("   Run: python eval_metrics.py --day09-data")
        return None
    
    with open(metrics_file, "r", encoding="utf-8") as f:
        return json.load(f)


def load_day09_metrics(metrics_file: str = "../day09/lab/artifacts/eval_report.json") -> Optional[Dict[str, Any]]:
    """Load Day 09 metrics từ file."""
    if not os.path.exists(metrics_file):
        print(f"⚠️  Day 09 metrics not found: {metrics_file}")
        print("   Run: cd ../day09/lab && python eval_trace.py")
        return None
    
    with open(metrics_file, "r", encoding="utf-8") as f:
        return json.load(f)


def extract_day09_metrics(day09_data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract metrics từ Day 09 eval_report.json."""
    multi_agent = day09_data.get("day09_multi_agent", {})
    
    # Parse từ trace analysis
    avg_confidence = multi_agent.get("avg_confidence", 0.0)
    avg_latency_ms = multi_agent.get("avg_latency_ms", 0)
    
    # Parse abstain rate
    hitl_rate_str = multi_agent.get("hitl_rate", "0/0 (0%)")
    abstain_count = 0
    total = multi_agent.get("total_traces", 0)
    if "/" in hitl_rate_str:
        abstain_count = int(hitl_rate_str.split("/")[0])
    abstain_rate_pct = round(100 * abstain_count / total, 1) if total > 0 else 0.0
    
    # Multi-hop accuracy (cần tính từ traces)
    # TODO: Implement multi-hop detection cho Day 09
    multi_hop_accuracy_pct = 0.0  # Placeholder
    
    return {
        "avg_confidence": avg_confidence,
        "avg_latency_ms": avg_latency_ms,
        "abstain_rate_pct": abstain_rate_pct,
        "multi_hop_accuracy_pct": multi_hop_accuracy_pct,
        "total_questions": total,
    }


def calculate_delta(day08_val: float, day09_val: float, is_percentage: bool = False) -> str:
    """Tính delta và format."""
    if day08_val == 0 and day09_val == 0:
        return "0"
    
    delta = day09_val - day08_val
    
    if is_percentage:
        return f"{delta:+.1f}%"
    else:
        return f"{delta:+.0f}" if abs(delta) >= 1 else f"{delta:+.3f}"


def estimate_debug_time(routing_visibility: bool) -> str:
    """Ước tính thời gian debug."""
    if routing_visibility:
        return "~5-10"  # Multi-agent có trace rõ ràng
    else:
        return "~15-30"  # Single agent khó debug hơn


def generate_comparison_table(
    day08_metrics: Dict[str, Any],
    day09_metrics: Dict[str, Any],
) -> str:
    """Tạo bảng so sánh markdown."""
    
    d8 = day08_metrics.get("metrics", {})
    d9 = day09_metrics
    
    # Extract values
    d8_conf = d8.get("avg_confidence", 0.0)
    d9_conf = d9.get("avg_confidence", 0.0)
    
    d8_lat = d8.get("avg_latency_ms", 0)
    d9_lat = d9.get("avg_latency_ms", 0)
    
    d8_abs = d8.get("abstain_rate_pct", 0.0)
    d9_abs = d9.get("abstain_rate_pct", 0.0)
    
    d8_mh = d8.get("multi_hop_accuracy_pct", 0.0)
    d9_mh = d9.get("multi_hop_accuracy_pct", 0.0)
    
    # Calculate deltas
    delta_conf = calculate_delta(d8_conf, d9_conf)
    delta_lat = calculate_delta(d8_lat, d9_lat)
    delta_abs = calculate_delta(d8_abs, d9_abs, is_percentage=True)
    delta_mh = calculate_delta(d8_mh, d9_mh, is_percentage=True)
    
    # Debug time estimates
    d8_debug = estimate_debug_time(False)
    d9_debug = estimate_debug_time(True)
    delta_debug = "Faster" if d9_debug < d8_debug else "Similar"
    
    # Build table
    table = f"""# So sánh Day 08 (Single Agent) vs Day 09 (Multi-Agent)

## Metrics Comparison

| Metric | Day 08 (Single Agent) | Day 09 (Multi-Agent) | Delta | Ghi chú |
|--------|----------------------|---------------------|-------|---------|
| Avg confidence | {d8_conf:.3f} | {d9_conf:.3f} | {delta_conf} | Độ tin cậy retrieval |
| Avg latency (ms) | {d8_lat} | {d9_lat} | {delta_lat} | Thời gian xử lý |
| Abstain rate (%) | {d8_abs:.1f}% | {d9_abs:.1f}% | {delta_abs} | % câu trả về "không đủ info" |
| Multi-hop accuracy | {d8_mh:.1f}% | {d9_mh:.1f}% | {delta_mh} | % câu multi-hop trả lời đúng |
| Routing visibility | ✗ Không có | ✓ Có route_reason | N/A | Khả năng debug |
| Debug time (estimate) | {d8_debug} phút | {d9_debug} phút | {delta_debug} | Thời gian tìm ra 1 bug |

## Analysis

### 1. Confidence
- **Day 08**: {d8_conf:.3f} - Dựa trên retrieval scores từ hybrid search
- **Day 09**: {d9_conf:.3f} - Dựa trên worker confidence và routing logic
- **Delta**: {delta_conf} - {'Day 09 tốt hơn' if d9_conf > d8_conf else 'Day 08 tốt hơn' if d8_conf > d9_conf else 'Tương đương'}

### 2. Latency
- **Day 08**: {d8_lat}ms - Single RAG pipeline
- **Day 09**: {d9_lat}ms - Multi-agent với routing overhead
- **Delta**: {delta_lat}ms - {'Day 09 chậm hơn do routing' if d9_lat > d8_lat else 'Day 09 nhanh hơn' if d8_lat > d9_lat else 'Tương đương'}

### 3. Abstain Rate
- **Day 08**: {d8_abs:.1f}% - Dựa trên prompt grounding rules
- **Day 09**: {d9_abs:.1f}% - Dựa trên HITL trigger và confidence threshold
- **Delta**: {delta_abs} - {'Day 09 abstain nhiều hơn (an toàn hơn)' if d9_abs > d8_abs else 'Day 08 abstain nhiều hơn' if d8_abs > d9_abs else 'Tương đương'}

### 4. Multi-hop Accuracy
- **Day 08**: {d8_mh:.1f}% - Single retrieval pass
- **Day 09**: {d9_mh:.1f}% - Multi-worker coordination
- **Delta**: {delta_mh} - {'Day 09 tốt hơn cho câu phức tạp' if d9_mh > d8_mh else 'Day 08 tốt hơn' if d8_mh > d9_mh else 'Tương đương'}

### 5. Routing Visibility
- **Day 08**: ✗ Không có - Black box, khó debug
- **Day 09**: ✓ Có route_reason - Mỗi câu có trace rõ ràng: supervisor route → workers called → MCP tools
- **Benefit**: Day 09 dễ debug hơn nhiều, có thể test từng worker độc lập

### 6. Debug Time
- **Day 08**: {d8_debug} phút - Phải đọc code và log để tìm bug
- **Day 09**: {d9_debug} phút - Có trace file chi tiết, dễ identify worker nào sai
- **Benefit**: Day 09 giảm thời gian debug ~50%

## Kết luận

### Ưu điểm Day 09 (Multi-Agent):
1. **Modularity**: Mỗi worker có trách nhiệm rõ ràng, dễ maintain
2. **Debuggability**: Trace file chi tiết, routing visibility
3. **Extensibility**: Thêm worker mới không ảnh hưởng code cũ
4. **MCP Integration**: Có thể extend capability qua MCP tools

### Ưu điểm Day 08 (Single Agent):
1. **Simplicity**: Code đơn giản hơn, ít moving parts
2. **Latency**: {'Nhanh hơn' if d8_lat < d9_lat else 'Tương đương'} (không có routing overhead)
3. **Easy to understand**: Toàn bộ logic trong 1 file

### Trade-offs:
- **Day 08** phù hợp cho: RAG đơn giản, không cần extend, team nhỏ
- **Day 09** phù hợp cho: Hệ thống phức tạp, cần scale, nhiều loại câu hỏi khác nhau

---

Generated: {day08_metrics.get('timestamp', 'N/A')}
"""
    
    return table


def main():
    parser = argparse.ArgumentParser(description="Compare Day 08 vs Day 09")
    parser.add_argument("--day08-file", default="results/day08_metrics.json", help="Day 08 metrics file")
    parser.add_argument("--day09-file", default="../day09/lab/artifacts/eval_report.json", help="Day 09 metrics file")
    parser.add_argument("--output", default="results/comparison_report.md", help="Output markdown file")
    args = parser.parse_args()
    
    print("\n" + "="*70)
    print("Day 08 vs Day 09 Comparison")
    print("="*70)
    
    # Load metrics
    print(f"\n📊 Loading Day 08 metrics from: {args.day08_file}")
    day08_data = load_day08_metrics(args.day08_file)
    
    print(f"📊 Loading Day 09 metrics from: {args.day09_file}")
    day09_data = load_day09_metrics(args.day09_file)
    
    if not day08_data:
        print("\n❌ Missing Day 08 metrics. Run first:")
        print("   python eval_metrics.py --day09-data")
        return
    
    if not day09_data:
        print("\n❌ Missing Day 09 metrics. Run first:")
        print("   cd ../day09/lab && python eval_trace.py")
        return
    
    # Extract Day 09 metrics
    day09_metrics = extract_day09_metrics(day09_data)
    
    # Generate comparison table
    print("\n📝 Generating comparison report...")
    report = generate_comparison_table(day08_data, day09_metrics)
    
    # Save report
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(report, encoding="utf-8")
    
    print(f"\n✅ Comparison report saved to: {output_path}")
    print("\n" + "="*70)
    print(report)
    print("="*70)


if __name__ == "__main__":
    main()
