"""FUNCTION CALLING với dữ liệu chứng khoán THẬT từ KBS (KB Securities).

Mirror của `weather_function_calling.py`, nhưng thay tool mock `get_weather(city)`
bằng 5 tool gọi TRỰC TIẾP KBS IIS API (public, không cần key) — theo
`KBS_API_DOCUMENTATION.md`:

    1. get_price_board(symbols)                        -> POST /stock/iss (§5.1)
    2. get_history(symbol, start_date, end_date, ...)  -> GET /stocks/{s}/data_{iv} (§2.1)
    3. get_company_overview(symbol)                    -> GET /stockinfo/profile/{s} (§3.1)
    4. get_finance(symbol, report_type, period)        -> GET /stock/finance-info/{s} (§4.1)
    5. get_group_symbols(group)                        -> GET /index/{group}/stocks (§1.2)

Khác file weather ở 1 điểm: agent là CLASS giữ
`self.history: list[types.Content]` — agent CÓ MEMORY qua nhiều lượt chat.

Cách chạy:
    pip install -r ../requirements.txt httpx
    export GEMINI_API_KEY=...
    python kbs_stock_function_calling.py
"""

from __future__ import annotations

import json

import httpx
from google import genai
from google.genai import types

MODEL = "gemini-2.5-flash"

# KBS chặn request không có User-Agent (trả 400 "Request Blocked"),
# nên mọi call đều dùng header trình duyệt.
BASE_URL = "https://kbbuddywts.kbsec.com.vn/iis-server/investment"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    ),
    "Accept": "application/json",
    "x-lang": "vi",
}

SYSTEM_INSTRUCTION = (
    "Bạn là trợ lý chứng khoán Việt Nam, trả lời bằng tiếng Việt tự nhiên. "
    "Bạn có 5 công cụ lấy dữ liệu THẬT từ KBS: get_price_board (bảng giá realtime), "
    "get_history (giá lịch sử OHLCV), get_company_overview (hồ sơ công ty), "
    "get_finance (báo cáo tài chính: KQKD/CDKT/LCTT/CSTC), "
    "get_group_symbols (danh sách mã theo sàn/nhóm như HOSE, 30=VN30). "
    "Mã chứng khoán viết HOA (VD: ACB, FPT). "
    "Ngày tháng cho tool dùng định dạng YYYY-MM-DD. "
    "Tóm tắt ngắn gọn, kèm số liệu cụ thể và disclaimer "
    "'không phải lời khuyên đầu tư'."
)

# ---------------------------------------------------------------------------
# 1. Schemas khai báo cho model (viết tay — cùng pattern file weather)
# ---------------------------------------------------------------------------

get_price_board_declaration = types.FunctionDeclaration(
    name="get_price_board",
    description=(
        "Bảng giá realtime nhiều mã (giá khớp, bid/ask 3 bước, khối ngoại). "
        "KBS §5.1 POST /stock/iss."
    ),
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "symbols": types.Schema(
                type=types.Type.ARRAY,
                items=types.Schema(type=types.Type.STRING),
                description='Danh sách mã HOA. VD: ["ACB", "FPT"]',
            ),
        },
        required=["symbols"],
    ),
)

get_history_declaration = types.FunctionDeclaration(
    name="get_history",
    description=(
        "Giá lịch sử OHLCV của 1 mã hoặc chỉ số (VNINDEX, VN30...). "
        "KBS §2.1 GET /stocks/{symbol}/data_{interval}."
    ),
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "symbol": types.Schema(
                type=types.Type.STRING,
                description="Mã CK hoặc chỉ số, viết HOA. VD: ACB, VNINDEX",
            ),
            "start_date": types.Schema(
                type=types.Type.STRING,
                description="Ngày bắt đầu YYYY-MM-DD. VD: 2025-01-01",
            ),
            "end_date": types.Schema(
                type=types.Type.STRING,
                description="Ngày kết thúc YYYY-MM-DD. VD: 2025-01-10",
            ),
            "interval": types.Schema(
                type=types.Type.STRING,
                description="Khung nến: day, week, month (mặc định day)",
            ),
        },
        required=["symbol", "start_date", "end_date"],
    ),
)

get_company_overview_declaration = types.FunctionDeclaration(
    name="get_company_overview",
    description=(
        "Hồ sơ công ty: mô hình kinh doanh, vốn điều lệ, lãnh đạo, sàn niêm yết. "
        "KBS §3.1 GET /stockinfo/profile/{symbol}."
    ),
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "symbol": types.Schema(
                type=types.Type.STRING, description="Mã CK, viết HOA. VD: ACB"
            ),
        },
        required=["symbol"],
    ),
)

