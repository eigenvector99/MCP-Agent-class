"""
STEP 2. 데이터 조물조물 해 보기

실행: python step2_explore_db.py

에이전트를 만들기 전에, 우리가 다룰 데이터가 어떻게 생겼는지 직접 확인합니다.
여기서 쓴 SQL 질문들이 그대로 MCP 서버의 '도구'가 됩니다.
"""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "data" / "my_projects.db"


def show(conn: sqlite3.Connection, title: str, sql: str, params: tuple = ()) -> None:
    print(f"\n■ {title}")
    cur = conn.execute(sql, params)
    cols = [c[0] for c in cur.description]
    print("  " + " | ".join(cols))
    for row in cur.fetchall():
        print("  " + " | ".join("" if v is None else str(v) for v in row))


def main() -> None:
    if not DB_PATH.exists():
        print("DB가 없습니다. 먼저 python step1_setup_db.py 를 실행하세요.")
        return

    conn = sqlite3.connect(DB_PATH)

    # 1) 어떤 표(테이블)가 있을까?
    show(conn, "테이블 목록", "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")

    # 2) 프로젝트 전체 보기
    show(conn, "프로젝트", "SELECT id, name, status, due_date FROM projects")

    # 3) 진행 중인 할 일만 보기
    show(conn, "진행 중인 할 일", "SELECT id, title, priority, due_date FROM tasks WHERE status = '진행 중'")

    # 4) 두 표를 이어서(JOIN) 보기: 할 일이 어느 프로젝트 것인지
    show(
        conn,
        "앞으로 7일 안에 마감인 할 일",
        """
        SELECT t.id, p.name AS project, t.title, t.due_date
        FROM tasks t JOIN projects p ON p.id = t.project_id
        WHERE t.status != '완료' AND t.due_date BETWEEN date('now', 'localtime') AND date('now', 'localtime', '+7 day')
        ORDER BY t.due_date
        """,
    )

    # 5) 집계: 프로젝트별 진행률
    show(
        conn,
        "프로젝트별 진행률",
        """
        SELECT p.name,
               COUNT(t.id) AS total,
               SUM(t.status = '완료') AS done,
               CAST(100.0 * SUM(t.status = '완료') / COUNT(t.id) AS INTEGER) || '%' AS progress
        FROM projects p LEFT JOIN tasks t ON t.project_id = p.id
        GROUP BY p.id
        """,
    )

    conn.close()


if __name__ == "__main__":
    main()
