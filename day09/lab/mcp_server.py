"""
mcp_server.py — MCP Server dùng FastMCP library
Sprint 3: Implement ít nhất 2 MCP tools.

Tools available:
    1. search_kb(query, top_k)                              → tìm kiếm Knowledge Base
    2. get_ticket_info(ticket_id)                           → tra cứu thông tin ticket (mock)
    3. check_access_permission(access_level, requester_role, is_emergency)  → kiểm tra quyền
    4. create_ticket(priority, title, description)          → tạo ticket mới (mock)

Chạy server:
    python mcp_server.py
    # Mặc định: http://localhost:8000/mcp

Dùng từ agent (MCP client):
    from mcp import ClientSession
    from mcp.client.streamable_http import streamablehttp_client
"""

import os
import json
from datetime import datetime
from typing import Optional
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("lab-mcp-server")


# ─────────────────────────────────────────────
# Mock Data
# ─────────────────────────────────────────────

MOCK_TICKETS = {
    "P1-LATEST": {
        "ticket_id": "IT-9847",
        "priority": "P1",
        "title": "API Gateway down — toàn bộ người dùng không đăng nhập được",
        "status": "in_progress",
        "assignee": "nguyen.van.a@company.internal",
        "created_at": "2026-04-13T22:47:00",
        "sla_deadline": "2026-04-14T02:47:00",
        "escalated": True,
        "escalated_to": "senior_engineer_team",
        "notifications_sent": ["slack:#incident-p1", "email:incident@company.internal", "pagerduty:oncall"],
    },
    "IT-1234": {
        "ticket_id": "IT-1234",
        "priority": "P2",
        "title": "Feature login chậm cho một số user",
        "status": "open",
        "assignee": None,
        "created_at": "2026-04-13T09:15:00",
        "sla_deadline": "2026-04-14T09:15:00",
        "escalated": False,
    },
}

ACCESS_RULES = {
    1: {
        "required_approvers": ["Line Manager"],
        "emergency_can_bypass": False,
        "note": "Standard user access",
    },
    2: {
        "required_approvers": ["Line Manager", "IT Admin"],
        "emergency_can_bypass": True,
        "emergency_bypass_note": "Level 2 có thể cấp tạm thời với approval đồng thời của Line Manager và IT Admin on-call.",
        "note": "Elevated access",
    },
    3: {
        "required_approvers": ["Line Manager", "IT Admin", "IT Security"],
        "emergency_can_bypass": False,
        "note": "Admin access — không có emergency bypass",
    },
}


# ─────────────────────────────────────────────
# Tools
# ─────────────────────────────────────────────

@mcp.tool()
def search_kb(query: str, top_k: int = 3) -> dict:
    """
    Tìm kiếm Knowledge Base nội bộ bằng semantic search.
    Trả về top-k chunks liên quan nhất.

    Args:
        query: Câu hỏi hoặc keyword cần tìm
        top_k: Số chunks cần trả về (mặc định 3)
    """
    try:
        import sys
        sys.path.insert(0, os.path.dirname(__file__))
        from workers.retrieval import retrieve_dense
        chunks = retrieve_dense(query, top_k=top_k)
        sources = list({c["source"] for c in chunks})
        return {
            "chunks": chunks,
            "sources": sources,
            "total_found": len(chunks),
        }
    except Exception as e:
        return {
            "chunks": [
                {
                    "text": f"[MOCK] Không thể query ChromaDB: {e}. Kết quả giả lập.",
                    "source": "mock_data",
                    "score": 0.5,
                }
            ],
            "sources": ["mock_data"],
            "total_found": 1,
        }


@mcp.tool()
def get_ticket_info(ticket_id: str) -> dict:
    """
    Tra cứu thông tin ticket từ hệ thống Jira nội bộ.

    Args:
        ticket_id: ID ticket (VD: IT-1234, P1-LATEST)
    """
    ticket = MOCK_TICKETS.get(ticket_id.upper())
    if ticket:
        return ticket
    return {
        "error": f"Ticket '{ticket_id}' không tìm thấy trong hệ thống.",
        "available_mock_ids": list(MOCK_TICKETS.keys()),
    }


@mcp.tool()
def check_access_permission(
    access_level: int,
    requester_role: str,
    is_emergency: bool = False,
) -> dict:
    """
    Kiểm tra điều kiện cấp quyền truy cập theo Access Control SOP.

    Args:
        access_level: Level cần cấp (1, 2, hoặc 3)
        requester_role: Vai trò của người yêu cầu
        is_emergency: Có phải khẩn cấp không (mặc định False)
    """
    rule = ACCESS_RULES.get(access_level)
    if not rule:
        return {"error": f"Access level {access_level} không hợp lệ. Levels: 1, 2, 3."}

    notes = []
    if is_emergency and rule.get("emergency_can_bypass"):
        notes.append(rule.get("emergency_bypass_note", ""))
    elif is_emergency and not rule.get("emergency_can_bypass"):
        notes.append(f"Level {access_level} KHÔNG có emergency bypass. Phải follow quy trình chuẩn.")

    return {
        "access_level": access_level,
        "can_grant": True,
        "required_approvers": rule["required_approvers"],
        "approver_count": len(rule["required_approvers"]),
        "emergency_override": is_emergency and rule.get("emergency_can_bypass", False),
        "notes": notes,
        "source": "access_control_sop.txt",
    }


@mcp.tool()
def create_ticket(priority: str, title: str, description: str = "") -> dict:
    """
    Tạo ticket mới trong hệ thống Jira (MOCK — không tạo thật trong lab).

    Args:
        priority: Mức độ ưu tiên (P1, P2, P3, P4)
        title: Tiêu đề ticket
        description: Mô tả chi tiết (tuỳ chọn)
    """
    mock_id = f"IT-{9900 + hash(title) % 99}"
    ticket = {
        "ticket_id": mock_id,
        "priority": priority,
        "title": title,
        "description": description[:200],
        "status": "open",
        "created_at": datetime.now().isoformat(),
        "url": f"https://jira.company.internal/browse/{mock_id}",
        "note": "MOCK ticket — không tồn tại trong hệ thống thật",
    }
    print(f"  [MCP create_ticket] MOCK: {mock_id} | {priority} | {title[:50]}")
    return ticket



# Entry point
# ─────────────────────────────────────────────

if __name__ == "__main__":
    # Chạy MCP server qua streamable-http (mặc định port 8000)
    # Client kết nối tại: http://localhost:8000/mcp
    mcp.run(transport="streamable-http")
