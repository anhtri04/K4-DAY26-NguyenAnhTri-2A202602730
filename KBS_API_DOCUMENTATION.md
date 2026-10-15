# KBS (KB Securities) API Documentation

## Overview

This document describes the API endpoints used by the KBS (KB Securities) data provider for Vietnamese stock market data.

**Base URL:**
- IIS Server: `https://kbbuddywts.kbsec.com.vn/iis-server/investment`

> **Note:** The SAS Server (`https://kbbuddywts.kbsec.com.vn/sas`) is deprecated. All endpoints now use the IIS Server base URL.

---

## 1. Listing Module

### 1.1 Get All Stock Symbols
**Endpoint:** `GET /stock/search/data`

**Full URL:** `https://kbbuddywts.kbsec.com.vn/iis-server/investment/stock/search/data`

**Description:** Retrieve all stock symbols with basic information.

**Response Format:** JSON Array
```json
[
  {
    "symbol": "ACB",
    "name": "Ngân hàng TMCP Á Châu",
    "nameEn": "Asia Commercial Bank",
    "exchange": "HOSE",
    "type": "stock",
    "index": 1234,
    "re": 25000,
    "ceiling": 27500,
    "floor": 22500
  }
]
```

**Mapped Methods:**
- `all_symbols()` - Returns symbol and organ_name
- `symbols_by_exchange()` - Returns detailed symbol information

---

### 1.2 Get Symbols by Group/Index
**Endpoint:** `GET /index/{group_code}/stocks`

**Full URL:** `https://kbbuddywts.kbsec.com.vn/iis-server/investment/index/{group_code}/stocks`

**Supported Group Codes:**

**Exchange Codes:**
- `HOSE` - Ho Chi Minh Stock Exchange
- `HNX` - Hanoi Stock Exchange  
- `UPCOM` - UPCOM Market

**Index Codes (Use Numeric Format):**
- `30` - VN30 (30 largest stocks on HOSE)
- `100` - VN100 (100 largest stocks on HOSE)
- `MID` - VNMidCap (Mid-cap index)
- `SML` - VNSmallCap (Small-cap index)
- `SI` - VNSI (Small-cap index)
- `X50` - VNX50 (50 largest stocks across HOSE and HNX)
- `XALL` - VNXALL (All stocks on HOSE and HNX)
- `ALL` - VNALL (All stocks on HOSE and HNX)
- `HNX30` - HNX30 (30 largest stocks on HNX)

**Other Asset Types:**
- `FUND` - ETF (Exchange Traded Funds)
- `CW` - Covered Warrants
- `BOND` - Bonds
- `DER` - Derivatives (Futures)

**Note:** For index groups (VN30, VN100, etc.), use the numeric code (e.g., `30` not `VN30`).
Exchange codes (HOSE, HNX, UPCOM) work as-is.

**Response Format:** JSON Array of symbols
```json
["ACB", "BCM", "BID", "BVH", ...]
```

**Mapped Method:** `symbols_by_group(group)`

---

### 1.3 Get All Industries
**Endpoint:** `GET /sector/all`

**Full URL:** `https://kbbuddywts.kbsec.com.vn/iis-server/investment/sector/all`

**Response Format:** JSON Array
```json
[
  {
    "code": 1,
    "name": "Bán buôn"
  },
  {
    "code": 2,
    "name": "Bảo hiểm"
  }
]
```

**Mapped Method:** Internal use for `symbols_by_industries()`

---

### 1.4 Get Symbols by Industry
**Endpoint:** `GET /sector/stock`

**Full URL:** `https://kbbuddywts.kbsec.com.vn/iis-server/investment/sector/stock?code={industry_code}&l=1`

**Query Parameters:**
- `code` (required): Industry code
- `l` (optional): Language (1 for Vietnamese)

**Response Format:** JSON Object
```json
{
  "stocks": [
    {"sb": "ACB"},
    {"sb": "BID"}
  ]
}
```

**Mapped Method:** `symbols_by_industries()`

---

## 2. Quote Module

### 2.1 Get Historical Price Data
**Endpoint:** `GET /stocks/{symbol}/data_{interval}` (for stocks)
**Endpoint:** `GET /index/{symbol}/data_{interval}` (for indices)

