# helloWeb — 規格文件（v.003，2026-05-08）

## 專案概述

單頁 Web App，示範「前端留言 → 自動建立 GitHub PR → AI Agent Pipeline 處理 → 自動合併」的完整流程。
技術棧：Vanilla HTML5 + JavaScript（無框架）+ GitHub Actions + Claude API。

---

## 功能規格

### 功能 0：專案標題列
- 卡片頂部顯示 `專案-helloWeb` 標籤（紫藍漸層 `#667eea → #764ba2`，白字，圓角膠囊）
- 標籤右側並排顯示版本號與發佈時間戳記，格式：`v.003 | YYYY-MM-DD HH:MM:SS`

### 功能 1：問候訊息
- `<h1>` 共四行：前兩行顯示 `hello 楊政憲`，第三行顯示 `hello 楊政憲 楊政憲 楊政憲`（名字重複三次），第四行顯示 `hello 楊政憲 楊政憲 楊政憲 楊政憲`（名字重複四次）
- 「hello」為粉紅色 `#ed64a6`，「楊政憲」為紫藍色 `#667eea`

### 功能 2：即時時鐘
- DOM id：`clock`，格式 `HH:MM:SS`，每秒更新

### 功能 3：頁面副標題
- `<p id="subtitle">` 顯示「我的個人頁面」

### 功能 4：GitHub Token 管理
- Token 以 `localStorage` key `gh_token` 儲存於瀏覽器本機
- 頁面底部「設定 / 更換 GitHub Token」按鈕，點擊開啟 Modal
- Modal 內含 password 輸入欄（`id="token-input"`）、取消 / 儲存按鈕
- 需要 Token 才能送出留言，若尚未設定則自動彈出 Modal 要求輸入
- 若 API 回傳 401 / Bad credentials，自動清除舊 Token 並提示重新設定

### 功能 5：留言送出 → 自動建立 GitHub PR
送出流程（全透過 GitHub REST API，使用者的 Token 授權）：

1. 取得 `master` 最新 commit SHA（`GET /repos/{repo}/git/refs/heads/master`）
2. 建立新 branch：`comment-{ISO8601時間戳}`
3. 在新 branch 上建立檔案：`comments/{timestamp}.md`，內容含留言文字與提交時間
4. 建立 PR：title 取留言前 72 字元，body 含完整留言與來源標注

輸入規格：
- `<input type="text" id="comment-input" maxlength="200">`
- `<button id="submit-btn">` 送出
- 支援 Enter 鍵送出
- 防 XSS：一律用 `textContent` 不用 `innerHTML`
- 送出期間 input + button 皆 disabled

Base64 編碼：用 `btoa(unescape(encodeURIComponent(str)))` 支援中文

### 功能 6：PR 狀態即時追蹤
- PR 建立後立即在留言列表插入條目，含 PR 連結與 CI 狀態徽章
- 狀態徽章（`class="pr-status"`）：⏳ 處理中（`pending`）/ ✅ 完成（`success`）/ ❌ 失敗（`failure`）/ ⏱️ 逾時
- 輪詢機制：每 10 秒查詢 `GET /repos/{repo}/commits/{headSha}/check-runs`
- 最多輪詢 36 次（6 分鐘），逾時顯示 `⏱️ 逾時`
- 網路錯誤靜默重試（catch 後繼續 setTimeout）

### 功能 7：留言紀錄列表
- `<ul id="comments">` 顯示本 session 內送出的所有留言
- 每筆含：留言文字、PR 連結（另開新分頁）、CI 狀態徽章
- 新留言用 `prepend` 插入最前面

---

## GitHub Actions Pipeline（`pr-agent-pipeline.yml`）

觸發條件：PR `opened` 或 `synchronize`（限同 repo，不處理 fork）

流程：`classify (Haiku)` → `resolver_qa retry loop (Sonnet x3)` → `merge`

---

## Issue-Driven Development Pipeline（`issue-driven-pipeline.yml`）

### 概述

IDD（Issue-Driven Development）流程：

```
建立 Issue → 自動建立 feature/issue-N branch + PR
          → pr-agent-pipeline 接手（classify → resolver → qa → merge）
          → Issue 自動關閉（PR body 含 Resolves #N）
```

觸發條件：Issue `opened`

### ROLLBACK 流程（緊急三分鐘回退協議）

使用 `.github/ISSUE_TEMPLATE/rollback.yml` 建立結構化 Issue，觸發全自動 `git revert`：

```
建立 Issue（[ROLLBACK] 回退到 commit <hash>）
  → IDD Pipeline 建立 feature/issue-N branch + PR
  → classify：偵測 [ROLLBACK] 前綴 → mode=ROLLBACK（跳過 Haiku API 呼叫）
  → resolver：git cat-file -t 驗證 hash → git revert <hash> --no-edit → push
              衝突時 git revert --abort + PR comment 通知人工介入
  → qa：結構性驗證（index.html 存在 + <html>/<body> 標籤），不呼叫 Sonnet / pytest
  → auto-merge
```

