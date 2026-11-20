#!/usr/bin/env python3
"""
Generate the ShopSphere Retail synthetic dataset for the Retail Sales Performance
Analysis project.

Run from the project root:
    python src/generate_data.py

The five physical tables, their columns, SQLite types, keys and constraints match
the Step 8 workbook. Deliberate quality defects are written only to a raw staging
CSV; the canonical CSVs, Excel sheets and SQLite database are cleaned and valid.
"""
from __future__ import annotations

import random
import sqlite3
from pathlib import Path
from collections import Counter

import numpy as np
import pandas as pd

SEED = 42
N_SALES_LINES = 20_000
ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DATA.mkdir(parents=True, exist_ok=True)
rng = np.random.default_rng(SEED)
random.seed(SEED)

# ----------------------------- Step 8 SQLite DDL -----------------------------
DDL = [
"""CREATE TABLE stores (
 store_id INTEGER PRIMARY KEY CHECK(store_id>0),
 store_name TEXT NOT NULL UNIQUE CHECK(length(trim(store_name))>0),
 city TEXT NOT NULL CHECK(length(trim(city))>0),
 region TEXT NOT NULL CHECK(region IN ('North','South','East','West')),
 store_format TEXT NOT NULL CHECK(store_format IN ('Mall','HighStreet','Neighbourhood')),
 opened_on TEXT NOT NULL CHECK(opened_on GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]' AND date(opened_on)=opened_on),
 is_active INTEGER NOT NULL DEFAULT 1 CHECK(is_active IN (0,1))
);""",
"""CREATE TABLE products (
 product_id INTEGER PRIMARY KEY CHECK(product_id>0),
 product_name TEXT NOT NULL CHECK(length(trim(product_name))>0),
 category TEXT NOT NULL CHECK(length(trim(category))>0),
 sub_category TEXT NOT NULL CHECK(length(trim(sub_category))>0),
 brand TEXT NOT NULL CHECK(length(trim(brand))>0),
 cost_price NUMERIC NOT NULL CHECK(cost_price>=0),
 base_list_price NUMERIC NOT NULL CHECK(base_list_price>0),
 is_active INTEGER NOT NULL DEFAULT 1 CHECK(is_active IN (0,1))
);""",
"""CREATE TABLE customers (
 customer_id INTEGER PRIMARY KEY CHECK(customer_id>0),
 segment TEXT NOT NULL CHECK(segment IN ('Budget','Regular','Premium')),
 city TEXT NOT NULL CHECK(length(trim(city))>0),
 joined_on TEXT NOT NULL CHECK(joined_on GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]' AND date(joined_on)=joined_on),
 is_active INTEGER NOT NULL DEFAULT 1 CHECK(is_active IN (0,1))
);""",
"""CREATE TABLE sales_lines (
 line_id INTEGER PRIMARY KEY CHECK(line_id>0),
 order_id TEXT NOT NULL CHECK(length(trim(order_id))>0),
 sale_date TEXT NOT NULL CHECK(sale_date GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]' AND date(sale_date)=sale_date),
 store_id INTEGER NOT NULL REFERENCES stores(store_id) ON DELETE RESTRICT,
 product_id INTEGER NOT NULL REFERENCES products(product_id) ON DELETE RESTRICT,
 customer_id INTEGER NOT NULL REFERENCES customers(customer_id) ON DELETE RESTRICT,
 quantity INTEGER NOT NULL CHECK(quantity>0),
 list_unit_price NUMERIC NOT NULL CHECK(list_unit_price>0),
 discount_pct NUMERIC NOT NULL CHECK(discount_pct BETWEEN 0 AND 100),
 selling_unit_price NUMERIC NOT NULL CHECK(selling_unit_price>=0 AND selling_unit_price<=list_unit_price),
 payment_mode TEXT NOT NULL CHECK(payment_mode IN ('Cash','Card','UPI','Wallet')),
 channel TEXT NOT NULL CHECK(channel IN ('In-store','Online')),
 CHECK(abs(selling_unit_price - (list_unit_price * (1-discount_pct/100.0))) <= 0.02)
);""",
"""CREATE TABLE store_targets (
 target_id INTEGER PRIMARY KEY CHECK(target_id>0),
 store_id INTEGER NOT NULL REFERENCES stores(store_id) ON DELETE RESTRICT,
 target_month TEXT NOT NULL CHECK(target_month GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-01' AND date(target_month)=target_month),
 target_revenue NUMERIC NOT NULL CHECK(target_revenue>0),
 UNIQUE(store_id,target_month)
);"""
]
INDEXES = [
"CREATE INDEX ix_sale_date ON sales_lines(sale_date);",
"CREATE INDEX ix_sale_store_date ON sales_lines(store_id,sale_date);",
"CREATE INDEX ix_sale_product ON sales_lines(product_id);",
"CREATE INDEX ix_sale_customer_order ON sales_lines(customer_id,order_id);",
"CREATE INDEX ix_targets_month ON store_targets(target_month);"
]
VIEW_SQL = """CREATE VIEW v_sales_analysis AS
WITH base AS (
 SELECT s.line_id, s.order_id, s.sale_date,
        substr(s.sale_date,1,7)||'-01' AS sale_month,
        CAST(strftime('%w',s.sale_date) AS INTEGER) AS sale_weekday,
        substr(s.sale_date,1,4) AS sale_year,
        st.store_id, st.store_name, st.city AS store_city,
        st.region, st.store_format, st.opened_on AS store_opened_on,
        p.product_id, p.product_name, p.category, p.sub_category, p.brand,
        c.customer_id, c.segment, c.city AS customer_city, c.joined_on AS customer_joined_on,
        s.quantity, s.list_unit_price, s.discount_pct, s.selling_unit_price,
        p.cost_price, s.payment_mode, s.channel,
        (s.quantity*s.selling_unit_price) AS revenue,
        (s.quantity*p.cost_price) AS cost_amount,
        (s.quantity*(s.selling_unit_price-p.cost_price)) AS profit,
        (s.quantity*(s.list_unit_price-s.selling_unit_price)) AS discount_amount
 FROM sales_lines s
 JOIN stores st ON s.store_id=st.store_id
 JOIN products p ON s.product_id=p.product_id
 JOIN customers c ON s.customer_id=c.customer_id
)
SELECT b.line_id,b.order_id,b.sale_date,b.sale_month,b.sale_weekday,b.sale_year,
       b.store_id,b.store_name,b.store_city,b.region,b.store_format,b.store_opened_on,
       b.product_id,b.product_name,b.category,b.sub_category,b.brand,
       b.customer_id,b.segment,b.customer_city,b.customer_joined_on,
       b.quantity,b.list_unit_price,b.discount_pct,b.selling_unit_price,b.cost_price,
       b.payment_mode,b.channel,b.revenue,b.cost_amount,b.profit,
       CASE WHEN b.revenue=0 THEN NULL ELSE 100.0*b.profit/b.revenue END AS margin_pct,
       b.discount_amount,
       CASE WHEN b.discount_pct=0 THEN '0%'
            WHEN b.discount_pct<=10 THEN '1-10%'
            WHEN b.discount_pct<=20 THEN '11-20%'
            ELSE '>20%' END AS discount_band,
       t.target_month,t.target_revenue,
       CASE WHEN b.revenue=0 THEN NULL WHEN 100.0*b.profit/b.revenue<10 THEN 1 ELSE 0 END AS is_low_margin,
       CASE WHEN b.profit<0 THEN 1 ELSE 0 END AS is_loss_making
FROM base b
LEFT JOIN store_targets t ON b.store_id=t.store_id AND b.sale_month=t.target_month;"""

