"""
STEP 3. MCP 서버 만들기 — 개인 DB를 다루는 '도구 상자'

이 파일은 직접 실행하는 프로그램이 아닙니다.
에이전트(step4)나 Claude 데스크톱 앱이 이 파일을 실행해서, 안에 있는 도구를 빌려 씁니다.

동작만 먼저 확인하고 싶다면:  python step3_test_server.py

※ 주의: stdio 방식 MCP 서버에서는 print()를 쓰면 안 됩니다.
   표준출력(stdout)이 에이전트와 대화하는 통로라서, print가 끼어들면 통신이 깨집니다.
"""

import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path

from mcp.server.mcpserver import MCPServer  # mcp 2.x 기준 (1.x의 FastMCP가 MCPServer로 바뀜)

DB_PATH = Path(__file__).parent / "data" / "my_projects.db"

TASK_STATUSES = ["할 일", "진행 중", "완료"]
PROJECT_STATUSES = ["진행 중", "보류", "완료"]
PRIORITIES = ["높음", "보통", "낮음"]

mcp = MCPServer("personal-db")


def connect() -> sqlite3.Connection:
    if not DB_PATH.exists():
        raise FileNotFoundError("DB가 없습니다. 먼저 python step1_setup_db.py 를 실행하세요.")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # 결과를 {컬럼이름: 값} 형태로 받기
    return conn


def rows(cur: sqlite3.Cursor) -> list[dict]:
    return [dict(r) for r in cur.fetchall()]


# ──────────────────────────────────────────────
# 조회 도구 (읽기만 함)
# ──────────────────────────────────────────────

@mcp.tool()
def get_overview() -> dict:
    """오늘 날짜와 전체 현황(프로젝트별 진행률, 기한 지난 할 일, 7일 안에 마감인 할 일)을 한 번에 요약한다.
    사용자가 '요즘 상황', '브리핑', '뭐부터 해야 해?'처럼 전체를 물으면 가장 먼저 사용한다."""
    today = date.today().isoformat()
    week_later = (date.today() + timedelta(days=7)).isoformat()
    with connect() as conn:
        progress = rows(conn.execute(
            """SELECT p.id, p.name, p.status,
                      COUNT(t.id) AS total, COALESCE(SUM(t.status = '완료'), 0) AS done
               FROM projects p LEFT JOIN tasks t ON t.project_id = p.id
               GROUP BY p.id ORDER BY p.id"""))
        overdue = rows(conn.execute(
            """SELECT t.id, p.name AS project, t.title, t.priority, t.due_date
               FROM tasks t JOIN projects p ON p.id = t.project_id
               WHERE t.status != '완료' AND t.due_date < ? ORDER BY t.due_date""", (today,)))
        due_soon = rows(conn.execute(
            """SELECT t.id, p.name AS project, t.title, t.priority, t.due_date
               FROM tasks t JOIN projects p ON p.id = t.project_id
               WHERE t.status != '완료' AND t.due_date BETWEEN ? AND ? ORDER BY t.due_date""",
            (today, week_later)))
    return {"today": today, "projects": progress, "overdue": overdue, "due_within_7_days": due_soon}


@mcp.tool()
def list_projects(status: str | None = None) -> list[dict]:
    """프로젝트 목록을 돌려준다. status로 거를 수 있다('진행 중', '보류', '완료')."""
    sql = "SELECT id, name, description, status, start_date, due_date FROM projects"
    params: tuple = ()
    if status:
        sql += " WHERE status = ?"
        params = (status,)
    with connect() as conn:
        return rows(conn.execute(sql + " ORDER BY id", params))


@mcp.tool()
def list_tasks(
    project_id: int | None = None,
    status: str | None = None,
    due_within_days: int | None = None,
) -> list[dict]:
    """할 일 목록을 돌려준다. 조건은 모두 선택 사항이다.
    - project_id: 특정 프로젝트의 할 일만 (프로젝트 id는 list_projects로 확인)
    - status: '할 일', '진행 중', '완료' 중 하나
    - due_within_days: 오늘부터 N일 안에 마감인 미완료 할 일만 (기한 지난 것 포함)"""
    sql = """SELECT t.id, t.project_id, p.name AS project, t.title, t.status,
                    t.priority, t.due_date, t.done_at
             FROM tasks t JOIN projects p ON p.id = t.project_id WHERE 1=1"""
    params: list = []
    if project_id is not None:
        sql += " AND t.project_id = ?"
        params.append(project_id)
    if status:
        sql += " AND t.status = ?"
        params.append(status)
    if due_within_days is not None:
        limit = (date.today() + timedelta(days=due_within_days)).isoformat()
        sql += " AND t.status != '완료' AND t.due_date <= ?"
        params.append(limit)
    sql += " ORDER BY t.due_date IS NULL, t.due_date"
    with connect() as conn:
        return rows(conn.execute(sql, params))