**Full URL:** 
- Stocks: `https://kbbuddywts.kbsec.com.vn/iis-server/investment/stocks/{symbol}/data_{interval}`
- Indices: `https://kbbuddywts.kbsec.com.vn/iis-server/investment/index/{symbol}/data_{interval}`

**Supported Intervals:**
- `1P` - 1 minute
- `5P` - 5 minutes
- `15P` - 15 minutes
- `30P` - 30 minutes
- `60P` - 1 hour
- `day` - Daily
- `week` - Weekly
- `month` - Monthly

**Query Parameters:**
- `sdate` (required): Start date (DD-MM-YYYY format)
- `edate` (required): End date (DD-MM-YYYY format)

**Response Format:** JSON Object
```json
{
  "symbol": "ACB",
  "data_day": [
    {
      "t": "2025-01-10 07:00",
      "o": "20806.8384",
      "h": "20848.6192",
      "l": "20639.7152",
      "c": "20639.7152",
      "v": "4710900"
    }
  ]
}
```

**Mapped Method:** `history(start, end, interval)`

**Field Mapping:**
- `t` → `time` (format: `yyyy-MM-dd HH:mm`)
- `o` → `open`
- `h` → `high`
- `l` → `low`
- `c` → `close`
- `v` → `volume`

**Price Normalization Note:**
- **Stocks:** Prices are returned as decimal strings in actual VND (e.g., `20806.8384`). No division is required for values that contain decimal places.
- **Indices:** Prices are returned as actual index values (e.g., `1245.6`).
- **Legacy integer format:** Some older responses may return integer values (e.g., `25100`) which should be divided by 1000.

---

### 2.2 Get Intraday Trade History
**Endpoint:** `GET /trade/history/{symbol}`

**Full URL:** `https://kbbuddywts.kbsec.com.vn/iis-server/investment/trade/history/{symbol}`

**Query Parameters:**
- `page` (optional): Page number (default: 1)
- `limit` (optional): Records per page (default: 100)

**Response Format:** JSON Object
```json
{
  "data": [
    {
      "t": "2026-04-23 14:45:04:40",
      "TD": "23/04/2026",
      "SB": "ACB",
      "FT": "14:45:00",
      "LC": "B",
      "FMP": 23500,
      "FCV": -100,
      "FV": 115400,
      "AVO": 14035700,
      "AVA": 331233060000
    }
  ]
}
```

**Mapped Method:** `intraday(page, page_size)`

**Field Mapping:**
- `t` → `timestamp`
- `TD` → `trading_date`
- `SB` → `symbol`
- `FT` → `time`
- `LC` → `side` (B=buy, S=sell, empty=unknown)
- `FMP` → `price` (divided by 1000)
- `FCV` → `price_change`
- `FV` → `match_volume`
- `AVO` → `accumulated_volume`
- `AVA` → `accumulated_value`

---

## 3. Company Module

### 3.1 Get Company Profile
**Endpoint:** `GET /stockinfo/profile/{symbol}`

**Full URL:** `https://kbbuddywts.kbsec.com.vn/iis-server/investment/stockinfo/profile/{symbol}?l=1`

**Query Parameters:**
- `l` (optional): Language (1 for Vietnamese)

**Response Format:** JSON Object
```json
{
  "SM": "Business model description",
  "SB": "ACB",
  "FD": "24/04/1993",
  "CC": 51367,
  "HM": 13229,
  "LD": "09/12/2020",
  "FV": 10000,
  "EX": "HOSE",
  "LP": 26400,
  "VL": 5137,
  "CTP": "CEO Name",
  "CTPP": "CEO Position",
  "IS": "Inspector Name",
  "ISP": "Inspector Position",
  "FP": "License Number",
  "BP": "Business Code",
  "TC": "Tax Code",
  "KT": "Auditor",
  "TY": "Company Type",
  "ADD": "Address",
  "PHONE": "Phone",
  "FAX": "Fax",
  "EMAIL": "Email",
  "URL": "Website",
  "BRANCH": [...],
  "HS": "History",
  "KLCPNY": 15.5,
  "SFV": 500000000,
  "KLCPLH": 4300000000,
  "AD": "2025-12-31",
  "Subsidiaries": [...],
  "Leaders": [...],
  "Ownership": [...],
  "Shareholders": [...],
  "CharterCapital": [...],
  "LaborStructure": [...]
}
```