get_finance_declaration = types.FunctionDeclaration(
    name="get_finance",
    description=(
        "Báo cáo tài chính: KQKD (lãi/lỗ), CDKT (cân đối), LCTT (tiền tệ), "
        "CSTC (chỉ số). KBS §4.1 GET /stock/finance-info/{symbol}."
    ),
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "symbol": types.Schema(
                type=types.Type.STRING, description="Mã CK, viết HOA. VD: ACB"
            ),
            "report_type": types.Schema(
                type=types.Type.STRING,
                description="Loại báo cáo: KQKD, CDKT, LCTT, CSTC (mặc định KQKD)",
            ),
            "period": types.Schema(
                type=types.Type.STRING,
                description='Kỳ: "year" (năm) hoặc "quarter" (quý, mặc định)',
            ),
        },
        required=["symbol"],
    ),
)

get_group_symbols_declaration = types.FunctionDeclaration(
    name="get_group_symbols",
    description=(
        "Danh sách mã theo sàn/nhóm: HOSE, HNX, UPCOM, 30 (=VN30), "
        "100 (=VN100), HNX30, FUND (=ETF), CW, BOND. KBS §1.2."
    ),
    parameters=types.Schema(
        type=types.Type.OBJECT,
        properties={
            "group": types.Schema(
                type=types.Type.STRING,
                description='Mã nhóm. VD: "HOSE", "30", "HNX", "FUND"',
            ),
        },
        required=["group"],
    ),
)

TOOLS = [
    types.Tool(
        function_declarations=[
            get_price_board_declaration,
            get_history_declaration,
            get_company_overview_declaration,
            get_finance_declaration,
            get_group_symbols_declaration,
        ]
    )
]


# ---------------------------------------------------------------------------
# 2. Thực thi tool — gọi TRỰC TIẾP KBS IIS API (không qua vnstock)
# ---------------------------------------------------------------------------

def _to_kbs_date(yyyy_mm_dd: str) -> str:
    """LLM đưa YYYY-MM-DD -> KBS cần DD-MM-YYYY (§2.1 sdate/edate)."""
    y, m, d = yyyy_mm_dd.strip().split("-")
    return f"{d}-{m}-{y}"


def get_price_board(symbols: list[str]) -> str:
    """§5.1 POST /stock/iss — bảng giá realtime. Giá int -> chia 1000 ra VND."""
    clean = [s.strip().upper() for s in symbols][:20]  # batch gọn, tránh spam
    with httpx.Client(timeout=30.0, headers=HEADERS) as client:
        r = client.post(f"{BASE_URL}/stock/iss", json={"code": ",".join(clean)})
        r.raise_for_status()
        raw = r.json()
    out = [
        {
            "symbol": row.get("SB"),
            "exchange": row.get("EX"),
            "ref": row.get("RE"),
            "ceil": row.get("CL"),
            "floor": row.get("FL"),
            "open": row.get("OP"),
            "high": row.get("HI"),
            "low": row.get("LO"),
            "match_price": row.get("CP"),
            "match_vol": row.get("CV"),
            "change": row.get("CH"),
            "pct_change": row.get("CHP"),
            "bid": [(row.get(f"B{i}"), row.get(f"V{i}")) for i in (1, 2, 3)],
            "ask": [(row.get(f"S{i}"), row.get(f"U{i}")) for i in (1, 2, 3)],
            "foreign_buy": row.get("FB"),
            "foreign_sell": row.get("FR"),
        }
        for row in raw
    ]
    return json.dumps({"source": "KBS", "board": out},
                      ensure_ascii=False, default=str)


def get_history(
    symbol: str, start_date: str, end_date: str, interval: str = "day"
) -> str:
    """§2.1 GET /stocks/{s}/data_{interval} — OHLCV (giá đã là VND, không chia)."""
    symbol = symbol.strip().upper()
    interval = (interval or "day").strip()
    if symbol in ("VNINDEX", "HNXINDEX", "UPCOMINDEX", "VN30", "HNX30", "VN100"):
        url = f"{BASE_URL}/index/{symbol}/data_{interval}"
    else:
        url = f"{BASE_URL}/stocks/{symbol}/data_{interval}"
    params = {"sdate": _to_kbs_date(start_date), "edate": _to_kbs_date(end_date)}
    with httpx.Client(timeout=30.0, headers=HEADERS) as client:
        r = client.get(url, params=params)
        r.raise_for_status()
        data = r.json()
    key = f"data_{interval}"
    rows = [
        {"time": d.get("t"), "open": d.get("o"), "high": d.get("h"),
         "low": d.get("l"), "close": d.get("c"), "volume": d.get("v")}
        for d in data.get(key, [])
    ]
    return json.dumps(
        {"source": "KBS", "symbol": symbol, "interval": interval,
         "rows": len(rows), "data": rows},
        ensure_ascii=False, default=str,
    )


