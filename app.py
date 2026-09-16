import html
import json
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

app = FastAPI(title="방명록")

DATA_FILE = Path(__file__).parent / "guestboard.json"

NAME_MAX_LEN = 20
MESSAGE_MAX_LEN = 300

AVATAR_COLORS = ["#2f9e44", "#37b24d", "#40c057", "#51cf66", "#0ca678", "#12b886"]


def load_entries() -> list[dict]:
    if not DATA_FILE.exists():
        return []
    with DATA_FILE.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_entries(entries: list[dict]) -> None:
    with DATA_FILE.open("w", encoding="utf-8") as f:
        json.dump(entries, f, ensure_ascii=False, indent=2)


def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def avatar_color(name: str) -> str:
    return AVATAR_COLORS[sum(ord(c) for c in name) % len(AVATAR_COLORS)]


def format_datetime(iso_str: str) -> str:
    dt = datetime.fromisoformat(iso_str)
    return dt.strftime("%Y년 %m월 %d일 %H:%M")


PAGE_TEMPLATE = """
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>방명록</title>
<style>
    :root {{
        --green-dark: #1b4332;
        --green: #2d6a4f;
        --green-mid: #40916c;
        --green-light: #74c69d;
        --green-pale: #d8f3dc;
        --bg: #f4faf6;
    }}
    * {{ box-sizing: border-box; }}
    body {{
        font-family: "Apple SD Gothic Neo", "Malgun Gothic", "Segoe UI", sans-serif;
        background: var(--bg);
        margin: 0;
        padding: 0 16px 60px;
        color: #1b1b1b;
    }}
    .header {{
        max-width: 640px;
        margin: 0 auto;
        padding: 48px 0 24px;
        text-align: center;
    }}
    .header h1 {{
        color: var(--green-dark);
        font-size: 2.2rem;
        margin: 0 0 6px;
    }}
    .header p {{
        color: var(--green-mid);
        margin: 0;
        font-size: 0.95rem;
    }}
    .container {{
        max-width: 640px;
        margin: 0 auto;
    }}
    .card {{
        background: #fff;
        border-radius: 14px;
        box-shadow: 0 2px 10px rgba(27, 67, 50, 0.08);
        padding: 24px;
        margin-bottom: 24px;
    }}
    .form-card h2 {{
        margin-top: 0;
        color: var(--green-dark);
        font-size: 1.15rem;
    }}
    label {{
        display: block;
        font-size: 0.85rem;
        color: var(--green);
        margin-bottom: 6px;
        font-weight: 600;
    }}
    input[type=text], textarea {{
        width: 100%;
        padding: 10px 12px;
        border: 1.5px solid var(--green-pale);
        border-radius: 8px;
        font-size: 0.95rem;
        font-family: inherit;
        margin-bottom: 16px;
        resize: vertical;
        transition: border-color 0.15s;
    }}
    input[type=text]:focus, textarea:focus {{
        outline: none;
        border-color: var(--green-light);
    }}
    textarea {{ min-height: 90px; }}
    button {{
        background: var(--green);
        color: #fff;
        border: none;
        border-radius: 8px;
        padding: 10px 22px;
        font-size: 0.95rem;
        font-weight: 600;
        cursor: pointer;
        transition: background 0.15s;
    }}
    button:hover {{ background: var(--green-dark); }}
    .count {{
        color: var(--green-mid);
        font-size: 0.9rem;
        margin: 0 4px 12px;
    }}
    .entry {{
        background: #fff;
        border-radius: 14px;
        box-shadow: 0 2px 10px rgba(27, 67, 50, 0.06);
        padding: 18px 20px;
        margin-bottom: 14px;
        border-left: 5px solid var(--green-light);
        position: relative;
    }}
    .entry-header {{
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 8px;
    }}
    .avatar {{
        width: 34px;
        height: 34px;
        border-radius: 50%;
        color: #fff;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        font-size: 0.95rem;
        flex-shrink: 0;
    }}
    .entry-name {{
        font-weight: 700;
        color: var(--green-dark);
    }}
    .entry-date {{
        font-size: 0.78rem;
        color: #999;
        margin-left: auto;
    }}
    .entry-message {{
        white-space: pre-wrap;
        line-height: 1.5;
        color: #333;
        word-break: break-word;
    }}
    .delete-form {{
        position: absolute;
        top: 14px;
        right: 16px;
    }}
    .delete-btn {{
        background: none;
        color: #bbb;
        border: none;
        padding: 2px 6px;
        font-size: 0.8rem;
        cursor: pointer;
    }}
    .delete-btn:hover {{ color: #d9534f; }}
    .empty {{
        text-align: center;
        color: var(--green-mid);
        padding: 40px 0;
        font-size: 0.95rem;
    }}
</style>
</head>
<body>
    <div class="header">
        <h1>🌿 방명록</h1>
        <p>다녀가신 흔적을 따뜻한 한마디로 남겨주세요</p>
    </div>
    <div class="container">
        <div class="card form-card">
            <h2>글 남기기</h2>
            <form method="post" action="/add">
                <label>이름</label>
                <input type="text" name="name" maxlength="{name_max}" placeholder="이름을 입력하세요" required>
                <label>메시지</label>
                <textarea name="message" maxlength="{message_max}" placeholder="방명록 내용을 남겨주세요" required></textarea>
                <button type="submit">등록하기</button>
            </form>
        </div>
        <p class="count">총 {count}개의 글</p>
        {entries_html}
    </div>
</body>
</html>
"""

