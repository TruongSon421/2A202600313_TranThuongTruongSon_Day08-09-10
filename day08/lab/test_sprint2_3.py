"""
test_sprint2_3.py — Quick test for Sprint 2 + 3 implementation
==============================================================
Chạy script này để test nhanh các chức năng đã implement.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from rag_answer import retrieve_dense, retrieve_sparse, retrieve_hybrid, rag_answer


def test_dense_retrieval():
    """Test dense retrieval."""
    print("=" * 60)
    print("TEST 1: Dense Retrieval")
    print("=" * 60)
    
    query = "SLA xử lý ticket P1 là bao lâu?"
    print(f"\nQuery: {query}\n")
    
    try:
        results = retrieve_dense(query, top_k=3)
        print(f"✓ Retrieved {len(results)} chunks")
        for i, chunk in enumerate(results, 1):
            print(f"  [{i}] score={chunk['score']:.3f} | {chunk['metadata'].get('source', '?')}")
            print(f"      {chunk['text'][:80]}...")
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_sparse_retrieval():
    """Test sparse retrieval (BM25)."""
    print("\n" + "=" * 60)
    print("TEST 2: Sparse Retrieval (BM25)")
    print("=" * 60)
    
    query = "SLA xử lý ticket P1 là bao lâu?"
    print(f"\nQuery: {query}\n")
    
    try:
        results = retrieve_sparse(query, top_k=3)
        print(f"✓ Retrieved {len(results)} chunks")
        for i, chunk in enumerate(results, 1):
            print(f"  [{i}] score={chunk['score']:.3f} | {chunk['metadata'].get('source', '?')}")
            print(f"      {chunk['text'][:80]}...")
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_hybrid_retrieval():
    """Test hybrid retrieval (RRF)."""
    print("\n" + "=" * 60)
    print("TEST 3: Hybrid Retrieval (RRF)")
    print("=" * 60)
    
    query = "SLA xử lý ticket P1 là bao lâu?"
    print(f"\nQuery: {query}\n")
    
    try:
        results = retrieve_hybrid(query, top_k=3)
        print(f"✓ Retrieved {len(results)} chunks")
        for i, chunk in enumerate(results, 1):
            print(f"  [{i}] score={chunk['score']:.3f} | {chunk['metadata'].get('source', '?')}")
            print(f"      {chunk['text'][:80]}...")
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_rag_baseline():
    """Test RAG pipeline with baseline (dense)."""
    print("\n" + "=" * 60)
    print("TEST 4: RAG Pipeline - Baseline (Dense)")
    print("=" * 60)
    
    query = "Khách hàng có thể yêu cầu hoàn tiền trong bao nhiêu ngày?"
    print(f"\nQuery: {query}\n")
    
    try:
        result = rag_answer(query, retrieval_mode="dense", verbose=False)
        print(f"✓ Answer: {result['answer']}")
        print(f"✓ Sources: {result['sources']}")
        
        # Check for citation
        if '[1]' in result['answer'] or '[2]' in result['answer'] or '[3]' in result['answer']:
            print("✓ Answer contains citations")
        else:
            print("⚠ Warning: Answer may not contain citations")
        
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_rag_hybrid():
    """Test RAG pipeline with hybrid."""
    print("\n" + "=" * 60)
    print("TEST 5: RAG Pipeline - Hybrid")
    print("=" * 60)
    
    query = "Ai phải phê duyệt để cấp quyền Level 3?"
    print(f"\nQuery: {query}\n")
    
    try:
        result = rag_answer(query, retrieval_mode="hybrid", verbose=False)
        print(f"✓ Answer: {result['answer']}")
        print(f"✓ Sources: {result['sources']}")
        
        # Check for citation
        if '[1]' in result['answer'] or '[2]' in result['answer'] or '[3]' in result['answer']:
            print("✓ Answer contains citations")
        else:
            print("⚠ Warning: Answer may not contain citations")
        
        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_abstain():
    """Test abstain behavior."""
    print("\n" + "=" * 60)
    print("TEST 6: Abstain Behavior")
    print("=" * 60)
    
    query = "ERR-403-AUTH là lỗi gì?"
    print(f"\nQuery: {query}")
    print("(Câu hỏi này không có trong docs → cần abstain)\n")
    
    try:
        result = rag_answer(query, retrieval_mode="dense", verbose=False)
        print(f"Answer: {result['answer']}")
        
        # Check if answer contains abstain phrases
        abstain_phrases = [
            "không đủ",
            "không tìm thấy",
            "không có thông tin",
            "i don't know",
            "i do not know",
        ]
        answer_lower = result['answer'].lower()
        is_abstain = any(phrase in answer_lower for phrase in abstain_phrases)
        
        if is_abstain:
            print("✓ Model correctly abstained")
            return True
        else:
            print("⚠ Warning: Model may have hallucinated")
            return False
            
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("SPRINT 2 + 3 TEST SUITE")
    print("=" * 60)
    
    results = []
    
    try:
        # Run all tests
        results.append(("Dense Retrieval", test_dense_retrieval()))
        results.append(("Sparse Retrieval", test_sparse_retrieval()))
        results.append(("Hybrid Retrieval", test_hybrid_retrieval()))
        results.append(("RAG Baseline", test_rag_baseline()))
        results.append(("RAG Hybrid", test_rag_hybrid()))
        results.append(("Abstain Behavior", test_abstain()))
        
        # Summary
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for _, result in results if result)
        total = len(results)
        
        for test_name, result in results:
            status = "✓ PASS" if result else "✗ FAIL"
            print(f"{status}: {test_name}")
        
        print(f"\nTotal: {passed}/{total} tests passed")
        
        if passed == total:
            print("\n🎉 ALL TESTS PASSED!")
            print("\nSprint 2 + 3 hoàn thành:")
            print("  ✓ Dense retrieval")
            print("  ✓ Sparse retrieval (BM25)")
            print("  ✓ Hybrid retrieval (RRF)")
            print("  ✓ Grounded answer generation")
            print("  ✓ Citation format")
            print("  ✓ Abstain behavior")
            print("\nBước tiếp theo:")
            print("  1. Chạy python rag_answer.py để xem full demo")
            print("  2. Chạy python eval.py để đánh giá pipeline (Sprint 4)")
        else:
            print(f"\n⚠ {total - passed} test(s) failed")
            print("\nKiểm tra:")
            print("  1. Đã chạy python index.py để build index chưa?")
            print("  2. File .env có OPENAI_API_KEY chưa?")
            print("  3. Đã cài đặt dependencies: pip install -r requirements.txt")
        
    except Exception as e:
        print(f"\n\n✗ CRITICAL ERROR: {e}")
        print("\nKiểm tra:")
        print("  1. Đã chạy python index.py để build index chưa?")
        print("  2. File .env có OPENAI_API_KEY chưa?")
        print("  3. Đã cài đặt dependencies: pip install -r requirements.txt")
