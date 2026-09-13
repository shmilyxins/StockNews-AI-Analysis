# AI 个股分析：支持 火山方舟Anthropic协议 / OpenAI兼容接口，无 Key 时回退规则版
import os
import re
import requests

# 简易 .env 加载（backend/.env，不覆盖已有环境变量）
_ENV_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
if os.path.exists(_ENV_PATH):
    for line in open(_ENV_PATH, encoding="utf-8"):
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

# 协议一：Anthropic Messages（火山方舟 /api/coding 等）
ANTHROPIC_BASE = os.environ.get("ANTHROPIC_BASE_URL", "")
ANTHROPIC_KEY = os.environ.get("ANTHROPIC_AUTH_TOKEN") or os.environ.get("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", "glm-5.3-flash[1m]")
# 协议二：OpenAI 兼容（DeepSeek 等）
BASE = os.environ.get("OPENAI_BASE_URL", "https://api.deepseek.com")
KEY = os.environ.get("OPENAI_API_KEY", "")
MODEL = os.environ.get("OPENAI_MODEL", "deepseek-chat")


def _anthropic_analyze(profile: dict, klines: list, news: list) -> str:
    closes = [k["close"] for k in klines]
    vols = [k["volume"] for k in klines]
    recent = closes[-6:]
    chg5 = (recent[-1] / recent[-6] - 1) * 100 if len(closes) > 5 else 0
    vol_ratio = (sum(vols[-3:]) / 3) / (sum(vols[-20:-3]) / 17) if len(vols) > 20 and sum(vols[-20:-3]) else 1
    prompt = f"""你是资深的A股分析师。请基于以下数据写一份简明个股分析（300字以内，分点）。
注意：仅供学习研究，结尾加一句"以上内容不构成投资建议"。

【个股】{profile.get('name')}({profile.get('code')})
【现价】{profile.get('price')}  今日涨跌 {profile.get('pct')}%  换手率 {profile.get('turnover')}%
【估值】PE {profile.get('pe')}  PB {profile.get('pb')}  总市值 {profile.get('mktcap')}
【近5日】收盘 {recent}，5日累计涨跌 {chg5:.2f}%
【量能】近3日均量/前17日均量 = {vol_ratio:.2f}
【近期快讯】
{chr(10).join('- ' + (n.get('summary') or n.get('title') or '')[:80] for n in news[:5])}

请输出：一、技术面 二、量价与资金 三、消息面 四、风险提示。"""

    r = requests.post(
        f"{ANTHROPIC_BASE.rstrip('/')}/v1/messages",
        headers={"x-api-key": ANTHROPIC_KEY,
                 "anthropic-version": "2023-06-01",
                 "content-type": "application/json"},
        json={"model": ANTHROPIC_MODEL, "max_tokens": 2000,
              "messages": [{"role": "user", "content": prompt}]},
        timeout=120)
    r.raise_for_status()
    content = r.json().get("content", [])
    return "".join(b.get("text", "") for b in content if b.get("type") == "text").strip()


def _llm_analyze(profile: dict, klines: list, news: list) -> str:
    closes = [k["close"] for k in klines]
    vols = [k["volume"] for k in klines]
    recent = closes[-6:]
    chg5 = (recent[-1] / recent[-6] - 1) * 100 if len(closes) > 5 else 0
    vol_ratio = (sum(vols[-3:]) / 3) / (sum(vols[-20:-3]) / 17) if len(vols) > 20 and sum(vols[-20:-3]) else 1
    prompt = f"""你是资深的A股分析师。请基于以下数据写一份简明个股分析（300字以内，分点）。
注意：仅供学习研究，结尾加一句"以上内容不构成投资建议"。

【个股】{profile.get('name')}({profile.get('code')})
【现价】{profile.get('price')}  今日涨跌 {profile.get('pct')}%  换手率 {profile.get('turnover')}%
【估值】PE {profile.get('pe')}  PB {profile.get('pb')}  总市值 {profile.get('mktcap')}
【近5日】收盘 {recent}，5日累计涨跌 {chg5:.2f}%
【量能】近3日均量/前17日均量 = {vol_ratio:.2f}
【近期快讯】
{chr(10).join('- ' + (n.get('summary') or n.get('title') or '')[:80] for n in news[:5])}

请输出：一、技术面 二、量价与资金 三、消息面 四、风险提示。"""

    r = requests.post(
        f"{BASE}/chat/completions",
        headers={"Authorization": f"Bearer {KEY}"},
        json={"model": MODEL,
              "messages": [{"role": "user", "content": prompt}],
              "temperature": 0.5, "max_tokens": 800},
        timeout=60)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"]


def _rule_analyze(profile: dict, klines: list, news: list) -> str:
    lines = [f"【{profile.get('name')}({profile.get('code')})】规则版分析（未配置LLM Key）", ""]
    closes = [k["close"] for k in klines]
    vols = [k["volume"] for k in klines]
    if not closes:
        lines.append("一、技术面")
        lines.append("· 暂无K线数据")
    else:
        chg5 = (closes[-1] / closes[-6] - 1) * 100 if len(closes) > 5 else 0
        chg20 = (closes[-1] / closes[-21] - 1) * 100 if len(closes) > 20 else 0
        vol_ratio = (sum(vols[-3:]) / 3) / (sum(vols[-20:-3]) / 17) if len(vols) > 20 and sum(vols[-20:-3]) else 1
        ma5 = sum(closes[-5:]) / 5
        ma20 = sum(closes[-20:]) / 20 if len(closes) >= 20 else ma5
        lines.append("一、技术面")
        lines.append(f"· 现价 {profile.get('price')}，5日涨跌 {chg5:.2f}%，20日涨跌 {chg20:.2f}%")
        lines.append(f"· MA5={ma5:.2f} / MA20={ma20:.2f}，现价位于{'上方，短线偏强' if closes[-1] >= ma5 else '下方，短线偏弱'}")
        lines.append("")
        lines.append("二、量价与资金")
        lines.append(f"· 近3日均量为前17日均量的 {vol_ratio:.2f} 倍，{'放量' if vol_ratio > 1.3 else '缩量' if vol_ratio < 0.7 else '量能平稳'}")
    lines.append(f"· 换手率 {profile.get('turnover')}%，PE {profile.get('pe')}，PB {profile.get('pb')}")
    lines.append("")
    lines.append("三、消息面")
    if news:
        for n in news[:3]:
            lines.append(f"· {(n.get('summary') or n.get('title') or '')[:60]}")
    else:
        lines.append("· 暂无相关快讯")
    lines.append("")
    lines.append("四、风险提示")
    lines.append("· 数据仅基于公开行情与快讯，分析供学习研究使用")
    lines.append("")
    lines.append("以上内容不构成投资建议。")
    return "\n".join(lines)


def analyze(profile: dict, klines: list, news: list) -> dict:
    notes = []
    if ANTHROPIC_KEY and ANTHROPIC_BASE:
        try:
            return {"mode": "llm", "content": _anthropic_analyze(profile, klines, news)}
        except Exception as e:
            notes.append(f"[Anthropic调用失败({type(e).__name__})]")
    if KEY:
        try:
            out = {"mode": "llm", "content": _llm_analyze(profile, klines, news)}
            if notes:
                out["content"] = " ".join(notes) + "\n\n" + out["content"]
            return out
        except Exception as e:
            notes.append(f"[OpenAI兼容调用失败({type(e).__name__})]")
    content = _rule_analyze(profile, klines, news)
    if notes:
        content = " ".join(notes) + " 已回退规则版。\n\n" + content
    return {"mode": "rule", "content": content}
