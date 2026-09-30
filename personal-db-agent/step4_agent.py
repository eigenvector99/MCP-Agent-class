"""
STEP 4. OpenAI Agents SDK로 에이전트 만들고 MCP 서버 연결하기

실행: python step4_agent.py
      나> 뒤에 질문을 입력하면 에이전트가 답합니다. '끝'을 입력하면 종료합니다.

준비: .env 파일에 OPENAI_API_KEY 를 넣어 두세요. (.env.example 참고)

※ 이 단계의 에이전트는 질문마다 새로 생각하기 때문에 앞 대화를 기억하지 못합니다.
   대화 기억, 삭제 승인, 도구 호출 로그는 STEP 5에서 더합니다.
"""

import asyncio
import os
import sys
from datetime import date
from pathlib import Path

from dotenv import load_dotenv
from agents import Agent, Runner
from agents.mcp import MCPServerStdio

load_dotenv()  # .env 파일의 OPENAI_API_KEY 를 환경변수로 불러오기

# API 키 점검: .env가 없거나, 예시 문구를 그대로 두었으면 여기서 멈춘다
api_key = os.getenv("OPENAI_API_KEY", "")
if not api_key.startswith("sk-") or "여기에" in api_key:
    sys.exit("OPENAI_API_KEY를 찾지 못했습니다. 폴더 맨 위에 .env 파일이 있는지, 본인 키(sk-...)를 넣었는지 확인하세요.")

SERVER_PATH = Path(__file__).parent / "step3_mcp_server.py"

INSTRUCTIONS = f"""
너는 사용자의 개인 프로젝트 DB를 관리하는 비서다. 오늘은 {date.today().isoformat()}이다.
- 답하기 전에 반드시 도구로 DB를 조회하고, DB에 없는 내용은 지어내지 않는다.
- 날짜는 'YYYY-MM-DD'로 다루되, 사용자에게는 '3일 남음', '2일 지남'처럼 알려 준다.
- 할 일을 추가하거나 바꾼 뒤에는 무엇이 바뀌었는지 한 줄로 확인해 준다.
- 답변은 한국어로, 짧고 보기 좋게 정리한다.
"""


async def main() -> None:
    # 1) MCP 서버를 '하위 프로세스'로 띄우고 연결한다
    async with MCPServerStdio(
        name="personal-db",
        params={"command": sys.executable, "args": [str(SERVER_PATH)]},
        cache_tools_list=True,  # 도구 목록을 매번 다시 받지 않도록 저장
    ) as db_server:

        # 2) 에이전트 정의: 이름 + 지시문 + (MCP 서버에서 온) 도구
        agent = Agent(
            name="개인 DB 매니저",
            instructions=INSTRUCTIONS,
            mcp_servers=[db_server],
            model=os.getenv("OPENAI_MODEL") or None,  # 비워 두면 SDK 기본 모델 사용
        )

        # 3) 대화 루프: 질문이 들어올 때마다 Runner가 '판단 → 도구 호출 → 결과 확인'을 돌린다
        print("개인 DB 매니저입니다. 무엇을 도와드릴까요? ('끝' 입력 시 종료)")
        while True:
            question = input("\n나> ").strip()
            if question in ("끝", "exit", "quit"):
                break
            if not question:
                continue

            result = await Runner.run(agent, question)
            print(f"\n에이전트> {result.final_output}")


if __name__ == "__main__":
    asyncio.run(main())