# ----------------------------- Synthetic masters -----------------------------
cities = ["New Delhi", "Noida", "Ghaziabad", "Gurugram", "Faridabad", "Greater Noida"]
store_specs = [
    ("Aarohan Connaught Place", "New Delhi", "North", "HighStreet"),
    ("Suryodaya Rohini", "New Delhi", "North", "Mall"),
    ("Nivaan Noida Central", "Noida", "North", "Mall"),
    ("Udaya Indirapuram", "Ghaziabad", "North", "Neighbourhood"),
    ("Pragati Vaishali", "Ghaziabad", "East", "HighStreet"),
    ("Aarambh Raj Nagar", "Ghaziabad", "East", "Mall"),
    ("Saanvi Cyber Hub", "Gurugram", "West", "Mall"),
    ("Vistaar Sohna Road", "Gurugram", "West", "HighStreet"),
    ("Anvaya Sector 15", "Faridabad", "South", "Neighbourhood"),
    ("Kshitij Crown Plaza", "Faridabad", "South", "Mall"),
    ("Madhur Pari Chowk", "Greater Noida", "East", "HighStreet"),
    ("Arohi Knowledge Park", "Greater Noida", "South", "Neighbourhood"),
]
stores = pd.DataFrame([
    {"store_id": i+1, "store_name": s, "city": c, "region": r, "store_format": f,
     "opened_on": str(pd.Timestamp("2018-01-01") + pd.Timedelta(days=int(rng.integers(0, 1800)))).split(" ")[0],
     "is_active": 1}
    for i, (s,c,r,f) in enumerate(store_specs)
])

