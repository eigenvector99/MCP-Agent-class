"""
STEP 3-1. MCP 서버가 잘 동작하는지 LLM 없이 확인하기

실행: python step3_test_server.py

API 키가 없어도 됩니다. 서버를 띄워서 도구 목록을 받아 오고, 도구 하나를 직접 불러 봅니다.
여기서 문제가 없어야 STEP 4에서 에이전트에 연결했을 때도 잘 동작합니다.
"""

import asyncio
import sys
from pathlib import Path

from agents.mcp import MCPServerStdio

SERVER_PATH = Path(__file__).parent / "step3_mcp_server.py"


async def main() -> None:
    async with MCPServerStdio(
        name="personal-db",
        params={"command": sys.executable, "args": [str(SERVER_PATH)]},
    ) as server:
        tools = await server.list_tools()
        print(f"도구 {len(tools)}개를 찾았습니다.")
        for tool in tools:
            first_line = (tool.description or "").splitlines()[0]
            print(f"  - {tool.name}: {first_line}")

        print("\nget_overview 를 직접 호출해 봅니다.")
        result = await server.call_tool("get_overview", {})
        print(result.content[0].text[:600], "...")


if __name__ == "__main__":
    asyncio.run(main())
