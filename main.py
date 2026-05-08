import os
import requests
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
SMTP_SERVER = "smtp.qq.com"
SMTP_PORT = 465
EMAIL = os.environ["EMAIL"]
PASSWORD = os.environ["PASSWORD"]
API_KEY = os.environ["API_KEY"]
# ====== 获取涨幅榜 ======
import requests

def get_top_gainers():
    url = "https://query1.finance.yahoo.com/v1/finance/screener/predefined/saved?formatted=true&scrIds=day_gainers&count=5"

    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        resp = requests.get(url, headers=headers, timeout=10)
        data = resp.json()

        quotes = data["finance"]["result"][0]["quotes"]
        return quotes[:5]

    except Exception as e:
        print("获取失败:", e)
        return []

# ====== 简单概念判断 ======
concept = get_concept(s.get('shortName', s['symbol']))
    name = name.lower()
    if "bio" in name or "thera" in name:
        return "生物医药 / 创新药"
    if "ai" in name or "tech" in name:
        return "AI / 科技"
    if "energy" in name:
        return "能源"
    if "space" in name or "rocket" in name:
        return "商业航天"
    return "小盘题材 / 资金驱动"

# ====== 生成邮件内容 ======
def build_email():
    stocks = get_top_gainers()
    today = datetime.now().strftime("%Y-%m-%d")
    content = f"【{today} 美股涨幅榜 TOP5】\n\n"

    if not stocks:
        content += "⚠️ 未能获取股票数据，请检查 API KEY 或网络。\n"
    else:
        for i, s in enumerate(stocks, 1):
            concept = get_concept(s['name'])
            content += f"{i}) {s['symbol']} - {s['name']}\n"
            content += f"涨幅：{s['changesPercentage']}\n"
            content += f"核心概念：{concept}\n\n"

    content += "【提示】小盘股波动极大，请注意风险。\n"
    return content

# ====== 发送邮件 ======
def send_email():
    content = build_email()
    msg = MIMEText(content, "plain", "utf-8")
    msg["Subject"] = "美股涨幅榜日报"
    msg["From"] = EMAIL
    msg["To"] = EMAIL

    try:
        server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT)
        server.login(EMAIL, PASSWORD)
        server.sendmail(EMAIL, [EMAIL], msg.as_string())
        server.quit()
        print("邮件发送成功")
    except Exception as e:
        print("邮件发送失败:", e)

if __name__ == "__main__":
    send_email()
