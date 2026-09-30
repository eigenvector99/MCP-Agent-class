# 개인 DB 관리 에이전트 실습 폴더

OpenAI Agents SDK와 MCP 서버로 **내 프로젝트·할 일 DB를 말로 관리하는 에이전트**를 만듭니다.

## 폴더 구성

| 파일 | 하는 일 |
|---|---|
| `step1_setup_db.py` | 실습용 SQLite DB(`data/my_projects.db`)를 만드는 파이썬 스크립트(주문서). 망가뜨렸을 때 다시 실행하면 초기화 |
| `step2_explore_db.py` | 데이터를 SQL로 직접 살펴본다 |
| `step3_mcp_server.py` | DB를 다루는 도구 7개를 가진 MCP 서버 (직접 실행하면 무응답 대기가 정상) |
| `step3_test_server.py` | API 키 없이 MCP 서버 동작을 확인한다 |
| `step4_agent.py` | Agents SDK 에이전트에 MCP 서버를 연결해 대화한다 (앞 대화 기억은 아직 없음) |
| `step5_agent_chat.py` | 대화 기억 · 삭제 승인 · 도구 호출 로그를 더한 대화형 에이전트 |
| `report_template.md` | 공유용 보고서 양식 |

## 준비

> **파이썬 3.10 이상이 필요합니다.** `mcp`, `openai-agents`는 3.9 이하에서 설치되지 않아
> `No matching distribution found for mcp` 오류가 납니다. 최신 버전(3.14)을 설치하고,
> 명령어에 **버전 번호를 붙여** 부르세요. 번호 없이 `python3`만 쓰면 컴퓨터에 원래 있던 옛 버전이 잡힐 수 있습니다.

```bash
# 0. 파이썬 설치 확인
# macOS: brew install python@3.14  (또는 python.org 설치 파일)
python3.14 --version
# Windows: python.org 설치 파일 실행 ("Add python.exe to PATH"가 보이면 체크)
py -3.14 --version

# 1. 가상환경 만들고 켜기
# macOS / Linux
python3.14 -m venv .venv
source .venv/bin/activate #가상환경 폴도에 bin 폴더가 아닌 script 폴더가 있는 경우 script/activate 로 변경
# Windows
py -3.14 -m venv .venv
.venv\Scripts\activate

# 2. 버전 확인 후 패키지 설치
python --version        # 3.14.x 가 나와야 함
pip install -r requirements.txt

# 3. API 키 설정: .env.example 을 복사해 .env 로 이름을 바꾸고 키 입력
```

## 실행 순서

```bash
python step1_setup_db.py        # DB 만들기
python step2_explore_db.py      # 데이터 살펴보기
python step3_test_server.py     # MCP 서버 점검 (API 키 불필요)
python step4_agent.py          # 대화형 ('끝' 입력 시 종료)
python step5_agent_chat.py     # 대화 기억 · 삭제 승인 · 도구 호출 로그 추가
```

## 같은 MCP 서버를 Claude 데스크톱 앱에 연결하기

Claude 데스크톱 앱 설정의 개발자 메뉴에서 설정 파일(`claude_desktop_config.json`)을 열고 아래를 추가한 뒤 앱을 다시 시작합니다.
경로는 본인 컴퓨터의 **절대 경로**로 바꾸세요. 절대경로란, /Users/사용자계정/DBR/personal-db-agent 와 같이 컴퓨터 내 파일이 저장된 주소를 의미합니다. 보통 파일탐색기 혹은 finder(맥)에서 정보를 추출할 수 있습니다.

```json
{
  "mcpServers": {
    "personal-db": {
      "command": "/절대경로/personal-db-agent/.venv/bin/python",
      "args": ["/절대경로/personal-db-agent/step3_mcp_server.py"]
    }
  }
}
```

Windows는 `command`를 `C:\\...\\personal-db-agent\\.venv\\Scripts\\python.exe`처럼 적습니다.

## 자주 막히는 곳

- **`No matching distribution found for mcp`** → 파이썬이 3.9 이하. 3.14 설치 후 `python3.14 -m venv .venv`(Windows는 `py -3.14 -m venv .venv`)로 가상환경을 다시 만들기
- **`python3.14: command not found`** → 3.14가 아직 설치되지 않음. 설치 후 터미널을 새로 열기
- **`No module named 'mcp.server.fastmcp'`** → 인터넷의 옛 예제(mcp 1.x) 코드. 이 폴더는 mcp 2.x 기준이라 `from mcp.server.mcpserver import MCPServer`를 쓴다
- **`python step3_mcp_server.py` 실행 후 아무 반응이 없음** → 정상. 에이전트의 요청을 기다리는 상태라 출력이 없다. `Ctrl + C`로 끄고, 점검은 `python step3_test_server.py`로 한다 (step4·step5는 서버를 알아서 켜고 끈다)
- **VS Code에서 `dotenv`, `agents` 같은 import에 노란 줄** → 코드 문제가 아니라 VS Code가 가상환경을 보지 않는 것. `Cmd/Ctrl + Shift + P` → `Python: Select Interpreter` → `.venv` 안의 파이썬(3.14) 선택
- **`OPENAI_API_KEY를 찾지 못했습니다`** → 폴더 맨 위에 `.env` 파일이 있는지, 예시 문구 대신 본인 키를 넣었는지 확인. 또한 .env.example 으로 파일 이름이 되어있는지 확인. '.example'은 지워줘야합니다.
- **`DB가 없습니다`** → `python step1_setup_db.py`를 먼저 실행
- **`OPENAI_API_KEY` 오류** → `.env` 파일 이름과 위치(폴더 맨 위)를 확인
- **MCP 서버가 응답하지 않음** → `step3_mcp_server.py`에 `print()`를 넣지 않았는지 확인 (stdio 통신이 깨짐)
- **공유할 때** → `.env`, `.venv` 폴더는 빼고 공유