def get_company_overview(symbol: str) -> str:
    """§3.1 GET /stockinfo/profile/{s} — hồ sơ công ty (lược bớt HTML dài)."""
    symbol = symbol.strip().upper()
    with httpx.Client(timeout=30.0, headers=HEADERS) as client:
        r = client.get(f"{BASE_URL}/stockinfo/profile/{symbol}", params={"l": 1})
        r.raise_for_status()
        p = r.json()
    return json.dumps(
        {
            "source": "KBS", "symbol": symbol,
            "exchange": p.get("EX"),
            "founded": p.get("FD"), "listing_date": p.get("LD"),
            "charter_capital": p.get("CC"), "employees": p.get("HM"),
            "ceo": p.get("CTP"), "address": p.get("ADD"),
            "phone": p.get("PHONE"), "website": p.get("URL"),
            "free_float_pct": p.get("KLCPNY"),
            "outstanding_shares": p.get("KLCPLH"),
            # SM/HS là HTML dài — cắt 500 ký tự đầu cho gọn token
            "business_model": str(p.get("SM", ""))[:500],
            "history": str(p.get("HS", ""))[:500],
        },
        ensure_ascii=False, default=str,
    )


_REPORT_TYPES = {"KQKD", "CDKT", "LCTT", "CSTC"}


def get_finance(
    symbol: str, report_type: str = "KQKD", period: str = "quarter"
) -> str:
    """§4.1 GET /stock/finance-info/{s} — KQKD/CDKT/LCTT/CSTC, year|quarter."""
    symbol = symbol.strip().upper()
    report_type = (report_type or "KQKD").strip().upper()
    if report_type not in _REPORT_TYPES:
        return json.dumps({"error": f"report_type phải là một trong {sorted(_REPORT_TYPES)}"})
    term = "1" if (period or "").strip().lower() == "year" else "2"
    params = {
        "type": report_type, "termtype": term, "termType": term,
        "code": symbol, "page": 1, "pageSize": 4, "languageid": 1,
    }
    with httpx.Client(timeout=30.0, headers=HEADERS) as client:
        r = client.get(f"{BASE_URL}/stock/finance-info/{symbol}", params=params)
        r.raise_for_status()
        data = r.json()
    periods = [
        {"term": f"{h.get('TermName')} {h.get('YearPeriod')}",
         "audited": h.get("AuditedStatus")}
        for h in data.get("Head", [])
    ]
    content = data.get("Content", {})
    rows: list[dict] = []
    for group_name, items in content.items():  # CSTC có nhiều nhóm ratio
        for it in items:
            rows.append({
                "group": group_name,
                "item": it.get("Name") or it.get("NameEn"),
                "values": [it.get(f"Value{i}") for i in (1, 2, 3, 4)],
            })
            if len(rows) >= 40:  # gọn token: tối đa 40 dòng
                break
        if len(rows) >= 40:
            break
    return json.dumps(
        {"source": "KBS", "symbol": symbol, "report": report_type,
         "periods": periods, "rows": rows},
        ensure_ascii=False, default=str,
    )


def get_group_symbols(group: str) -> str:
    """§1.2 GET /index/{group}/stocks — mã theo sàn/nhóm (HOSE, 30=VN30...)."""
    group = group.strip().upper()
    with httpx.Client(timeout=30.0, headers=HEADERS) as client:
        r = client.get(f"{BASE_URL}/index/{group}/stocks")
        r.raise_for_status()
        data = r.json()
    symbols = data.get("data") if isinstance(data, dict) else data
    return json.dumps({"source": "KBS", "group": group,
                       "count": len(symbols), "symbols": symbols},
                      ensure_ascii=False, default=str)


# Dispatcher: tên tool model trả về -> hàm Python thật (app chạy, không phải model)
TOOL_EXECUTORS = {
    "get_price_board": get_price_board,
    "get_history": get_history,
    "get_company_overview": get_company_overview,
    "get_finance": get_finance,
    "get_group_symbols": get_group_symbols,
}


