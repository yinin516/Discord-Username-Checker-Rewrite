# Discord Username Checker v8

An async Discord username availability checker. Fork of [Cloudzik1337's CloudChecker](https://github.com/Cloudzik1337/DiscordUsernameChecker).

Discord 用戶名可用性檢查工具（異步版）。基於 [Cloudzik1337 的 CloudChecker](https://github.com/Cloudzik1337/DiscordUsernameChecker) 重寫。

---

## Features / 功能

| English | 中文 |
|---------|------|
| Async Architecture - 3-5x faster | 異步架構 - 速度提升 3-5 倍 |
| HTTP, SOCKS4, SOCKS5 proxy support | 支持 HTTP、SOCKS4、SOCKS5 代理 |
| Smart retry with different proxies | 智能重試，自動換代理 |
| Auto-adjust concurrency | 自動調整併發數 |
| Progress memory - resume on restart | 記憶進度，重啟可繼續 |
| Random order checking | 隨機順序檢查 |
| Bilingual UI (English/中文) | 雙語界面 |

---

## Requirements / 需求

- Python 3.10+
- Proxies (residential recommended) / 代理（建議住宅代理）

---

## Installation / 安裝

```bash
git clone https://github.com/yinin516/DiscordUsernameChecker.git
cd DiscordUsernameChecker
```

**First time / 第一次使用**: Double-click `run.bat` to install dependencies / 雙擊 `run.bat` 安裝依賴

---

## Usage / 使用方法

### 1. First Run / 首次運行

**Windows**: Double-click `run.bat` / 雙擊 `run.bat`

This will: / 這會：
- Install dependencies / 安裝依賴
- Create `data/`, `logs/`, `results/` folders / 創建資料夾
- Start the checker / 啟動檢查器

After first run, you can also use: / 之後也可以用：
```bash
python cloud_checker_v8.py
```

### 2. Add Proxies / 添加代理

Edit `data/proxies.txt`: / 編輯 `data/proxies.txt`：

```
# HTTP
192.168.1.1:8080
user:pass@192.168.1.2:8080

# SOCKS5
socks5://192.168.1.3:1080
socks5://user:pass@192.168.1.4:1080

# SOCKS4
socks4://192.168.1.5:1080
```

### 3. Run / 運行

```bash
python cloud_checker_v8.py
```

**Menu Options / 選單：**

| # | English | 中文 |
|---|---------|------|
| 1 | Use existing list (skip checked) | 使用現有列表（跳過已檢查）|
| 2 | Generate new (clear history) | 生成新組合（清除記錄）|
| 3 | Clear history | 清除檢查記錄 |
| 4 | Generate new (keep history) | 生成新組合（保留記錄）|

### 4. Word Finder (Optional) / 單詞搜尋（可選）

Find leet variants from your hits: / 從結果中搜尋相似變體：

```bash
python word_finder_v2.py
```

Example / 例如: `attack` → `4tt4ck`, `att4ck`, `a77ack`

---

## Output / 輸出

| File | Description |
|------|-------------|
| `results/hits.txt` | Available usernames / 可用用戶名 |
| `data/checked.txt` | Checked history (for resume) / 檢查記錄（用於續傳）|

---

## Proxy Guide / 代理指南

| Type / 類型 | Works? | Notes / 備註 |
|-------------|--------|--------------|
| Datacenter / 數據中心 | ❌ | Blocked / 被封鎖 |
| Public/Free / 公共免費 | ❌ | Abused / 已被濫用 |
| Residential / 住宅 | ✅ | Recommended / 推薦 |
| Mobile/4G / 移動網路 | ✅ | Best / 最佳 |

---

## Credits / 致謝

- Original / 原版: [Cloudzik1337](https://github.com/Cloudzik1337/DiscordUsernameChecker)
- v8 Rewrite / v8 重寫: [yinin516](https://github.com/yinin516) with [Claude](https://claude.ai)

---

## License / 授權

MIT License
