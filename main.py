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
def get_sector(symbol):
    try:
        stock = yf.Ticker(symbol)
        info = stock.info

        industry = str(info.get("industry", "")).lower()
        summary = str(info.get("longBusinessSummary", "")).lower()

        text = industry + " " + summary

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

    except:
        return "其他 / 小盘题材"

# ====== 统计最强板块 ======
def get_top_sectors(stocks):
    counter = Counter()

    for s in stocks:
        symbol = s["symbol"]
        sector = get_sector(symbol)
        counter[sector] += 1

    return counter.most_common(5)

# ====== 生成邮件 ======
def build_email():
    stocks = get_top_gainers()

    today = datetime.now().strftime("%Y-%m-%d")
    content = f"【{today} 美股市场日报】\n\n"

    # ===== 个股 TOP5 =====
    content += "📈 美股涨幅 TOP5：\n\n"

    for i, s in enumerate(stocks[:5], 1):
        name = s.get("shortName", s["symbol"])
        change = s.get("regularMarketChangePercent", 0)

        if isinstance(change, dict):
            change = change.get("raw", 0)

        content += f"{i}) {s['symbol']} - {name}\n"
        content += f"涨幅：{change:.2f}%\n\n"

    # ===== 板块 TOP5 =====
    content += "🧠 今日强势板块 TOP5：\n\n"

    sectors = get_top_sectors(stocks)

    for i, (sec, count) in enumerate(sectors, 1):
        content += f"{i}) {sec}（{count} 只入选）\n"

    content += "\n⚠️ 仅供参考，不构成投资建议"

    return content

# ====== 发送邮件 ======
def send_email():
    msg = MIMEText(build_email(), "plain", "utf-8")
    msg["Subject"] = "美股涨幅榜 & 板块日报"
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

# ====== 主程序 ======
if __name__ == "__main__":
    send_email()
