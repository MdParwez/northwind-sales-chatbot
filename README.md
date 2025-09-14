
---

# 🛒 Northwind Sales Chatbot

An **AI-powered chatbot** that interacts with the classic **Northwind Sales Database**, enabling users to ask natural language questions about sales, products, customers, and orders. The chatbot translates user queries into SQL (via LLM) and returns accurate business insights in real-time.

---

## ✨ Features

✅ **Natural Language Queries** – Ask questions like *"Which product sold the most in Q2?"* or *"Top 5 customers by revenue last year"*
✅ **Conversational AI** – Uses LLMs to understand and respond intelligently
✅ **Database Integration** – Connects to the Northwind database for live data retrieval
✅ **Sales Insights** – Generate KPIs, trends, and visual summaries
✅ **User-friendly UI** – Chat interface for easy interaction
✅ **Extensible** – Can plug into other databases or APIs with minimal changes

---

## 🏗️ Tech Stack

* **Backend**: Python (FastAPI / Flask)
* **Frontend**: React + Tailwind (chat UI)
* **Database**: Northwind SQL (SQLite / SQL Server / PostgreSQL)
* **AI Layer**: LLM (OpenAI / Groq / custom adapter)
* **Authentication**: Optional (JWT/OAuth)
* **Deployment**: Docker + GitHub Actions CI/CD

---

## 🚀 Getting Started

### 1️⃣ Clone the repo

```bash
git clone https://github.com/your-username/northwind-sales-chatbot.git
cd northwind-sales-chatbot
```

### 2️⃣ Install dependencies

```bash
# Backend
cd backend
pip install -r requirements.txt

# Frontend
cd frontend
npm install
```

### 3️⃣ Setup environment

Create a `.env` file in the backend folder:

```env
OPENAI_API_KEY=your_api_key_here
DATABASE_URL=sqlite:///northwind.db
```

### 4️⃣ Run locally

```bash
# Backend
uvicorn main:app --reload

# Frontend
npm run dev
```

App will be available at **[http://localhost:3000](http://localhost:3000)** 🎉

---

## 💡 Example Queries

* *"Show me the top 10 best-selling products"*
* *"Who are the top 5 customers in 1997?"*
* *"What was the monthly revenue trend last year?"*
* *"Which salesperson closed the highest number of orders?"*

---

## 📊 Sample Output

✅ Natural language → SQL → Insight

> **Query:** "Top 5 customers by sales in 1997"
> **SQL Generated:**
>
> ```sql
> SELECT c.CompanyName, SUM(od.Quantity * od.UnitPrice) AS TotalSales
> FROM Orders o
> JOIN Customers c ON o.CustomerID = c.CustomerID
> JOIN [Order Details] od ON o.OrderID = od.OrderID
> WHERE strftime('%Y', o.OrderDate) = '1997'
> GROUP BY c.CompanyName
> ORDER BY TotalSales DESC
> LIMIT 5;
> ```
>
> **Result:** Table + chart with top customers

---
