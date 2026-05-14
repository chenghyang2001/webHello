# Session：IDD Template 系統建立（2026-05-14）

## 目標

建立可攜式 IDD（Issue-Driven Development）AI PR Pipeline 的完整工具鏈：

1. 公開 GitHub Template Repo
2. 兩個 Skills（新建 / 加入現有 repo）

## 完成項目

### chenghyang2001/idd-template

- 公開 GitHub Template Repo（`is_template: true`）
- URL：<https://github.com/chenghyang2001/idd-template>
- commit：`a89fd2f`（2026-05-14）
- 包含：3 workflows + 3 Python agents + pipeline.config.json + requirements.txt + README + .gitignore

### 核心 Pipeline

```
Issue 建立
  → issue-driven-pipeline.yml：建 feature/issue-N branch + PR
  → pr-agent-pipeline.yml：classify → resolver → qa → merge
  → auto-merge-comment-pr.yml：自動合併 comment-* branch
```

### QA 修復（3 輪 Writer→QA→Reviewer）

| 輪次 | MUST_FIX | 說明 |
|------|----------|------|
| R1 | M1~M4 + A1 | bot-loop 改用 email 偵測、ROLLBACK MAX_ATTEMPTS=1 等 |
| R2 | M1 PR body shell injection、M2 run_cmd_repr 假設 Python | printf+mktemp、python_aliases |
| R3 | trap cleanup（≤3 行豁免）| 通過 |

### Skills

| Skill | 觸發 | 功能 |
|-------|------|------|
| `new-repo-idd` | new-repo-idd / idd 新專案 | 從 template 建新 GitHub Repo |
| `add-idd-to-repo` | add-idd-to-repo / 幫這個 repo 加 idd | 為現有 repo 加入 IDD Pipeline |

## 關鍵設計決策

- `pipeline.config.json` 為唯一客製點（spec_file / implementation_target / test_target / language / run_command）
- bot-loop guard 用 committer email（`%ae`），不用 author name（可偽造）
- ROLLBACK MAX_ATTEMPTS=1：第二次 revert 同一 commit 會 conflict
- Language-aware security scan：html/js 查 XSS；python 查 RCE
- Issue body 用 printf + mktemp + --body-file 避免 shell injection
- run_cmd_repr 先判斷 python_aliases，非 Python 直接用原始命令

## 取消項目

- `idd-template-private`（VPS FastAPI webhook）：使用公開 template 建立私有 repo（`--private`）即可，GitHub Actions 2000 min/月足夠