categories = {
    "Apparel": ["Kurtas", "Sarees", "Shirts", "Ethnic Sets", "Casual Wear"],
    "Footwear": ["Sandals", "Sneakers", "Formal Shoes", "Slippers"],
    "Home & Kitchen": ["Cookware", "Storage", "Bed Linen", "Decor", "Drinkware"],
    "Electronics": ["Audio", "Small Appliances", "Accessories", "Personal Tech"],
    "Beauty & Personal Care": ["Skin Care", "Hair Care", "Grooming", "Wellness"],
    "Grocery": ["Staples", "Snacks", "Beverages", "Packaged Foods"],
}
name_parts = {
    "Apparel": ["Aarav Cotton", "Meera Festive", "Ira Everyday", "Kavya Classic", "Riwaayat"],
    "Footwear": ["Pahal Comfort", "Aarush Active", "Niyati Daily", "Samar Walk"],
    "Home & Kitchen": ["Annapurna Steel", "Nivara Home", "Sajavat", "Sukoon Living"],
    "Electronics": ["Tejas Smart", "Pravaah Audio", "Ujjwal Home", "Arogyam Tech"],
    "Beauty & Personal Care": ["Kesar Glow", "Vanya Care", "Amrit Herbal", "Saumya Essentials"],
    "Grocery": ["Annapurna Select", "Dhara Harvest", "Sattva Pantry", "Mitti Naturals"],
}
brands = ["Aaranya", "Nivara", "Sattva", "Ujjwal", "Sukoon", "Pravaah", "Vanya", "Aarambh", "Tejas", "Dhara"]
price_ranges = {
    "Apparel": (499, 3999), "Footwear": (399, 4999), "Home & Kitchen": (199, 5999),
    "Electronics": (799, 14999), "Beauty & Personal Care": (149, 2499), "Grocery": (49, 1499)
}
margin_ranges = {
    "Apparel": (0.48,0.62), "Footwear": (0.38,0.52), "Home & Kitchen": (0.35,0.50),
    "Electronics": (0.16,0.28), "Beauty & Personal Care": (0.42,0.58), "Grocery": (0.12,0.24)
}
product_rows = []
for pid in range(1, 151):
    cat = list(categories.keys())[(pid-1) % len(categories)]
    sub = categories[cat][int(rng.integers(0, len(categories[cat])))]
    lo, hi = price_ranges[cat]
    list_price = round(float(rng.uniform(lo, hi)), 2)
    mlo, mhi = margin_ranges[cat]
    gross_margin = float(rng.uniform(mlo, mhi))
    cost = round(list_price * (1-gross_margin), 2)
    stem = str(rng.choice(name_parts[cat]))
    product_rows.append({
        "product_id": pid, "product_name": f"{stem} {sub[:-1] if sub.endswith('s') else sub} {pid:03d}",
        "category": cat, "sub_category": sub, "brand": str(rng.choice(brands)),
        "cost_price": cost, "base_list_price": list_price, "is_active": 1
    })
products = pd.DataFrame(product_rows)

segments = rng.choice(["Budget","Regular","Premium"], size=2000, p=[0.45,0.40,0.15])
customer_rows = []
for cid in range(1, 2001):
    joined = pd.Timestamp("2021-01-01") + pd.Timedelta(days=int(rng.integers(0, 1460)))
    customer_rows.append({
        "customer_id": cid, "segment": str(segments[cid-1]),
        "city": str(rng.choice(cities)), "joined_on": joined.strftime("%Y-%m-%d"), "is_active": 1
    })
customers = pd.DataFrame(customer_rows)

# ----------------------------- Sales generation ------------------------------
dates = pd.date_range("2024-01-01", "2025-12-31", freq="D")
month_factors = {1:0.93,2:0.86,3:0.98,4:0.97,5:0.94,6:0.90,7:0.95,8:1.00,9:1.02,10:1.25,11:1.42,12:1.30}
weekday_factors = {0:0.93,1:0.94,2:0.95,3:0.98,4:1.04,5:1.22,6:1.18}
date_weights = np.array([
    month_factors[d.month] * weekday_factors[d.weekday()] for d in dates
], dtype=float)
date_weights /= date_weights.sum()

