import random
import uuid

from fastapi import Cookie, FastAPI, Form
from fastapi.responses import HTMLResponse, RedirectResponse

app = FastAPI(title="숫자 맞추기 게임")

games: dict[str, dict] = {}

PAGE = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>숫자 맞추기 게임</title>
    <style>
        body {{ font-family: sans-serif; max-width: 480px; margin: 60px auto; text-align: center; }}
        input[type=number] {{ font-size: 1.2rem; padding: 6px; width: 120px; text-align: center; }}
        button {{ font-size: 1.2rem; padding: 6px 16px; }}
        .message {{ font-size: 1.1rem; margin: 20px 0; min-height: 1.5em; }}
        .attempts {{ color: #666; }}
    </style>
</head>
<body>
    <h1>1부터 100 사이의 숫자를 맞춰보세요!</h1>
    <p class="message">{message}</p>
    <p class="attempts">시도 횟수: {attempts}</p>
    <form method="post" action="/guess">
        <input type="number" name="guess" min="1" max="100" required autofocus>
        <button type="submit">확인</button>
    </form>
    <form method="post" action="/reset" style="margin-top: 12px;">
        <button type="submit">다시 시작</button>
    </form>
</body>
</html>
"""


def new_game() -> dict:
    return {"answer": random.randint(1, 100), "attempts": 0, "message": "숫자를 입력해보세요.", "won": False}


def get_or_create_session(session_id: str | None) -> tuple[str, dict]:
    if session_id and session_id in games:
        return session_id, games[session_id]

    session_id = str(uuid.uuid4())
    game = new_game()
    games[session_id] = game
    return session_id, game


@app.get("/", response_class=HTMLResponse)
def index(session_id: str | None = Cookie(default=None)):
    session_id, game = get_or_create_session(session_id)

    html = PAGE.format(message=game["message"], attempts=game["attempts"])
    response = HTMLResponse(html)
    response.set_cookie("session_id", session_id)
    return response


@app.post("/guess")
def guess(guess: int = Form(...), session_id: str | None = Cookie(default=None)):
    session_id, game = get_or_create_session(session_id)

    if not game["won"]:
        game["attempts"] += 1

        if guess < game["answer"]:
            game["message"] = "더 높은 숫자입니다."
        elif guess > game["answer"]:
            game["message"] = "더 낮은 숫자입니다."
        else:
            game["message"] = f"정답입니다! {game['attempts']}번 만에 맞추셨습니다. 축하합니다!"
            game["won"] = True

    response = RedirectResponse("/", status_code=303)
    response.set_cookie("session_id", session_id)
    return response


@app.post("/reset")
def reset(session_id: str | None = Cookie(default=None)):
    session_id = session_id or str(uuid.uuid4())
    games[session_id] = new_game()

    response = RedirectResponse("/", status_code=303)
    response.set_cookie("session_id", session_id)
    return response


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
