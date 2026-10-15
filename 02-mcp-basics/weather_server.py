"""MCP SERVER minh hoạ — công bố tool `get_weather` qua giao thức MCP.

Khác với function calling: tool nằm ở một server ĐỘC LẬP. Server tự "khai
báo" tool của mình; bất kỳ MCP client nào (Claude Code, Claude Desktop,
Cursor, hoặc weather_client.py) cũng cắm vào dùng được mà không cần biết
code bên trong.

Schema của tool được TỰ ĐỘNG sinh ra từ type hints + docstring.

Chạy trực tiếp:
    pip install -r ../requirements.txt
    python weather_server.py

Đăng ký với Claude Code (làm 1 lần, dùng mãi):
    claude mcp add weather -- python /đường/dẫn/tới/weather_server.py
"""

from mcp.server.mcpserver import MCPServer

mcp = MCPServer("weather")

_MOCK_DB = {
    "Hanoi": "29°C, trời mưa",
    "Haiphong": "33°C, mưa rào",
    "Danang": "30°C, nhiều mây",
}

_FORECAST_DB = {
    "Hanoi": ["29°C, trời mưa", "30°C, mưa nhẹ", "31°C, nhiều mây"],
    "Haiphong": ["33°C, mưa rào", "32°C, mưa rào", "31°C, âm u"],
    "Danang": ["30°C, nhiều mây", "31°C, nắng nhẹ", "32°C, nắng"],
}


@mcp.tool()
def get_weather(city: str) -> str:
    """Lấy thời tiết hiện tại của một thành phố."""
    return f"{city}: {_MOCK_DB.get(city, '28°C, không có dữ liệu chi tiết')}"


@mcp.tool()
def get_forecast(city: str, days: int = 3) -> str:
    """Lấy dự báo thời tiết N ngày tới cho một thành phố.

    Args:
        city: Tên thành phố (ví dụ: "Hanoi", "Haiphong", "Danang").
        days: Số ngày dự báo (1-3, mặc định 3).
    """
    days = max(1, min(days, 3))
    daily = _FORECAST_DB.get(city, ["28°C, không có dữ liệu chi tiết"] * 3)
    lines = [f"Ngày {i + 1}: {daily[i]}" for i in range(days)]
    return f"Dự báo {city} ({days} ngày):\n" + "\n".join(lines)


if __name__ == "__main__":
    mcp.run()  # mặc định chạy qua stdio