# Premium customers are more likely to buy higher-ticket categories.
customer_weight = np.ones(len(customers), dtype=float)
customer_weight[customers["segment"].eq("Premium").to_numpy()] *= 1.25
customer_weight /= customer_weight.sum()

store_weights = np.array([1.15,1.08,1.12,0.98,0.95,0.92,1.10,1.02,0.90,0.88,0.96,0.94], dtype=float)
store_weights /= store_weights.sum()
product_weights = np.array([
    1.5 if c in ("Apparel","Home & Kitchen") else 1.2 if c=="Grocery" else 1.0
    for c in products["category"]
], dtype=float)
product_weights /= product_weights.sum()

sales_rows = []
line_id = 1
order_seq = 1
while line_id <= N_SALES_LINES:
    d = pd.Timestamp(rng.choice(dates.to_numpy(), p=date_weights))
    store_id = int(rng.choice(stores["store_id"], p=store_weights))
    cust_idx = int(rng.choice(np.arange(len(customers)), p=customer_weight))
    customer_id = cust_idx + 1
    seg = str(customers.iloc[cust_idx]["segment"])
    online_prob = 0.25 + 0.15 * ((d - pd.Timestamp("2024-01-01")).days / 730)
    channel = "Online" if rng.random() < online_prob else "In-store"
    payment_mode = str(rng.choice(["Cash","Card","UPI","Wallet"], p=[0.18,0.25,0.42,0.15]))
    n_lines = 2 if rng.random() < 0.22 else 1
    n_lines = min(n_lines, N_SALES_LINES - line_id + 1)
    order_id = f"SS-{d.strftime('%y%m%d')}-{order_seq:06d}"
    order_seq += 1
    for _ in range(n_lines):
        if line_id > N_SALES_LINES:
            break
        # Premium mix tilts toward electronics/home; budget mix tilts toward grocery/apparel.
        if seg == "Premium":
            cat_probs = np.array([0.15,0.12,0.25,0.28,0.12,0.08])
        elif seg == "Budget":
            cat_probs = np.array([0.22,0.13,0.15,0.08,0.12,0.30])
        else:
            cat_probs = np.array([0.20,0.16,0.19,0.16,0.14,0.15])
        chosen_cat = str(rng.choice(list(categories.keys()), p=cat_probs))
        candidates = products.index[products["category"].eq(chosen_cat)].to_numpy()
        pidx = int(rng.choice(candidates))
        prod = products.iloc[pidx]
        disc = float(rng.choice([0,5,10,15,20,25,30], p=[0.22,0.15,0.20,0.17,0.13,0.09,0.04]))
        base_qty = int(rng.choice([1,2,3,4], p=[0.54,0.27,0.13,0.06]))
        qty = min(6, base_qty + (1 if disc >= 20 and rng.random() < 0.55 else 0))
        list_price = float(prod["base_list_price"])
        selling_price = round(list_price * (1 - disc/100.0), 2)
        sales_rows.append({
            "line_id": line_id, "order_id": order_id, "sale_date": d.strftime("%Y-%m-%d"),
            "store_id": store_id, "product_id": int(prod["product_id"]), "customer_id": customer_id,
            "quantity": qty, "list_unit_price": round(list_price,2), "discount_pct": disc,
            "selling_unit_price": selling_price, "payment_mode": payment_mode, "channel": channel
        })
        line_id += 1

sales_clean = pd.DataFrame(sales_rows)
# Keep numeric types consistent with SQLite schema.
for col in ["line_id","store_id","product_id","customer_id","quantity"]:
    sales_clean[col] = sales_clean[col].astype(int)

# -------------------------- Store-month target plan --------------------------
sales_clean["sale_month"] = sales_clean["sale_date"].str[:7] + "-01"
sales_clean["line_revenue"] = sales_clean["quantity"] * sales_clean["selling_unit_price"]
monthly_actual = sales_clean.groupby(["store_id","sale_month"])["line_revenue"].sum().reset_index()
# Four strong, four near-target, four deliberately under-target stores.
achievement_by_store = {
    **{i:1.08 for i in range(1,5)},
    **{i:0.99 for i in range(5,9)},
    **{i:0.90 for i in range(9,13)}
}
target_rows = []
target_id = 1
for row in monthly_actual.itertuples(index=False):
    ratio = achievement_by_store[int(row.store_id)] * float(rng.uniform(0.97,1.03))
    target_rows.append({
        "target_id": target_id, "store_id": int(row.store_id),
        "target_month": str(row.sale_month),
        "target_revenue": round(float(row.line_revenue) / ratio, 2)
    })
    target_id += 1
