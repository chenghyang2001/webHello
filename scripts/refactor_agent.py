"""自動重構代理：依照 Architectural Directive 重構 index.html（繁體中文）"""

import os
import sys
import subprocess
from datetime import datetime
from pathlib import Path

import anthropic
import requests

# Architectural Directive：傳給 Claude 的完整重構指示
ARCHITECTURAL_DIRECTIVE = """你是一位對乾淨、優雅程式碼極度執著的資深軟體架構師。

任務：分析並重構以下 HTML/JavaScript 程式碼。

嚴格遵守以下規則：
1. 尋找重複：掃描並找出任何重複的邏輯或程式碼區塊
2. 抽取模組：將重複代碼提取為乾淨、可重複使用的工具函數或共用元件
3. 嚴格禁令：絕對不要添加任何新功能或改變用戶界面。唯一目標是讓架構更精簡
4. 補充註解：為任何複雜的程式碼提取加入清晰的行內註解（Inline comments）

如果有任何值得重構的地方，回傳完整的重構後 HTML（只有 HTML 內容，不要說明文字）。
如果程式碼已經足夠乾淨，無需重構，只需回傳字串：NO_REFACTOR_NEEDED"""


def send_telegram(message: str) -> None:
    """發送 Telegram 通知，失敗不中斷主流程。

    採用 fire-and-forget 設計：Telegram 發送失敗不應阻止重構流程正常結束。
    Telegram 通知為可選功能，未設定環境變數時靜默跳過。
    """
    bot_token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
    if not bot_token or not chat_id:
        print("警告：TELEGRAM_BOT_TOKEN 或 TELEGRAM_CHAT_ID 未設定，跳過通知", file=sys.stderr)
        return

    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    try:
        response = requests.post(
            url,
            json={"chat_id": chat_id, "text": message},
            timeout=10,
        )
        if not response.ok:
            print(f"警告：Telegram 通知失敗（HTTP {response.status_code}）", file=sys.stderr)
    except requests.RequestException as e:
        # Telegram 失敗不中斷主流程，僅記錄警告
        print(f"警告：Telegram 通知發送失敗：{e}", file=sys.stderr)


def create_github_pr(branch_name: str, today: str) -> str:
    """用 GitHub REST API 建立 PR，回傳 PR URL；失敗回傳空字串。

    使用 GITHUB_TOKEN（Actions 內建）進行認證，避免硬編碼憑證。
    """
    github_token = os.environ.get("GITHUB_TOKEN", "")
    repo = os.environ.get("GITHUB_REPOSITORY", "")

    if not github_token or not repo:
        print("錯誤：GITHUB_TOKEN 或 GITHUB_REPOSITORY 未設定", file=sys.stderr)
        return ""

    api_url = f"https://api.github.com/repos/{repo}/pulls"
    headers = {
        "Authorization": f"Bearer {github_token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    body_text = (
        f"## 自動重構 PR — {today}\n\n"
        "### 執行摘要\n"
        "此 PR 由 Architectural Directive 自動重構代理生成。\n\n"
        "**重構原則**：\n"
        "- 消除重複邏輯，提取可重複使用的工具函數\n"
        "- 不添加新功能，不改變使用者介面\n"
        "- 為複雜的代碼提取加入清晰的行內註解\n\n"
        "### 審查要點\n"
        "請確認重構後的行為與原版完全一致，無功能性變更。\n"
    )
    payload = {
        "title": f"refactor: 自動重構 index.html [{today}]",
        "body": body_text,
        "head": branch_name,
        "base": "master",
    }

    try:
        response = requests.post(api_url, headers=headers, json=payload, timeout=30)
        if response.ok:
            pr_url = response.json().get("html_url", "")
            print(f"PR 建立成功：{pr_url}")
            return pr_url
        else:
            print(
                f"錯誤：建立 PR 失敗（HTTP {response.status_code}）：{response.text}",
                file=sys.stderr,
            )
            return ""
    except requests.RequestException as e:
        print(f"錯誤：建立 PR 時發生網路錯誤：{e}", file=sys.stderr)
        return ""


def checkout_or_create_branch(branch_name: str, repo_root: str) -> None:
    """建立或切換到指定 branch，若 remote 已存在則先 fetch 再 checkout。

    前次失敗可能留下同名 branch，直接 checkout -b 會以 exit 128 失敗；
    先偵測 remote 是否已有該 branch，決定用 checkout -b 或 fetch + checkout。
    """
    check_result = subprocess.run(
        ["git", "ls-remote", "--heads", "origin", branch_name],
        cwd=repo_root,
        capture_output=True,
        text=True,
    )
    if check_result.stdout.strip():
        # Remote branch 已存在（前次失敗遺留），fetch 後直接切換
        print(f"Remote branch '{branch_name}' 已存在，切換到既有 branch")
        subprocess.run(
            ["git", "fetch", "origin", branch_name],
            cwd=repo_root,
            check=True,
        )
        subprocess.run(
            ["git", "checkout", branch_name],
            cwd=repo_root,
            check=True,
        )
    else:
        # Remote 無此 branch，建立新的本地 branch
        subprocess.run(
            ["git", "checkout", "-b", branch_name],
            cwd=repo_root,
            check=True,
        )