**Mapped Method:** `overview()`

**Field Mapping:**
- `SM` → `business_model`
- `SB` → `symbol`
- `FD` → `founded_date`
- `CC` → `charter_capital`
- `HM` → `number_of_employees`
- `LD` → `listing_date`
- `FV` → `par_value`
- `EX` → `exchange`
- `LP` → `listing_price`
- `VL` → `listed_volume`
- `CTP` → `ceo_name`
- `CTPP` → `ceo_position`
- `IS` → `inspector_name`
- `ISP` → `inspector_position`
- `FP` → `establishment_license`
- `BP` → `business_code`
- `TC` → `tax_id`
- `KT` → `auditor`
- `TY` → `company_type`
- `ADD` → `address`
- `PHONE` → `phone`
- `FAX` → `fax`
- `EMAIL` → `email`
- `URL` → `website`
- `BRANCH` → `branches`
- `HS` → `history`
- `KLCPNY` → `free_float_percentage`
- `SFV` → `free_float`
- `KLCPLH` → `outstanding_shares`
- `AD` → `as_of_date`

---

### 3.2 Get Company Events
**Endpoint:** `GET /stockinfo/event/{symbol}`

**Full URL:** `https://kbbuddywts.kbsec.com.vn/iis-server/investment/stockinfo/event/{symbol}`

**Query Parameters:**
- `l` (optional): Language (1 for Vietnamese)
- `p` (optional): Page number (default: 1)
- `s` (optional): Page size (default: 10)
- `eID` (optional): Event type filter (1-5)
  - 1: Đại hội cổ đông (AGM)
  - 2: Trả cổ tức (Dividend)
  - 3: Phát hành (Issuance)
  - 4: Giao dịch cổ đông nội bộ (Insider trading)
  - 5: Sự kiện khác (Other)

**Mapped Method:** `events(event_type, page, page_size)`

---

### 3.3 Get Company News
**Endpoint:** `GET /stockinfo/news/{symbol}`

**Full URL:** `https://kbbuddywts.kbsec.com.vn/iis-server/investment/stockinfo/news/{symbol}`

**Query Parameters:**
- `l` (optional): Language (1 for Vietnamese)
- `p` (optional): Page number (default: 1)
- `s` (optional): Page size (default: 10)

**Response Format:** JSON Array
```json
[
  {
    "Head": "Article summary...",
    "ArticleID": 1432485,
    "Title": "Article title...",
    "PublishTime": "2026-04-23T12:20:14.71",
    "URL": "/2026/04/article-slug.htm"
  }
]
```

**Mapped Method:** `news(page, page_size)`

---

### 3.4 Get Insider Trading
**Endpoint:** `GET /stockinfo/news/internal-trading/{symbol}`

**Full URL:** `https://kbbuddywts.kbsec.com.vn/iis-server/investment/stockinfo/news/internal-trading/{symbol}`

**Query Parameters:**
- `l` (optional): Language (1 for Vietnamese)
- `p` (optional): Page number (default: 1)
- `s` (optional): Page size (default: 10)

**Mapped Method:** `insider_trading(page, page_size)`

---

## 4. Finance Module

### 4.1 Get Financial Reports
**Endpoint:** `GET /stock/finance-info/{symbol}`

**Full URL:** `https://kbbuddywts.kbsec.com.vn/iis-server/investment/stock/finance-info/{symbol}`

**Query Parameters:**
- `type` (required): Report type
  - `KQKD` - Income Statement (Kết quả kinh doanh)
  - `CDKT` - Balance Sheet (Cân đối kế toán)
  - `LCTT` - Cash Flow (Lưu chuyển tiền tệ trực tiếp)
  - `CSTC` - Financial Ratios (Chỉ số tài chính)
  - `CTKH` - Planned Indicators (Chỉ tiêu kế hoạch)
  - `BCTT` - Summary Financial Report (Báo cáo tài chính tóm tắt)
- `termtype` (required): Period type (`1`=year, `2`=quarter)
- `termType` (required): Same as `termtype` (both required)
- `code` (required): Stock symbol (e.g., `ACB`)
- `page` (optional): Page number (default: 1)
- `pageSize` (optional): Records per page (default: 4)
- `unit` (optional): Unit (`1000000000`=billions VND)
- `languageid` (optional): Language (`1`=Vietnamese)