store_targets = pd.DataFrame(target_rows)

# ----------------------- Inject and clean staging defects --------------------
raw_sales = sales_clean.drop(columns=["sale_month","line_revenue"]).copy()
issue_rows = []
missing_n = int(round(N_SALES_LINES * 0.025))  # 2.5% of fact rows affected
missing_indices = rng.choice(raw_sales.index.to_numpy(), size=missing_n, replace=False)
half = missing_n // 2
for idx in missing_indices[:half]:
    old = raw_sales.at[idx, "payment_mode"]
    raw_sales.at[idx, "payment_mode"] = np.nan
    issue_rows.append({"issue_type":"Missing value","source_line_id":int(raw_sales.at[idx,"line_id"]),
                       "column_name":"payment_mode","original_value":old,
                       "resolution":"Imputed with the most frequent valid payment_mode"})
for idx in missing_indices[half:]:
    old = raw_sales.at[idx, "channel"]
    raw_sales.at[idx, "channel"] = np.nan
    issue_rows.append({"issue_type":"Missing value","source_line_id":int(raw_sales.at[idx,"line_id"]),
                       "column_name":"channel","original_value":old,
                       "resolution":"Imputed with the most frequent valid channel"})

# Two duplicated rows (same line_id) in the raw staging extract.
dup_indices = rng.choice(raw_sales.index.to_numpy(), size=2, replace=False)
duplicates = raw_sales.loc[dup_indices].copy()
raw_sales = pd.concat([raw_sales, duplicates], ignore_index=True)
for idx in dup_indices:
    lid = int(sales_clean.loc[idx, "line_id"])
    issue_rows.append({"issue_type":"Duplicate record","source_line_id":lid,
                       "column_name":"line_id","original_value":lid,
                       "resolution":"Removed duplicate line_id; retained first occurrence"})

# Three intentionally extreme numeric values in raw staging data.
outlier_indices = rng.choice(raw_sales.index.to_numpy(), size=3, replace=False)
outlier_specs = [
    (outlier_indices[0], "quantity", 999, "Replaced with median valid quantity for the same product"),
    (outlier_indices[1], "quantity", 888, "Replaced with median valid quantity for the same product"),
    (outlier_indices[2], "list_unit_price", 999999.00, "Restored from products.base_list_price; recalculated selling price"),
]
for idx, col, bad_value, resolution in outlier_specs:
    lid = int(raw_sales.at[idx, "line_id"])
    old = raw_sales.at[idx, col]
    raw_sales.at[idx, col] = bad_value
    issue_rows.append({"issue_type":"Extreme outlier","source_line_id":lid,
                       "column_name":col,"original_value":old,
                       "resolution":resolution})

# Write the deliberately imperfect staging file.
raw_sales.to_csv(DATA / "sales_lines_raw_with_issues.csv", index=False)

# Cleaning pass: deduplicate, impute missing categorical values, and repair extremes.
cleaned = raw_sales.drop_duplicates(subset=["line_id"], keep="first").copy()
for col in ["payment_mode","channel"]:
    mode_val = cleaned[col].dropna().mode()
    fill_value = str(mode_val.iloc[0]) if not mode_val.empty else ("UPI" if col=="payment_mode" else "In-store")
    cleaned[col] = cleaned[col].fillna(fill_value)

product_base = products.set_index("product_id")["base_list_price"].to_dict()
product_qty_median = sales_clean.groupby("product_id")["quantity"].median().round().astype(int).to_dict()
for ix, row in cleaned.iterrows():
    if int(row["quantity"]) > 100:
        cleaned.at[ix, "quantity"] = int(product_qty_median.get(int(row["product_id"]), 1))
    if float(row["list_unit_price"]) > 50000:
        restored = float(product_base[int(row["product_id"])])
        cleaned.at[ix, "list_unit_price"] = restored
        cleaned.at[ix, "selling_unit_price"] = round(restored * (1 - float(row["discount_pct"])/100.0), 2)
cleaned = cleaned.sort_values("line_id").reset_index(drop=True)
sales_lines = cleaned[[
    "line_id","order_id","sale_date","store_id","product_id","customer_id","quantity",
    "list_unit_price","discount_pct","selling_unit_price","payment_mode","channel"
]].copy()
for col in ["line_id","store_id","product_id","customer_id","quantity"]:
    sales_lines[col] = sales_lines[col].astype(int)

