# 东方财富公开接口封装
import json
import re
import time
import requests

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0 Safari/537.36"
S = requests.Session()
S.headers.update({"User-Agent": UA, "Referer": "https://quote.eastmoney.com/"})

INDEX_SECIDS = "1.000001,0.399001,0.399006,100.HSI,124.HSTECH,100.HXC"


def _get(url, **kw):
    last = None
    for attempt in range(4):
        try:
            u = url
            if attempt % 2 == 1 and "push2.eastmoney.com" in u:
                u = u.replace("push2.eastmoney.com", "push2delay.eastmoney.com")
            r = S.get(u, timeout=15, **kw)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            last = e
            time.sleep(1.5 + 1.5 * attempt)
    raise last


def get_indices():
    """市场概览：主要指数实时行情"""
    j = _get("https://push2.eastmoney.com/api/qt/ulist.np/get",
             params={"fltt": 2, "secids": INDEX_SECIDS,
                     "fields": "f2,f3,f4,f12,f14"})
    out = []
    for d in (j.get("data") or {}).get("diff", []):
        out.append({"code": str(d.get("f12")), "name": d.get("f14"),
                    "price": d.get("f2"), "chg": d.get("f4"), "pct": d.get("f3")})
    return out


def get_hot_boards(top=8):
    """风口概念板块（按涨幅）+ 领涨股"""
    j = _get("https://push2.eastmoney.com/api/qt/clist/get",
             params={"pn": 1, "pz": top, "po": 1, "np": 1, "fltt": 2,
                     "invt": 2, "fid": "f3", "fs": "m:90+t:3",
                     "fields": "f2,f3,f12,f14,f104,f105,f128,f140,f136"})
    out = []
    for d in (j.get("data") or {}).get("diff", []):
        out.append({"board": d.get("f14"), "board_code": d.get("f12"),
                    "pct": d.get("f3"), "up_count": d.get("f104"),
                    "down_count": d.get("f105"),
                    "leader": d.get("f128"), "leader_code": d.get("f140"),
                    "leader_pct": d.get("f136")})
    return out


def get_board_stocks(board_code, pz=10):
    """板块内个股（按涨幅）"""
    j = _get("https://push2.eastmoney.com/api/qt/clist/get",
             params={"pn": 1, "pz": pz, "po": 1, "np": 1, "fltt": 2,
                     "invt": 2, "fid": "f3", "fs": f"b:{board_code}",
                     "fields": "f2,f3,f8,f12,f14,f100"})
    out = []
    for d in (j.get("data") or {}).get("diff", []):
        out.append({"code": str(d.get("f12")), "name": d.get("f14"),
                    "price": d.get("f2"), "pct": d.get("f3"),
                    "turnover": d.get("f8"), "industry": d.get("f100")})
    return out


def _tx_symbol(secid):
    """1.600519 -> sh600519 / 0.000001 -> sz000001"""
    mkt, code = secid.split(".", 1)
    if code.startswith(("4", "8")):
        return "bj" + code
    return ("sh" if mkt == "1" else "sz") + code


def _tencent_kline(secid, days=120):
    """腾讯日K（前复权）"""
    sym = _tx_symbol(secid)
    r = requests.get("https://web.ifzq.gtimg.cn/appstock/app/fqkline/get",
                     params={"param": f"{sym},day,,,{days},qfq"},
                     headers={"User-Agent": UA}, timeout=15)
    r.raise_for_status()
    d = (r.json().get("data") or {}).get(sym) or {}
    rows = d.get("qfqday") or d.get("day") or []
    klines = []
    for row in rows:
        dt, o, c, h, l, vol = row[0], row[1], row[2], row[3], row[4], row[5]
        klines.append({"date": dt, "open": float(o), "close": float(c),
                       "high": float(h), "low": float(l),
                       "volume": int(float(vol)), "amount": 0})
    return {"name": d.get("qt") and None or sym, "code": secid.split(".")[1], "klines": klines}


def _em_kline(secid, days=120):
    j = _get("https://push2his.eastmoney.com/api/qt/stock/kline/get",
             params={"secid": secid, "klt": 101, "fqt": 1, "lmt": days,
                     "end": 20500101,
                     "fields1": "f1,f2,f3,f4,f5,f6",
                     "fields2": "f51,f52,f53,f54,f55,f56,f57"})
    d = j.get("data") or {}
    klines = []
    for line in d.get("klines", []):
        dt, o, c, h, l, vol, amt = line.split(",")
        klines.append({"date": dt, "open": float(o), "close": float(c),
                       "high": float(h), "low": float(l),
                       "volume": int(vol), "amount": float(amt)})
    return {"name": d.get("name"), "code": d.get("code"), "klines": klines}


def get_kline(secid, days=120):
    """个股日K：腾讯为主源，东财为备源"""
    try:
        return _tencent_kline(secid, days)
    except Exception:
        return _em_kline(secid, days)


def _tencent_quote(secid):
    """腾讯实时报价，GBK文本协议"""
    sym = _tx_symbol(secid)
    r = requests.get(f"https://qt.gtimg.cn/q={sym}",
                     headers={"User-Agent": UA}, timeout=15)
    r.encoding = "gbk"
    fields = r.text.split('"')[1].split("~")
    f = lambda i: fields[i] if i < len(fields) else ""
    cap = float(f(45)) * 1e8 if f(45) else None
    return {"code": f(2), "name": f(1), "price": float(f(3) or 0),
            "pct": float(f(32) or 0), "open": float(f(5) or 0),
            "high": float(f(33) or 0), "low": float(f(34) or 0),
            "volume": float(f(36) or 0) * 100, "amount": float(f(37) or 0) * 1e4,
            "turnover": float(f(38) or 0), "pe": float(f(39) or 0),
            "pb": float(f(46) or 0), "mktcap": cap}