ENTRY_TEMPLATE = """
<div class="entry">
    <div class="entry-header">
        <div class="avatar" style="background:{color};">{initial}</div>
        <span class="entry-name">{name}</span>
        <span class="entry-date">{date}</span>
    </div>
    <div class="entry-message">{message}</div>
    {delete_form}
</div>
"""

DELETE_FORM_TEMPLATE = """
<form class="delete-form" method="post" action="/delete/{entry_id}" onsubmit="return confirm('삭제하시겠습니까?');">
    <button type="submit" class="delete-btn">삭제</button>
</form>
"""

EMPTY_HTML = '<div class="empty">아직 작성된 글이 없습니다. 첫 번째 글을 남겨보세요!</div>'


def render_page(request: Request) -> str:
    entries = load_entries()
    client_ip = get_client_ip(request)

    if not entries:
        entries_html = EMPTY_HTML
    else:
        blocks = []
        for entry in reversed(entries):
            name = html.escape(entry["name"])
            message = html.escape(entry["message"])
            delete_form = (
                DELETE_FORM_TEMPLATE.format(entry_id=entry["id"])
                if entry.get("ip") == client_ip
                else ""
            )
            blocks.append(
                ENTRY_TEMPLATE.format(
                    color=avatar_color(entry["name"]),
                    initial=html.escape(entry["name"][0].upper()),
                    name=name,
                    date=format_datetime(entry["created_at"]),
                    message=message,
                    delete_form=delete_form,
                )
            )
        entries_html = "".join(blocks)

    return PAGE_TEMPLATE.format(
        name_max=NAME_MAX_LEN,
        message_max=MESSAGE_MAX_LEN,
        count=len(entries),
        entries_html=entries_html,
    )


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return render_page(request)


@app.post("/add")
def add_entry(request: Request, name: str = Form(...), message: str = Form(...)):
    name = name.strip()[:NAME_MAX_LEN]
    message = message.strip()[:MESSAGE_MAX_LEN]

    if name and message:
        entries = load_entries()
        entries.append(
            {
                "id": str(uuid.uuid4()),
                "name": name,
                "message": message,
                "created_at": datetime.now().isoformat(),
                "ip": get_client_ip(request),
            }
        )
        save_entries(entries)

    return RedirectResponse("/", status_code=303)


@app.post("/delete/{entry_id}")
def delete_entry(entry_id: str, request: Request):
    client_ip = get_client_ip(request)
    entries = load_entries()
    entries = [e for e in entries if not (e["id"] == entry_id and e.get("ip") == client_ip)]
    save_entries(entries)
    return RedirectResponse("/", status_code=303)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
