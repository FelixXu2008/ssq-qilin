#!/usr/bin/env python3
"""
双色球开奖数据爬虫（多源兼容版）
支持国内外网络环境，GitHub Actions 可用
"""

import json
import re
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

try:
    import requests
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "-q"])
    import requests

DATA_FILE = Path(__file__).parent / "data.json"
MAX_RETRIES = 2
RETRY_DELAY = 2

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
}


# ============================================================
# 数据源 1：中国福彩网官方 API（国内网络优先）
# ============================================================
def fetch_from_cwl(limit=30):
    print(f"[源1-福彩网] 抓取最近 {limit} 期...")
    url = "https://www.cwl.gov.cn/cwl_admin/front/cwlkj/search/kjxx/findDrawNotice"
    params = {
        "name": "ssq", "issueCount": limit,
        "issueStart": "", "issueEnd": "",
        "dayStart": "", "dayEnd": "",
        "pageNo": 1, "pageSize": limit, "systemType": "PC",
    }
    headers = {**HEADERS, "Referer": "https://www.cwl.gov.cn/ygkj/wqkjgg/ssq/"}

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.get(url, params=params, headers=headers, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            results = []
            for item in data.get("result", []):
                results.append({
                    "period": item["code"],
                    "date": item["date"][:10],
                    "red": [int(x) for x in item["red"].split(",")],
                    "blue": int(item["blue"]),
                })
            if results:
                print(f"[源1-福彩网] ✅ 成功 {len(results)} 期")
                return results
        except Exception as e:
            print(f"[源1-福彩网] 第{attempt}次失败: {e}")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)
    return None


# ============================================================
# 数据源 2：500.com 图表数据（国内外均可访问）
# ============================================================
def fetch_from_500(limit=30):
    print(f"[源2-500.com] 抓取最近 {limit} 期...")
    url = "https://datachart.500.com/ssq/history/newinc/history.php"

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=10)
            resp.raise_for_status()
            html = resp.text

            results = []
            # 匹配表格行：<tr><td>期号</td><td>红1</td>...<td>红6</td><td>蓝</td></tr>
            pattern = r'<tr[^>]*>\s*<td[^>]*>(\d{7})</td>(.*?)</tr>'
            rows = re.findall(pattern, html, re.DOTALL)

            for period, row_content in rows[:limit]:
                nums = re.findall(r'>(\d+)<', row_content)
                if len(nums) >= 7:
                    results.append({
                        "period": period,
                        "date": "",
                        "red": [int(x) for x in nums[:6]],
                        "blue": int(nums[6]),
                    })

            if results:
                print(f"[源2-500.com] ✅ 成功 {len(results)} 期")
                return results
        except Exception as e:
            print(f"[源2-500.com] 第{attempt}次失败: {e}")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)
    return None


# ============================================================
# 数据源 3：网易彩票 API（国内外均可）
# ============================================================
def fetch_from_163(limit=30):
    print(f"[源3-网易彩票] 抓取最近 {limit} 期...")
    url = "https://caipiao.163.com/award/getAwardInfo.html"
    params = {"gameEn": "ssq", "periodNum": limit}

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.get(url, params=params, headers=HEADERS, timeout=10)
            resp.raise_for_status()
            data = resp.json()

            results = []
            for item in data.get("data", {}).get("list", []):
                period = item.get("period", "")
                date_str = item.get("awardTime", "")[:10]
                red_str = item.get("winningNumber", "")
                # 网易格式: "01,05,11,19,27,32|04"
                if "|" in red_str:
                    red_part, blue_part = red_str.split("|")
                    red = [int(x) for x in red_part.split(",")]
                    blue = int(blue_part)
                else:
                    continue
                results.append({
                    "period": period,
                    "date": date_str,
                    "red": red,
                    "blue": blue,
                })

            if results:
                print(f"[源3-网易彩票] ✅ 成功 {len(results)} 期")
                return results
        except Exception as e:
            print(f"[源3-网易彩票] 第{attempt}次失败: {e}")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)
    return None


