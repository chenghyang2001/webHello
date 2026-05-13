# helloWeb — CLAUDE.md

給 Claude Code 的專案導覽。每個 session 開始時必讀。

---

## 專案概述

**helloWeb** 是「留言自動觸發 AI PR Pipeline」的示範專案。
使用者在網頁輸入留言 → 前端自動建立 GitHub PR → GitHub Actions 啟動三段 AI Agent（classify → resolver → qa）→ 自動合併。

- **線上網址**：https://chenghyang2001.github.io/helloWeb/
- **Repo**：chenghyang2001/helloWeb
- **部署方式**：GitHub Pages（master branch 根目錄）

---

## 技術棧

| 層級 | 技術 |
|------|------|
| 前端 | HTML5 + Vanilla JavaScript（單一 index.html，無框架） |
| AI Pipeline | Anthropic Claude API（Haiku classify / Sonnet resolver+qa） |
| CI/CD | GitHub Actions（pr-agent-pipeline.yml） |
| 部署 | GitHub Pages（push master 即生效） |

---

## 專案結構

```
helloWeb/
├── index.html                    # 主頁面（單一檔案，含所有前端邏輯）
├── spec.md                       # 功能規格文件（v.003）
├── CLAUDE.md                     # 本檔案
├── pipeline.config.json          # Pipeline 設定
├── scripts/
│   ├── classify_pr.py            # Claude Haiku：分類 PR 意圖
│   ├── resolver_agent.py         # Claude Sonnet：處理 PR（可修改檔案）
│   └── qa_agent.py               # Claude Sonnet：QA 驗證
├── comments/                     # PR 合併後的留言 Markdown 檔
├── doc/                          # Session 摘要與文件
└── .github/workflows/
    └── pr-agent-pipeline.yml     # 主 Pipeline（classify→resolver→qa→merge）
```

---

## Git 工作流規則（專案特定，覆蓋全域預設）

### 核心原則：永遠不直接在 master 上修改功能性程式碼

| 改動類型 | 必用方式 |
|---------|---------|
| `index.html`（任何功能或樣式改動） | **feature branch → PR → merge** |
| `scripts/*.py`（AI agent 腳本） | **feature branch → PR → merge** |
| `.github/workflows/*.yml`（CI/CD） | **feature branch → PR → merge** |
| `pipeline.config.json` | **feature branch → PR → merge** |
| `README.md` / `spec.md` / `CLAUDE.md`（純文件） | 可直接 commit 到 master |
| `comments/`（自動產生的留言檔） | 由 pipeline 自動處理，不手動改 |
| `doc/`（session 摘要） | 可直接 commit 到 master |

### Branch 命名規範

```
feature/<簡短英文描述>
例：feature/add-dark-mode
    feature/update-resolver-prompt
    feature/fix-pr-polling
```

### 為什麼這個專案要比全域規則更嚴格？

這個專案本身就是 **AI PR Pipeline 的示範**。如果 Claude 直接改 master，
就違背了「Branch → PR → AI 審查 → Merge」的示範精神。
功能性改動應該走 PR，讓 resolver/qa agent 也能審查 Claude 自己的改動。

---

## Pipeline 防護機制（重要！不可破壞）

| 機制 | 說明 |
|------|------|
| Bot-loop 防護 | 最後 committer 是 `github-actions[bot]` → 跳過整條 pipeline |
| Race condition 防護 | `concurrency: cancel-in-progress: true` 同一 PR 只跑一個 |
| Fork 安全 | 只處理同 repo PR，fork PR 拿不到 secrets |
| 自動合併範圍 | merge job 只對 `comment-*` branch 執行 |

修改 `pr-agent-pipeline.yml` 時必須確保以上四個機制完整保留。

---

## 環境需求

- **Anthropic API Key**：存在 GitHub Secret `ANTHROPIC_API_KEY`（需有 Credits）
- **GitHub PAT**：使用者瀏覽器的 `localStorage.gh_token`（Classic，需 `repo` + `workflow` 權限）
- **GitHub Pages**：已啟用，source = master branch 根目錄

---

## 本地開發

```bash
# 不需安裝任何套件，直接開啟
open index.html
# 或用 VS Code Live Server
```

---

## CI/CD 操作原則（第4章精華，Claude 必須遵守）

這些原則來自書中第4章，是 Claude 協助使用者做 CI/CD 相關工作時的行為準則。

### 絕對禁止

- ❌ 建議手動用 FTP 或 scp 傳檔上伺服器
- ❌ 把任何 Token / API Key / 密碼寫進 YAML 或程式碼本體
- ❌ 一次累積大量功能才部署（高風險、高壓力）

### 必須做到

- ✅ **所有部署走 GitHub Actions 自動化**，Merge 觸發，人工零介入
- ✅ **所有機密存 GitHub Secrets**，YAML 裡用 `${{ secrets.XXX }}` 引用
- ✅ **YAML 由 Claude 生成**，使用者只需審閱並點 Merge
- ✅ **小批次頻繁部署**：收到回饋 → Claude 修 → Merge → 60 秒上線，每天可部署多次
- ✅ **部署流程設計要包含 rollback 能力**（git revert 或 workflow 回退版本）

### helloWeb 的 60 秒部署流程

```
T=0s   使用者在網頁送出留言（觸發 PR 建立）
T=~10s Actions 機器人醒來，啟動 classify job
T=~35s resolver 修改檔案並 push 到 PR branch
T=~60s qa 驗證通過，merge job 自動合併
T=~90s GitHub Pages 重新 build，全球可見
```

### 新增或修改 Workflow 時的 checklist

```
- [ ] 觸發條件是否正確（on: pull_request / push）
- [ ] 所有機密用 secrets.XXX，不寫死
- [ ] 四個防護機制完整保留（bot-loop / concurrency / fork / merge scope）
- [ ] 有 needs: 確保 job 依序執行
- [ ] merge job 只對 comment-* branch 執行
```

---

## 已知踩坑

- `resolver_agent.py` 分類為 `DEBUGGER` mode 時會修改 index.html，這是正常行為
- API Credits 不足會讓 classify job 直接 fail（exit 1），PR 不會自動合併
- GitHub Pages build 約需 30-60 秒，push 後要等一下才能看到更新
