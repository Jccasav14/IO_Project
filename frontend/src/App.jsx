import React, { useMemo, useState } from "react";

const DEFAULT_VARS = 2;
const DEFAULT_CONS = 3;
const DEFAULT_PROBLEM_TEXT = `PROBLEMA EMPRESARIAL

Una empresa comercializadora nacional dedicada a la distribucion de productos de consumo masivo opera con dos plantas de produccion y tres centros de distribucion que abastecen a distintos clientes ubicados en varias ciudades del pais. Actualmente, la empresa enfrenta elevados costos operativos, retrasos en las entregas y una gestion ineficiente de inventarios.

Las decisiones relacionadas con la asignacion de produccion, transporte de productos, seleccion de rutas de distribucion y reposicion de inventarios se realizan de manera empirica, sin el apoyo de modelos matematicos que permitan optimizar los recursos disponibles. Como consecuencia, se presentan problemas de sobrestock en algunos centros de distribucion y desabastecimiento en otros, asi como un uso ineficiente de la red logistica.

La empresa no cuenta con una herramienta computacional que integre modelos de optimizacion para analizar diferentes escenarios y evaluar el impacto de cambios en la demanda, costos de transporte y capacidades operativas, lo que dificulta la toma de decisiones estrategicas y afecta su competitividad y rentabilidad.`;

function makeMatrix(rows, cols, fill = 0) {
  return Array.from({ length: rows }, () =>
    Array.from({ length: cols }, () => fill)
  );
}


function circleLayout(nodes, width, height) {
  const cx = width / 2;
  const cy = height / 2;
  const r = Math.min(width, height) * 0.35;
  const n = nodes.length || 1;
  const pos = {};
  nodes.forEach((id, i) => {
    const ang = (2 * Math.PI * i) / n - Math.PI / 2;
    pos[id] = {
      x: cx + r * Math.cos(ang),
      y: cy + r * Math.sin(ang),
    };
  });
  return pos;
}