# ============================================================
# 数据源 4：新浪彩票 API（国内外均可）
# ============================================================
def fetch_from_sina(limit=30):
    print(f"[源4-新浪彩票] 抓取最近 {limit} 期...")
    url = "https://match.lottery.sina.com.cn/lotto/pc_zst/index"
    params = {"type": "ssq"}

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.get(url, headers=HEADERS, timeout=10)
            resp.raise_for_status()
            html = resp.text

            results = []
            # 新浪走势图页面包含开奖数据
            # 格式: data-period="2026081" data-red="06,10,12,15,24,27" data-blue="12"
            pattern = r'data-period="(\d{7})"[^>]*data-red="([^"]+)"[^>]*data-blue="(\d+)"'
            matches = re.findall(pattern, html)

            if not matches:
                # 备用正则
                pattern = r'"periodNo"\s*:\s*"(\d{7})".*?"redBall"\s*:\s*"([^"]+)".*?"blueBall"\s*:\s*"(\d+)"'
                matches = re.findall(pattern, html, re.DOTALL)

            for period, red_str, blue_str in matches[:limit]:
                red = [int(x.strip()) for x in red_str.split(",") if x.strip().isdigit()]
                if len(red) == 6:
                    results.append({
                        "period": period,
                        "date": "",
                        "red": red,
                        "blue": int(blue_str),
                    })

            if results:
                print(f"[源4-新浪彩票] ✅ 成功 {len(results)} 期")
                return results
        except Exception as e:
            print(f"[源4-新浪彩票] 第{attempt}次失败: {e}")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)
    return None


# ============================================================
# 数据源 5：GitHub 公开数据仓库（最稳定，全球可达）
# ============================================================
def fetch_from_github_repo(limit=30):
    """从 GitHub 上的公开双色球数据仓库抓取"""
    print(f"[源5-GitHub仓库] 抓取最近 {limit} 期...")
    # 多个公开数据仓库，逐个尝试
    repos = [
        "https://raw.githubusercontent.com/nicecai/ssq-data/main/ssq.json",
        "https://raw.githubusercontent.com/nicecai/ssq-data/main/data.json",
    ]

    for url in repos:
        for attempt in range(1, MAX_RETRIES + 1):
            try:
                resp = requests.get(url, headers=HEADERS, timeout=10)
                if resp.status_code != 200:
                    continue
                data = resp.json()

                # 兼容不同格式
                items = data if isinstance(data, list) else data.get("data", data.get("latest", []))
                results = []
                for item in items[:limit]:
                    period = item.get("period") or item.get("issue") or item.get("code", "")
                    red = item.get("red") or item.get("redBall", [])
                    blue = item.get("blue") or item.get("blueBall", 0)
                    date = item.get("date") or item.get("awardDate", "")

                    if isinstance(red, str):
                        red = [int(x) for x in red.split(",")]
                    if isinstance(blue, str):
                        blue = int(blue)

                    if len(red) == 6 and blue > 0:
                        results.append({
                            "period": str(period),
                            "date": str(date)[:10],
                            "red": [int(x) for x in red],
                            "blue": int(blue),
                        })

                if results:
                    print(f"[源5-GitHub仓库] ✅ 成功 {len(results)} 期")
                    return results
            except Exception as e:
                print(f"[源5-GitHub仓库] {url} 第{attempt}次失败: {e}")
                if attempt < MAX_RETRIES:
                    time.sleep(RETRY_DELAY)
    return None


# ============================================================
# 主流程
# ============================================================
def load_existing_data():
    if DATA_FILE.exists():
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return None


def save_data(results):
    now = datetime.now(timezone(timedelta(hours=8))).isoformat()
    results.sort(key=lambda x: x["period"], reverse=True)

    output = {"latest": results, "updated": now}
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n{'='*50}")
    print(f"✅ 数据已保存 → {DATA_FILE.name}")
    print(f"   最新: 第{results[0]['period']}期 ({results[0].get('date', 'N/A')})")
    print(f"   红球: {results[0]['red']}  蓝球: {results[0]['blue']}")
    print(f"   共 {len(results)} 期 | 更新: {now}")
    print(f"{'='*50}")


def main():
    print("=" * 50)
    print("🎱 双色球开奖数据爬虫 (多源版)")
    print("=" * 50)
    print()

    # 按优先级逐个尝试数据源
    sources = [
        ("福彩网",    fetch_from_cwl),       # 国内优先
        ("500.com",   fetch_from_500),        # 国内外均可
        ("网易彩票",  fetch_from_163),        # 国内外均可
        ("新浪彩票",  fetch_from_sina),       # 国内外均可
        ("GitHub仓库", fetch_from_github_repo), # 全球可达
    ]

    results = None
    for name, fetcher in sources:
        results = fetcher(limit=30)
        if results:
            break
        print(f"   ↳ {name} 失败，尝试下一个源...\n")

    if not results:
        print("\n❌ 所有数据源均失败！")
        existing = load_existing_data()
        if existing:
            print("📦 保留已有数据不覆盖")
            sys.exit(0)
        else:
            print("💥 无任何可用数据")
            sys.exit(1)

    # 合并历史数据
    existing = load_existing_data()
    if existing:
        existing_periods = {item["period"] for item in existing.get("latest", [])}
        for item in results:
            if item["period"] not in existing_periods:
                existing["latest"].append(item)
        existing["latest"].sort(key=lambda x: x["period"], reverse=True)
        results = existing["latest"]

    save_data(results)


if __name__ == "__main__":
    main()