**ROLLBACK Issue Template**（`.github/ISSUE_TEMPLATE/rollback.yml`）欄位：
- `commit_hash`：目標穩定版本的 7–40 字元 hex commit hash
- `reason`：回退原因說明
- `confirm`：操作確認 checkbox（確認目標為已知穩定版本、了解 revert 不刪除歷史）

**commit hash 解析規則**（`resolver_agent.py extract_commit_hash()`）：
1. 標題 inline 格式：`[ROLLBACK] 回退到 commit d1a2b4f`
2. Issue template 結構化欄位：`### 目標 commit hash\n\nd1a2b4f`

### 防護機制
- **Bot-loop 防護**：跳過 `github-actions[bot]` 建立的 Issue（`if: github.event.issue.user.login != 'github-actions[bot]'`）
- **Concurrency 防護**：同一 Issue 重複觸發時取消前次（`group: issue-to-pr-{issue.number}`）

### Job 流程

| 步驟 | 說明 |
|------|------|
| Checkout | 取出 master |
| Configure git identity | 設定 `github-actions[bot]` 身份 |
| Create branch and open PR | 建立 `feature/issue-{N}` branch，開 PR（body 含 `Resolves #N`）|

### Bot-loop 防護
最後一個 commit 若由 `github-actions[bot]` 提交 → 整條 pipeline 跳過，避免無限迴圈。

### 同 PR 併發取消
```yaml
concurrency:
  group: pr-agent-${{ github.event.pull_request.number }}
  cancel-in-progress: true
```

### Job 流程

| Job | 模型 | 腳本 | 說明 |
|-----|------|------|------|
| `classify` | Claude Haiku | `scripts/classify_pr.py` | 判斷 PR 意圖，輸出 `mode`；標題含 `[ROLLBACK]` 時快速路徑直接輸出 `ROLLBACK`，不呼叫 API |
| `resolver_qa` | Claude Sonnet | `scripts/resolver_agent.py` + `scripts/qa_agent.py` | Resolver + QA retry loop（最多 3 次）；ROLLBACK 模式繞過 AI 生成直接執行 `git revert`，QA 僅做 HTML 結構驗證 |
| `merge` | — | `gh pr merge` | 對 `comment-*` 及 `feature/*` branch 自動合併並刪除 branch（需 `resolver_qa` 成功） |

環境變數：
- `ANTHROPIC_API_KEY`：GitHub Secret
- `GH_TOKEN`：`secrets.GITHUB_TOKEN`（自動注入）
- 模型 ID 定義在 workflow-level `env`，方便統一升級

---

## 部署方式

- **GitHub Pages**：master branch 根目錄 `index.html` 直接掛載，push 即生效
- **Repo**：`chenghyang2001/helloWeb`
- **URL**：`https://chenghyang2001.github.io/helloWeb/`（或同 repo 的 Pages URL）

---

## 技術規格

| 項目 | 規格 |
|------|------|
| 前端語言 | HTML5 + Vanilla JS（無框架） |
| 單一檔案 | `index.html` |
| 中文支援 | `lang="zh-TW"`，Base64 編碼用 `unescape(encodeURIComponent)` |
| 響應式 | `max-width: 480px` 卡片，手機與桌面均可使用 |
| Token 儲存 | `localStorage`（瀏覽器本機，不送伺服器）|
| API 目標 | `https://api.github.com` |
| CI 模型 | classify: Haiku（省成本）/ resolver, qa: Sonnet |

---

## 檔案結構

```
helloWeb/
├── index.html                          # 主頁面（單一檔案）
├── spec.md                             # 本規格文件
├── pipeline.config.json                # Pipeline 設定
├── requirements.txt                    # Python 依賴版本鎖定（供 Dependabot 掃描）
├── scripts/
│   ├── classify_pr.py                  # Haiku 分類 PR
│   ├── resolver_agent.py               # Sonnet 處理 PR
│   └── qa_agent.py                     # Sonnet QA 驗證
├── comments/                           # PR 自動合併後的留言檔案
├── .github/
│   ├── dependabot.yml                  # Dependabot 自動追蹤 pip / Actions 版本更新
│   └── workflows/
│       ├── pr-agent-pipeline.yml       # 主 Pipeline（classify→resolver→qa→merge）
│       ├── issue-driven-pipeline.yml   # IDD Pipeline（Issue → branch + PR → pipeline 接手）
│       └── auto-merge-comment-pr.yml   # 舊版（已停用，改由 pipeline merge job 負責）
└── doc/
    └── github-vibe-coding-books.md     # 書單參考
```