# ──────────────────────────────────────────────
# 변경 도구 (DB를 바꿈)
# ──────────────────────────────────────────────

@mcp.tool()
def add_task(project_id: int, title: str, due_date: str | None = None, priority: str = "보통") -> dict:
    """프로젝트에 새 할 일을 추가한다. due_date는 'YYYY-MM-DD' 형식, priority는 '높음'/'보통'/'낮음'."""
    if priority not in PRIORITIES:
        return {"error": f"priority는 {PRIORITIES} 중 하나여야 합니다."}
    with connect() as conn:
        if not conn.execute("SELECT 1 FROM projects WHERE id = ?", (project_id,)).fetchone():
            return {"error": f"{project_id}번 프로젝트가 없습니다. list_projects로 id를 확인하세요."}
        cur = conn.execute(
            "INSERT INTO tasks (project_id, title, status, priority, due_date, created_at) "
            "VALUES (?, ?, '할 일', ?, ?, ?)",
            (project_id, title, priority, due_date, date.today().isoformat()),
        )
        conn.commit()
        return {"ok": True, "task_id": cur.lastrowid, "title": title}


@mcp.tool()
def update_task(
    task_id: int,
    status: str | None = None,
    priority: str | None = None,
    due_date: str | None = None,
    title: str | None = None,
) -> dict:
    """할 일의 상태·우선순위·마감일·제목을 바꾼다. 바꿀 항목만 넣으면 된다.
    status를 '완료'로 바꾸면 완료일(done_at)이 오늘로 기록된다."""
    if status and status not in TASK_STATUSES:
        return {"error": f"status는 {TASK_STATUSES} 중 하나여야 합니다."}
    if priority and priority not in PRIORITIES:
        return {"error": f"priority는 {PRIORITIES} 중 하나여야 합니다."}
    changes: dict = {}
    if status:
        changes["status"] = status
        changes["done_at"] = date.today().isoformat() if status == "완료" else None
    if priority:
        changes["priority"] = priority
    if due_date:
        changes["due_date"] = due_date
    if title:
        changes["title"] = title
    if not changes:
        return {"error": "바꿀 항목이 없습니다."}
    sets = ", ".join(f"{k} = ?" for k in changes)
    with connect() as conn:
        cur = conn.execute(f"UPDATE tasks SET {sets} WHERE id = ?", (*changes.values(), task_id))
        conn.commit()
        if cur.rowcount == 0:
            return {"error": f"{task_id}번 할 일이 없습니다."}
    return {"ok": True, "task_id": task_id, "changed": changes}


@mcp.tool()
def delete_task(task_id: int) -> dict:
    """할 일을 영구 삭제한다. 되돌릴 수 없으므로, 완료 처리로 충분한 경우에는 update_task를 쓴다."""
    with connect() as conn:
        row = conn.execute("SELECT title FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if not row:
            return {"error": f"{task_id}번 할 일이 없습니다."}
        conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()
    return {"ok": True, "deleted_task_id": task_id, "title": row["title"]}


@mcp.tool()
def add_project(name: str, description: str = "", due_date: str | None = None) -> dict:
    """새 프로젝트를 만든다. 상태는 '진행 중', 시작일은 오늘로 기록된다."""
    with connect() as conn:
        cur = conn.execute(
            "INSERT INTO projects (name, description, status, start_date, due_date) VALUES (?, ?, '진행 중', ?, ?)",
            (name, description, date.today().isoformat(), due_date),
        )
        conn.commit()
        return {"ok": True, "project_id": cur.lastrowid, "name": name}


if __name__ == "__main__":
    mcp.run()  # 기본값: stdio 방식
