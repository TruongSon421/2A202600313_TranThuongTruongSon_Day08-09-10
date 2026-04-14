"""
eval_metrics.py — Tính metrics để so sánh với Day 09 Multi-Agent
================================================================
Metrics:
  - Avg confidence: Độ tin cậy trung bình (dựa trên retrieval score)
  - Avg latency (ms): Thời gian xử lý trung bình
  - Abstain rate (%): Tỷ lệ câu trả "không đủ info"
  - Multi-hop accuracy: Độ chính xác câu hỏi multi-hop (cần nhiều tài liệu)

Chạy:
    python eval_metrics.py                           # Chạy với test_questions.json từ Day 09
    python eval_metrics.py --grading                 # Chạy với grading_questions.json từ Day 09
    python eval_metrics.py --day08-data              # Chạy với test_questions.json từ Day 08
"""

import json
import os
import sys
import time
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

# Add day08/lab to path để import rag_answer
sys.path.insert(0, str(Path(__file__).parent))
from rag_answer import rag_answer

# =============================================================================
# CẤU HÌNH
# =============================================================================

# Cấu hình pipeline (dùng variant tốt nhất từ Sprint 3)
PIPELINE_CONFIG = {
    "retrieval_mode": "hybrid",
    "top_k_search": 10,
    "top_k_select": 3,
    "use_rerank": False,
    "dense_weight": 0.6,
    "sparse_weight": 0.4,
}

# Ngưỡng để xác định abstain
ABSTAIN_KEYWORDS = [
    "không đủ dữ liệu",
    "không tìm thấy thông tin",
    "không có thông tin",
    "thiếu thông tin",
    "không đủ thông tin",
    "không có trong tài liệu",
]

# Danh sách câu hỏi multi-hop (cần nhiều tài liệu hoặc nhiều bước suy luận)
# Dựa trên Day 09 test_questions.json
MULTI_HOP_QUESTION_IDS = [
    "q12",   # Temporal policy scoping
    "q13",   # Access Control + SLA context (multi-doc)
    "q15",   # SLA + Access Control (multi-doc, multi-worker)
    "gq09",  # SLA P1 + Access Control (grading questions)
    "gq02",  # Temporal policy scoping (grading questions)
    "gq10",  # Policy exception (grading questions)
]


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def is_abstain(answer: str) -> bool:
    """Kiểm tra xem câu trả lời có phải là abstain không."""
    answer_lower = answer.lower()
    return any(keyword in answer_lower for keyword in ABSTAIN_KEYWORDS)


def calculate_confidence(chunks_used: List[Dict[str, Any]]) -> float:
    """
    Tính confidence score dựa trên retrieval scores.
    
    Confidence = average của top-3 retrieval scores
    Range: 0.0 - 1.0
    """
    if not chunks_used:
        return 0.0
    
    scores = [chunk.get("score", 0.0) for chunk in chunks_used]
    return sum(scores) / len(scores) if scores else 0.0


def check_multi_hop_accuracy(
    question_id: str,
    answer: str,
    expected_sources: List[str],
    retrieved_sources: List[str],
) -> bool:
    """
    Kiểm tra accuracy cho câu hỏi multi-hop.
    
    Criteria:
    1. Không phải abstain (trừ khi expected là abstain)
    2. Retrieve được ít nhất 1 expected source
    3. Answer không rỗng
    """
    # Nếu không phải câu multi-hop, return None
    if question_id not in MULTI_HOP_QUESTION_IDS:
        return None
    
    # Nếu abstain mà không nên abstain
    if is_abstain(answer) and expected_sources:
        return False
    
    # Nếu không có answer
    if not answer or len(answer.strip()) < 10:
        return False
    
    # Kiểm tra source coverage (partial match)
    if expected_sources:
        found = False
        for expected in expected_sources:
            expected_name = expected.split("/")[-1].replace(".pdf", "").replace(".md", "").replace(".txt", "")
            if any(expected_name.lower() in r.lower() for r in retrieved_sources):
                found = True
                break
        if not found:
            return False
    
    return True


# =============================================================================
# RUN EVALUATION WITH METRICS
# =============================================================================