def get_quote(secid):
    """个股实时报价：腾讯为主源，东财为备源"""
    try:
        return _tencent_quote(secid)
    except Exception:
        j = _get("https://push2.eastmoney.com/api/qt/stock/get",
                 params={"secid": secid, "fltt": 2, "invt": 2,
                         "fields": "f43,f44,f45,f46,f47,f48,f50,f57,f58,f60,f62,f84,f85,f116,f117,f162,f167,f168,f169,f170,f171"})
        d = j.get("data") or {}
        return {"code": str(d.get("f57", "")), "name": d.get("f58"),
                "price": d.get("f43"), "high": d.get("f44"), "low": d.get("f45"),
                "open": d.get("f46"), "volume": d.get("f47"), "amount": d.get("f48"),
                "turnover": d.get("f168"), "pe": d.get("f162"), "pb": d.get("f167"),
                "mktcap": d.get("f116"), "pct": d.get("f170")}


_STOCK_CACHE = {"ts": 0.0, "list": []}


def get_all_stocks():
    """全A股代码表（分页拉取，缓存1小时），用于本地搜索"""
    if _STOCK_CACHE["list"] and time.time() - _STOCK_CACHE["ts"] < 3600:
        return _STOCK_CACHE["list"]
    lst, page, total = [], 1, None
    while True:
        try:
            j = _get("https://push2delay.eastmoney.com/api/qt/clist/get",
                     params={"pn": page, "pz": 100, "po": 1, "np": 1, "fltt": 2,
                             "invt": 2, "fid": "f12",
                             "fs": "m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23",
                             "fields": "f12,f14"})
        except Exception:
            break
        data = j.get("data") or {}
        diff = data.get("diff", [])
        total = data.get("total") or 0
        for d in diff:
            code = str(d.get("f12"))
            lst.append({"code": code, "name": d.get("f14"),
                        "quote_id": code_to_secid(code)})
        if page * 100 >= total or not diff:
            break
        page += 1
        time.sleep(0.2)
    if lst:
        _STOCK_CACHE["ts"] = time.time()
        _STOCK_CACHE["list"] = lst
    return lst


def search_stock(keyword, count=8):
    """本地搜索：代码前缀 / 名称包含"""
    kw = (keyword or "").strip().upper()
    res = []
    for s in get_all_stocks():
        if s["code"].startswith(kw) or kw in s["name"]:
            res.append(s)
            if len(res) >= count:
                break
    return res


def get_fast_news(size=20):
    """7x24 财经快讯"""
    j = _get("https://np-listapi.eastmoney.com/comm/web/getFastNewsList",
             params={"client": "web", "biz": "web_724", "fastColumn": "102",
                     "sortEnd": "", "pageSize": size, "req_trace": "1"})
    out = []
    for d in ((j.get("data") or {}).get("fastNewsList") or []):
        title = (d.get("title") or "").strip()
        summary = (d.get("summary") or "").strip()
        code = d.get("code") or ""
        out.append({"time": d.get("showTime", ""),
                    "title": title or (summary[:30] + "…" if len(summary) > 30 else summary),
                    "summary": summary, "important": d.get("level") in ("B", "A"),
                    "url": f"https://finance.eastmoney.com/a/{code}.html" if code else ""})
    return out


def get_forecast(page=1, size=20, report_date="", sort="date"):
    """业绩报表（净利润同比榜，近似原站盈利预测更新榜）"""
    sort_map = {"profit": "SJLTZ", "rev": "YSTZ", "date": "NOTICE_DATE"}
    params = {"reportName": "RPT_LICO_FN_CPD", "columns": "ALL",
              "sortColumns": sort_map.get(sort, "NOTICE_DATE"),
              "sortTypes": "-1", "pageSize": size, "pageNumber": page}
    if report_date:
        params["filter"] = f"(REPORTDATE='{report_date}')"
    j = _get("https://datacenter-web.eastmoney.com/api/data/v1/get", params=params)
    out = []
    for d in ((j.get("result") or {}).get("data") or []):
        out.append({"date": (d.get("NOTICE_DATE") or "")[:10],
                    "report_date": (d.get("REPORTDATE") or "")[:10],
                    "code": d.get("SECURITY_CODE"), "name": d.get("SECURITY_NAME_ABBR"),
                    "rev_pct": round(d.get("YSTZ") or 0, 2),
                    "profit_pct": round(d.get("SJLTZ") or 0, 2),
                    "eps": d.get("BASIC_EPS"),
                    "industry": d.get("PUBLISHNAME")})
    return out


def secid_from_quote_id(qid):
    """QuoteID 如 1.600519 直接可用"""
    return qid if re.match(r"^\d+\.\w+$", qid or "") else None


def code_to_secid(code):
    """纯代码猜测市场: 6/9开头沪, 其余深"""
    code = str(code)
    if code.startswith(("6", "9", "5")):
        return f"1.{code}"
    if code.startswith(("8", "4")):
        return f"0.{code}"
    return f"0.{code}"
