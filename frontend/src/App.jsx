import React, { useEffect, useState } from "react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from "recharts";
import { api } from "./api.js";

const Card = ({ title, children }) => (
  <div className="bg-white rounded-xl shadow p-5 mb-5"><h2 className="font-semibold text-slate-700 mb-3">{title}</h2>{children}</div>);
const inp = "border rounded px-3 py-2 w-full";
const btn = "bg-blue-600 hover:bg-blue-700 text-white rounded px-4 py-2";

function Login({ onDone }) {
  const [f, setF] = useState({ username: "", password: "", hospital_id: "H1" }); const [reg, setReg] = useState(false); const [err, setErr] = useState("");
  const go = async () => { try {
    if (reg) await api("/auth/register", { method: "POST", body: f });
    const r = await api("/auth/login", { method: "POST", form: { username: f.username, password: f.password } });
    localStorage.setItem("token", r.access_token); onDone();
  } catch (e) { setErr(e.message); } };
  return (<div className="max-w-sm mx-auto mt-24"><Card title="MediTrust AI - Doctor Login">
    <input className={inp + " mb-2"} placeholder="Username" onChange={e => setF({ ...f, username: e.target.value })} />
    <input className={inp + " mb-2"} type="password" placeholder="Password" onChange={e => setF({ ...f, password: e.target.value })} />
    {reg && <input className={inp + " mb-2"} placeholder="Hospital ID (H1/H2/H3)" value={f.hospital_id} onChange={e => setF({ ...f, hospital_id: e.target.value })} />}
    {err && <p className="text-red-600 text-sm mb-2">{err}</p>}
    <button className={btn} onClick={go}>{reg ? "Register & Login" : "Login"}</button>
    <button className="ml-3 text-sm text-blue-600" onClick={() => setReg(!reg)}>{reg ? "Have an account?" : "New doctor?"}</button>
  </Card></div>);
}

const FIELDS = [["name", "Name", "text"], ["age", "Age"], ["sex", "Sex (1=M,0=F)"], ["cp", "Chest pain type (0-3)"],
  ["trestbps", "Blood pressure"], ["chol", "Cholesterol"], ["thalach", "Max heart rate"], ["restecg", "ECG result (0-2)"]];

function Patients({ onPredict }) {
  const [list, setList] = useState([]); const [f, setF] = useState({});
  const load = () => api("/patients").then(setList); useEffect(() => { load(); }, []);
  const add = async () => {
    const b = { ...f }; FIELDS.slice(1).forEach(([k]) => b[k] = Number(b[k] || 0));
    await api("/patients", { method: "POST", body: b }); setF({}); load(); };
  return (<Card title="Patients">
    <div className="grid grid-cols-4 gap-2 mb-3">{FIELDS.map(([k, l, t]) =>
      <input key={k} className={inp} placeholder={l} type={t || "number"} value={f[k] || ""} onChange={e => setF({ ...f, [k]: e.target.value })} />)}
      <button className={btn} onClick={add}>Add patient</button></div>
    <table className="w-full text-sm"><thead><tr className="text-left text-slate-500"><th>Name</th><th>Age</th><th>BP</th><th>Chol</th><th></th></tr></thead>
      <tbody>{list.map(p => <tr key={p.id} className="border-t"><td>{p.name}</td><td>{p.age}</td><td>{p.trestbps}</td><td>{p.chol}</td>
        <td><button className="text-blue-600" onClick={() => onPredict(p)}>Predict</button></td></tr>)}</tbody></table>
  </Card>);
}

