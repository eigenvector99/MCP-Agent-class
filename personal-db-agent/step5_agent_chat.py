"""
STEP 5. 대화형 에이전트로 키우기 (바이브코딩 확장 예시)

실행: python step5_agent_chat.py
      종료하려면 '끝' 또는 'exit' 입력

STEP 4에서 세 가지를 더했습니다.
  ① 대화 기억   : SQLiteSession — 앞에서 한 말을 기억한다 ("그거 완료로 바꿔 줘"가 통한다)
  ② 삭제 승인   : require_approval — delete_task 를 부르기 전에 사람에게 y/n 을 묻는다
  ③ 도구 호출 로그 : 에이전트가 어떤 도구를 불렀는지 화면에 보여 준다
"""

import asyncio
import os
import sys
from datetime import date
from pathlib import Path

from dotenv import load_dotenv
from agents import Agent, Runner, SQLiteSession
from agents.mcp import MCPServerStdio

load_dotenv()

# API 키 점검: .env가 없거나, 예시 문구를 그대로 두었으면 여기서 멈춘다
api_key = os.getenv("OPENAI_API_KEY", "")
if not api_key.startswith("sk-") or "여기에" in api_key:
    sys.exit("OPENAI_API_KEY를 찾지 못했습니다. 폴더 맨 위에 .env 파일이 있는지, 본인 키(sk-...)를 넣었는지 확인하세요.")

SERVER_PATH = Path(__file__).parent / "step3_mcp_server.py"
MEMORY_PATH = Path(__file__).parent / "data" / "chat_memory.db"

INSTRUCTIONS = f"""
너는 사용자의 개인 프로젝트 DB를 관리하는 비서다. 오늘은 {date.today().isoformat()}이다.
- 답하기 전에 반드시 도구로 DB를 조회하고, DB에 없는 내용은 지어내지 않는다.
- '그거', '아까 그 일'처럼 가리키는 말은 앞 대화에서 찾아 해석한다. 애매하면 되묻는다.
- 날짜는 'YYYY-MM-DD'로 다루되, 사용자에게는 '3일 남음', '2일 지남'처럼 알려 준다.
- 할 일을 추가하거나 바꾼 뒤에는 무엇이 바뀌었는지 한 줄로 확인해 준다.
- 삭제가 거절되면 완료 처리 같은 다른 방법을 제안한다.
- 답변은 한국어로, 짧고 보기 좋게 정리한다.
"""


def ask_approval(result, state) -> None:
    """에이전트가 승인이 필요한 도구를 부르려 하면, 사람에게 직접 물어본다."""
    for item in result.interruptions:
        answer = input(f"  ⚠ '{item.name}' 실행 요청 {item.arguments} — 허용할까요? (y/n) ").strip().lower()
        if answer == "y":
            state.approve(item)
        else:
            state.reject(item, rejection_message="사용자가 삭제를 거절했습니다.")


def print_tool_calls(result) -> None:
    for item in result.new_items:
        if item.type == "tool_call_item":
            name = getattr(item.raw_item, "name", "도구")
            print(f"  · 도구 호출: {name}")


async def main() -> None:
    session = SQLiteSession("my-session", str(MEMORY_PATH))  # ① 대화 기억

    async with MCPServerStdio(
        name="personal-db",
        params={"command": sys.executable, "args": [str(SERVER_PATH)]},
        cache_tools_list=True,
        require_approval={"delete_task": "always"},  # ② 삭제는 사람 승인 필요
    ) as db_server:
        agent = Agent(
            name="개인 DB 매니저",
            instructions=INSTRUCTIONS,
            mcp_servers=[db_server],
            model=os.getenv("OPENAI_MODEL") or None,
        )

        print("개인 DB 매니저입니다. 무엇을 도와드릴까요? ('끝' 입력 시 종료)")
        while True:
            question = input("\n나> ").strip()
            if question in ("끝", "exit", "quit"):
                break
            if not question:
                continue

            result = await Runner.run(agent, question, session=session)
            while result.interruptions:  # 승인 대기 중이면 물어보고 이어서 실행
                state = result.to_state()
                ask_approval(result, state)
                result = await Runner.run(agent, state, session=session)

            print_tool_calls(result)  # ③ 도구 호출 로그
            print(f"\n에이전트> {result.final_output}")


if __name__ == "__main__":
    asyncio.run(main())
