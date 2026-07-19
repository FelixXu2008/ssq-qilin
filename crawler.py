#!/usr/bin/env python3
"""
双色球开奖数据爬虫
从中国福彩网抓取历史开奖数据，输出到 data.json
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
    print("正在安装 requests...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "-q"])
    import requests

# ===== 配置 =====
# 中国福彩网 API（JSON 接口，稳定可靠）
CWL_API = "https://www.cwl.gov.cn/cwl_admin/front/cwlkj/search/kjxx/findDrawNotice"
# 备用：500.com 开奖历史
BACKUP_API = "https://datachart.500.com/ssq/history/newinc/history.php"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Referer": "https://www.cwl.gov.cn/ygkj/wqkjgg/ssq/",
}

DATA_FILE = Path(__file__).parent / "data.json"
MAX_RETRIES = 3
RETRY_DELAY = 2  # 秒


def fetch_from_cwl(limit=30):
    """从中国福彩网官方 API 抓取"""
    print(f"[福彩网] 正在抓取最近 {limit} 期数据...")
    params = {
        "name": "ssq",
        "issueCount": limit,
        "issueStart": "",
        "issueEnd": "",
        "dayStart": "",
        "dayEnd": "",
        "pageNo": 1,
        "pageSize": limit,
        "systemType": "PC",
    }

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.get(CWL_API, params=params, headers=HEADERS, timeout=15)
            resp.raise_for_status()
            data = resp.json()

            results = []
            for item in data.get("result", []):
                # 解析红球和蓝球
                red = [int(x) for x in item["red"].split(",")]
                blue = int(item["blue"])
                results.append({
                    "period": item["code"],           # 期号，如 "2026080"
                    "date": item["date"][:10],        # 日期，如 "2026-07-14"
                    "red": red,
                    "blue": blue,
                })

            if results:
                print(f"[福彩网] 成功获取 {len(results)} 期数据")
                return results

        except Exception as e:
            print(f"[福彩网] 第 {attempt} 次尝试失败: {e}")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)

    return None


def fetch_from_500(limit=30):
    """备用：从 500.com 抓取"""
    print(f"[500.com] 正在抓取最近 {limit} 期数据...")

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            resp = requests.get(BACKUP_API, headers=HEADERS, timeout=15)
            resp.raise_for_status()
            html = resp.text

            # 解析表格数据
            # 格式: 期号 | 红球1-6 | 蓝球
            pattern = r'<tr[^>]*>\s*<td>(\d{7})</td>\s*' \
                      r'<td[^>]*>(\d+)</td>\s*' \
                      r'<td[^>]*>(\d+)</td>\s*' \
                      r'<td[^>]*>(\d+)</td>\s*' \
                      r'<td[^>]*>(\d+)</td>\s*' \
                      r'<td[^>]*>(\d+)</td>\s*' \
                      r'<td[^>]*>(\d+)</td>\s*' \
                      r'<td[^>]*>(\d+)</td>'

            matches = re.findall(pattern, html)
            if not matches:
                # 尝试另一种格式
                pattern = r'<tr>\s*<td>(\d{7})</td>(.*?)</tr>'
                rows = re.findall(pattern, html, re.DOTALL)
                results = []
                for period, row_content in rows[:limit]:
                    nums = re.findall(r'>(\d+)<', row_content)
                    if len(nums) >= 7:
                        red = [int(x) for x in nums[:6]]
                        blue = int(nums[6])
                        results.append({
                            "period": period,
                            "date": "",  # 500.com 部分格式没有日期
                            "red": red,
                            "blue": blue,
                        })
            else:
                results = []
                for m in matches[:limit]:
                    period = m[0]
                    red = [int(m[i]) for i in range(1, 7)]
                    blue = int(m[7])
                    results.append({
                        "period": period,
                        "date": "",
                        "red": red,
                        "blue": blue,
                    })

            if results:
                print(f"[500.com] 成功获取 {len(results)} 期数据")
                return results

        except Exception as e:
            print(f"[500.com] 第 {attempt} 次尝试失败: {e}")
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY)

    return None


def fetch_from_apijson(limit=30):
    """备用方案2：公开 API"""
    print(f"[API] 正在尝试公开数据接口...")

    apis = [
        {
            "url": "https://api.jisuapi.com/caipiao/history",
            "params": {"appkey": "", "caipiaoid": "14", "issueno": ""},
            "note": "需要 appkey，跳过",
            "skip": True,
        },
        {
            "url": f"https://www.mxnzp.com/api/lottery/common/latest?code=ssq&app_id=&app_secret=",
            "note": "需要 app_id，跳过",
            "skip": True,
        },
    ]

    # 这些公开 API 大多需要注册，先跳过
    return None


def load_existing_data():
    """加载已有数据"""
    if DATA_FILE.exists():
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return None


def merge_data(existing, fresh):
    """合并新旧数据，去重"""
    if not existing or not fresh:
        return fresh

    existing_periods = {item["period"] for item in existing.get("latest", [])}
    merged = list(existing.get("latest", []))

    for item in fresh:
        if item["period"] not in existing_periods:
            merged.append(item)

    # 按期号倒序排列（最新在前）
    merged.sort(key=lambda x: x["period"], reverse=True)
    return merged


def save_data(results):
    """保存到 data.json"""
    now = datetime.now(timezone(timedelta(hours=8))).isoformat()

    # 确保按期号倒序
    results.sort(key=lambda x: x["period"], reverse=True)

    output = {
        "latest": results,
        "updated": now,
    }

    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 数据已保存到 {DATA_FILE}")
    print(f"   最新一期: 第 {results[0]['period']} 期 ({results[0].get('date', '未知日期')})")
    print(f"   红球: {results[0]['red']}  蓝球: {results[0]['blue']}")
    print(f"   共 {len(results)} 期数据")
    print(f"   更新时间: {now}")


def main():
    print("=" * 50)
    print("🎱 双色球开奖数据爬虫")
    print("=" * 50)
    print()

    # 优先从官方 API 抓取
    results = fetch_from_cwl(limit=30)

    # 官方接口失败，尝试备用
    if not results:
        print("\n⚠️  官方接口失败，尝试备用方案...")
        results = fetch_from_500(limit=30)

    # 所有来源都失败
    if not results:
        print("\n❌ 所有数据源均抓取失败！")
        # 如果有旧数据，保留不覆盖
        existing = load_existing_data()
        if existing:
            print("📦 保留已有数据，未覆盖")
            sys.exit(0)
        else:
            print("💥 无任何可用数据")
            sys.exit(1)

    # 合并已有数据（保留历史）
    existing = load_existing_data()
    if existing:
        existing_latest = existing.get("latest", [])
        existing_periods = {item["period"] for item in existing_latest}
        # 把新数据中有但旧数据中没有的加进去
        for item in results:
            if item["period"] not in existing_periods:
                existing_latest.append(item)
        existing_latest.sort(key=lambda x: x["period"], reverse=True)
        results = existing_latest

    save_data(results)


if __name__ == "__main__":
    main()