**Response Format:** JSON Object
```json
{
  "Audit": [
    {
      "AuditedStatusCode": "CKT",
      "Description": "Chưa kiểm toán",
      "DescriptionEn": "Unaudited"
    }
  ],
  "Unit": [
    {
      "UnitedCode": "HN",
      "UnitedName": "Hợp nhất",
      "UnitedNameEN": "Consolidated"
    }
  ],
  "Head": [
    {
      "ID": 1,
      "CompanyID": 885,
      "YearPeriod": 2025,
      "TermCode": "Q4",
      "TermName": "Quý 4",
      "TermNameEN": "Quarter 4",
      "ReportTermID": 5,
      "DisplayOrdering": 11,
      "United": "HN",
      "AuditedStatus": "CKT",
      "PeriodBegin": "202510",
      "PeriodEnd": "202512",
      "ReportDate": "2026-01-26T00:00:00",
      "CreatedDate": "2026-01-28T16:48:55.743",
      "AuditStatusID": 4,
      "LastUpdate": "2026-03-06T11:38:08.89",
      "DatePubDepartment": "2026-01-28T00:00:00",
      "TotalRow": 55,
      "BusinessType": 3
    }
  ],
  "Content": {
    "Kết quả kinh doanh": [
      {
        "ID": 1,
        "ReportNormID": 53,
        "Name": "Doanh thu bán hàng",
        "NameEn": "Revenue",
        "CssStyle": "",
        "ParentReportNormID": 0,
        "ReportComponentName": "Kết quả kinh doanh",
        "ReportComponentNameEn": "Income Statement",
        "Unit": "VNĐ",
        "UnitEn": "VND",
        "OrderType": null,
        "OrderingComponent": null,
        "RowNumber": null,
        "ReportComponentTypeID": 9,
        "ChildTotal": 0,
        "Levels": 0,
        "Value1": 1000000000,
        "Value2": 950000000,
        "Value3": 900000000,
        "Value4": 850000000
      }
    ]
  }
}
```

**Content Keys by Report Type:**
- `KQKD` → `Kết quả kinh doanh`
- `CDKT` → `Cân đối kế toán`
- `LCTT` → `Lưu chuyển tiền tệ trực tiếp`
- `CSTC` → Multiple keys (ratio groups, e.g., `Nhóm chỉ số đánh giá`, `Nhóm chỉ sộ khả năng sinh lời`, etc.)

**Mapped Methods:**
- `income_statement(period)` → type=KQKD
- `balance_sheet(period)` → type=CDKT
- `cash_flow(period)` → type=LCTT
- `ratio(period)` → type=CSTC

**Notes:**
- To retrieve up to 8 periods, make two requests (`page=1` and `page=2`) and merge the `Value1-4` from page 2 into `Value5-8`.
- `CSTC` responses contain multiple content keys (one per ratio group). All items should be collected across all keys.

---

## 5. Trading Module

### 5.1 Get Price Board (Real-time)
**Endpoint:** `POST /stock/iss`

**Full URL:** `https://kbbuddywts.kbsec.com.vn/iis-server/investment/stock/iss`

**Request Headers:**
```
Accept-Language: en-US,en;q=0.9,vi;q=0.8
Content-Type: application/json
x-lang: vi
```

**Request Body:**
```json
{
  "code": "ACB,VNM,HPG"
}
```

**Response Format:** JSON Array
```json
[
  {
    "TT": 14035700,
    "PP": 0,
    "HI": 23900,
    "TV": 331233060000,
    "LO": 23500,
    "LS": "5136656599",
    "CHP": -0.423728813559322,
    "V1": 1272400,
    "V2": 490400,
    "V3": 358000,
    "ULS": "",
    "IN": "ASB",
    "OIC": "",
    "TSI": "",
    "EP": "0.0",
    "ER": "",
    "B1": "23500.0",
    "AP": 23599,
    "B2": 23450,
    "B3": 23400,
    "RE": 23600,
    "EX": "HOSE",
    "FB": 1212100,
    "FC": "10",
    "S1": "23600.0",
    "S2": 23650,
    "S3": 23700,
    "FL": 21950,
    "FO": 1540996979,
    "FTY": "",
    "FR": 129985806,
    "PTQ": 0,
    "FS": 8692200,
    "SB": "ACB",
    "PTV": 0,
    "TLQ": "5136656599",
    "ST": "2",
    "OP": 23550,
    "P1": "115400",
    "P2": "23500.0",
    "CH": -100,
    "CL": 25250,
    "CP": 23500,
    "TB": 0,
    "PMP": 0,
    "CV": 115400,
    "t": 1776931500753,
    "PMQ": 0,
    "TO": 0,
    "U1": 32300,
    "U2": 110400,
    "U3": 78400,
    "MS": "K"
  }
]
```

