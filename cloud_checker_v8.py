"""
Async Cloud Checker v7 - 簡單版
保持原版邏輯，異步提升效率
被限流的用戶名會換代理重試，直到得到明確結果

支持代理格式：
  HTTP:   host:port 或 user:pass@host:port
  SOCKS5: socks5://host:port 或 socks5://user:pass@host:port
"""

import asyncio
import aiohttp
from aiohttp_socks import ProxyConnector, ProxyType
from pathlib import Path
from time import time
import json
import sys
import os
import random
import itertools

VERSION = "8.0.0"

# ==================== 語言設定 ====================

LANG = "en"

TEXTS = {
    "en": {
        "select_lang": "Select language / 選擇語言:\n  1. English\n  2. 中文\n>>> ",
        "loaded_proxies": "Loaded {count} proxies",
        "current_list": "Current list has {count} usernames, {checked} already checked",
        "option_1": "1. Use existing list (auto-skip checked)",
        "option_2": "2. Generate new combinations (clear history)",
        "option_3": "3. Clear check history, start fresh",
        "option_4": "4. Generate new combinations (keep history)",
        "select": "Select",
        "length_prompt": "Username length 2-4 (single like 3, or range like 2-4)",
        "generating": "Generating...",
        "length_n": "Length {n}: +{count}",
        "shuffling": "Shuffling randomly...",
        "generated": "Generated {count} combinations (randomly sorted)",
        "generated_keep": "Generated {count} combinations (keep history, randomly sorted)",
        "cleared_history": "Cleared check history",
        "skipped": "Skipped {count} already checked usernames",
        "all_done": "All checked!",
        "to_check": "To check: {count} usernames",
        "initial_concurrent": "Initial concurrency (recommended 50-200)",
        "auto_adjust": "Enable auto-adjust concurrency? (y/n, default n)",
        "min_concurrent": "Min concurrency (default 20)",
        "max_concurrent": "Max concurrency (default 500)",
        "auto_enabled": "Auto-adjust enabled: {min} ~ {max}",
        "starting_in": "Starting in {n}s... (Ctrl+C to cancel)",
        "interrupted": "User interrupted",
        "adjust_concurrent": "Auto-adjust: {old} → {new} (RL rate: {ratio})",
        "done": "Done",
        "total_requests": "Total requests",
        "available": "Available",
        "taken": "Taken",
        "ratelimited": "Rate limited",
        "elapsed": "Elapsed",
        "avg_rps": "Avg RPS",
        "no_proxy_error": "Error: No proxies in data/proxies.txt!",
        "add_proxy_hint": "Add proxies, one per line (host:port or user:pass@host:port)",
    },
    "zh": {
        "select_lang": "Select language / 選擇語言:\n  1. English\n  2. 中文\n>>> ",
        "loaded_proxies": "已載入 {count} 個代理",
        "current_list": "當前列表有 {count} 個用戶名，已檢查過 {checked} 個",
        "option_1": "1. 使用現有列表（自動跳過已檢查的）",
        "option_2": "2. 生成新的組合（清除記錄）",
        "option_3": "3. 清除檢查記錄，從頭開始",
        "option_4": "4. 生成新的組合（保留檢查記錄）",
        "select": "選擇",
        "length_prompt": "用戶名長度 2-4（單個如 3，或範圍如 2-4）",
        "generating": "生成中...",
        "length_n": "長度 {n}: +{count}",
        "shuffling": "隨機打亂順序...",
        "generated": "已生成 {count} 個組合（已隨機排序）",
        "generated_keep": "已生成 {count} 個組合（保留記錄，已隨機排序）",
        "cleared_history": "已清除檢查記錄",
        "skipped": "跳過 {count} 個已檢查的用戶名",
        "all_done": "全部都檢查完了！",
        "to_check": "待檢查：{count} 個用戶名",
        "initial_concurrent": "初始併發數（建議 50-200）",
        "auto_adjust": "是否啟用自動調整併發？(y/n，默認 n)",
        "min_concurrent": "最低併發數（默認 20）",
        "max_concurrent": "最高併發數（默認 500）",
        "auto_enabled": "自動調整已啟用: {min} ~ {max}",
        "starting_in": "{n} 秒後開始... (Ctrl+C 取消)",
        "interrupted": "用戶中斷",
        "adjust_concurrent": "自動調整併發: {old} → {new} (限流率: {ratio})",
        "done": "完成",
        "total_requests": "總請求數",
        "available": "可用用戶名",
        "taken": "已佔用",
        "ratelimited": "限流次數",
        "elapsed": "總耗時",
        "avg_rps": "平均 RPS",
        "no_proxy_error": "錯誤：data/proxies.txt 沒有代理！",
        "add_proxy_hint": "請添加代理，每行一個 (host:port 或 user:pass@host:port)",
    }
}

