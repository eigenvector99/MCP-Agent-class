"""
STEP 1. 실습용 개인 DB 만들기

실행: python step1_setup_db.py
결과: data/my_projects.db 파일이 새로 만들어집니다.
      (이미 있으면 지우고 처음 상태로 다시 만듭니다. 실습 중 DB를 망가뜨렸을 때도 이 파일을 다시 실행하세요.)

마감일은 '오늘'을 기준으로 계산되므로, 언제 실행해도 "이번 주 마감", "기한 지난 일" 같은 질문이 자연스럽게 동작합니다.
"""

import sqlite3
from datetime import date, timedelta
from pathlib import Path

DB_PATH = Path(__file__).parent / "data" / "my_projects.db"

SCHEMA = """
CREATE TABLE projects (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL,
    description TEXT,
    status      TEXT NOT NULL DEFAULT '진행 중',   -- '진행 중' | '보류' | '완료'
    start_date  TEXT,                               -- YYYY-MM-DD
    due_date    TEXT                                -- YYYY-MM-DD
);

CREATE TABLE tasks (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id  INTEGER NOT NULL REFERENCES projects(id),
    title       TEXT NOT NULL,
    status      TEXT NOT NULL DEFAULT '할 일',      -- '할 일' | '진행 중' | '완료'
    priority    TEXT NOT NULL DEFAULT '보통',       -- '높음' | '보통' | '낮음'
    due_date    TEXT,                               -- YYYY-MM-DD
    created_at  TEXT NOT NULL,
    done_at     TEXT
);
"""

# (이름, 설명, 상태, 시작일 오프셋, 마감일 오프셋)  ※ 오프셋 = 오늘로부터 며칠
PROJECTS = [
    ("블로그 리뉴얼", "개인 기술 블로그 디자인과 카테고리 개편", "진행 중", -30, 20),
    ("가계부 앱 만들기", "사이드 프로젝트: 지출을 기록하는 모바일 웹앱", "진행 중", -45, 40),
    ("정보처리기사 준비", "필기와 실기 대비 공부 계획", "진행 중", -60, 25),
    ("이사 준비", "다음 달 이사를 위한 준비 목록", "보류", -10, 35),
    ("독서 모임 운영", "월 1회 독서 모임 기획과 진행", "완료", -120, -5),
]

# (프로젝트 번호, 할 일, 상태, 우선순위, 마감 오프셋, 생성 오프셋, 완료 오프셋)
TASKS = [
    (1, "새 블로그 테마 고르기", "완료", "보통", -20, -28, -21),
    (1, "카테고리 구조 다시 짜기", "진행 중", "높음", 2, -15, None),
    (1, "예전 글 30개 태그 정리", "할 일", "보통", 9, -12, None),
    (1, "소개 페이지 새로 쓰기", "할 일", "낮음", 16, -5, None),
    (2, "화면 설계서 작성", "완료", "높음", -30, -44, -32),
    (2, "지출 입력 화면 개발", "진행 중", "높음", -2, -25, None),
    (2, "월별 통계 차트 붙이기", "할 일", "보통", 12, -20, None),
    (2, "베타 테스터 5명 모집", "할 일", "낮음", 30, -3, None),
    (3, "필기 기출 3회분 풀기", "완료", "높음", -15, -55, -16),
    (3, "데이터베이스 과목 복습", "진행 중", "높음", 4, -20, None),
    (3, "실기 프로그래밍 문제 정리", "할 일", "높음", 6, -10, None),
    (3, "모의고사 1회 보기", "할 일", "보통", 20, -7, None),
    (4, "이사업체 견적 3곳 받기", "할 일", "높음", -1, -9, None),
    (4, "버릴 가구 목록 만들기", "할 일", "보통", 14, -8, None),
    (4, "전입신고 서류 확인", "할 일", "낮음", 33, -8, None),
    (5, "11월 도서 선정 투표", "완료", "보통", -40, -60, -41),
    (5, "모임 장소 예약", "완료", "보통", -20, -35, -22),
    (5, "후기 정리해서 공유", "완료", "낮음", -6, -18, -6),
]


def d(offset: int | None) -> str | None:
    """오늘로부터 offset일 뒤의 날짜를 'YYYY-MM-DD' 문자열로 돌려줍니다."""
    if offset is None:
        return None
    return (date.today() + timedelta(days=offset)).isoformat()


def main() -> None:
    DB_PATH.parent.mkdir(exist_ok=True)
    if DB_PATH.exists():
        DB_PATH.unlink()

    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA)
    conn.executemany(
        "INSERT INTO projects (name, description, status, start_date, due_date) VALUES (?, ?, ?, ?, ?)",
        [(n, desc, s, d(start), d(due)) for n, desc, s, start, due in PROJECTS],
    )
    conn.executemany(
        "INSERT INTO tasks (project_id, title, status, priority, due_date, created_at, done_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        [(p, t, s, pr, d(due), d(created), d(done)) for p, t, s, pr, due, created, done in TASKS],
    )
    conn.commit()
    conn.close()
    print(f"DB 생성 완료: {DB_PATH}")
    print(f"프로젝트 {len(PROJECTS)}개, 할 일 {len(TASKS)}개")


if __name__ == "__main__":
    main()
