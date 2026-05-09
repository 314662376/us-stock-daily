import os
import requests
from datetime import datetime
from email.mime.text import MIMEText
import smtplib
import yfinance as yf
from collections import Counter

# ====== 邮箱配置 ======
SMTP_SERVER = "smtp.qq.com"
SMTP_PORT = 465
EMAIL = os.environ.get("EMAIL")
PASSWORD = os.environ.get("PASSWORD")  # QQ邮箱SMTP授权码

if not EMAIL or not PASSWORD:
    raise Exception("❌ EMAIL 或 PASSWORD 未配置，请检查 GitHub Secrets")

# ====== 获取涨幅榜 TOP50 ======
def get_top_gainers():
    url = "https://query1.finance.yahoo.com/v1/finance/screener/predefined/saved"
    params = {
        "scrIds": "day_gainers",
        "count": 50,
        "formatted": "true"
    }
    headers = {"User-Agent": "Mozilla/5.0"}

    resp = requests.get(url, params=params, headers=headers, timeout=10)
    data = resp.json()
    return data["finance"]["result"][0]["quotes"]

# ====== 板块识别 ======
def get_sector(text):
    text = text.lower()
    if any(x in text for x in ["lithium", "battery", "energy", "solar", "wind", "renewable"]):
        return "能源 / 锂电 / 新能源"
    if any(x in text for x in ["ai", "artificial intelligence", "semiconductor", "chip", "software"]):
        return "AI / 半导体 / 科技"
    if any(x in text for x in ["biotech", "pharma", "drug"]):
        return "生物医药"
    if any(x in text for x in ["cloud", "saas", "platform"]):
        return "云计算"
    if any(x in text for x in ["space", "rocket", "aerospace"]):
        return "商业航天"
    return "其他 / 小盘题材"

# ====== 统计最强板块 ======
def get_top_sectors(stocks):
    counter = Counter()
    symbols = [s['symbol'] for s in stocks]
    batch = yf.Tickers(" ".join(symbols))
    for s in stocks:
        symbol = s['symbol']
        try:
            info = batch.tickers[symbol].info
            text = (str(info.get("industry","")) + " " + str(info.get("longBusinessSummary",""))).lower()
            sector = get_sector(text)
        except:
            sector = "其他 / 小盘题材"
        counter[sector] += 1
    return counter.most_common(5)

# ====== 筛选市值大于 1000 亿 USD 的个股（批量获取） ======
def filter_large_cap(stocks, min_market_cap=100_000_000_000):
    symbols = [s['symbol'] for s in stocks]
    batch = yf.Tickers(" ".join(symbols))
    large_caps = []
    for s in stocks:
        symbol = s['symbol']
        try:
            info = batch.tickers[symbol].info
            market_cap = info.get("marketCap", 0)
            if market_cap >= min_market_cap:
                change = s.get("regularMarketChangePercent", 0)
                if isinstance(change, dict):
                    change = change.get("raw", 0)
                large_caps.append({
                    "symbol": symbol,
                    "name": s.get("shortName", symbol),
                    "change": change,
                    "marketCap": market_cap
                })
        except:
            continue
    return sorted(large_caps, key=lambda x: x["change"], reverse=True)[:10]

# ====== 生成邮件 ======
def build_email():
    stocks = get_top_gainers()
    today = datetime.now().strftime("%Y-%m-%d")
    content = f"【{today} 美股市场日报】\n\n"

    # 个股 TOP5
    content += "📈 美股涨幅 TOP5（不限制市值）：\n\n"
    for i, s in enumerate(stocks[:5], 1):
        name = s.get("shortName", s["symbol"])
        change = s.get("regularMarketChangePercent", 0)
        if isinstance(change, dict):
            change = change.get("raw", 0)
        content += f"{i}) {s['symbol']} - {name}\n涨幅：{change:.2f}%\n\n"

    # 市值大于1000亿
    content += "🏦 市值 ≥1000 亿 USD，涨幅 TOP10：\n\n"
    large_caps = filter_large_cap(stocks)
    if large_caps:
        for i, s in enumerate(large_caps, 1):
            content += f"{i}) {s['symbol']} - {s['name']}\n涨幅：{s['change']:.2f}% | 市值：{s['marketCap']/1e9:.1f}B USD\n\n"
    else:
        content += "暂无符合条件的股票。\n\n"

    # 板块 TOP5
    content += "🧠 今日强势板块 TOP5（基于 TOP50）：\n\n"
    sectors = get_top_sectors(stocks)
    for i, (sec, count) in enumerate(sectors, 1):
        content += f"{i}) {sec}（{count} 只入选）\n"

    content += "\n⚠️ 仅供参考，不构成投资建议"
    return content

# ====== 发送邮件 ======
def send_email():
    msg = MIMEText(build_email(), "plain", "utf-8")
    msg["Subject"] = "美股涨幅榜 & 市值榜 & 板块日报"
    msg["From"] = EMAIL
    msg["To"] = EMAIL
    try:
        print("📧 正在发送邮件...")
        server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT)
        server.login(EMAIL, PASSWORD)
        server.sendmail(EMAIL, [EMAIL], msg.as_string())
        server.quit()
        print("✅ 邮件发送成功")
    except Exception as e:
        print("❌ 邮件发送失败:", e)

if __name__ == "__main__":
    send_email()