# ---------------------------------------------------------------------------
# 3. Agent CLASS có memory (khác file weather: history là state của object,
#    không phải biến local trong run())
# ---------------------------------------------------------------------------

class KBSStockAgent:
    """Agent chứng khoán KBS với memory hội thoại.

    Attributes:
        history: list[types.Content] — toàn bộ hội thoại (user + model +
            function_response). Giữ qua nhiều lần chat(), nên agent "nhớ"
            mã đã hỏi trước đó (VD: hỏi tiếp "còn VCB thì sao?").
    """

    def __init__(
        self,
        model: str = MODEL,
        system_instruction: str = SYSTEM_INSTRUCTION,
    ) -> None:
        self.client = genai.Client()
        self.model = model
        self.system_instruction = system_instruction
        # ★ MEMORY: List[] sống cùng object, không reset sau mỗi chat()
        self.history: list[types.Content] = []

    # -- memory helpers -----------------------------------------------------
    def reset(self) -> None:
        """Xoá memory, bắt đầu hội thoại mới."""
        self.history = []

    @property
    def turns(self) -> int:
        """Số lượt user đã chat (để quan sát memory trong report)."""
        return sum(1 for c in self.history if c.role == "user")

    # -- main loop (mirror run() của file weather, nhưng dùng self.history) -
    def chat(self, prompt: str, verbose: bool = True) -> str:
        """Gửi 1 lượt prompt, tự xử lý function calling, trả về câu trả lời cuối."""
        # 1. Append lượt user vào MEMORY (không tạo list mới!)
        self.history.append(
            types.Content(role="user", parts=[types.Part.from_text(text=prompt)])
        )

        # 2. Gọi model kèm tool schemas
        resp = self.client.models.generate_content(
            model=self.model,
            contents=self.history,
            config=types.GenerateContentConfig(
                tools=TOOLS,
                system_instruction=self.system_instruction,
            ),
        )

        # 3. Vòng lặp: model yêu cầu tool -> APP chạy KBS thật -> trả kết quả lại
        while resp.function_calls:
            self.history.append(resp.candidates[0].content)

            function_responses = []
            for fc in resp.function_calls:
                if verbose:
                    print(f"  [model yêu cầu] {fc.name}({fc.args})")
                executor = TOOL_EXECUTORS.get(fc.name)
                if executor is None:  # tool lạ model tự bịa -> báo lại cho model
                    result = json.dumps({"error": f"Unknown tool: {fc.name}"})
                else:
                    try:
                        result = executor(**fc.args)  # <-- APP chạy KBS, không phải model
                    except Exception as e:  # lỗi mạng / mã sai / symbol 404
                        result = json.dumps({"error": str(e)}, ensure_ascii=False)
                if verbose:
                    print(f"  [app thực thi]  -> {result[:300]}...")
                function_responses.append(
                    types.Part.from_function_response(
                        name=fc.name, response={"result": result}
                    )
                )

            self.history.append(
                types.Content(role="user", parts=function_responses)
            )
            resp = self.client.models.generate_content(
                model=self.model,
                contents=self.history,
                config=types.GenerateContentConfig(
                    tools=TOOLS,
                    system_instruction=self.system_instruction,
                ),
            )

        # 4. Lưu câu trả lời cuối vào MEMORY rồi trả về
        self.history.append(resp.candidates[0].content)
        return resp.text


# Giữ hàm run() dạng function cho tương thích với file weather (stateless, 1-shot)
def run(prompt: str) -> str:
    """One-shot helper (không memory) — tạo agent mới mỗi lần gọi."""
    return KBSStockAgent().chat(prompt)


if __name__ == "__main__":
    agent = KBSStockAgent()
    # Lượt 1: bảng giá realtime nhiều mã
    q1 = "Giá hiện tại của ACB và FPT thế nào?"
    print(f"User: {q1}\n")
    print("Trả lời:", agent.chat(q1))
    print(f"\n--- memory: {len(agent.history)} blocks, {agent.turns} turns ---\n")
    # Lượt 2: memory — hỏi tiếp mã khác mà không cần nhắc lại context
    q2 = "Cho anh lịch sử giá ACB từ 2025-01-01 đến 2025-01-10, kèm KQKD quý gần nhất."
    print(f"User: {q2}\n")
    print("Trả lời:", agent.chat(q2))
    print(f"\n--- memory: {len(agent.history)} blocks, {agent.turns} turns ---")
