# Contributing to helloWeb

## 一般貢獻流程

1. 查看 [GitHub Issues](https://github.com/chenghyang2001/helloWeb/issues) 確認任務
2. 建立 feature branch：`git checkout -b feature/<簡短描述>`
3. 完成後建立 PR → AI Pipeline 自動審查
4. QA 通過後自動合併

## Branch 命名規範

| 類型 | 格式 | 範例 |
|------|------|------|
| 新功能 | `feature/<描述>` | `feature/add-dark-mode` |
| 修 bug | `fix/<描述>` | `fix/token-validation` |
| 每月重構 | `refactor/YYYY-MM` | `refactor/2026-05` |
| 文件更新 | `docs/<描述>` | `docs/update-readme` |

---

## 每月重構衝刺（維護節奏）

> 來源：Mastering Claude Code & GitHub — 第 6 章「Monthly Refactoring Routine」

### 時機

每月第一個週末建立一個重構 PR，標籤 `monthly-refactor`。

### 鐵律：這個 PR 絕對不能做的事

- ❌ 新增功能
- ❌ 改變 UI 外觀
- ❌ 更新依賴套件（另開 PR）

### 這個 PR 只做這些

- ✅ 提取重複邏輯到函式（index.html 的 JS / Python scripts）
- ✅ 改善命名（含糊的變數名 → 具體名稱）
- ✅ 清理過長函式（> 30 行的函式拆開）
- ✅ 加入「為什麼」的 inline comment（解釋非顯而易見的邏輯）
- ✅ 移除未使用的程式碼

### 操作步驟

```bash
# 1. 建立當月重構分支
git checkout -b refactor/2026-06

# 2. 掃描技術債
#    - 函式 > 30 行？
#    - 重複的邏輯出現 2 次以上？
#    - 命名含糊（data, tmp, result）？

# 3. 重構並提交
git commit -m "每月重構 2026-06：<具體說明做了什麼>"

# 4. 建立 PR，加上 monthly-refactor label
gh pr create --label monthly-refactor --title "每月重構 2026-06" --fill
```

---

## Issue 驅動開發（Issue-Driven Development）

每個功能改動都必須對應一個 Issue：

1. 先建 Issue 描述問題或需求
2. 在 commit 訊息結尾加 `Resolves #N`
3. PR 合併後 Issue 自動關閉

這讓 repo 保有完整的「為什麼改這段程式碼」的稽核軌跡。

---

## Issue Label 說明

| Label | 用途 |
|-------|------|
| `enhancement` | 新功能請求 |
| `bug` | 程式錯誤回報 |
| `monthly-refactor` | 每月重構衝刺 PR |
| `tech-debt` | 技術債記錄（還沒要處理但先記下來） |
| `documentation` | 文件更新 |

---

## 緊急 Rollback

線上出問題時：建立 Issue → 套用 **Rollback** 範本 → AI Pipeline 自動執行 `git revert`。
詳細步驟見 [README.md](README.md)「緊急 Rollback SOP」章節。
