#!/bin/bash
# run_comparison.sh — Chạy toàn bộ quy trình so sánh Day 08 vs Day 09
# ========================================================================

echo "=========================================="
echo "Day 08 vs Day 09 Comparison Pipeline"
echo "=========================================="

# Step 1: Chạy Day 08 evaluation với Day 09 data
echo ""
echo "Step 1: Running Day 08 evaluation with Day 09 test questions..."
python eval_metrics.py --output results/day08_metrics.json

if [ $? -ne 0 ]; then
    echo "❌ Day 08 evaluation failed!"
    exit 1
fi

# Step 2: Kiểm tra Day 09 metrics có sẵn chưa
echo ""
echo "Step 2: Checking Day 09 metrics..."
if [ ! -f "../day09/lab/artifacts/eval_report.json" ]; then
    echo "⚠️  Day 09 metrics not found. Running Day 09 evaluation..."
    cd ../day09/lab
    python eval_trace.py
    cd ../../day08/lab
fi

# Step 3: So sánh metrics
echo ""
echo "Step 3: Generating comparison report..."
python compare_with_day09.py --output results/comparison_report.md

if [ $? -ne 0 ]; then
    echo "❌ Comparison failed!"
    exit 1
fi

# Step 4: Hiển thị kết quả
echo ""
echo "=========================================="
echo "✅ Comparison complete!"
echo "=========================================="
echo ""
echo "Results:"
echo "  - Day 08 metrics: results/day08_metrics.json"
echo "  - Comparison report: results/comparison_report.md"
echo ""
echo "View report:"
echo "  cat results/comparison_report.md"
echo ""