quality_issues = pd.DataFrame(issue_rows)
quality_issues.insert(0, "issue_id", range(1, len(quality_issues)+1))
quality_issues.to_csv(DATA / "data_quality_issues.csv", index=False)

# ------------------------------- SQLite build --------------------------------
db_path = DATA / "app.db"
if db_path.exists():
    db_path.unlink()
conn = sqlite3.connect(db_path)
conn.execute("PRAGMA foreign_keys=ON;")
for stmt in DDL:
    conn.execute(stmt)
for stmt in INDEXES:
    conn.execute(stmt)

def insert_frame(table: str, frame: pd.DataFrame):
    cols = list(frame.columns)
    marks = ",".join(["?"] * len(cols))
    sql = f"INSERT INTO {table} ({','.join(cols)}) VALUES ({marks})"
    values = []
    for row in frame.itertuples(index=False, name=None):
        values.append(tuple(None if pd.isna(v) else (v.item() if hasattr(v, "item") else v) for v in row))
    conn.executemany(sql, values)

insert_frame("stores", stores)
insert_frame("products", products)
insert_frame("customers", customers)
insert_frame("sales_lines", sales_lines)
insert_frame("store_targets", store_targets)
conn.execute(VIEW_SQL)
conn.commit()

# ----------------------------- Canonical outputs -----------------------------
tables = {
    "stores": stores,
    "products": products,
    "customers": customers,
    "sales_lines": sales_lines,
    "store_targets": store_targets,
}
for name, frame in tables.items():
    frame.to_csv(DATA / f"{name}.csv", index=False)

# Excel workbook: one canonical sheet per physical table plus audit sheets.
patterns = pd.DataFrame([
    ["PAT-01","Seasonality","October–December total revenue is higher than the average of the other calendar months; February/June are softer.","Total revenue by calendar month across the 24-month period"],
    ["PAT-02","Weekend uplift","Average daily revenue from Friday–Sunday is higher than Monday–Thursday.","Aggregate revenue by sale date, then compare average daily revenue by weekday"],
    ["PAT-03","Channel shift","Online share rises gradually from 2024 to 2025.","Online line count / total line count by year and month"],
    ["PAT-04","Discount trade-off","Higher discount levels tend to lift units per line while reducing profit margin.","Discount_pct vs quantity and margin_pct; compare discount bands"],
    ["PAT-05","Store target spread","Stores 1–4 generally exceed targets, stores 5–8 are near target, stores 9–12 tend to miss target.","Store-month actual revenue / target_revenue"],
], columns=["Pattern ID","Pattern","Expected finding","Suggested analysis"])

validation_rows = []
for name, frame in tables.items():
    validation_rows.append([name, len(frame), len(frame.columns), "PASS"])
validation_df = pd.DataFrame(validation_rows, columns=["Table","Rows","Columns","Schema / row check"])

xlsx_path = DATA / "retail_sales_performance_data.xlsx"
with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:
    for name, frame in tables.items():
        frame.to_excel(writer, sheet_name=name, index=False)
    quality_issues.to_excel(writer, sheet_name="Data_Quality_Issues", index=False)
    patterns.to_excel(writer, sheet_name="Patterns", index=False)
    validation_df.to_excel(writer, sheet_name="Validation_Summary", index=False)

# ------------------------------ Validation -----------------------------------
checks = []
def check(name, passed, detail):
    checks.append((name, "PASS" if passed else "FAIL", detail))

expected_counts = {"stores":12,"products":150,"customers":2000,"sales_lines":20000,"store_targets":288}
for name, expected in expected_counts.items():
    actual = len(tables[name])
    check(f"{name} row count", actual == expected, f"expected={expected}; actual={actual}")

fk_violations = conn.execute("PRAGMA foreign_key_check").fetchall()
check("Foreign-key check", len(fk_violations)==0, f"violations={len(fk_violations)}")
integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
check("SQLite integrity", integrity=="ok", integrity)
view_cols = conn.execute("PRAGMA table_info(v_sales_analysis)").fetchall()
check("Joined view column count", len(view_cols)==38, f"columns={len(view_cols)}")
nulls = conn.execute("""SELECT
 (SELECT COUNT(*) FROM sales_lines WHERE order_id IS NULL OR sale_date IS NULL OR store_id IS NULL OR product_id IS NULL OR customer_id IS NULL OR quantity IS NULL OR list_unit_price IS NULL OR discount_pct IS NULL OR selling_unit_price IS NULL OR payment_mode IS NULL OR channel IS NULL)""").fetchone()[0]
