import csv
import io
import random
from datetime import date, timedelta

HEADER: list[str] = [
    "Order ID",
    "Order Date",
    "Customer Name",
    "Product Category",
    "Revenue",
    "Cost",
    "Region",
]

CUSTOMERS: list[tuple[str, float]] = [
    ("Northwind Retail", 1.9),
    ("Acme Industrial", 1.6),
    ("Bluepeak Logistics", 1.3),
    ("Harborline Foods", 1.1),
    ("Vertex Software", 1.0),
    ("Copperfield Group", 0.9),
    ("Lakeside Clinics", 0.8),
    ("Summit Outdoors", 0.7),
    ("Ridgeway Motors", 0.6),
    ("Orchard & Vine", 0.5),
    ("Beacon Media", 0.4),
    ("Ironwood Supply", 0.3),
]

PRODUCTS: list[tuple[str, float, float]] = [
    ("Enterprise Licence", 2400.0, 900.0),
    ("Professional Licence", 950.0, 260.0),
    ("Hardware Bundle", 1750.0, 520.0),
    ("Onboarding Services", 640.0, 180.0),
    ("Support Retainer", 420.0, 90.0),
    ("Training Workshop", 310.0, 70.0),
]

REGIONS: list[str] = ["North", "South", "East", "West"]

# Cost as a share of revenue per product line, so profit analysis has real signal.
COST_RATIOS: dict[str, float] = {
    "Enterprise Licence": 0.42,
    "Professional Licence": 0.48,
    "Hardware Bundle": 0.74,
    "Onboarding Services": 0.61,
    "Support Retainer": 0.55,
    "Training Workshop": 1.06,
}

_DATE_FORMATS: list[str] = ["%Y-%m-%d", "%m/%d/%Y", "%b %d, %Y", "%d-%b-%Y"]


def _money_text(value: float, style: int) -> str:
    if style == 0:
        return f"${value:,.2f}"
    if style == 1:
        return f"{value:,.2f}"
    return f"{value:.2f}"


def demo_rows() -> list[list[str]]:
    """Build a realistic but deliberately messy sales export."""
    rng = random.Random(20240607)
    today = date.today()
    start = today - timedelta(days=365)
    rows: list[list[str]] = []
    order_no = 10248

    weights = [w for _, w in CUSTOMERS]
    for day_offset in range(0, 366):
        current = start + timedelta(days=day_offset)
        if current.weekday() >= 5 and rng.random() < 0.75:
            continue
        if rng.random() < 0.55:
            continue
        for _ in range(rng.randint(1, 2)):
            customer = rng.choices(CUSTOMERS, weights=weights, k=1)[0][0]
            product, base, spread = rng.choice(PRODUCTS)
            season = 1.0 + (day_offset / 365) * 0.35
            amount = max(45.0, rng.gauss(base * season, spread))
            ratio = COST_RATIOS.get(product, 0.6) * rng.uniform(0.92, 1.08)
            cost = max(10.0, amount * ratio)
            rows.append(
                [
                    f"ORD-{order_no}",
                    current.strftime(rng.choice(_DATE_FORMATS)),
                    customer,
                    product,
                    _money_text(round(amount, 2), rng.randint(0, 2)),
                    _money_text(round(cost, 2), rng.randint(0, 2)),
                    rng.choice(REGIONS),
                ]
            )
            order_no += 1

    # Two customers deliberately go quiet so retention analysis has signal.
    cutoff = int(len(rows) * 0.6)
    quiet = ("Beacon Media", "Ironwood Supply")
    rows = [
        row
        for index, row in enumerate(rows)
        if not (row[2] in quiet and index > cutoff)
    ]

    # Inject the kind of mess a real export contains.
    if len(rows) > 40:
        rows.insert(12, ["", "", "", "", "", "", ""])
        rows.insert(31, ["", "", "", "", "", "", ""])
        rows.insert(20, list(rows[19]))  # exact duplicate row
        rows.insert(45, list(rows[44]))  # exact duplicate row
        rows[8][1] = "not available"  # invalid date
        rows[27][1] = "??"  # invalid date
        rows[15][4] = "n/a"  # invalid revenue
        rows[38][4] = "pending"  # invalid revenue
        rows[52][2] = ""  # missing customer
        rows[60][6] = ""  # missing region

    return rows


def demo_csv_bytes() -> bytes:
    """Serialise the demo dataset as a CSV export, banner rows included."""
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(
        ["Northwind Analytics — Sales Export", "", "", "", "", "", ""]
    )
    writer.writerow(
        [
            f"Generated {date.today().strftime('%d %b %Y')}",
            "",
            "",
            "",
            "",
            "",
            "",
        ]
    )
    writer.writerow(HEADER)
    for row in demo_rows():
        writer.writerow(row)
    return buffer.getvalue().encode("utf-8")