def run_evaluation_with_metrics(
    questions_file: str,
    config: Dict[str, Any],
    verbose: bool = True,
) -> Dict[str, Any]:
    """
    Chạy evaluation và tính các metrics.
    
    Returns:
        Dict chứa:
        - results: list kết quả từng câu
        - metrics: dict các metrics tổng hợp
    """
    # Load questions
    with open(questions_file, "r", encoding="utf-8") as f:
        questions = json.load(f)
    
    print(f"\n{'='*70}")
    print(f"Running evaluation: {questions_file}")
    print(f"Total questions: {len(questions)}")
    print(f"Config: {config}")
    print('='*70)
    
    results = []
    total_confidence = 0.0
    total_latency_ms = 0.0
    abstain_count = 0
    multi_hop_correct = 0
    multi_hop_total = 0
    
    for i, q in enumerate(questions, 1):
        question_id = q.get("id", f"q{i:02d}")
        query = q["question"]
        expected_sources = q.get("expected_sources", [])
        
        if verbose:
            print(f"\n[{i:02d}/{len(questions)}] {question_id}: {query[:65]}...")
        
        # Measure latency
        start_time = time.time()
        
        try:
            result = rag_answer(
                query=query,
                retrieval_mode=config.get("retrieval_mode", "dense"),
                top_k_search=config.get("top_k_search", 10),
                top_k_select=config.get("top_k_select", 3),
                use_rerank=config.get("use_rerank", False),
                dense_weight=config.get("dense_weight", 0.6),
                sparse_weight=config.get("sparse_weight", 0.4),
                verbose=False,
            )
            
            answer = result["answer"]
            chunks_used = result["chunks_used"]
            sources = result["sources"]
            
        except Exception as e:
            answer = f"PIPELINE_ERROR: {e}"
            chunks_used = []
            sources = []
        
        end_time = time.time()
        latency_ms = (end_time - start_time) * 1000
        
        # Calculate metrics
        confidence = calculate_confidence(chunks_used)
        is_abstain_answer = is_abstain(answer)
        multi_hop_acc = check_multi_hop_accuracy(question_id, answer, expected_sources, sources)
        
        # Accumulate
        total_confidence += confidence
        total_latency_ms += latency_ms
        if is_abstain_answer:
            abstain_count += 1
        if multi_hop_acc is not None:
            multi_hop_total += 1
            if multi_hop_acc:
                multi_hop_correct += 1
        
        # Store result
        row = {
            "id": question_id,
            "question": query,
            "answer": answer,
            "sources": sources,
            "confidence": round(confidence, 3),
            "latency_ms": round(latency_ms),
            "is_abstain": is_abstain_answer,
            "is_multi_hop": multi_hop_acc is not None,
            "multi_hop_correct": multi_hop_acc if multi_hop_acc is not None else None,
            "expected_sources": expected_sources,
        }
        results.append(row)
        
        if verbose:
            print(f"  Answer: {answer[:80]}...")
            print(f"  Confidence: {confidence:.3f} | Latency: {latency_ms:.0f}ms | Abstain: {is_abstain_answer}")
            if multi_hop_acc is not None:
                print(f"  Multi-hop: {'✓' if multi_hop_acc else '✗'}")
    
    # Calculate aggregate metrics
    total = len(results)
    metrics = {
        "total_questions": total,
        "avg_confidence": round(total_confidence / total, 3) if total > 0 else 0.0,
        "avg_latency_ms": round(total_latency_ms / total) if total > 0 else 0,
        "abstain_count": abstain_count,
        "abstain_rate_pct": round(100 * abstain_count / total, 1) if total > 0 else 0.0,
        "multi_hop_total": multi_hop_total,
        "multi_hop_correct": multi_hop_correct,
        "multi_hop_accuracy_pct": round(100 * multi_hop_correct / multi_hop_total, 1) if multi_hop_total > 0 else 0.0,
    }
    
    # Print summary
    print(f"\n{'='*70}")
    print("METRICS SUMMARY")
    print('='*70)
    print(f"Avg confidence:      {metrics['avg_confidence']:.3f}")
    print(f"Avg latency (ms):    {metrics['avg_latency_ms']}")
    print(f"Abstain rate (%):    {metrics['abstain_rate_pct']}% ({abstain_count}/{total})")
    print(f"Multi-hop accuracy:  {metrics['multi_hop_accuracy_pct']}% ({multi_hop_correct}/{multi_hop_total})")
    print('='*70)
    
    return {
        "results": results,
        "metrics": metrics,
        "config": config,
        "timestamp": datetime.now().isoformat(),
    }