**Mapped Method:** `price_board(symbols_list)`

**Field Mapping:**
- `SB` → `symbol`
- `t` → `time` (timestamp in milliseconds)
- `EX` → `exchange`
- `CL` → `ceiling_price`
- `FL` → `floor_price`
- `RE` → `reference_price`
- `CP` → `close_price` / `match_price`
- `CV` → `match_volume`
- `OP` → `open_price`
- `HI` → `high_price`
- `LO` → `low_price`
- `AP` → `average_price`
- `TV` → `total_value`
- `CH` → `price_change`
- `CHP` → `percent_change`
- `B1`, `B2`, `B3` → `bid_price_1`, `bid_price_2`, `bid_price_3`
- `V1`, `V2`, `V3` → `bid_vol_1`, `bid_vol_2`, `bid_vol_3`
- `S1`, `S2`, `S3` → `ask_price_1`, `ask_price_2`, `ask_price_3`
- `U1`, `U2`, `U3` → `ask_vol_1`, `ask_vol_2`, `ask_vol_3`
- `FB` → `foreign_buy_volume`
- `FR` → `foreign_sell_volume`
- `TT` → `total_trades`
- `LS` → `total_shares`
- `TLQ` → `total_listed_shares`
- `FS` → `foreign_room`
- `FO` → `foreign_ownership`
- `FC` → `face_value`
- `ST` → `status`
- `MS` → `match_status`
- `PP` → `prior_price`

---

## 6. Supported Index Symbols

The following index symbols are supported for historical data:
- `VNINDEX` - VN-Index
- `HNXINDEX` - HNX-Index
- `UPCOMINDEX` - UPCOM-Index
- `VN30` - VN30 Index
- `HNX30` - HNX30 Index
- `VN100` - VN100 Index

---

## 7. Asset Type Detection

KBS automatically detects asset types:
- **Stock:** Regular stock symbols (e.g., ACB, VNM, HPG)
- **Index:** Index symbols listed above
- **Derivative:** Futures contracts (e.g., VN30F2501M, VN30F2502)
- **ETF:** ETF symbols (e.g., E1VFVN30)
- **Bond:** Bond symbols
- **Covered Warrant:** CW symbols

---

## 8. Error Handling

**Common HTTP Status Codes:**
- `200` - Success
- `400` - Bad Request (invalid parameters)
- `404` - Not Found (invalid symbol or endpoint)
- `500` - Internal Server Error

**Response Error Format:**
```json
{
  "status": 404,
  "message": "Data not found"
}
```

---

## 9. Rate Limiting

No explicit rate limiting is documented. However, it is recommended to:
- Add delays between requests
- Use reasonable page sizes
- Cache results when possible
- Use proxy rotation for high-frequency requests

---

## 10. Data Normalization

### Price Values
- **Price Board & Intraday:** Price values are returned as integers and should be divided by 1000 to get the actual price in VND.
- **Historical Data:** Stock prices are returned as decimal strings in actual VND (no division needed). Indices are returned as actual index values.

### Volume Values
Volume values are returned as integers representing actual share counts.

### Timestamps
- Historical data: `yyyy-MM-dd HH:mm` format (e.g., `2025-01-10 07:00`)
- Intraday data: Custom format (`yyyy-MM-dd HH:mm:ss:SS` with milliseconds)
- Price board: Unix timestamp in milliseconds

---

## 11. Data Source Attribution

When using data from KBS, please attribute:
- **Source:** KB Securities (KBS)
- **Provider:** kbbuddywts.kbsec.com.vn
- **Data Type:** Vietnamese Stock Market Data

---

*Last Updated: April 23, 2026*
*Version: 1.1.0*
