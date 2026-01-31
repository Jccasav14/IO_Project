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

  function rowLabel(i, basis, varNames) {
    if (i === 0) return "Z";
    if (Array.isArray(basis) && Array.isArray(varNames)) {
      const idx = basis[i - 1];
      if (Number.isInteger(idx) && idx >= 0 && idx < varNames.length) {
        return varNames[idx];
      }
    }
    return `R${i}`;
  }

  function renderTableau(tableau, varNames, basis) {
    if (!Array.isArray(tableau) || tableau.length === 0) return <div className="empty">Sin tabla.</div>;
    return (
      <div className="table-wrap">
        <table className="tableau">
          <thead>
            <tr>
              <th>Fila</th>
              {Array.isArray(varNames) && varNames.map((n) => <th key={`h-${n}`}>{n}</th>)}
              <th>Solucion</th>
            </tr>
          </thead>
          <tbody>
            {tableau.map((row, i) => (
              <tr key={`t-${i}`}>
                <td>{rowLabel(i, basis, varNames)}</td>
                {row.slice(0, -1).map((v, j) => (
                  <td key={`t-${i}-${j}`}>{fmt(v)}</td>
                ))}
                <td>{fmt(i === 0 ? -row[row.length - 1] : row[row.length - 1])}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  }

  function formatRowOps(rowOps) {
    if (!Array.isArray(rowOps) || rowOps.length === 0) return [];
    return rowOps;
  }

  const historyGroups = useMemo(() => {
    const h = result?.tableau_history;
    if (!h) return [];
    return Array.isArray(h) ? h : [h];
  }, [result]);

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
              <div className="module-card disabled">
                <h3>Redes</h3>
                <p>Ruta más corta, Árbol mínimo, Flujo máximo, Costo mínimo</p>
                <button disabled>Próximamente</button>
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
            <h2>Iteraciones</h2>
            {!historyGroups.length ? (
              <div className="empty">Sin iteraciones disponibles.</div>
            ) : (
              historyGroups.map((group, gi) => (
                <div key={`hg-${gi}`} className="result-box">
                  <h3>{group.label || `Fase ${gi + 1}`}</h3>
                  {Array.isArray(group.items) && group.items.length ? (
                    group.items.map((item) => {
                      const varNames = group.var_names || [];
                      const enterName =
                        Number.isInteger(item.enter) && item.enter >= 0 && item.enter < varNames.length
                          ? varNames[item.enter]
                          : null;
                      const leaveName =
                        Number.isInteger(item.leave_var) && item.leave_var >= 0 && item.leave_var < varNames.length
                          ? varNames[item.leave_var]
                          : null;
                      const pivotInfo =
                        enterName || leaveName
                          ? ` (entra ${enterName || "?"}${leaveName ? `, sale ${leaveName}` : ""})`
                          : "";

                      const isPrep = Array.isArray(item.row_ops) && item.row_ops.length > 0 && item.iteration === 0;
                      const title = isPrep ? "Preparacion Fase II" : `Iteracion ${item.iteration}`;
                      return (
                        <details className="details" key={`it-${group.label}-${item.iteration}`}>
                          <summary>{title}{pivotInfo}</summary>
                          {item.pivot && (
                            <div className="kv" style={{ marginTop: 10 }}>
                              <div><strong>Pivote:</strong> fila {item.pivot.row}, col {item.pivot.col}</div>
                              <div><strong>Valor pivote:</strong> {fmt(item.pivot.value)}</div>
                            </div>
                          )}
                          {formatRowOps(item.row_ops).length > 0 && (
                            <div style={{ marginTop: 8 }}>
                              <strong>Operaciones de fila:</strong>
                              <ul className="list">
                                {formatRowOps(item.row_ops).map((op, idx) => (
                                  <li key={`op-${item.iteration}-${idx}`}>{op}</li>
                                ))}
                              </ul>
                            </div>
                          )}
                          {renderTableau(item.tableau, varNames, item.basis)}
                        </details>
                      );
                    })
                  ) : (
                    <div className="empty">Sin iteraciones.</div>
                  )}
                </div>
              ))
            )}
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
    </div>
  );
}

export default App;
