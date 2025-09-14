import sqlite3, os, urllib.request

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "northwind.sqlite")
JPWHITE3_SQL = "https://raw.githubusercontent.com/jpwhite3/northwind-SQLite3/master/Northwind.Sqlite3.create.sql"

MINI_SQL = """
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS Customers (
  CustomerID TEXT PRIMARY KEY,
  CompanyName TEXT,
  ContactName TEXT,
  Country TEXT
);
CREATE TABLE IF NOT EXISTS Employees (
  EmployeeID INTEGER PRIMARY KEY,
  LastName TEXT,
  FirstName TEXT
);
CREATE TABLE IF NOT EXISTS Products (
  ProductID INTEGER PRIMARY KEY,
  ProductName TEXT,
  CategoryID INTEGER
);
CREATE TABLE IF NOT EXISTS Orders (
  OrderID INTEGER PRIMARY KEY,
  CustomerID TEXT,
  EmployeeID INTEGER,
  OrderDate TEXT,
  FOREIGN KEY(CustomerID) REFERENCES Customers(CustomerID),
  FOREIGN KEY(EmployeeID) REFERENCES Employees(EmployeeID)
);
CREATE TABLE IF NOT EXISTS OrderDetails (
  OrderID INTEGER,
  ProductID INTEGER,
  UnitPrice REAL,
  Quantity INTEGER,
  Discount REAL,
  FOREIGN KEY(OrderID) REFERENCES Orders(OrderID),
  FOREIGN KEY(ProductID) REFERENCES Products(ProductID)
);

INSERT OR IGNORE INTO Customers VALUES
('ALFKI','Alfreds Futterkiste','Maria Anders','Germany'),
('ANATR','Ana Trujillo Emparedados y helados','Ana Trujillo','Mexico'),
('BERGS','Berglunds snabbköp','Christina Berglund','Sweden'),
('BLAUS','Blauer See Delikatessen','Hanna Moos','Germany');

INSERT OR IGNORE INTO Employees VALUES
(1,'Davolio','Nancy'),
(2,'Fuller','Andrew'),
(3,'Leverling','Janet');

INSERT OR IGNORE INTO Products VALUES
(1,'Chai',1),(2,'Chang',1),(3,'Aniseed Syrup',2),(4,'Ikura',2);

-- Simple monthly orders across 1997
INSERT OR IGNORE INTO Orders VALUES
(10001,'ALFKI',1,'1997-01-15'),
(10002,'ANATR',2,'1997-02-20'),
(10003,'BERGS',1,'1997-03-03'),
(10004,'ALFKI',3,'1997-04-18'),
(10005,'BLAUS',2,'1997-05-27'),
(10006,'ALFKI',1,'1997-06-04'),
(10007,'ANATR',2,'1997-07-12'),
(10008,'BERGS',3,'1997-08-22'),
(10009,'BLAUS',1,'1997-09-10'),
(10010,'ALFKI',2,'1997-10-08'),
(10011,'ANATR',1,'1997-11-19'),
(10012,'BERGS',3,'1997-12-05');

INSERT OR IGNORE INTO OrderDetails VALUES
(10001,1,18.0,120,0.00),
(10002,2,19.0,110,0.00),
(10003,3,10.0,130,0.00),
(10004,4,31.0,90,0.05),
(10005,1,18.0,140,0.00),
(10006,2,19.0,150,0.10),
(10007,3,10.0,160,0.00),
(10008,4,31.0,95,0.00),
(10009,1,18.0,170,0.00),
(10010,2,19.0,175,0.00),
(10011,3,10.0,180,0.00),
(10012,4,31.0,200,0.00);
"""

def ensure_db():
    if os.path.exists(DB_PATH):
        return
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    # Try: build from official script via Python executescript (no sqlite3 CLI dependency)
    try:
        print("Seeding Northwind (full) via jpwhite3 script...")
        sql_bytes = urllib.request.urlopen(JPWHITE3_SQL, timeout=20).read()
        sql = sql_bytes.decode("utf-8")
        conn = sqlite3.connect(DB_PATH)
        conn.executescript(sql)
        conn.commit()
        conn.close()
        print("Northwind DB created from script.")
        return
    except Exception as e:
        print("Full seed failed, falling back to mini demo dataset:", e)

    # Fallback: tiny demo dataset (works offline)
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(MINI_SQL)
    conn.commit()
    conn.close()
    print("Northwind mini demo DB created.")

def get_conn():
    ensure_db()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def run_query(sql: str, params: tuple = ()):
    conn = get_conn()
    try:
        cur = conn.execute(sql, params)
        rows = cur.fetchall()
        columns = [d[0] for d in cur.description]
        out_rows = [[row[c] for c in columns] for row in rows]
        return columns, out_rows
    finally:
        conn.close()

def get_schema():
    conn = get_conn()
    cur = conn.cursor()
    tables = ["Orders","OrderDetails","Products","Customers","Categories","Employees","Shippers","Suppliers"]
    schema = {}
    for t in tables:
        try:
            cur.execute(f'PRAGMA table_info("{t}")')
            cols = [r[1] for r in cur.fetchall()]
            if cols: schema[t] = cols
        except Exception:
            pass
    conn.close()
    return schema

import json
def schema_json():
    return json.dumps(get_schema(), indent=2)