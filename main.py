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

# ====== 中文名字典（市值TOP100美股常见）=====
cn_dict = {
    "AAPL": "苹果",
    "MSFT": "微软",
    "GOOGL": "谷歌",
    "AMZN": "亚马逊",
    "TSLA": "特斯拉",
    "NVDA": "英伟达",
    "BRK-B": "伯克希尔·哈撒韦",
    "META": "Meta",
    "UNH": "联合健康",
    "JNJ": "强生",
    "V": "Visa",
    "WMT": "沃尔玛",
    "PG": "宝洁",
    "JPM": "摩根大通",
    "MA": "万事达",
    "HD": "家得宝",
    "PYPL": "PayPal",
    "DIS": "迪士尼",
    "ADBE": "Adobe",
    "NFLX": "奈飞",
    "KO": "可口可乐",
    "PEP": "百事可乐",
    "XOM": "埃克森美孚",
    "CVX": "雪佛龙",
    "MRK": "默克",
    "ABBV": "艾伯维",
    "PFE": "辉瑞",
    "ABT": "雅培",
    "TMO": "赛默飞世尔",
    "ORCL": "甲骨文",
    "INTC": "英特尔",
    "CSCO": "思科",
    "CRM": "Salesforce",
    "ACN": "埃森哲",
    "NKE": "耐克",
    "MCD": "麦当劳",
    "LLY": "礼来",
    "AVGO": "博通",
    "COST": "好市多",
    "TXN": "德州仪器",
    "QCOM": "高通",
    "MDT": "美敦力",
    "NEE": "下一能源",
    "LIN": "林德",
    "HON": "霍尼韦尔",
    "LOW": "劳氏",
    "PM": "菲利普莫里斯",
    "SBUX": "星巴克",
    "BMY": "百时美施贵宝",
    "UNP": "联合太平洋铁路",
    "AMGN": "安进",
    "RTX": "雷神",
    "GILD": "吉利德",
    "IBM": "IBM",
    "BA": "波音",
    "CAT": "卡特彼勒",
    "DE": "约翰迪尔",
    "MMM": "3M",
    "GS": "高盛",
    "AXP": "美国运通",
    "BLK": "贝莱德",
    "BKNG": "Booking",
    "CVS": "CVS",
    "MDLZ": "亿滋国际",
    "SYK": "史赛克",
    "ANTM": "安泰保险",
    "ISRG": "Intuitive Surgical",
    "FISV": "Fiserv",
    "ADI": "亚德诺",
    "MU": "美光",
    "SPGI": "标普全球",
    "LRCX": "拉姆研究",
    "NOW": "ServiceNow",
    "CHTR": "Charter",
    "APD": "空气化工产品",
    "CSX": "CSX铁路",
    "CCI": "城市中心",
    "EL": "欧莱雅",
    "MDLZ": "亿滋",
    "TMUS": "T-Mobile",
    "ZTS": "智飞生物",
    "VRTX": "Vertex",
    "EA": "艺电",
    "ADP": "ADP",
    "ROST": "Ross Stores",
    "T": "AT&T",
    "VZ": "Verizon",
    "PLD": "Prologis",
    "ISRG": "直觉手术",
    "ABMD": "ABIOMED",
    "REGN": "再生元",
    "BIIB": "Biogen",
    "LMT": "洛克希德马丁",
    "HON": "霍尼韦尔",
    "UPS": "联合包裹",
    "FDX": "联邦快递",
    "SYK": "史赛克",
    "BK": "富国银行",
    "MS": "摩根士丹利",
    "CL": "宝洁（消费品）",
    "SHW": "舒尔茨油漆",
    "CCI": "城市中心投资",
}

# ====== 获取涨幅榜 TOP50 ======
def get_top_gainers():
    url = "https://query1.finance.yahoo.com/v1/finance/screener/predefined/saved"
    params = {"scrIds": "day_gainers", "count": 50, "formatted": "true"}
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
            text = (str(info.get("industry", "")) + " " + str(info.get("longBusinessSummary", ""))).lower()
            sector = get_sector(text)
        except:
            sector = "其他 / 小盘题材"
        counter[sector] += 1
    return counter.most_common(5)

# ====== 筛选市值大于 1000 亿 USD 的个股 ======
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
                    "cn_name": cn_dict.get(symbol, ""),
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
        symbol = s['symbol']
        name = s.get("shortName", symbol)
        cn_name = cn_dict.get(symbol, "")
        change = s.get("regularMarketChangePercent", 0)
        if isinstance(change, dict):
            change = change.get("raw", 0)
        content += f"{i}) {symbol} - {name} - {cn_name}\n涨幅：{change:.2f}%\n\n"

    # 市值大于1000亿 USD
    content += "🏦 市值 ≥1000 亿 USD，涨幅 TOP10：\n\n"
    large_caps = filter_large_cap(stocks)
    if large_caps:
        for i, s in enumerate(large_caps, 1):
            content += f"{i}) {s['symbol']} - {s['name']} - {s['cn_name']}\n"
            content += f"涨幅：{s['change']:.2f}% | 市值：{s['marketCap']/1e9:.1f}B USD\n\n"
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

# ====== 主程序 ======
if __name__ == "__main__":
    send_email()
