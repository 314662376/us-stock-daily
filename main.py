import requests
import smtplib
from email.mime.text import MIMEText
from datetime import datetime

# ====== 邮箱配置 ======
SMTP_SERVER = "smtp.qq.com"
SMTP_PORT = 465
EMAIL = "314662376@qq.com"
PASSWORD = "onxajmqsxwcabgdi"

# ====== 获取涨幅榜 ======
def get_top_gainers():
API_KEY = "cUgV2hlvx1sB2qZaohAuR0wOx34Evt4y"

url = f"https://financialmodelingprep.com/api/v3/stock_market/gainers?apikey={API_KEY}"
resp = requests.get(url)
    try:
        data = resp.json()
    except:
        return []
        resp = requests.get(url)
print(resp.status_code)
print(resp.text[:200])

    # ⚠️ 兼容异常返回
    if isinstance(data, dict):
        for k in ["mostGainers", "gainers", "data"]:
            if k in data and isinstance(data[k], list):
                data = data[k]
                break
        else:
            return []

    if not isinstance(data, list):
        return []

    return data[:5]

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

# ====== 生成邮件 ======
def build_email():
    stocks = get_top_gainers()
    today = datetime.now().strftime("%Y-%m-%d")

    content = f"【{today} 美股涨幅榜 TOP5】\n\n"

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

    server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT)
    server.login(EMAIL, PASSWORD)
    server.sendmail(EMAIL, [EMAIL], msg.as_string())
    server.quit()

if __name__ == "__main__":
    send_email()