def validate_html_response(result: str) -> bool:
    """驗證 Claude 回傳內容是否為有效 HTML。

    Claude 可能回傳 Markdown 包覆的 HTML（```html...```）或錯誤訊息，
    直接寫入 index.html 會導致 GitHub Pages 顯示原始文字而非網頁。
    """
    stripped = result.strip()
    return (
        stripped.lower().startswith("<!doctype")
        or "<html" in stripped.lower()
    )


def main() -> None:
    """主流程：讀取 index.html → Claude 重構 → 建立 PR → 通知 Telegram。"""

    # 環境變數檢查：只有 ANTHROPIC_API_KEY 是必填；Telegram 為可選通知管道
    required_env = ["ANTHROPIC_API_KEY"]
    missing = [k for k in required_env if not os.environ.get(k)]
    if missing:
        print(f"錯誤：缺少必要環境變數：{missing}", file=sys.stderr)
        sys.exit(1)

    today = datetime.utcnow().strftime("%Y-%m-%d")
    branch_name = f"refactor/{today}"
    print(f"今日日期（UTC）：{today}，目標 branch：{branch_name}")

    # index.html 路徑從腳本位置推算，避免硬編碼
    repo_root = Path(__file__).parent.parent
    index_path = repo_root / "index.html"

    if not index_path.exists():
        print(f"錯誤：找不到 index.html（預期路徑：{index_path}）", file=sys.stderr)
        sys.exit(1)

    html_content = index_path.read_text(encoding="utf-8")
    print(f"已讀取 index.html（{len(html_content)} 字元）")

    # 呼叫 Claude Sonnet 依照 Architectural Directive 進行重構
    try:
        client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        message = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=8192,
            messages=[
                {
                    "role": "user",
                    "content": f"{ARCHITECTURAL_DIRECTIVE}\n\n---\n\n{html_content}",
                }
            ],
        )
        result = message.content[0].text
        print(f"Claude 回應長度：{len(result)} 字元")
    except anthropic.APIError as e:
        error_msg = f"[helloWeb] 重構失敗（{today}）：Claude API 錯誤 — {e}"
        print(f"錯誤：{error_msg}", file=sys.stderr)
        send_telegram(error_msg)
        sys.exit(1)

    # 若 Claude 判斷無需重構，只發 Telegram 通知後正常退出
    if result.strip() == "NO_REFACTOR_NEEDED":
        notice = f"[helloWeb] 重構檢查完成（{today}）：index.html 無需重構，架構已夠乾淨。"
        print(notice)
        send_telegram(notice)
        return

    # HTML sanity check：防止 Markdown 包覆或錯誤訊息覆蓋 index.html 導致 Pages 損壞
    if not validate_html_response(result):
        error_msg = (
            f"[helloWeb] 重構失敗（{today}）：Claude 回傳非 HTML 內容\n"
            f"前 100 字元：{result.strip()[:100]}"
        )
        print(error_msg, file=sys.stderr)
        send_telegram(error_msg)
        sys.exit(1)

    # 有重構內容：建立 branch、commit、push、建立 PR
    try:
        checkout_or_create_branch(branch_name, str(repo_root))
        index_path.write_text(result, encoding="utf-8")
        subprocess.run(
            ["git", "add", "index.html"],
            cwd=str(repo_root),
            check=True,
        )
        subprocess.run(
            ["git", "commit", "-m", f"refactor: 自動重構 index.html [{today}]"],
            cwd=str(repo_root),
            check=True,
        )
        subprocess.run(
            ["git", "push", "origin", branch_name],
            cwd=str(repo_root),
            check=True,
        )
    except subprocess.CalledProcessError as e:
        error_msg = f"[helloWeb] 重構失敗（{today}）：git 操作失敗 — {e}"
        print(f"錯誤：{error_msg}", file=sys.stderr)
        send_telegram(error_msg)
        sys.exit(1)

    pr_url = create_github_pr(branch_name, today)

    if pr_url:
        notice = (
            f"[helloWeb] 重構 PR 已建立！\n"
            f"日期：{today}\n"
            f"Branch：{branch_name}\n"
            f"PR：{pr_url}"
        )
    else:
        notice = (
            f"[helloWeb] 重構完成但建立 PR 失敗（{today}）\n"
            f"Branch：{branch_name} 已推送，請手動建立 PR。"
        )

    print(notice)
    send_telegram(notice)


if __name__ == "__main__":
    main()
