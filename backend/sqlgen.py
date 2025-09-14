import re
from typing import Dict, Any

def generate_sql_and_chart(question: str) -> Dict[str, Any]:
    q = question.lower().strip()

    # Helper: extract "top N" if present; default = 5 (for top lists)
    m = re.search(r"top\s*(\d+)", q)
    topn = int(m.group(1)) if m else 5

    # ---- TIME / TREND ----
    if ("monthly" in q) or ("per month" in q) or ("by month" in q) or ("trend" in q):
        return {
            "sql": """
SELECT STRFTIME('%Y-%m', o.OrderDate) AS month,
       ROUND(SUM(od.UnitPrice*od.Quantity*(1-od.Discount)),2) AS revenue
FROM Orders o
JOIN OrderDetails od ON od.OrderID=o.OrderID
GROUP BY 1
ORDER BY 1;
""".strip(),
            "chart": {
                "kind": "line",
                "xField": "month",
                "yField": "revenue",
                "title": "Monthly Sales",
                "subtitle": "Northwind • USD"
            },
            "forecast": ("forecast" in q or "next" in q),
            "periods": 3,
            "insight": "Monthly revenue trend with optional forecast.",
        }

    # ---- COUNTRY MIX (explicit pie support) ----
    if ("share" in q) or ("by country" in q) or ("country" in q and "pie" in q):
        return {
            "sql": """
SELECT c.Country AS country,
       ROUND(SUM(od.UnitPrice*od.Quantity*(1-od.Discount)),2) AS revenue
FROM Orders o
JOIN Customers c ON c.CustomerID=o.CustomerID
JOIN OrderDetails od ON od.OrderID=o.OrderID
GROUP BY c.Country
ORDER BY revenue DESC;
""".strip(),
            "chart": {
                "kind": "pie",
                "xField": "country",
                "yField": "revenue",
                "title": "Sales by Country",
                "subtitle": "Northwind • USD"
            },
            "insight": "Country mix of revenue with % shares.",
        }

    # ---- CATEGORY MIX (pie) ----
    if ("category" in q) and (("share" in q) or ("pie" in q) or ("by category" in q)):
        return {
            "sql": """
SELECT c.CategoryName AS category,
       ROUND(SUM(od.UnitPrice*od.Quantity*(1-od.Discount)),2) AS revenue
FROM Orders o
JOIN OrderDetails od ON od.OrderID=o.OrderID
JOIN Products p ON p.ProductID=od.ProductID
JOIN Categories c ON c.CategoryID=p.CategoryID
GROUP BY c.CategoryName
ORDER BY revenue DESC;
""".strip(),
            "chart": {
                "kind": "pie",
                "xField": "category",
                "yField": "revenue",
                "title": "Revenue Share by Category",
                "subtitle": "Northwind • USD"
            },
            "insight": "Category mix of revenue with % shares.",
        }

    # ---- CUSTOMERS (bar by default; pie if asked) ----
    if "customer" in q or "customers" in q:
        want_pie = ("pie" in q) or ("share" in q)
        return {
            "sql": f"""
SELECT c.CompanyName AS customer,
       ROUND(SUM(od.UnitPrice*od.Quantity*(1-od.Discount)),2) AS revenue
FROM Orders o
JOIN Customers c ON c.CustomerID=o.CustomerID
JOIN OrderDetails od ON od.OrderID=o.OrderID
GROUP BY c.CompanyName
ORDER BY revenue DESC
LIMIT {topn};
""".strip(),
            "chart": {
                "kind": "pie" if want_pie else "bar",
                "xField": "customer",
                "yField": "revenue",
                "title": (f"Top {topn} Customers by Revenue" if not want_pie else f"Revenue Share • Top {topn} Customers"),
                "subtitle": "Northwind • USD"
            },
            "insight": (f"Top {topn} customers by revenue." if not want_pie else f"Top {topn} customers as a revenue share."),
        }

    # ---- PRODUCTS (bar by default; pie if asked) ----
    if "product" in q or "products" in q:
        want_pie = ("pie" in q) or ("share" in q)
        return {
            "sql": f"""
SELECT p.ProductName AS product,
       ROUND(SUM(od.UnitPrice*od.Quantity*(1-od.Discount)),2) AS revenue
FROM Orders o
JOIN OrderDetails od ON od.OrderID=o.OrderID
JOIN Products p ON p.ProductID=od.ProductID
GROUP BY p.ProductName
ORDER BY revenue DESC
LIMIT {topn};
""".strip(),
            "chart": {
                "kind": "pie" if want_pie else "bar",
                "xField": "product",
                "yField": "revenue",
                "title": (f"Top {topn} Products by Revenue" if not want_pie else f"Revenue Share • Top {topn} Products"),
                "subtitle": "Northwind • USD"
            },
            "insight": (f"Top {topn} products by revenue." if not want_pie else f"Top {topn} products as a revenue share."),
        }

    # ---- EMPLOYEES (bar) ----
    if "employee" in q or "salesperson" in q or "rep" in q:
        return {
            "sql": f"""
SELECT (e.FirstName || ' ' || e.LastName) AS employee,
       ROUND(SUM(od.UnitPrice*od.Quantity*(1-od.Discount)),2) AS revenue
FROM Orders o
JOIN Employees e ON e.EmployeeID=o.EmployeeID
JOIN OrderDetails od ON od.OrderID=o.OrderID
GROUP BY employee
ORDER BY revenue DESC
LIMIT {topn};
""".strip(),
            "chart": {
                "kind": "bar",
                "xField": "employee",
                "yField": "revenue",
                "title": f"Top {topn} Employees by Sales",
                "subtitle": "Northwind • USD"
            },
            "insight": f"Top {topn} employees by total sales.",
        }

    # ---- DEFAULT (top products bar) ----
    return {
        "sql": """
SELECT p.ProductName AS item,
       ROUND(SUM(od.UnitPrice*od.Quantity*(1-od.Discount)),2) AS revenue
FROM Orders o
JOIN OrderDetails od ON od.OrderID=o.OrderID
JOIN Products p ON p.ProductID=od.ProductID
GROUP BY p.ProductName
ORDER BY revenue DESC
LIMIT 10;
""".strip(),
        "chart": {
            "kind": "bar",
            "xField": "item",
            "yField": "revenue",
            "title": "Top Items",
            "subtitle": "Northwind • USD"
        },
        "insight": "Top items by revenue.",
    }
