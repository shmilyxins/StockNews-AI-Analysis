# AI StockLink 复现 - 后端
# 王岢老师测试: 快速复现 www.aistocklink.cn 核心模块
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from services import em, ai

app = FastAPI(title="AI StockLink 复现版", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])


@app.get("/api/indices")
def indices():
    return em.get_indices()


@app.get("/api/news")
def news(size: int = 20):
    return em.get_fast_news(size)


@app.get("/api/hot-leaders")
def hot_leaders():
    """风口概念 + 领涨股"""
    boards = em.get_hot_boards(8)
    for b in boards:
        b["leaders_detail"] = em.get_board_stocks(b["board_code"], 5)
    return boards


@app.get("/api/hot-burst")
def hot_burst():
    """机构调研推荐热门股：概念热度+个股动量+换手率 简化评分"""
    boards = em.get_hot_boards(10)
    candidates, seen = [], set()
    for rank, b in enumerate(boards):
        heat = max(0, 40 - rank * 4)          # 板块热度分
        for st in em.get_board_stocks(b["board_code"], 6):
            code = st["code"]
            if code in seen:
                continue
            seen.add(code)
            pct, turnover = st.get("pct") or 0, st.get("turnover") or 0
            momentum = max(-10, min(20, pct * 2))       # 动量分
            activity = max(0, min(30, turnover * 1.5))  # 活跃度分
            score = round(heat + momentum + activity)
            level = "高" if score >= 75 else "中" if score >= 55 else "低"
            candidates.append({**st, "keyword": b["board"], "board": b["board"],
                               "heat": heat, "score": score, "level": level})
    candidates.sort(key=lambda x: -x["score"])
    return candidates[:5]


@app.get("/api/forecast")
def forecast(page: int = 1, size: int = 20, report_date: str = "", sort: str = "date"):
    """业绩预测/业绩报表：report_date 如 2026-06-30；sort=date|profit|rev"""
    return em.get_forecast(page, size, report_date=report_date, sort=sort)


@app.get("/api/trend-score")
def trend_score():
    """趋势股评分：60日动量+主力资金+量比+换手率 四因子（基于60日涨幅Top200样本）"""
    import datetime
    stocks = []
    for pn in (1, 2):
        try:
            j = em._get("https://push2.eastmoney.com/api/qt/clist/get",
                        params={"pn": pn, "pz": 100, "po": 1, "np": 1, "fltt": 2,
                                "invt": 2, "fid": "f24",
                                "fs": "m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23",
                                "fields": "f2,f3,f8,f10,f12,f14,f24,f62"})
        except Exception:
            continue
        stocks += (j.get("data") or {}).get("diff", [])
    # 过滤 ST 与停牌(无价格)
    pool = [s for s in stocks
            if "ST" not in (s.get("f14") or "") and s.get("f2") not in ("-", None)]
    if not pool:
        return []

    def norm(key):
        import bisect
        numeric = sorted(v for v in (s.get(key) for s in pool)
                         if isinstance(v, (int, float)))
        def f(v):
            if not isinstance(v, (int, float)) or not numeric:
                return 0.0
            i = bisect.bisect_left(numeric, v)
            return i / max(1, len(numeric) - 1) * 100
        return f

    n_mom, n_flow, n_vol = norm("f24"), norm("f62"), norm("f10")
    for s in pool:
        turnover = s.get("f8")
        turnover = float(turnover) if isinstance(turnover, (int, float)) else 0.0
        # 换手率适中最佳(5%~15%)，过高扣分
        t_score = max(0, 100 - abs(turnover - 10) * 8)
        score = round(n_mom(s.get("f24")) * 0.35 + n_flow(s.get("f62")) * 0.25
                      + n_vol(s.get("f10")) * 0.2 + t_score * 0.2)
        level = "高" if score >= 75 else "中" if score >= 55 else "低"
        stocks.append  # noqa
        flow = s.get("f62")
        flow = float(flow) if isinstance(flow, (int, float)) else 0.0
        s.update({"score": score, "level": level,
                  "flow_wan": round(flow / 1e4),
                  "date": datetime.date.today().isoformat()})
    pool.sort(key=lambda x: -x["score"])
    out = [{"code": str(s.get("f12")), "name": s.get("f14"), "price": s.get("f2"),
            "pct": s.get("f3"), "mom60": s.get("f24"), "vol_ratio": s.get("f10"),
            "turnover": s.get("f8"), "flow_wan": s.get("flow_wan"),
            "score": s["score"], "level": s["level"]} for s in pool]
    return out[:50]


@app.get("/api/stock/search")
def stock_search(keyword: str = Query(..., min_length=1)):
    return em.search_stock(keyword)


def _resolve_secid(code_or_qid: str) -> str:
    s = em.secid_from_quote_id(code_or_qid)
    return s or em.code_to_secid(code_or_qid)


@app.get("/api/stock/{code}/kline")
def stock_kline(code: str, days: int = 120):
    try:
        return em.get_kline(_resolve_secid(code), days)
    except Exception:
        raise HTTPException(404, "未获取到该股票K线数据")


@app.get("/api/stock/{code}/profile")
def stock_profile(code: str):
    try:
        return em.get_quote(_resolve_secid(code))
    except Exception:
        raise HTTPException(404, "未获取到该股票行情")


@app.get("/api/stock/{code}/ai-analysis")
def stock_ai_analysis(code: str):
    secid = _resolve_secid(code)
    try:
        profile = em.get_quote(secid)
    except Exception:
        raise HTTPException(404, "未获取到该股票行情")
    try:
        kdata = em.get_kline(secid, 30)
        klines = kdata["klines"]
    except Exception:
        klines = []
    kw = profile.get("name") or profile.get("code") or code
    try:
        news = em.get_fast_news(30)
        news = [n for n in news if kw in (n.get("summary") or "") + (n.get("title") or "")][:5]
    except Exception:
        news = []
    return ai.analyze(profile, klines, news)