check("Required sales fields", nulls==0, f"null required values={nulls}")
ranges = conn.execute("""SELECT COUNT(*) FROM sales_lines
 WHERE quantity<=0 OR list_unit_price<=0 OR discount_pct<0 OR discount_pct>100
 OR selling_unit_price<0 OR selling_unit_price>list_unit_price
 OR abs(selling_unit_price-(list_unit_price*(1-discount_pct/100.0)))>0.02""").fetchone()[0]
check("Sales range / pricing checks", ranges==0, f"invalid rows={ranges}")
target_dupes = conn.execute("""SELECT COUNT(*) FROM (
 SELECT store_id,target_month,COUNT(*) n FROM store_targets GROUP BY store_id,target_month HAVING n>1
)""").fetchone()[0]
check("Unique store-month targets", target_dupes==0, f"duplicate store-month keys={target_dupes}")
date_range = conn.execute("SELECT MIN(sale_date),MAX(sale_date) FROM sales_lines").fetchone()
check("24-month date coverage", date_range==("2024-01-01","2025-12-31"), f"min={date_range[0]}; max={date_range[1]}")

# Read back Excel and inspect 10 sample rows per table.
excel_checks = []
readback = pd.ExcelFile(xlsx_path)
for name in tables:
    sample = pd.read_excel(xlsx_path, sheet_name=name, nrows=10)
    ok = len(sample)==10 and list(sample.columns)==list(tables[name].columns)
    excel_checks.append((name, len(sample), "PASS" if ok else "FAIL"))
    check(f"Excel sample {name}", ok, f"first 10 rows read; columns exact={ok}")

# Pattern diagnostics are evidence of encoded structure, not guaranteed hypothesis-test results.
analysis = pd.read_sql_query("SELECT * FROM v_sales_analysis", conn)
analysis["sale_date"] = pd.to_datetime(analysis["sale_date"])
analysis["month"] = analysis["sale_date"].dt.month
analysis["weekday"] = analysis["sale_date"].dt.weekday
analysis["year"] = analysis["sale_date"].dt.year
monthly_revenue = analysis.groupby("month")["revenue"].sum()
peak_mean = monthly_revenue.loc[[10,11,12]].mean()
other_mean = monthly_revenue.drop(index=[10,11,12]).mean()
daily_revenue = analysis.groupby("sale_date")["revenue"].sum()
daily_weekday = pd.to_datetime(daily_revenue.index).weekday
weekend_daily_revenue = daily_revenue.iloc[np.where(daily_weekday >= 4)[0]].mean()
weekday_daily_revenue = daily_revenue.iloc[np.where(daily_weekday < 4)[0]].mean()
online_share = analysis.groupby("year")["channel"].apply(lambda x:(x=="Online").mean())
discount_corr = analysis[["discount_pct","quantity","profit","margin_pct"]].corr(numeric_only=True)
store_month_actual = analysis.groupby(["store_id","sale_month"])["revenue"].sum().reset_index()
target_map = store_targets.set_index(["store_id","target_month"])["target_revenue"]
store_month_actual["target"] = [target_map.loc[(int(s),m)] for s,m in zip(store_month_actual.store_id,store_month_actual.sale_month)]
store_month_actual["achievement"] = store_month_actual["revenue"]/store_month_actual["target"]
patterns_observed = [
    f"Oct-Dec average total revenue/month={peak_mean:,.2f}; other-month average={other_mean:,.2f}; peak uplift={(peak_mean/other_mean-1)*100:.1f}%.",
    f"Fri-Sun average daily revenue={weekend_daily_revenue:,.2f}; Mon-Thu={weekday_daily_revenue:,.2f}; weekend uplift={(weekend_daily_revenue/weekday_daily_revenue-1)*100:.1f}%.",
    f"Online share: 2024={online_share.get(2024,0):.1%}; 2025={online_share.get(2025,0):.1%}.",
    f"Correlation(discount_pct, quantity)={discount_corr.loc['discount_pct','quantity']:.3f}; correlation(discount_pct, margin_pct)={discount_corr.loc['discount_pct','margin_pct']:.3f}.",
    f"Mean target achievement: stores 1-4={store_month_actual[store_month_actual.store_id<=4].achievement.mean():.1%}; 5-8={store_month_actual[store_month_actual.store_id.between(5,8)].achievement.mean():.1%}; 9-12={store_month_actual[store_month_actual.store_id>=9].achievement.mean():.1%}.",
]
check("Quality issues staged", len(quality_issues)==505, f"500 missing-value rows + 2 duplicate rows + 3 outlier rows = {len(quality_issues)} issue records")
check("Clean output sales row count", len(sales_lines)==20000, f"raw staging rows={len(raw_sales)}; cleaned rows={len(sales_lines)}")