def t(key: str, **kwargs) -> str:
    text = TEXTS.get(LANG, TEXTS["en"]).get(key, key)
    return text.format(**kwargs) if kwargs else text

# ==================== 全局變量 ====================

RPS = 0
REQUESTS = 0
AVAILABLE = 0
TAKEN = 0
RATELIMITED = 0
CONCURRENT = 100
AUTO_ADJUST = False

# ==================== 顏色 ====================

class Colors:
    RESET = "\033[0m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    CYAN = "\033[36m"
    GREY = "\033[90m"

# ==================== 配置 ====================

def load_config():
    Path("data").mkdir(exist_ok=True)
    config_path = Path("data/config.json")
    if not config_path.exists():
        config_path.write_text("{}")
    try:
        with open(config_path, "r") as f:
            return json.load(f)
    except:
        return {}

# ==================== 代理 ====================

def load_proxies():
    Path("data").mkdir(exist_ok=True)
    proxy_path = Path("data/proxies.txt")
    if not proxy_path.exists():
        proxy_path.write_text("")
    with open(proxy_path, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]

# ==================== 核心檢查 ====================

async def check_username(session: aiohttp.ClientSession, name: str, proxy: str, timeout: int) -> tuple[str, dict | None]:
    global REQUESTS
    
    if proxy.startswith("socks5://") or proxy.startswith("socks4://"):
        proxy_url = proxy
    elif "://" not in proxy:
        proxy_url = f"http://{proxy}"
    else:
        proxy_url = proxy
    
    try:
        if proxy_url.startswith("socks"):
            connector = ProxyConnector.from_url(proxy_url)
            async with aiohttp.ClientSession(connector=connector, headers={"Content-Type": "application/json"}) as socks_session:
                async with socks_session.post(
                    "https://discord.com/api/v9/unique-username/username-attempt-unauthed",
                    json={"username": name},
                    timeout=aiohttp.ClientTimeout(total=timeout)
                ) as resp:
                    REQUESTS += 1
                    if resp.status == 200:
                        data = await resp.json()
                        return ("taken", data) if data.get("taken") else ("available", data)
                    elif resp.status == 429:
                        return ("ratelimited", await resp.json())
                    return ("error", None)
        else:
            async with session.post(
                "https://discord.com/api/v9/unique-username/username-attempt-unauthed",
                json={"username": name},
                proxy=proxy_url,
                timeout=aiohttp.ClientTimeout(total=timeout)
            ) as resp:
                REQUESTS += 1
                if resp.status == 200:
                    data = await resp.json()
                    return ("taken", data) if data.get("taken") else ("available", data)
                elif resp.status == 429:
                    return ("ratelimited", await resp.json())
                return ("error", None)
    except:
        return ("error", None)

async def worker(queue, session, proxies, proxy_index, timeout, lock, longest_name, worker_id, active_workers):
    global AVAILABLE, TAKEN, RPS, RATELIMITED, CONCURRENT
    
    while True:
        if AUTO_ADJUST and worker_id >= CONCURRENT:
            active_workers[worker_id] = False
            await asyncio.sleep(1)
            continue
        
        active_workers[worker_id] = True
        
        try:
            name = await asyncio.wait_for(queue.get(), timeout=1.0)
        except asyncio.TimeoutError:
            if queue.empty():
                break
            continue
        
        tried_proxies = set()
        result = None
        
        while len(tried_proxies) < len(proxies):
            async with lock:
                proxy_index["i"] = (proxy_index["i"] + 1) % len(proxies)
                proxy = proxies[proxy_index["i"]]
            
            if proxy in tried_proxies:
                continue
            tried_proxies.add(proxy)
            
            status, data = await check_username(session, name, proxy, timeout)
            proxy_display = proxy[:15] + "..." if len(proxy) > 18 else proxy
            
            if status == "available":
                AVAILABLE += 1
                active = sum(active_workers.values()) if AUTO_ADJUST else CONCURRENT
                print(f"[{Colors.GREEN}+{Colors.RESET}] Available: {Colors.CYAN}{name:<{longest_name}}{Colors.RESET} | RPS: {Colors.CYAN}{RPS:>4}{Colors.RESET} | RL: {Colors.YELLOW}{RATELIMITED}{Colors.RESET} | W: {Colors.CYAN}{active}{Colors.RESET} | Proxy: {Colors.GREY}{proxy_display}{Colors.RESET}")
                async with lock:
                    with open("results/hits.txt", "a", encoding="utf-8") as f:
                        f.write(name + "\n")
                    with open("data/checked.txt", "a", encoding="utf-8") as f:
                        f.write(name + "\n")
                result = "done"
                break
            
            elif status == "taken":
                TAKEN += 1
                active = sum(active_workers.values()) if AUTO_ADJUST else CONCURRENT
                print(f"[{Colors.RED}-{Colors.RESET}]    Taken: {Colors.CYAN}{name:<{longest_name}}{Colors.RESET} | RPS: {Colors.CYAN}{RPS:>4}{Colors.RESET} | RL: {Colors.YELLOW}{RATELIMITED}{Colors.RESET} | W: {Colors.CYAN}{active}{Colors.RESET} | Proxy: {Colors.GREY}{proxy_display}{Colors.RESET}")
                async with lock:
                    with open("data/checked.txt", "a", encoding="utf-8") as f:
                        f.write(name + "\n")
                result = "done"
                break
            
            elif status == "ratelimited":
                RATELIMITED += 1
        
        if result != "done":
            await queue.put(name)
            await asyncio.sleep(5)
        
        queue.task_done()

async def rps_calculator():
    global RPS, REQUESTS
    while True:
        before = REQUESTS
        await asyncio.sleep(1)
        RPS = REQUESTS - before

async def auto_adjust_concurrency(semaphore, min_concurrent, max_concurrent):
    global CONCURRENT, RATELIMITED, REQUESTS, AUTO_ADJUST
    
    last_rl, last_req, stable = 0, 0, 0
    
    while AUTO_ADJUST:
        await asyncio.sleep(5)
        new_rl = RATELIMITED - last_rl
        new_req = REQUESTS - last_req
        if new_req == 0:
            continue
        
        ratio = new_rl / new_req
        last_rl, last_req = RATELIMITED, REQUESTS
        old = CONCURRENT
        
        if ratio > 0.7:
            CONCURRENT = max(min_concurrent, int(CONCURRENT * 0.6))
        elif ratio > 0.5:
            CONCURRENT = max(min_concurrent, int(CONCURRENT * 0.8))
        elif ratio > 0.3:
            CONCURRENT = max(min_concurrent, int(CONCURRENT * 0.9))
        elif ratio < 0.1:
            stable += 1
            if stable >= 3:
                CONCURRENT = min(max_concurrent, int(CONCURRENT * 1.2))
                stable = 0
        else:
            stable = 0
        
        if CONCURRENT != old:
            print(f"\n[{Colors.CYAN}⚙{Colors.RESET}] {t('adjust_concurrent', old=old, new=CONCURRENT, ratio=f'{ratio:.1%}')}\n")

# ==================== 主程序 ====================

def print_banner():
    print(f"""
{Colors.GREY}
   _____ _                 _    _____ _               _             
  / ____| |               | |  / ____| |             | |            
 | |    | | ___  _   _  __| | | |    | |__   ___  ___| | _____ _ __ 
 | |    | |/ _ \\| | | |/ _` | | |    | '_ \\ / _ \\/ __| |/ / _ \\ '__|
 | |____| | (_) | |_| | (_| | | |____| | | |  __/ (__|   <  __/ |   
  \\_____|_|\\___/ \\__,_|\\__,_|  \\_____|_| |_|\\___|\\___|_|\\_\\___|_|   
{Colors.RESET}
                    {Colors.RED}@{Colors.RESET}  Async Version {VERSION}
""")

async def main():
    global REQUESTS, AVAILABLE, TAKEN, RPS, LANG, AUTO_ADJUST, CONCURRENT
    
    lang_choice = input(TEXTS["en"]["select_lang"]).strip()
    LANG = "zh" if lang_choice == "2" else "en"
    
    for d in ["data", "results", "logs"]:
        Path(d).mkdir(exist_ok=True)
    Path("results/hits.txt").touch()
    
    print_banner()
    
    config = load_config()
    timeout = config.get("timeout", 30)
    
    proxies = load_proxies()
    if not proxies:
        print(f"{Colors.RED}{t('no_proxy_error')}{Colors.RESET}")
        print(t('add_proxy_hint'))
        print()
        input(f"{Colors.YELLOW}>>>{Colors.RESET} " + ("Press Enter after adding proxies..." if LANG == "en" else "添加代理後按 Enter 繼續..."))
        proxies = load_proxies()
        if not proxies:
            print(f"{Colors.RED}" + ("Still no proxies found. Exiting." if LANG == "en" else "仍然沒有代理。退出。") + f"{Colors.RESET}")
            sys.exit(1)
    
    print(f"[{Colors.GREEN}+{Colors.RESET}] {t('loaded_proxies', count=len(proxies))}")
    
    names_path = Path("data/names_to_check.txt")
    checked_path = Path("data/checked.txt")
    names_path.touch()
    checked_path.touch()
    
    with open(names_path, "r", encoding="utf-8") as f:
        names = [line.strip() for line in f if line.strip()]
    with open(checked_path, "r", encoding="utf-8") as f:
        checked = set(line.strip() for line in f if line.strip())
    
    print(f"[{Colors.CYAN}?{Colors.RESET}] {t('current_list', count=len(names), checked=len(checked))}")
    print(f"    {t('option_1')}")
    print(f"    {t('option_2')}")
    print(f"    {t('option_3')}")
    print(f"    {t('option_4')}")
    choice = input(f"{t('select')} {Colors.YELLOW}>>>{Colors.RESET} ").strip()
    
    if choice == "3":
        checked_path.write_text("")
        checked = set()
        print(f"[{Colors.GREEN}+{Colors.RESET}] {t('cleared_history')}")
    
    if choice == "2":
        checked_path.write_text("")
        checked = set()
        length_input = input(f"{t('length_prompt')} {Colors.YELLOW}>>>{Colors.RESET} ").strip()
        chars = "abcdefghijklmnopqrstuvwxyz0123456789_."
        if "-" in length_input:
            s, e = map(int, length_input.split("-"))
            # 限制範圍 2-4
            s = max(2, min(s, 4))
            e = max(2, min(e, 4))
            lengths = range(s, e + 1)
        else:
            length = max(2, min(int(length_input), 4))
            lengths = [length]
        
        if int(length_input.split("-")[0] if "-" in length_input else length_input) > 4 or int(length_input.split("-")[-1] if "-" in length_input else length_input) > 4:
            print(f"[{Colors.YELLOW}!{Colors.RESET}] " + ("Max length is 4, adjusted." if LANG == "en" else "最大長度為 4，已調整。"))
        
        print(f"[{Colors.YELLOW}!{Colors.RESET}] {t('generating')}")
        names = []
        for length in lengths:
            before = len(names)
            names.extend("".join(c) for c in itertools.product(chars, repeat=length))
            print(f"    {t('length_n', n=length, count=len(names) - before)}")
        
        print(f"[{Colors.YELLOW}!{Colors.RESET}] {t('shuffling')}")
        random.shuffle(names)
        with open(names_path, "w", encoding="utf-8") as f:
            f.write("\n".join(names))
        print(f"[{Colors.GREEN}+{Colors.RESET}] {t('generated', count=len(names))}")
    
    elif choice == "4" or not names:
        length_input = input(f"{t('length_prompt')} {Colors.YELLOW}>>>{Colors.RESET} ").strip()
        chars = "abcdefghijklmnopqrstuvwxyz0123456789_."
        if "-" in length_input:
            s, e = map(int, length_input.split("-"))
            # 限制範圍 2-4
            s = max(2, min(s, 4))
            e = max(2, min(e, 4))
            lengths = range(s, e + 1)
        else:
            length = max(2, min(int(length_input), 4))
            lengths = [length]
        
        if int(length_input.split("-")[0] if "-" in length_input else length_input) > 4 or int(length_input.split("-")[-1] if "-" in length_input else length_input) > 4:
            print(f"[{Colors.YELLOW}!{Colors.RESET}] " + ("Max length is 4, adjusted." if LANG == "en" else "最大長度為 4，已調整。"))
        
        print(f"[{Colors.YELLOW}!{Colors.RESET}] {t('generating')}")
        names = []
        for length in lengths:
            before = len(names)
            names.extend("".join(c) for c in itertools.product(chars, repeat=length))
            print(f"    {t('length_n', n=length, count=len(names) - before)}")
        
        print(f"[{Colors.YELLOW}!{Colors.RESET}] {t('shuffling')}")
        random.shuffle(names)
        with open(names_path, "w", encoding="utf-8") as f:
            f.write("\n".join(names))
        print(f"[{Colors.GREEN}+{Colors.RESET}] {t('generated_keep', count=len(names))}")
    
    original = len(names)
    names = [n for n in names if n not in checked]
    if original - len(names) > 0:
        print(f"[{Colors.YELLOW}!{Colors.RESET}] {t('skipped', count=original - len(names))}")
    
    if not names:
        print(f"{Colors.GREEN}{t('all_done')}{Colors.RESET}")
        sys.exit(0)
    
    print(f"[{Colors.GREEN}+{Colors.RESET}] {t('to_check', count=len(names))}")
    longest_name = max(len(n) for n in names)
    
    concurrent = int(input(f"{t('initial_concurrent')} {Colors.YELLOW}>>>{Colors.RESET} ") or "100")
    CONCURRENT = concurrent
    
    auto_input = input(f"{t('auto_adjust')} {Colors.YELLOW}>>>{Colors.RESET} ").strip().lower()
    AUTO_ADJUST = auto_input in ["y", "yes", "1"]
    
    min_c, max_c = 20, 500
    if AUTO_ADJUST:
        min_c = int(input(f"{t('min_concurrent')} {Colors.YELLOW}>>>{Colors.RESET} ") or "20")
        max_c = int(input(f"{t('max_concurrent')} {Colors.YELLOW}>>>{Colors.RESET} ") or "500")
        print(f"[{Colors.GREEN}+{Colors.RESET}] {t('auto_enabled', min=min_c, max=max_c)}")
    
    print(f"\n[{Colors.YELLOW}!{Colors.RESET}] {t('starting_in', n=3)}")
    await asyncio.sleep(3)
    
    queue = asyncio.Queue()
    for name in names:
        await queue.put(name)
    
    lock = asyncio.Lock()
    proxy_index = {"i": 0}
    start_time = time()
    
    connector = aiohttp.TCPConnector(limit=concurrent * 2, limit_per_host=50)
    async with aiohttp.ClientSession(connector=connector, headers={"Content-Type": "application/json"}) as session:
        rps_task = asyncio.create_task(rps_calculator())
        adjust_task = asyncio.create_task(auto_adjust_concurrency(None, min_c, max_c)) if AUTO_ADJUST else None
        
        max_workers = max_c if AUTO_ADJUST else concurrent
        active_workers = {i: True for i in range(max_workers)}
        
        workers = [asyncio.create_task(worker(queue, session, proxies, proxy_index, timeout, lock, longest_name, i, active_workers)) for i in range(max_workers)]
        
        try:
            await queue.join()
        except KeyboardInterrupt:
            print(f"\n{Colors.YELLOW}{t('interrupted')}{Colors.RESET}")
        
        rps_task.cancel()
        if adjust_task:
            adjust_task.cancel()
        for w in workers:
            w.cancel()
    
    elapsed = time() - start_time
    print(f"""
{Colors.GREEN}========== {t('done')} =========={Colors.RESET}
{t('total_requests')}: {Colors.CYAN}{REQUESTS}{Colors.RESET}
{t('available')}: {Colors.GREEN}{AVAILABLE}{Colors.RESET}
{t('taken')}: {Colors.RED}{TAKEN}{Colors.RESET}
{t('ratelimited')}: {Colors.YELLOW}{RATELIMITED}{Colors.RESET}
{t('elapsed')}: {Colors.CYAN}{elapsed:.1f}{Colors.RESET}s
{t('avg_rps')}: {Colors.CYAN}{REQUESTS/elapsed:.1f}{Colors.RESET}
""")

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
