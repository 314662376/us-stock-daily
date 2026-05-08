import os
import requests
import smtplib
from email.mime.text import MIMEText
from datetime import datetime

# ====== 邮箱配置 ======
SMTP_SERVER = "smtp.qq.com"
SMTP_PORT = 465
EMAIL = os.environ.get("EMAIL")
PASSWORD = os.environ.get("PASSWORD")  # QQ 邮箱 SMTP 授权码

if not EMAIL or not PASSWORD:
    raise Exception("❌ EMAIL 或 PASSWORD 环境变量未设置，请检查 GitHub Secrets")

# ====== 获取涨幅榜（Yahoo Finance） ======
def get_top_gainers():
    url = "https://query1.finance.yahoo.com/v1/finance/screener/predefined/saved?formatted=true&scrIds=day_gainers&count=5"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        quotes = data["finance"]["result"][0]["quotes"]
        return quotes[:5]
    except Exception as e:
        print("❌ 获取股票数据失败:", e)
        return []

# ====== 简单概念判断 ======
def get_concept(name):
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
        content += "⚠️ 未能获取股票数据，请检查网络或 API。\n"
    else:
        for i, s in enumerate(stocks, 1):
            name = s.get("shortName", s["symbol"])
            concept = get_concept(name)
            change = s.get("regularMarketChangePercent", 0)
            content += f"{i}) {s['symbol']} - {name}\n"
            content += f"涨幅：{change:.2f}%\n"
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
