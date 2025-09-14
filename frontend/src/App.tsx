import React, { useRef, useState } from "react";
import { motion } from "framer-motion";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  LineChart,
  Line,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  CartesianGrid,
  LabelList,
} from "recharts";
import * as htmlToImage from "html-to-image";
import { Download, Copy, Image as ImageIcon, Moon, Sun, ChevronDown } from "lucide-react";

type ChartKind = "bar" | "line" | "pie";
type ChartSpec = {
  kind: ChartKind;
  xField: string;
  yField: string;
  data: Array<Record<string, any>>;
  title?: string;
  subtitle?: string;
};
type ApiReply = {
  chart: ChartSpec;
  insight: string;
  table?: { columns: string[]; rows: any[][] };
  meta?: { sql: string; elapsed_ms: number; row_count: number; forecast?: boolean; truncated?: boolean; used_llm?: boolean };
};
type ChatMessage = { role: "user"; content: string } | { role: "assistant"; reply: ApiReply };

function cn(...classes: Array<string | false | undefined>) { return classes.filter(Boolean).join(" "); }
function toCSV(columns: string[], rows: any[][]) {
  const header = columns.join(",");
  const body = rows.map(r =>
    r.map(v => {
      if (v == null) return "";
      const s = String(v).replace(/"/g, '""');
      return /[",\n]/.test(s) ? `"${s}"` : s;
    }).join(",")
  ).join("\n");
  return header + "\n" + body;
}
const COLORS = ["#2563eb","#10b981","#f59e0b","#ef4444","#8b5cf6","#14b8a6","#f97316","#06b6d4"];

function ChartRenderer({ spec }: { spec: ChartSpec }) {
  if (spec.kind === "bar") {
    return (
      <ResponsiveContainer width="100%" height={320}>
        <BarChart data={spec.data as any[]} margin={{ left: 8, right: 8, top: 8, bottom: 8 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey={spec.xField} tick={{ fontSize: 12 }} />
          <YAxis tick={{ fontSize: 12 }} />
          <Tooltip />
          <Legend />
          <Bar dataKey={spec.yField} radius={[6, 6, 0, 0]}>
            <LabelList dataKey={spec.yField} position="top" formatter={(v: any) => (typeof v === 'number' ? v.toLocaleString() : v)} />
            {(spec.data as any[]).map((_, i) => (<Cell key={i} fill={COLORS[i % COLORS.length]} />))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    );
  }
  if (spec.kind === "line") {
    const lineData = (spec.data as any[]);
    return (
      <ResponsiveContainer width="100%" height={320}>
        <LineChart data={lineData} margin={{ left: 8, right: 8, top: 8, bottom: 8 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey={spec.xField} tick={{ fontSize: 12 }} />
          <YAxis tick={{ fontSize: 12 }} />
          <Tooltip />
          <Legend />
          <Line type="monotone" dataKey="actual" stroke="#2563eb" strokeWidth={2} dot={{ r: 2 }} />
          <Line type="monotone" dataKey={spec.yField} stroke="#2563eb" strokeWidth={2} dot={{ r: 2 }} />
          <Line type="monotone" dataKey="forecast" stroke="#10b981" strokeDasharray="6 4" strokeWidth={2} dot={{ r: 2 }} />
        </LineChart>
      </ResponsiveContainer>
    );
  }
  const total = (spec.data as any[]).reduce((s, r: any) => s + Number(r[spec.yField] || 0), 0);
  return (
    <ResponsiveContainer width="100%" height={320}>
      <PieChart>
        <Tooltip formatter={(v: any) => (typeof v === 'number' ? v.toLocaleString() : v)} />
        <Legend />
        <Pie data={spec.data as any[]} dataKey={spec.yField} nameKey={spec.xField} outerRadius={110} innerRadius={40} paddingAngle={2}
          label={(d: any) => `${d[spec.xField]} ${(100 * (d.value / total)).toFixed(1)}%`}>
          {(spec.data as any[]).map((_: any, i: number) => (<Cell key={i} fill={COLORS[i % COLORS.length]} />))}
        </Pie>
      </PieChart>
    </ResponsiveContainer>
  );
}

function ChartCard({ reply }: { reply: ApiReply }) {
  const chartRef = useRef<HTMLDivElement>(null);
  const handleDownloadPNG = async () => {
    if (!chartRef.current) return;
    const dataUrl = await htmlToImage.toPng(chartRef.current);
    const a = document.createElement("a");
    a.href = dataUrl;
    a.download = (reply.chart.title || "chart").replace(/\s+/g, "-").toLowerCase() + ".png";
    a.click();
  };
  const handleCopySQL = async () => { if (reply.meta?.sql) await navigator.clipboard.writeText(reply.meta.sql); };
  const handleDownloadCSV = () => {
    if (!reply.table) return;
    const csv = toCSV(reply.table.columns, reply.table.rows);
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a"); a.href = url; a.download = "data.csv"; a.click(); URL.revokeObjectURL(url);
  };
  return (
    <div className="w-full bg-white dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 rounded-2xl shadow-sm overflow-hidden">
      <div className="flex items-center justify-between px-5 py-4 border-b border-zinc-100 dark:border-zinc-800">
        <div>
          <h3 className="text-zinc-900 dark:text-zinc-50 font-semibold">{reply.chart.title}</h3>
          {reply.chart.subtitle && (<p className="text-sm text-zinc-500 dark:text-zinc-400">{reply.chart.subtitle}</p>)}
        </div>
        <div className="flex items-center gap-2">
          <button onClick={handleCopySQL} title="Copy SQL" className="px-3 py-2 text-sm rounded-md bg-zinc-100 hover:bg-zinc-200 dark:bg-zinc-800 dark:hover:bg-zinc-700 text-zinc-800 dark:text-zinc-100 flex items-center gap-2"><Copy size={16} /> SQL</button>
          <button onClick={handleDownloadCSV} title="Download CSV" className="px-3 py-2 text-sm rounded-md bg-zinc-100 hover:bg-zinc-200 dark:bg-zinc-800 dark:hover:bg-zinc-700 text-zinc-800 dark:text-zinc-100 flex items-center gap-2"><Download size={16} /> CSV</button>
          <button onClick={handleDownloadPNG} title="Download chart as PNG" className="px-3 py-2 text-sm rounded-md bg-zinc-100 hover:bg-zinc-200 dark:bg-zinc-800 dark:hover:bg-zinc-700 text-zinc-800 dark:text-zinc-100 flex items-center gap-2"><ImageIcon size={16} /> PNG</button>
        </div>
      </div>
      <div ref={chartRef} className="px-3 pt-3 pb-4 bg-white dark:bg-zinc-900">
        <ChartRenderer spec={reply.chart} />
      </div>
      {reply.meta && (
        <div className="px-5 pb-4 text-xs text-zinc-500 dark:text-zinc-400">
          <span>Rows: {reply.meta.row_count}</span> · <span>Time: {reply.meta.elapsed_ms}ms</span> {reply.meta.used_llm ? "· LLM" : "· Heuristic"} {reply.meta.truncated ? "· (truncated)" : ""}
        </div>
      )}
    </div>
  );
}

function InsightCard({ insight }: { insight: string }) {
  return (
    <div className="w-full bg-gradient-to-br from-blue-50 to-emerald-50 dark:from-zinc-900 dark:to-zinc-900/40 border border-zinc-200 dark:border-zinc-800 rounded-2xl p-4">
      <p className="text-sm leading-6 text-zinc-800 dark:text-zinc-100">{insight}</p>
    </div>
  );
}

function DataAccordion({ table }: { table?: { columns: string[]; rows: any[][] } }) {
  const [open, setOpen] = useState(false);
  if (!table) return null;
  return (
    <div className="w-full">
      <button onClick={() => setOpen(v => !v)} className="mt-2 w-full flex items-center justify-between px-4 py-3 bg-zinc-50 hover:bg-zinc-100 dark:bg-zinc-900 dark:hover:bg-zinc-800 border border-zinc-200 dark:border-zinc-800 rounded-xl text-left">
        <span className="font-medium text-zinc-800 dark:text-zinc-100">View data</span>
        <ChevronDown className={cn("transition", open && "rotate-180")} size={18} />
      </button>
      {open && (
        <div className="mt-2 overflow-auto border border-zinc-200 dark:border-zinc-800 rounded-xl">
          <table className="min-w-full text-sm">
            <thead className="bg-zinc-100 dark:bg-zinc-800 text-zinc-800 dark:text-zinc-100">
              <tr>{table.columns.map((c, i) => (<th key={i} className="px-3 py-2 text-left font-semibold whitespace-nowrap">{c}</th>))}</tr>
            </thead>
            <tbody>
              {table.rows.map((r, i) => (
                <tr key={i} className={i % 2 ? "bg-white dark:bg-zinc-900" : "bg-zinc-50 dark:bg-zinc-950"}>
                  {r.map((v, j) => (<td key={j} className="px-3 py-2 text-zinc-700 dark:text-zinc-200 whitespace-nowrap">{typeof v === "number" ? v.toLocaleString() : String(v)}</td>))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

function UserBubble({ text }: { text: string }) {
  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.2 }} className="w-full flex justify-end">
      <div className="max-w-[75%] bg-blue-600 text-white rounded-2xl rounded-br-sm px-4 py-3 shadow">{text}</div>
    </motion.div>
  );
}

function AssistantBundle({ reply }: { reply: ApiReply }) {
  return (
    <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.25 }} className="w-full flex justify-start">
      <div className="max-w-[85%] flex flex-col gap-3">
        <ChartCard reply={reply} />
        <InsightCard insight={reply.insight} />
        <DataAccordion table={reply.table} />
      </div>
    </motion.div>
  );
}

export default function App() {
  const [dark, setDark] = useState(true);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const API_BASE = (import.meta as any).env?.VITE_API_BASE || "http://localhost:8000";

  async function send() {
    const q = input.trim();
    if (!q || loading) return;
    setInput("");
    setMessages(m => [...m, { role: "user", content: q }]);
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/chat`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ question: q }) });
      if (!res.ok) throw new Error(await res.text());
      const data = await res.json();
      setMessages(m => [...m, { role: "assistant", reply: data }]);
    } catch (e: any) {
      setMessages(m => [...m, { role:"assistant", reply: {
        chart: { kind:"bar", xField:"Message", yField:"Value", data:[{ Message:"Error", Value:1 }], title:"Oops", subtitle:"Backend error" },
        insight: String(e?.message || e),
        table: { columns:["error"], rows:[[String(e?.message || e)]] },
        meta: { sql:"", elapsed_ms:0, row_count:0 }
      }}]);
    } finally { setLoading(false); }
  }

  return (
    <div className={cn("min-h-screen w-full", dark && "dark")}>
      <div className="min-h-screen bg-zinc-50 dark:bg-zinc-950 text-zinc-900 dark:text-zinc-50">
        <header className="sticky top-0 z-10 backdrop-blur supports-[backdrop-filter]:bg-white/60 dark:supports-[backdrop-filter]:bg-zinc-950/60 bg-white/90 dark:bg-zinc-950/90 border-b border-zinc-200 dark:border-zinc-800">
          <div className="mx-auto max-w-6xl px-4 h-16 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="h-8 w-8 rounded-xl bg-gradient-to-br from-blue-600 to-emerald-500" />
              <div className="flex flex-col leading-tight">
                <span className="font-semibold">Northwind Sales Chatbot</span>
                <span className="text-xs text-zinc-500 dark:text-zinc-400">Conversational analytics • Recharts • Prophet</span>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <button onClick={() => setDark(d => !d)} className="px-3 py-2 text-sm rounded-md bg-zinc-100 hover:bg-zinc-200 dark:bg-zinc-800 dark:hover:bg-zinc-700 text-zinc-800 dark:text-zinc-100 flex items-center gap-2" title="Toggle theme">
                {dark ? <Sun size={16} /> : <Moon size={16} />}{dark ? "Light" : "Dark"}
              </button>
            </div>
          </div>
        </header>

        <main className="mx-auto max-w-6xl px-4 py-6">
          <div className="mb-5 flex flex-wrap gap-2">
            {["Top 5 products by revenue in 1997","Monthly sales 1997 and forecast next 3 months","Sales share by country (1997)","Top employees by sales this year"].map((s, i) => (
              <button onClick={() => setInput(s)} key={i} className="text-xs px-3 py-1 rounded-full bg-zinc-100 dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 text-zinc-700 dark:text-zinc-300">{s}</button>
            ))}
          </div>

          <div className="flex flex-col gap-4">
            {messages.map((m, i) => (m.role === "user" ? <UserBubble key={i} text={m.content} /> : <AssistantBundle key={i} reply={m.reply} />))}
            {loading && <div className="text-sm text-zinc-500">Thinking…</div>}
          </div>
        </main>

        <div className="sticky bottom-0 border-t border-zinc-200 dark:border-zinc-800 bg-white/90 dark:bg-zinc-950/90 backdrop-blur">
          <div className="mx-auto max-w-6xl px-4 py-3">
            <div className="flex items-center gap-2">
              <input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && send()}
                className="flex-1 h-11 rounded-xl px-4 bg-zinc-100 dark:bg-zinc-900 border border-zinc-200 dark:border-zinc-800 text-sm outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Type a question about sales…"
              />
              <button onClick={send} className="h-11 px-4 rounded-xl bg-blue-600 text-white text-sm font-medium disabled:opacity-50" disabled={loading || !input.trim()}>
                Send
              </button>
            </div>
         
          </div>
        </div>
      </div>
    </div>
  );
}