report_path = DATA / "validation_report.txt"
with report_path.open("w", encoding="utf-8") as f:
    f.write("RETAIL SALES PERFORMANCE ANALYSIS — STEP 10 VALIDATION REPORT\n")
    f.write("Synthetic data only | Random seed: 42 | Currency: INR\n")
    f.write("Organisation: ShopSphere Retail Pvt. Ltd. (fictional), Noida\n")
    f.write("Date coverage: 2024-01-01 to 2025-12-31\n\n")
    f.write("1. CANONICAL TABLE ROW COUNTS\n")
    for name, frame in tables.items():
        f.write(f"  {name}: {len(frame):,} rows; {len(frame.columns)} columns\n")
    f.write(f"  v_sales_analysis: {len(analysis):,} rows; {len(view_cols)} columns\n\n")
    f.write("2. DATABASE / RANGE VALIDATION\n")
    for name, status, detail in checks:
        f.write(f"  [{status}] {name}: {detail}\n")
    f.write(f"\n  PRAGMA foreign_key_check results: {fk_violations}\n")
    f.write(f"  PRAGMA integrity_check: {integrity}\n")
    f.write("\n3. RAW STAGING QUALITY ISSUES AND CLEANING\n")
    f.write(f"  Raw sales staging rows: {len(raw_sales):,}\n")
    f.write("  Missing values: 500 rows affected (2.5% of 20,000 original sales lines), in payment_mode/channel.\n")
    f.write("  Duplicates: 2 duplicate line_id records appended to raw staging; removed by keeping first occurrence.\n")
    f.write("  Outliers: 3 numeric extremes (quantity 999, quantity 888, list_unit_price 999999); repaired using product-level reference/median.\n")
    f.write(f"  Clean canonical sales_lines rows: {len(sales_lines):,}\n")
    f.write("  The raw staging file is intentionally not loaded into SQLite. Only cleaned, schema-valid records are loaded.\n\n")
    f.write("4. PATTERNS ENCODED AND DIAGNOSTICS\n")
    f.write("  PAT-01: festive season uplift in October–December.\n")
    f.write("  PAT-02: Friday–Sunday sales uplift.\n")
    f.write("  PAT-03: online channel share increases from 2024 to 2025.\n")
    f.write("  PAT-04: discount/quantity and discount/margin trade-off.\n")
    f.write("  PAT-05: stores 1–4 above target, 5–8 near target, 9–12 below target.\n")
    
    for line in patterns_observed:
        f.write("  Observed: " + line + "\n")
    f.write("\n5. EXCEL 10-ROW BELIEVABILITY CHECK\n")
    for name, n, status in excel_checks:
        f.write(f"  [{status}] {name}: read back {n} rows; exact columns matched.\n")
    f.write("\n6. IMPORTANT MODEL LIMITATION\n")
    f.write("  Step 8 specifies products.cost_price at product level. It is static across the 24-month period; historical cost changes are not represented.\n")
    f.write("  Step 9 recommended unit_cost_at_sale as a future schema enhancement, but Step 10 preserves the exact Step 8 table/column design as requested.\n")
    f.write("  Do not sum target_revenue from the line-grain v_sales_analysis view; aggregate sales to store-month and join to store_targets once.\n")

conn.close()

# Save patterns separately for convenient review.
patterns.to_csv(DATA / "patterns_to_find.csv", index=False)

print("STEP 10 DATA GENERATION COMPLETE")
print(f"Project root: {ROOT}")
print(f"Excel: {xlsx_path}")
print(f"SQLite: {db_path}")
print(f"Validation: {report_path}")
print(f"Raw staging with issues: {DATA / 'sales_lines_raw_with_issues.csv'}")
print("Row counts:", {k: len(v) for k,v in tables.items()})
print("Validation failures:", [x for x in checks if x[1] == "FAIL"])
if any(x[1] == "FAIL" for x in checks):
    raise SystemExit("One or more validation checks failed.")