function NetworkGraph({ model, highlightEdges = [], flowMap = null }) {
  if (!model || !Array.isArray(model.nodes) || model.nodes.length === 0) {
    return <p className="empty">No hay red para visualizar.</p>;
  }

  const width = 720;
  const height = 420;
  const pos = circleLayout(model.nodes, width, height);
  const hl = new Set(highlightEdges || []);
  const directed = !!model.directed;

  function edgeKey(u, v) {
    return `${u}->${v}`;
  }

  function isHighlighted(e) {
    const k1 = edgeKey(e.u, e.v);
    const k2 = edgeKey(e.v, e.u);
    return hl.has(k1) || (!directed && hl.has(k2));
  }

  const edges = Array.isArray(model.edges) ? model.edges : [];

  return (
    <div className="net-viz">
      <svg viewBox={`0 0 ${width} ${height}`} className="net-svg" role="img" aria-label="Red">
        <defs>
          <marker
            id="arrow"
            viewBox="0 0 10 10"
            refX="9"
            refY="5"
            markerWidth="7"
            markerHeight="7"
            orient="auto-start-reverse"
          >
            <path d="M 0 0 L 10 5 L 0 10 z" fill="currentColor" />
          </marker>
        </defs>

        {edges.map((e, i) => {
          const p1 = pos[e.u];
          const p2 = pos[e.v];
          if (!p1 || !p2) return null;

          const hi = isHighlighted(e);
          const hasFlow = flowMap && flowMap[edgeKey(e.u, e.v)] > 0;
          const cls = hi ? "edge edge-hi" : hasFlow ? "edge edge-flow" : "edge";

          const mx = (p1.x + p2.x) / 2;
          const my = (p1.y + p2.y) / 2;

          const labelParts = [];
          if (typeof e.w === "number") labelParts.push(`w=${e.w}`);
          if (typeof e.capacity === "number") labelParts.push(`cap=${e.capacity}`);
          if (typeof e.cost === "number") labelParts.push(`c=${e.cost}`);
          if (flowMap && flowMap[edgeKey(e.u, e.v)] > 0) labelParts.push(`f=${flowMap[edgeKey(e.u, e.v)]}`);

          const label = labelParts.join(" · ");

          return (
            <g key={`edge-${i}`}>
              <line
                x1={p1.x}
                y1={p1.y}
                x2={p2.x}
                y2={p2.y}
                className={cls}
                markerEnd={directed ? "url(#arrow)" : undefined}
              />
              {label ? (
                <text x={mx} y={my} className="edge-label">
                  {label}
                </text>
              ) : null}
            </g>
          );
        })}

        {model.nodes.map((id) => {
          const p = pos[id];
          return (
            <g key={`node-${id}`}>
              <circle cx={p.x} cy={p.y} r="18" className="node" />
              <text x={p.x} y={p.y + 5} textAnchor="middle" className="node-label">
                {id}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}

function App() {
  const [page, setPage] = useState("home");
  const [name, setName] = useState("LP_demo");
  const [sense, setSense] = useState("max");
  const [method, setMethod] = useState("auto");
  const [nVars, setNVars] = useState(DEFAULT_VARS);
  const [nCons, setNCons] = useState(DEFAULT_CONS);
  const [c, setC] = useState(Array.from({ length: DEFAULT_VARS }, () => 0));
  const [A, setA] = useState(makeMatrix(DEFAULT_CONS, DEFAULT_VARS, 0));
  const [ops, setOps] = useState(Array.from({ length: DEFAULT_CONS }, () => "<="));
  const [b, setB] = useState(Array.from({ length: DEFAULT_CONS }, () => 0));

  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [problemText, setProblemText] = useState(DEFAULT_PROBLEM_TEXT);
  const [aiError, setAiError] = useState("");
  const [aiLoading, setAiLoading] = useState(false);
  const [aiReport, setAiReport] = useState("");
  const [fileData, setFileData] = useState("");
  const [fileName, setFileName] = useState("");

  // Redes
  const [netMethod, setNetMethod] = useState("shortest_path");
  const [netNodesText, setNetNodesText] = useState("A,B,C,D,E");
  const [netDirected, setNetDirected] = useState(false);
  const [netSource, setNetSource] = useState("A");
  const [netTarget, setNetTarget] = useState("D");
  const [netSink, setNetSink] = useState("E");
  const [netDemand, setNetDemand] = useState(10);
  const [netEdges, setNetEdges] = useState([
    { u: "A", v: "B", w: 2, capacity: 0, cost: 0 },
    { u: "A", v: "C", w: 5, capacity: 0, cost: 0 },
    { u: "B", v: "C", w: 1, capacity: 0, cost: 0 },
    { u: "B", v: "D", w: 4, capacity: 0, cost: 0 },
    { u: "C", v: "D", w: 1, capacity: 0, cost: 0 },
    { u: "D", v: "E", w: 4, capacity: 0, cost: 0 },
  ]);
  const [netResult, setNetResult] = useState(null);
  const [netError, setNetError] = useState("");
  const [netLoading, setNetLoading] = useState(false);

  function parseNodes(text) {
    return String(text)
      .split(/[,\n]/)
      .map((s) => s.trim())
      .filter(Boolean);
  }

  function buildNetModel() {
    const nodes = parseNodes(netNodesText);
    const edges = (netEdges || [])
      .filter((e) => e && String(e.u).trim() && String(e.v).trim())
      .map((e) => {
        const out = { u: String(e.u).trim(), v: String(e.v).trim() };
        if (typeof e.w === "number" && !Number.isNaN(e.w)) out.w = e.w;
        if (typeof e.capacity === "number" && !Number.isNaN(e.capacity) && e.capacity > 0)
          out.capacity = e.capacity;
        if (typeof e.cost === "number" && !Number.isNaN(e.cost) && e.cost !== 0) out.cost = e.cost;
        return out;
      });

    const model = {
      nodes,
      edges,
      directed: !!netDirected,
    };

    if (netMethod === "shortest_path") {
      model.source = String(netSource).trim();
      model.target = String(netTarget).trim();
    }
    if (netMethod === "max_flow" || netMethod === "min_cost_flow") {
      model.source = String(netSource).trim();
      model.sink = String(netSink).trim();
    }
    if (netMethod === "min_cost_flow") {
      model.demand = Number(netDemand);
    }
    return model;
  }

  const netModelPreview = useMemo(() => {
    try {
      return JSON.stringify(buildNetModel(), null, 2);
    } catch {
      return "";
    }
  }, [netMethod, netNodesText, netDirected, netEdges, netSource, netTarget, netSink, netDemand]);

  function updateNetEdge(idx, field, value) {
    setNetEdges((prev) => {
      const next = (prev || []).map((e) => ({ ...e }));
      if (!next[idx]) next[idx] = { u: "", v: "", w: 0, capacity: 0, cost: 0 };
      next[idx][field] = value;
      return next;
    });
  }

  function addNetEdge() {
    setNetEdges((prev) => [...(prev || []), { u: "", v: "", w: 1, capacity: 1, cost: 0 }]);
  }

  function removeNetEdge(idx) {
    setNetEdges((prev) => (prev || []).filter((_, i) => i !== idx));
  }

  function loadNetExample(which) {
    if (which === "shortest_path") {
      setNetMethod("shortest_path");
      setNetDirected(false);
      setNetNodesText("A,B,C,D,E");
      setNetSource("A");
      setNetTarget("E");
      setNetEdges([
        { u: "A", v: "B", w: 2, capacity: 0, cost: 0 },
        { u: "A", v: "C", w: 5, capacity: 0, cost: 0 },
        { u: "B", v: "C", w: 1, capacity: 0, cost: 0 },
        { u: "B", v: "D", w: 4, capacity: 0, cost: 0 },
        { u: "C", v: "D", w: 1, capacity: 0, cost: 0 },
        { u: "D", v: "E", w: 4, capacity: 0, cost: 0 },
      ]);
    }
    if (which === "mst") {
      setNetMethod("mst");
      setNetDirected(false);
      setNetNodesText("A,B,C,D,E");
      setNetEdges([
        { u: "A", v: "B", w: 2, capacity: 0, cost: 0 },
        { u: "A", v: "C", w: 5, capacity: 0, cost: 0 },
        { u: "B", v: "C", w: 1, capacity: 0, cost: 0 },
        { u: "B", v: "D", w: 4, capacity: 0, cost: 0 },
        { u: "C", v: "D", w: 1, capacity: 0, cost: 0 },
        { u: "D", v: "E", w: 4, capacity: 0, cost: 0 },
      ]);
    }
    if (which === "max_flow") {
      setNetMethod("max_flow");
      setNetDirected(true);
      setNetNodesText("S,A,B,T");
      setNetSource("S");
      setNetSink("T");
      setNetEdges([
        { u: "S", v: "A", w: 0, capacity: 10, cost: 0 },
        { u: "S", v: "B", w: 0, capacity: 5, cost: 0 },
        { u: "A", v: "B", w: 0, capacity: 15, cost: 0 },
        { u: "A", v: "T", w: 0, capacity: 10, cost: 0 },
        { u: "B", v: "T", w: 0, capacity: 10, cost: 0 },
      ]);
    }
    if (which === "min_cost_flow") {
      setNetMethod("min_cost_flow");
      setNetDirected(true);
      setNetNodesText("S,A,B,T");
      setNetSource("S");
      setNetSink("T");
      setNetDemand(10);
      setNetEdges([
        { u: "S", v: "A", w: 0, capacity: 8, cost: 2 },
        { u: "S", v: "B", w: 0, capacity: 7, cost: 4 },
        { u: "A", v: "B", w: 0, capacity: 3, cost: 1 },
        { u: "A", v: "T", w: 0, capacity: 8, cost: 3 },
        { u: "B", v: "T", w: 0, capacity: 7, cost: 2 },
      ]);
    }
  }

  const netModel = useMemo(() => buildNetModel(), [netMethod, netNodesText, netDirected, netEdges, netSource, netTarget, netSink, netDemand]);
  const netHighlightEdges = Array.isArray(netResult?.highlight?.edges) ? netResult.highlight.edges : [];

  function derivePathNodes({ edges, source, target, directed }) {
    if (!Array.isArray(edges) || edges.length === 0 || !source || !target) return [];
    // Build adjacency from highlighted edges and try to walk from source to target.
    const adj = new Map();
    const add = (u, v) => {
      if (!adj.has(u)) adj.set(u, []);
      adj.get(u).push(v);
    };
    edges.forEach((k) => {
      const [u, v] = String(k).split("->");
      if (!u || !v) return;
      add(u, v);
      if (!directed) add(v, u);
    });
    const path = [source];
    const seen = new Set([source]);
    let cur = source;
    for (let i = 0; i < edges.length + 2; i++) {
      if (cur === target) break;
      const nxts = adj.get(cur) || [];
      const nxt = nxts.find((x) => !seen.has(x)) || nxts[0];
      if (!nxt) break;
      path.push(nxt);
      seen.add(nxt);
      cur = nxt;
    }
    if (path[path.length - 1] !== target) return [];
    return path;
  }


  const numberFormat = useMemo(
    () => new Intl.NumberFormat("es-EC", { maximumFractionDigits: 6 }),
    []
  );

  function fmt(n) {
    if (n === null || n === undefined || Number.isNaN(n)) return "—";
    return numberFormat.format(n);
  }

  function formatVector(x, prefix) {
    if (!Array.isArray(x)) return [];
    return x.map((v, i) => ({ key: `${prefix}${i + 1}`, value: fmt(v) }));
  }

  function formatNamedList(names) {
    if (!Array.isArray(names)) return [];
    return names.map((n) => ({ key: n, value: "" }));
  }

  function formatSlackList() {
    if (!Array.isArray(result?.slacks)) return [];
    return result.slacks.map((s, i) => {
      const op = ops[i];
      const label = op === "<=" ? `s${i + 1}` : op === ">=" ? `e${i + 1}` : `r${i + 1}`;
      return { key: label, value: fmt(s) };
    });
  }

  const modelJson = useMemo(() => {
    const constraints = A.map((row, i) => ({
      a: row.map(Number),
      op: ops[i],
      b: Number(b[i]),
    }));
    return {
      name,
      sense,
      c: c.map(Number),
      constraints,
    };
  }, [name, sense, c, A, ops, b]);

  function resizeVars(nextVars) {
    const n = Math.max(1, nextVars);
    setNVars(n);
    setC((prev) => {
      const next = prev.slice(0, n);
      while (next.length < n) next.push(0);
      return next;
    });
    setA((prev) => {
      const next = prev.map((row) => {
        const r = row.slice(0, n);
        while (r.length < n) r.push(0);
        return r;
      });
      return next;
    });
  }

  function resizeCons(nextCons) {
    const m = Math.max(1, nextCons);
    setNCons(m);
    setA((prev) => {
      const next = prev.slice(0, m);
      while (next.length < m) next.push(Array.from({ length: nVars }, () => 0));
      return next;
    });
    setOps((prev) => {
      const next = prev.slice(0, m);
      while (next.length < m) next.push("<=");
      return next;
    });
    setB((prev) => {
      const next = prev.slice(0, m);
      while (next.length < m) next.push(0);
      return next;
    });
  }

  function updateA(i, j, value) {
    setA((prev) => {
      const next = prev.map((row) => row.slice());
      next[i][j] = value;
      return next;
    });
  }

  async function solve() {
    setError("");
    setResult(null);
    setLoading(true);
    try {
      const res = await fetch("http://127.0.0.1:8000/solve", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ model: modelJson, method }),
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.error || "Error del solucionador");
      }
      setResult(data);
    } catch (err) {
      setError(String(err));
    } finally {
      setLoading(false);
    }
  }

  async function solveNetworks() {
    setNetError("");
    setNetResult(null);

    const model = buildNetModel();
    if (!Array.isArray(model.nodes) || model.nodes.length === 0) {
      setNetError("Debes ingresar al menos 1 nodo.");
      return;
    }
    if (!Array.isArray(model.edges) || model.edges.length === 0) {
      setNetError("Debes ingresar al menos 1 arista (u, v). ");
      return;
    }

    if (netMethod === "shortest_path") {
      if (!model.source || !model.target) {
        setNetError("Ruta más corta requiere source y target.");
        return;
      }
      const bad = model.edges.some((e) => typeof e.w !== "number");
      if (bad) {
        setNetError("Ruta más corta requiere pesos w en todas las aristas.");
        return;
      }
    }
    if (netMethod === "mst") {
      const bad = model.edges.some((e) => typeof e.w !== "number");
      if (bad) {
        setNetError("Árbol mínimo requiere pesos w en todas las aristas.");
        return;
      }
    }
    if (netMethod === "max_flow") {
      if (!model.source || !model.sink) {
        setNetError("Flujo máximo requiere source y sink.");
        return;
      }
      const bad = model.edges.some((e) => typeof e.capacity !== "number" || e.capacity <= 0);
      if (bad) {
        setNetError("Flujo máximo requiere capacity > 0 en todas las aristas.");
        return;
      }
    }
    if (netMethod === "min_cost_flow") {
      if (!model.source || !model.sink) {
        setNetError("Flujo de costo mínimo requiere source y sink.");
        return;
      }
      if (!(typeof model.demand === "number") || model.demand <= 0) {
        setNetError("Flujo de costo mínimo requiere demand > 0.");
        return;
      }
      const badCap = model.edges.some((e) => typeof e.capacity !== "number" || e.capacity <= 0);
      if (badCap) {
        setNetError("Flujo de costo mínimo requiere capacity > 0 en todas las aristas.");
        return;
      }
      const badCost = model.edges.some((e) => typeof e.cost !== "number");
      if (badCost) {
        setNetError("Flujo de costo mínimo requiere cost (puede ser 0) en todas las aristas.");
        return;
      }
    }

    setNetLoading(true);
    try {
      const res = await fetch("http://127.0.0.1:8001/solve/networks", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ method: netMethod, model }),
      });
      const data = await res.json();
      if (!res.ok) {
        setNetError(data?.error || "Error al resolver redes.");
      } else {
        setNetResult(data);
      }
    } catch (e) {
      setNetError("No se pudo conectar al servidor de Redes (http://127.0.0.1:8001). ¿Está encendido?");
    } finally {
      setNetLoading(false);
    }
  }


  async function analyzeWithAI() {
    setAiError("");
    setAiLoading(true);
    try {
      const payload = fileData
        ? { filename: fileName || "problem.pdf", file_data: fileData }
        : { text: problemText };
      const res = await fetch("http://127.0.0.1:8000/ai/parse", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.error || "Error al analizar con IA");
      }
      const m = data.model;
      if (!m) throw new Error("Respuesta vacia de la IA");
      if (data.summary) {
        setProblemText(data.summary);
      }
      const newVars = Array.isArray(m.c) ? m.c.length : 0;
      const newCons = Array.isArray(m.constraints) ? m.constraints.length : 0;
      setName(m.name || "LP");
      setSense(m.sense || "max");
      setNVars(Math.max(1, newVars));
      setNCons(Math.max(1, newCons));
      setC((m.c || []).map((v) => Number(v)));
      setA(
        (m.constraints || []).map((cst) =>
          (cst.a || []).map((v) => Number(v))
        )
      );
      setOps((m.constraints || []).map((cst) => cst.op || "<="));
      setB((m.constraints || []).map((cst) => Number(cst.b)));
      setResult(null);
    } catch (err) {
      setAiError(String(err));
    } finally {
      setAiLoading(false);
    }
  }

  async function generateReport() {
    setAiError("");
    setAiReport("");
    if (!result) {
      setAiError("Primero resuelve el modelo.");
      return;
    }
    setAiLoading(true);
    try {
      const res = await fetch("http://127.0.0.1:8000/ai/report", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          problem_text: problemText,
          model: modelJson,
          result,
        }),
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.error || "Error al generar informe");
      }
      setAiReport(data.report || "");
    } catch (err) {
      setAiError(String(err));
    } finally {
      setAiLoading(false);
    }
  }

  function renderInline(text) {
    const parts = text.split("**");
    const nodes = [];
    for (let i = 0; i < parts.length; i++) {
      const chunk = parts[i];
      if (!chunk) continue;
      if (i % 2 === 1) {
        nodes.push(<strong key={`b-${i}`}>{chunk}</strong>);
      } else {
        nodes.push(<span key={`t-${i}`}>{chunk}</span>);
      }
    }
    return nodes.length ? nodes : [text];
  }

  function cleanLine(line) {
    return line.replace(/^\*\s*/, "").replace(/\*$/g, "").trim();
  }

  function renderReport(text) {
    if (!text) return null;
    const lines = text.split(/\r?\n/);
    const blocks = [];
    let list = [];
    const flushList = () => {
      if (list.length) {
        blocks.push(
          <ul key={`ul-${blocks.length}`}>
            {list.map((item, idx) => (
              <li key={`li-${idx}`}>{renderInline(item)}</li>
            ))}
          </ul>
        );
        list = [];
      }
    };
    lines.forEach((line) => {
      const trimmed = cleanLine(line);
      if (!trimmed) {
        flushList();
        return;
      }
      if (trimmed.startsWith("*") || trimmed.startsWith("-")) {
        list.push(trimmed.replace(/^[-*]\s*/, ""));
        return;
      }
      flushList();
      blocks.push(<p key={`p-${blocks.length}`}>{renderInline(trimmed)}</p>);
    });
    flushList();
    return blocks;
  }

  return (
    <div className="page">
      {page === "home" && (
        <div className="home">
          <header className="home-hero">
            <div>
              <div className="uni">Universidad Central del Ecuador</div>
              <h1>Investigación Operativa</h1>
              <p className="subtitle">
                Plataforma académica para el análisis y resolución de problemas
                de optimización.
              </p>
            </div>
            <div className="home-card">
              <h3>Integrantes</h3>
              <ul>
                <li>Elser Gabriel Toro Cárdemas</li>
                <li>Augusto Ramses Riofrío Vaca</li>
                <li>Jean Carlos Casa Velasquez</li>
              </ul>
            </div>
          </header>

          <section className="panel">
            <h2>PROBLEMA EMPRESARIAL A RESOLVER</h2>
            <p>
              Una empresa comercializadora nacional dedicada a la distribución
              de productos de consumo masivo opera con dos plantas de producción
              y tres centros de distribución que abastecen a distintos clientes
              ubicados en varias ciudades del país. Actualmente, la empresa
              enfrenta elevados costos operativos, retrasos en las entregas y
              una gestión ineficiente de inventarios.
            </p>
            <p>
              Las decisiones relacionadas con la asignación de producción,
              transporte de productos, selección de rutas de distribución y
              reposición de inventarios se realizan de manera empírica, sin el
              apoyo de modelos matemáticos que permitan optimizar los recursos
              disponibles. Como consecuencia, se presentan problemas de
              sobrestock en algunos centros de distribución y desabastecimiento
              en otros, así como un uso ineficiente de la red logística.
            </p>
            <p>
              La empresa no cuenta con una herramienta computacional que
              integre modelos de optimización para analizar diferentes escenarios
              y evaluar el impacto de cambios en la demanda, costos de transporte
              y capacidades operativas, lo que dificulta la toma de decisiones
              estratégicas y afecta su competitividad y rentabilidad.
            </p>
          </section>

          <section className="panel">
            <h2>Módulos del sistema</h2>
            <div className="module-grid">
              <div className="module-card">
                <h3>Programación Lineal</h3>
                <p>Simplex, Gran M, Dos Fases, Dual</p>
                <button className="primary" onClick={() => setPage("lp")}>
                  Ir a Programación Lineal
                </button>
              </div>
              <div className="module-card disabled">
                <h3>Transporte</h3>
                <p>Costo mínimo, Esquina noroeste, Vogel, Optimalidad</p>
                <button disabled>Próximamente</button>
              </div>
              <div className="module-card">
                <h3>Redes</h3>
                <p>Ruta más corta, Árbol mínimo, Flujo máximo, Costo mínimo</p>
                <button className="primary" onClick={() => setPage("networks")}>
                  Ir a Redes
                </button>
              </div>
              <div className="module-card disabled">
                <h3>Inventario / Prog. Dinámica</h3>
                <p>Opcional según avance del proyecto</p>
                <button disabled>Próximamente</button>
              </div>
            </div>
          </section>
        </div>
      )}

      {page === "lp" && (
        <>
          <header className="hero">
            <div>
              <h1>Solucionador de Programación Lineal</h1>
              <p>
                Ingresa el modelo en forma estándar. El cálculo se hace con los
                métodos implementados en este proyecto, sin librerías externas.
              </p>
            </div>
            <div className="meta">
              <label>
                Nombre del modelo
                <input value={name} onChange={(e) => setName(e.target.value)} />
              </label>
              <label>
                Sentido del objetivo
                <select value={sense} onChange={(e) => setSense(e.target.value)}>
                  <option value="max">Maximizar</option>
                  <option value="min">Minimizar</option>
                </select>
              </label>
              <label>
                Método de solución
                <select value={method} onChange={(e) => setMethod(e.target.value)}>
                  <option value="auto">Automático</option>
                  <option value="simplex">Simplex</option>
                  <option value="two_phase">Dos Fases</option>
                  <option value="big_m">Gran M</option>
                  <option value="dual">Dual</option>
                </select>
              </label>
              <button className="ghost" onClick={() => setPage("home")}>
                Volver a inicio
              </button>
            </div>
          </header>

          <section className="panel">
            <h2>IA: carga y analisis del problema</h2>
            <div className="row">
              <label>
                Subir PDF (texto, no escaneado)
                <input
                  type="file"
                  accept="application/pdf"
                  onChange={(e) => {
                    const file = e.target.files && e.target.files[0];
                    if (!file) return;
                    setFileName(file.name);
                    const reader = new FileReader();
                    reader.onload = () => {
                      setFileData(String(reader.result || ""));
                    };
                    reader.readAsDataURL(file);
                  }}
                />
              </label>
              <button className="primary" onClick={analyzeWithAI} disabled={aiLoading}>
                {aiLoading ? "Analizando..." : "Analizar con IA"}
              </button>
            </div>
            <div className="section">
              <label>
                Contexto del problema (texto)
                <textarea
                  rows="8"
                  value={problemText}
                  onChange={(e) => setProblemText(e.target.value)}
                />
              </label>
              <div className="row">
                <button className="ghost" onClick={analyzeWithAI} disabled={aiLoading}>
                  {aiLoading ? "Analizando..." : "Analizar texto con IA"}
                </button>
              </div>
            </div>
            {aiError && <div className="error">IA: {aiError}</div>}
          </section>

          <section className="panel">
            <div className="row">
              <label>
                Número de variables (n)
                <input
                  type="number"
                  min="1"
                  value={nVars}
                  onChange={(e) => resizeVars(Number(e.target.value))}
                />
              </label>
              <label>
                Número de restricciones (m)
                <input
                  type="number"
                  min="1"
                  value={nCons}
                  onChange={(e) => resizeCons(Number(e.target.value))}
                />
              </label>
              <button className="primary" onClick={solve} disabled={loading}>
                {loading ? "Resolviendo..." : "Resolver"}
              </button>
            </div>

            <div className="section">
              <h2>Función objetivo</h2>
              <div className="grid">
                {c.map((val, j) => (
                  <label key={`c-${j}`}>
                    Coef. c{j + 1}
                    <input
                      type="number"
                      value={val}
                      onChange={(e) => {
                        const v = e.target.value;
                        setC((prev) => {
                          const next = prev.slice();
                          next[j] = v;
                          return next;
                        });
                      }}
                    />
                  </label>
                ))}
              </div>
            </div>

            <div className="section">
              <h2>Restricciones</h2>
              <div className="constraints">
                {A.map((row, i) => (
                  <div className="constraint" key={`row-${i}`}>
                    <div className="grid">
                      {row.map((val, j) => (
                        <label key={`a-${i}-${j}`}>
                          a{i + 1},{j + 1}
                          <input
                            type="number"
                            value={val}
                            onChange={(e) => updateA(i, j, e.target.value)}
                          />
                        </label>
                      ))}
                    </div>
                    <div className="row">
                      <label>
                        Operador
                        <select
                          value={ops[i]}
                          onChange={(e) => {
                            const v = e.target.value;
                            setOps((prev) => {
                              const next = prev.slice();
                              next[i] = v;
                              return next;
                            });
                          }}
                        >
                          <option value="<=">{`<=`}</option>
                          <option value=">=">{`>=`}</option>
                          <option value="=">{`=`}</option>
                        </select>
                      </label>
                      <label>
                        Término independiente (b)
                        <input
                          type="number"
                          value={b[i]}
                          onChange={(e) => {
                            const v = e.target.value;
                            setB((prev) => {
                              const next = prev.slice();
                              next[i] = v;
                              return next;
                            });
                          }}
                        />
                      </label>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </section>

          <section className="panel">
            <h2>Resultado</h2>
            {error && <div className="error">Error: {error}</div>}
            {!error && !result && <div className="empty">Sin resultados aún.</div>}
            {result && (
              <div className="result-box">
                <div>
                  <strong>Estado:</strong> {result.status}
                </div>
                <div>
                  <strong>Método usado:</strong> {result.method_used}
                </div>
                <div>
                  <strong>Valor objetivo:</strong> {fmt(result.objective_value)}
                </div>
                <div>
                  <strong>Solución x:</strong>
                  <div className="chips">
                    {formatVector(result.x, "V").map((item) => (
                      <span className="chip" key={item.key}>
                        {item.key}: {item.value}
                      </span>
                    ))}
                  </div>
                </div>
                {Array.isArray(result.slacks) && (
                  <div>
                    <strong>Holgura/Exceso (s/e):</strong>
                    <div className="chips">
                      {formatSlackList().map((item) => (
                        <span className="chip" key={item.key}>
                          {item.key}: {item.value}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
                {result.dual && Array.isArray(result.dual.shadow_prices) && (
                  <div>
                    <strong>Precios sombra (y):</strong>
                    <div className="chips">
                      {result.dual.shadow_prices.map((v, i) => (
                        <span className="chip" key={`y-${i}`}>
                          R{i + 1}: {fmt(v)}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
                {Array.isArray(result.basic_vars) && (
                  <div>
                    <strong>Variables básicas:</strong>
                    <div className="chips">
                      {formatNamedList(result.basic_vars).map((item) => (
                        <span className="chip" key={item.key}>
                          {item.key}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
                {Array.isArray(result.nonbasic_vars) && (
                  <div>
                    <strong>Variables no básicas:</strong>
                    <div className="chips">
                      {formatNamedList(result.nonbasic_vars).map((item) => (
                        <span className="chip" key={item.key}>
                          {item.key}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
                {result.message && (
                  <div>
                    <strong>Mensaje:</strong> {result.message}
                  </div>
                )}
              </div>
            )}
            <div className="section">
              <button className="primary" onClick={generateReport} disabled={aiLoading}>
                {aiLoading ? "Generando..." : "Generar informe (IA)"}
              </button>
              {aiReport && (
                <div className="report">
                  <h3>Analisis de sensibilidad</h3>
                  <div className="report-text">{renderReport(aiReport)}</div>
                </div>
              )}
            </div>
          </section>

          <section className="panel">
            <h2>Modelo (JSON)</h2>
            <pre className="code">{JSON.stringify(modelJson, null, 2)}</pre>
          </section>

          <section className="panel">
            <h2>Tabla final</h2>
            {!result || !Array.isArray(result.tableau) ? (
              <div className="empty">Sin tabla disponible.</div>
            ) : (
              <div className="table-wrap">
                <table className="tableau">
                  <thead>
                    <tr>
                      <th>Fila</th>
                      {Array.isArray(result.var_names) &&
                        result.var_names.map((n) => <th key={n}>{n}</th>)}
                      <th>Solución</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.tableau.map((row, i) => (
                      <tr key={`row-${i}`}>
                        <td>
                          {i === 0
                            ? "Z"
                            : Array.isArray(result.basic_vars)
                            ? result.basic_vars[i - 1] || `R${i}`
                            : `R${i}`}
                        </td>
                        {row.slice(0, -1).map((v, j) => (
                          <td key={`c-${i}-${j}`}>{fmt(v)}</td>
                        ))}
                        <td>{fmt(i === 0 ? -row[row.length - 1] : row[row.length - 1])}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>
        </>
      )}


      {page === "networks" && (
        <>
          <header className="hero">
            <div>
              <h1>Solucionador de Redes</h1>
              <p>
                Ruta más corta, Árbol de expansión mínima, Flujo máximo y Flujo de costo mínimo.
                Implementado desde cero (sin librerías de optimización).
              </p>
              <button className="ghost" onClick={() => setPage("home")}>
                ← Volver al inicio
              </button>
            </div>

            <div className="meta">
              <label>
                Método
                <select value={netMethod} onChange={(e) => setNetMethod(e.target.value)}>
                  <option value="shortest_path">Ruta más corta (Dijkstra)</option>
                  <option value="mst">Árbol de expansión mínima (Kruskal)</option>
                  <option value="max_flow">Flujo máximo (Edmonds–Karp)</option>
                  <option value="min_cost_flow">Flujo de costo mínimo (SSAP)</option>
                </select>
              </label>
              <button className="primary" onClick={solveNetworks} disabled={netLoading}>
                {netLoading ? "Resolviendo..." : "Resolver"}
              </button>
              <p className="hint">
                Servidor: <span className="mono">python network_api_server.py</span> (puerto 8001)
              </p>
            </div>
          </header>

          <section className="panel">
            <h2>Entrada</h2>
            <p className="empty">
              Ingresa nodos y aristas en un formato legible. El sistema generará el modelo automáticamente.
            </p>

            <div className="form-grid">
              <label>
                Nodos (separados por coma)
                <input
                  value={netNodesText}
                  onChange={(e) => setNetNodesText(e.target.value)}
                  placeholder="A,B,C,D,E"
                />
              </label>

              <label className="check">
                <input type="checkbox" checked={netDirected} onChange={(e) => setNetDirected(e.target.checked)} />
                Red dirigida
              </label>

              {(netMethod === "shortest_path" || netMethod === "max_flow" || netMethod === "min_cost_flow") ? (
                <label>
                  Source
                  <input value={netSource} onChange={(e) => setNetSource(e.target.value)} placeholder="A" />
                </label>
              ) : null}

              {netMethod === "shortest_path" ? (
                <label>
                  Target
                  <input value={netTarget} onChange={(e) => setNetTarget(e.target.value)} placeholder="D" />
                </label>
              ) : null}

              {(netMethod === "max_flow" || netMethod === "min_cost_flow") ? (
                <label>
                  Sink
                  <input value={netSink} onChange={(e) => setNetSink(e.target.value)} placeholder="T" />
                </label>
              ) : null}

              {netMethod === "min_cost_flow" ? (
                <label>
                  Demand
                  <input type="number" value={netDemand} onChange={(e) => setNetDemand(Number(e.target.value))} />
                </label>
              ) : null}
            </div>

            <div className="toolbar">
              <button className="ghost" onClick={() => loadNetExample("shortest_path")}>Ejemplo Ruta</button>
              <button className="ghost" onClick={() => loadNetExample("mst")}>Ejemplo Árbol mínimo</button>
              <button className="ghost" onClick={() => loadNetExample("max_flow")}>Ejemplo Flujo máximo</button>
              <button className="ghost" onClick={() => loadNetExample("min_cost_flow")}>Ejemplo Costo mínimo</button>
              <button className="ghost" onClick={addNetEdge}>+ Arista</button>
            </div>

            <div className="table-wrap">
              <table className="tableau">
                <thead>
                  <tr>
                    <th>u</th>
                    <th>v</th>
                    <th>{(netMethod === "max_flow" || netMethod === "min_cost_flow") ? "capacity" : "w"}</th>
                    <th>{netMethod === "min_cost_flow" ? "cost" : ""}</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {netEdges.map((e, i) => (
                    <tr key={`ne-${i}`}>
                      <td><input value={e.u} onChange={(ev) => updateNetEdge(i, "u", ev.target.value)} /></td>
                      <td><input value={e.v} onChange={(ev) => updateNetEdge(i, "v", ev.target.value)} /></td>
                      <td>
                        {(netMethod === "max_flow" || netMethod === "min_cost_flow") ? (
                          <input type="number" value={e.capacity} onChange={(ev) => updateNetEdge(i, "capacity", Number(ev.target.value))} />
                        ) : (
                          <input type="number" value={e.w} onChange={(ev) => updateNetEdge(i, "w", Number(ev.target.value))} />
                        )}
                      </td>
                      <td>
                        {netMethod === "min_cost_flow" ? (
                          <input type="number" value={e.cost} onChange={(ev) => updateNetEdge(i, "cost", Number(ev.target.value))} />
                        ) : null}
                      </td>
                      <td>
                        <button className="ghost" onClick={() => removeNetEdge(i)} title="Eliminar">✕</button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {netError ? <p className="error">{netError}</p> : null}

            <details className="details">
              <summary>Ver modelo generado (JSON)</summary>
              <pre className="code">{netModelPreview}</pre>
            </details>
          </section>

          <section className="panel">
            <h2>Visualización</h2>
            <NetworkGraph
              model={netModel}
              highlightEdges={netHighlightEdges}
              flowMap={netResult?.flow_map || null}
            />
          </section>

          <section className="panel">
            <h2>Resultado</h2>

            {!netResult && !netError && <p className="empty">Resuelve para ver resultados.</p>}

            {netResult ? (
              <>
                <div className="chips">
                  {Array.isArray(netResult?.summary) &&
                    netResult.summary.map((c) => (
                      <span className="chip" key={c}>
                        {c}
                      </span>
                    ))}
                </div>

                {netMethod === "shortest_path" ? (
                  <div className="kv">
                    <div><strong>Source:</strong> {netModel.source}</div>
                    <div><strong>Target:</strong> {netModel.target}</div>
                    <div><strong>Distancia:</strong> {fmt(netResult.distance ?? netResult.total_weight ?? netResult.cost)}</div>
                    <div><strong>Camino:</strong> {(Array.isArray(netResult.path_nodes) ? netResult.path_nodes : derivePathNodes({ edges: netHighlightEdges, source: netModel.source, target: netModel.target, directed: netModel.directed })).join(" → ") || "—"}</div>
                    <div><strong>Aristas:</strong> {netHighlightEdges.join(", ") || "—"}</div>
                  </div>
                ) : null}

                {netMethod === "mst" ? (
                  <div className="kv">
                    <div><strong>Aristas del árbol:</strong> {netHighlightEdges.join(", ") || "—"}</div>
                    <div><strong>Peso total:</strong> {fmt(netResult.total_weight ?? netResult.weight ?? null)}</div>
                  </div>
                ) : null}

                {netMethod === "max_flow" ? (
                  <>
                    <div className="kv">
                      <div><strong>Source:</strong> {netModel.source}</div>
                      <div><strong>Sink:</strong> {netModel.sink}</div>
                      <div><strong>Flujo máximo:</strong> {fmt(netResult.max_flow ?? netResult.value ?? null)}</div>
                    </div>
                    {netResult?.flow_map ? (
                      <div className="table-wrap">
                        <table className="tableau">
                          <thead><tr><th>Arista</th><th>Flujo</th></tr></thead>
                          <tbody>
                            {Object.entries(netResult.flow_map)
                              .filter(([, f]) => Number(f) > 0)
                              .map(([k, f]) => (
                                <tr key={k}><td>{k}</td><td>{fmt(f)}</td></tr>
                              ))}
                          </tbody>
                        </table>
                      </div>
                    ) : null}
                  </>
                ) : null}

                {netMethod === "min_cost_flow" ? (
                  <>
                    <div className="kv">
                      <div><strong>Source:</strong> {netModel.source}</div>
                      <div><strong>Sink:</strong> {netModel.sink}</div>
                      <div><strong>Demanda:</strong> {fmt(netModel.demand)}</div>
                      <div><strong>Costo total:</strong> {fmt(netResult.total_cost ?? netResult.cost ?? null)}</div>
                      <div><strong>Flujo enviado:</strong> {fmt(netResult.sent ?? netResult.total_flow ?? null)}</div>
                    </div>
                    {netResult?.flow_map ? (
                      <div className="table-wrap">
                        <table className="tableau">
                          <thead><tr><th>Arista</th><th>Flujo</th></tr></thead>
                          <tbody>
                            {Object.entries(netResult.flow_map)
                              .filter(([, f]) => Number(f) > 0)
                              .map(([k, f]) => (
                                <tr key={k}><td>{k}</td><td>{fmt(f)}</td></tr>
                              ))}
                          </tbody>
                        </table>
                      </div>
                    ) : null}
                  </>
                ) : null}

                <details className="details">
                  <summary>Ver respuesta completa (debug)</summary>
                  <pre className="code">{JSON.stringify(netResult, null, 2)}</pre>
                </details>
              </>
            ) : null}
          </section>
        </>
      )}

    </div>
  );
}

export default App;
