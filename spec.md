# index.html — 規格文件

## 目標

建立一個簡單的單頁 Web 應用程式，提供問候、即時時鐘與留言功能。

## 需求

### 功能 1：問候訊息
- 頁面顯示文字：`hello 楊政憲`
- 置於頁面頂部的 `<h1>` 標籤內

### 功能 2：即時時鐘
- 顯示目前時間（HH:MM:SS 格式）
- 每秒自動更新
- 時鐘元素的 DOM id 為 `clock`

### 功能 3：頁面副標題
- 在 `<h1>` 下方加入 `<p>` 標籤，顯示副標題文字：`我的個人頁面`
- id 為 `subtitle`

### 功能 4：留言功能
- 提供文字輸入欄（`<input type="text">`）
- 「送出」按鈕（id 為 `submit-btn`）
- 按下送出後，留言加入頁面清單（`<ul id="comments">`）
- 支援鍵盤 Enter 鍵送出
- 防 XSS：使用 `textContent` 而非 `innerHTML`

## 技術規格

- 語言：HTML5 + Vanilla JavaScript（無框架依賴）
- 單一檔案：`index.html`
- 支援繁體中文介面
- 響應式設計（手機與桌面均可使用）