# =============================================================================
# SAVE RESULTS
# =============================================================================

def save_results(data: Dict[str, Any], output_file: str) -> None:
    """Lưu kết quả ra file JSON."""
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ Results saved to: {output_path}")


# =============================================================================
# MAIN
# =============================================================================

def find_questions_file(filename: str, search_day09: bool = True) -> str:
    """
    Tìm file questions với nhiều đường dẫn khả dĩ.
    
    Args:
        filename: Tên file (vd: "test_questions.json")
        search_day09: Tìm trong Day 09 hay Day 08
    
    Returns:
        Đường dẫn tới file
    """
    script_dir = Path(__file__).parent  # day08/lab/
    
    if search_day09:
        # Tìm trong Day 09
        possible_paths = [
            script_dir / ".." / ".." / "day09" / "lab" / "data" / filename,  # Từ day08/lab
            Path("day09/lab/data") / filename,  # Từ root
            Path("../day09/lab/data") / filename,  # Từ day08/lab
        ]
    else:
        # Tìm trong Day 08
        possible_paths = [
            script_dir / "data" / filename,  # Từ day08/lab
            Path("day08/lab/data") / filename,  # Từ root
            Path("data") / filename,  # Từ day08/lab
        ]
    
    for path in possible_paths:
        if path.exists():
            return str(path)
    
    # Không tìm thấy
    raise FileNotFoundError(f"Cannot find {filename}. Tried: {[str(p) for p in possible_paths]}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Day 08 Lab — Metrics Evaluation")
    parser.add_argument("--grading", action="store_true", help="Use Day 09 grading_questions.json")
    parser.add_argument("--day08-data", action="store_true", help="Use Day 08 test_questions.json")
    parser.add_argument("--questions-file", type=str, help="Custom questions file path")
    parser.add_argument("--output", type=str, help="Output file (default: day08/lab/results/day08_metrics.json)")
    args = parser.parse_args()
    
    # Determine output file
    if not args.output:
        script_dir = Path(__file__).parent
        output_file = script_dir / "results" / "day08_metrics.json"
        args.output = str(output_file)
    
    # Determine questions file
    try:
        if args.questions_file:
            questions_file = args.questions_file
        elif args.day08_data:
            questions_file = find_questions_file("test_questions.json", search_day09=False)
        elif args.grading:
            questions_file = find_questions_file("grading_questions.json", search_day09=True)
        else:
            # Mặc định: dùng test_questions.json từ Day 09
            questions_file = find_questions_file("test_questions.json", search_day09=True)
    except FileNotFoundError as e:
        print(f"❌ {e}")
        print("\nAvailable options:")
        print("  python day08/lab/eval_metrics.py                    # Use Day 09 test_questions.json (default)")
        print("  python day08/lab/eval_metrics.py --grading          # Use Day 09 grading_questions.json")
        print("  python day08/lab/eval_metrics.py --day08-data       # Use Day 08 test_questions.json")
        print("\nOr run from day08/lab directory:")
        print("  cd day08/lab")
        print("  python eval_metrics.py")
        exit(1)
    
    # Check if file exists
    if not os.path.exists(questions_file):
        print(f"❌ File not found: {questions_file}")
        print("\nThis should not happen - file detection failed!")
        exit(1)
    
    # Run evaluation
    print(f"\n📋 Loading questions from: {questions_file}")
    
    data = run_evaluation_with_metrics(
        questions_file=questions_file,
        config=PIPELINE_CONFIG,
        verbose=True,
    )
    
    # Save results
    save_results(data, args.output)
    
    print("\n✅ Evaluation complete!")
    print(f"\nTo compare with Day 09:")
    print(f"  1. Run Day 09: cd ../day09/lab && python eval_trace.py")
    print(f"  2. Compare: python compare_with_day09.py")
    print(f"  3. View report: cat results/comparison_report.md")