function Prediction({ p, res, busy }) {
  if (busy) return <Card title="Prediction">Running model + SHAP...</Card>;
  if (!res) return <Card title="Prediction">Select a patient and click Predict.</Card>;
  const color = res.classification === "High Risk" ? "text-red-600" : res.classification === "Moderate Risk" ? "text-amber-600" : "text-green-600";
  return (<Card title={`Prediction - ${p.name}`}>
    <p className={`text-4xl font-bold ${color}`}>{res.risk_percent}% <span className="text-lg">{res.classification}</span></p>
    <p className="text-xs text-slate-500 mb-3">Model: {res.model_source} | Blockchain verified: {String(res.blockchain_verified)} | {res.latency_ms} ms</p>
    <h3 className="font-medium">Explainable AI (SHAP)</h3>
    <ResponsiveContainer width="100%" height={240}><BarChart data={res.explanation} layout="vertical">
      <XAxis type="number" /><YAxis type="category" dataKey="feature" width={80} /><Tooltip />
      <Bar dataKey="shap">{res.explanation.map((e, i) => <Cell key={i} fill={e.shap > 0 ? "#dc2626" : "#16a34a"} />)}</Bar></BarChart></ResponsiveContainer>
    <p className="text-xs text-slate-500">Red = increases risk, green = decreases. {res.explanation.slice(0, 3).map(e => `${e.feature}: ${e.impact}`).join(" | ")}</p>
  </Card>);
}

function Chain() {
  const [d, setD] = useState({ records: [] }); const [v, setV] = useState(null);
  useEffect(() => { api("/blockchain/logs").then(setD).catch(() => {}); }, []);
  return (<Card title={`Blockchain Verification (${d.mode || "-"})`}>
    <button className={btn + " mb-3"} onClick={() => api("/blockchain/verify").then(setV).catch(e => setV({ error: e.message }))}>Verify current global model</button>
    {v && <p className={v.verified ? "text-green-600" : "text-red-600"}>{v.error || (v.verified ? "VERIFIED" : "TAMPERED")} {v.hash && <code className="text-xs">{v.hash}</code>}</p>}
    <table className="w-full text-xs mt-2"><thead><tr className="text-left"><th>Ver</th><th>Hospital</th><th>Hash</th><th>Time</th></tr></thead>
      <tbody>{d.records.map(r => <tr key={r.id} className="border-t"><td>{r.version}</td><td>{r.hospitalId}</td>
        <td className="font-mono">{r.modelHash.slice(0, 20)}...</td><td>{new Date(r.timestamp * 1000).toLocaleString()}</td></tr>)}</tbody></table>
  </Card>);
}

function Analytics({ tick }) {
  const [a, setA] = useState(null); useEffect(() => { api("/analytics").then(setA); }, [tick]);
  if (!a) return null;
  const data = Object.entries(a.distribution).map(([name, value]) => ({ name, value })); const cols = ["#dc2626", "#f59e0b", "#16a34a"];
  return (<Card title="Analytics">
    <div className="flex gap-8 items-center"><div><p>Total predictions: <b>{a.total}</b></p><p>Avg risk: <b>{a.avg_risk}%</b></p><p>Avg latency: <b>{a.avg_latency_ms} ms</b></p></div>
      <PieChart width={220} height={160}><Pie data={data} dataKey="value" nameKey="name" outerRadius={60} label>{data.map((_, i) => <Cell key={i} fill={cols[i]} />)}</Pie><Tooltip /></PieChart></div>
  </Card>);
}

export default function App() {
  const [auth, setAuth] = useState(!!localStorage.getItem("token")); const [sel, setSel] = useState(null);
  const [res, setRes] = useState(null); const [busy, setBusy] = useState(false); const [tick, setTick] = useState(0);
  const predict = async p => { setSel(p); setBusy(true); try { setRes(await api(`/predict/${p.id}`, { method: "POST" })); setTick(t => t + 1); } catch (e) { alert(e.message); } setBusy(false); };
  if (!auth) return <Login onDone={() => setAuth(true)} />;
  return (<div className="max-w-5xl mx-auto p-6">
    <div className="flex justify-between mb-5"><h1 className="text-2xl font-bold text-blue-700">MediTrust AI</h1>
      <button className="text-sm text-slate-500" onClick={() => { localStorage.clear(); setAuth(false); }}>Logout</button></div>
    <Patients onPredict={predict} /><Prediction p={sel} res={res} busy={busy} /><Analytics tick={tick} /><Chain />
  </div>);
}
