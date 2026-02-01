"""
Word Finder - 從可用ID中找相似單詞
輸入你想要的單詞，從 hits.txt 找出相似的可用用戶名
"""

from pathlib import Path
import itertools

# ==================== 語言設定 ====================

LANG = "en"

TEXTS = {
    "en": {
        "select_lang": "Select language / 選擇語言:\n  1. English\n  2. 中文\n>>> ",
        "title": "Word Finder - Similar Username Search",
        "description": "Enter a word you want, find similar available IDs from hits.txt\nExample: enter 'attack' → find '4tt4ck', 'att4ck', etc.",
        "no_hits": "Error: results/hits.txt not found",
        "run_checker_first": "Please run cloud_checker first to find available usernames",
        "empty_hits": "Error: hits.txt is empty",
        "loaded": "Loaded {count} available usernames",
        "prompt": "Enter word (q to quit)",
        "found": "Found {count} similar available usernames:",
        "not_found": "No similar usernames found for '{query}'",
        "variants_hint": "Possible variants (but not available):",
        "exact": "exact match",
        "leet": "leet variant",
        "normalized": "normalized match",
        "bye": "Goodbye!",
        "press_enter": "Press Enter to exit...",
        "error": "Error",
    },
    "zh": {
        "select_lang": "Select language / 選擇語言:\n  1. English\n  2. 中文\n>>> ",
        "title": "Word Finder - 相似用戶名搜尋",
        "description": "輸入你想要的單詞，從已找到的可用ID中搜尋相似的\n例如：輸入 'attack' → 找出 '4tt4ck', 'att4ck' 等",
        "no_hits": "錯誤：找不到 results/hits.txt",
        "run_checker_first": "請先用 cloud_checker 找出可用的用戶名",
        "empty_hits": "錯誤：hits.txt 是空的",
        "loaded": "已載入 {count} 個可用用戶名",
        "prompt": "輸入想要的單詞 (q 退出)",
        "found": "找到 {count} 個相似的可用用戶名：",
        "not_found": "沒找到與 '{query}' 相似的可用用戶名",
        "variants_hint": "可能的變體（但都不可用）：",
        "exact": "完全匹配",
        "leet": "leet 變體",
        "normalized": "標準化匹配",
        "bye": "再見！",
        "press_enter": "按 Enter 退出...",
        "error": "錯誤",
    }
}

def t(key: str, **kwargs) -> str:
    text = TEXTS.get(LANG, TEXTS["en"]).get(key, key)
    return text.format(**kwargs) if kwargs else text

# ==================== 顏色 ====================

class Colors:
    RESET = "\033[0m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    CYAN = "\033[36m"
    BOLD = "\033[1m"

# ==================== Leet 轉換 ====================

# 正向：數字 → 字母
LEET_TO_LETTER = {
    '0': 'o',
    '1': 'i', 
    '3': 'e',
    '4': 'a',
    '5': 's',
    '7': 't',
    '8': 'b',
    '9': 'g'
}

# 反向：字母 → 可能的數字
LETTER_TO_LEET = {
    'o': ['o', '0'],
    'i': ['i', '1'],
    'e': ['e', '3'],
    'a': ['a', '4'],
    's': ['s', '5'],
    't': ['t', '7'],
    'b': ['b', '8'],
    'g': ['g', '9'],
}

def normalize(word: str) -> str:
    """把 leet 轉成正常字母"""
    result = word.lower()
    for num, letter in LEET_TO_LETTER.items():
        result = result.replace(num, letter)
    return result

def generate_leet_variants(word: str) -> set:
    """生成一個單詞的所有 leet 變體"""
    word = word.lower()
    
    # 每個字符的可能替換
    char_options = []
    for char in word:
        if char in LETTER_TO_LEET:
            char_options.append(LETTER_TO_LEET[char])
        else:
            char_options.append([char])
    
    # 生成所有組合
    variants = set()
    for combo in itertools.product(*char_options):
        variants.add(''.join(combo))
    
    return variants

def find_similar(target: str, available_names: set) -> list:
    """從可用名稱中找出與目標相似的"""
    target = target.lower().strip()
    results = []
    
    # 1. 完全匹配
    if target in available_names:
        results.append((target, t('exact')))
    
    # 2. 生成目標的所有 leet 變體，看哪些在可用列表中
    variants = generate_leet_variants(target)
    for variant in variants:
        if variant in available_names and variant != target:
            results.append((variant, t('leet')))
    
    # 3. 遍歷可用名稱，檢查標準化後是否匹配
    for name in available_names:
        if normalize(name) == target and name not in [r[0] for r in results]:
            results.append((name, t('normalized')))
    
    return results

# ==================== 主程序 ====================

def main():
    global LANG
    
    # 選擇語言
    lang_choice = input(TEXTS["en"]["select_lang"]).strip()
    LANG = "zh" if lang_choice == "2" else "en"
    
    print(f"""
{Colors.BOLD}========================================
      {t('title')}
========================================{Colors.RESET}

{t('description')}
""")
    
    # 載入可用名稱
    hits_file = Path("results/hits.txt")
    if not hits_file.exists():
        print(f"{Colors.RED}{t('no_hits')}{Colors.RESET}")
        print(t('run_checker_first'))
        input(t('press_enter'))
        return
    
    with open(hits_file, "r", encoding="utf-8") as f:
        available = set(line.strip().lower() for line in f if line.strip())
    
    if not available:
        print(f"{Colors.RED}{t('empty_hits')}{Colors.RESET}")
        input(t('press_enter'))
        return
    
    print(f"[{Colors.GREEN}+{Colors.RESET}] {t('loaded', count=len(available))}\n")
    
    # 互動搜尋
    while True:
        query = input(f"{t('prompt')} {Colors.YELLOW}>>>{Colors.RESET} ").strip()
        
        if query.lower() == 'q':
            break
        
        if not query:
            continue
        
        results = find_similar(query, available)
        
        if results:
            print(f"\n{Colors.GREEN}{t('found', count=len(results))}{Colors.RESET}")
            print("-" * 40)
            for name, match_type in results:
                print(f"  {Colors.CYAN}{name:<15}{Colors.RESET} ({match_type})")
            print("-" * 40)
        else:
            print(f"\n{Colors.RED}{t('not_found', query=query)}{Colors.RESET}")
            
            # 顯示可能的 leet 變體供參考
            variants = generate_leet_variants(query)
            if len(variants) > 1:
                print(f"{Colors.YELLOW}{t('variants_hint')}{Colors.RESET}")
                shown = list(variants)[:10]
                print(f"  {', '.join(shown)}{'...' if len(variants) > 10 else ''}")
        
        print()
    
    print(t('bye'))

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n")
    except Exception as e:
        import traceback
        print(f"{Colors.RED}{t('error')}: {e}{Colors.RESET}")
        traceback.print_exc()
        input(f"\n{t('press_enter')}")
