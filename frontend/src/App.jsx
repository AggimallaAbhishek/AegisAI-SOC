import { useEffect, useMemo, useState } from "react";
import { analyzeAlert, getHealth, getPlaybooks, searchKnowledge } from "./api";

const SAMPLE_ALERT = {
  source: "SIEM",
  host: "FIN-WS-442",
  user: "finance.admin",
  ip_address: "203.0.113.56",
  process_name: "mimikatz.exe",
  command_line: "mimikatz.exe sekurlsa::logonpasswords",
  description: "Potential credential dumping behavior detected on endpoint"
};

const EMPTY_ALERT = {
  source: "SIEM",
  host: "",
  user: "",
  ip_address: "",
  process_name: "",
  command_line: "",
  description: ""
};

const severityClass = {
  low: "sev-low",
  medium: "sev-medium",
  high: "sev-high",
  critical: "sev-critical"
};

function prettyTime(isoString) {
  try {
    return new Date(isoString).toLocaleString();
  } catch {
    return isoString;
  }
}

export default function App() {
  const [health, setHealth] = useState({ status: "checking", version: "-" });
  const [alertForm, setAlertForm] = useState(EMPTY_ALERT);
  const [analysis, setAnalysis] = useState(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [analyzeError, setAnalyzeError] = useState("");

  const [knowledgeQuery, setKnowledgeQuery] = useState("mimikatz");
  const [knowledgeLoading, setKnowledgeLoading] = useState(false);
  const [knowledgeResults, setKnowledgeResults] = useState([]);
  const [knowledgeError, setKnowledgeError] = useState("");

  const [playbooks, setPlaybooks] = useState([]);
  const [playbookError, setPlaybookError] = useState("");

  useEffect(() => {
    let active = true;

    async function loadHealth() {
      try {
        const data = await getHealth();
        if (!active) return;
        setHealth({ status: data.status, version: data.version || "-" });
      } catch {
        if (!active) return;
        setHealth({ status: "offline", version: "-" });
      }
    }

    async function loadPlaybooks() {
      try {
        const data = await getPlaybooks();
        if (!active) return;
        setPlaybooks(Array.isArray(data.playbooks) ? data.playbooks : []);
      } catch (error) {
        if (!active) return;
        setPlaybookError(error.message || "Failed to load playbooks");
      }
    }

    loadHealth();
    loadPlaybooks();

    const timer = setInterval(loadHealth, 15000);
    return () => {
      active = false;
      clearInterval(timer);
    };
  }, []);

  const canAnalyze = useMemo(
    () => alertForm.host.trim() && alertForm.description.trim(),
    [alertForm]
  );

  async function handleAnalyze(event) {
    event.preventDefault();
    setAnalyzeError("");
    setAnalyzing(true);
    try {
      const payload = {
        ...alertForm,
        source: alertForm.source || "SIEM"
      };
      const data = await analyzeAlert(payload);
      setAnalysis(data);
    } catch (error) {
      setAnalyzeError(error.message || "Failed to analyze alert");
    } finally {
      setAnalyzing(false);
    }
  }

  async function handleKnowledgeSearch(event) {
    event.preventDefault();
    const query = knowledgeQuery.trim();
    if (!query) return;

    setKnowledgeError("");
    setKnowledgeLoading(true);
    try {
      const data = await searchKnowledge(query);
      setKnowledgeResults(Array.isArray(data.results) ? data.results : []);
    } catch (error) {
      setKnowledgeError(error.message || "Knowledge search failed");
    } finally {
      setKnowledgeLoading(false);
    }
  }

  function updateField(name, value) {
    setAlertForm((prev) => ({ ...prev, [name]: value }));
  }

  function loadSample() {
    setAlertForm(SAMPLE_ALERT);
  }

  function clearForm() {
    setAlertForm(EMPTY_ALERT);
  }

  const severity = analysis?.triage?.severity || "low";

  return (
    <div className="app-shell">
      <div className="bg-orb orb-1" />
      <div className="bg-orb orb-2" />
      <div className="bg-orb orb-3" />

      <header className="hero reveal">
        <p className="eyebrow">Step 3 Frontend Console</p>
        <h1>AegisAI SOC Mission Panel</h1>
        <p>
          Unified incident workflow for alert intake, triage interpretation, and response actioning.
        </p>
        <div className="status-row">
          <span className={`health-pill ${health.status === "ok" ? "up" : "down"}`}>
            API {health.status === "ok" ? "online" : "offline"}
          </span>
          <span className="mono">v{health.version}</span>
          <span className="mono">Last check: {prettyTime(new Date().toISOString())}</span>
        </div>
      </header>

      <main className="layout reveal delay-1">
        <section className="panel form-panel">
          <div className="panel-head">
            <h2>Alert Intake</h2>
            <p>Submit structured security alerts to the SOC orchestrator.</p>
          </div>

          <form onSubmit={handleAnalyze} className="stack-12">
            <div className="grid two">
              <label>
                Source
                <input
                  value={alertForm.source}
                  onChange={(e) => updateField("source", e.target.value)}
                  placeholder="SIEM"
                />
              </label>
              <label>
                Host *
                <input
                  value={alertForm.host}
                  onChange={(e) => updateField("host", e.target.value)}
                  placeholder="FIN-WS-442"
                  required
                />
              </label>
            </div>

            <div className="grid two">
              <label>
                User
                <input
                  value={alertForm.user}
                  onChange={(e) => updateField("user", e.target.value)}
                  placeholder="finance.admin"
                />
              </label>
              <label>
                IP Address
                <input
                  value={alertForm.ip_address}
                  onChange={(e) => updateField("ip_address", e.target.value)}
                  placeholder="203.0.113.56"
                />
              </label>
            </div>

            <label>
              Process Name
              <input
                value={alertForm.process_name}
                onChange={(e) => updateField("process_name", e.target.value)}
                placeholder="mimikatz.exe"
              />
            </label>

            <label>
              Command Line
              <input
                value={alertForm.command_line}
                onChange={(e) => updateField("command_line", e.target.value)}
                placeholder="mimikatz.exe sekurlsa::logonpasswords"
              />
            </label>

            <label>
              Description *
              <textarea
                value={alertForm.description}
                onChange={(e) => updateField("description", e.target.value)}
                placeholder="Potential credential dumping behavior detected on endpoint"
                required
              />
            </label>

            <div className="button-row">
              <button type="submit" disabled={!canAnalyze || analyzing}>
                {analyzing ? "Analyzing..." : "Run Analysis"}
              </button>
              <button type="button" className="ghost" onClick={loadSample}>
                Load Sample
              </button>
              <button type="button" className="ghost" onClick={clearForm}>
                Clear
              </button>
            </div>

            {analyzeError && <p className="error">{analyzeError}</p>}
          </form>
        </section>

        <section className="panel output-panel">
          <div className="panel-head">
            <h2>Incident Output</h2>
            <p>Live response from the multi-agent analysis pipeline.</p>
          </div>

          {!analysis && <p className="placeholder">No analysis yet. Submit an alert to view output.</p>}

          {analysis && (
            <div className="stack-16">
              <div className="severity-row">
                <span className={`severity-chip ${severityClass[severity] || "sev-low"}`}>
                  {severity.toUpperCase()}
                </span>
                <span className="mono">Category: {analysis.triage.category}</span>
                <span className="mono">Priority: {analysis.response.containment_priority}</span>
              </div>

              <article className="result-card">
                <h3>Triage Reason</h3>
                <p>{analysis.triage.reason}</p>
              </article>

              <article className="result-card">
                <h3>Investigation</h3>
                <p className="mono">Confidence: {analysis.investigation.confidence.toFixed(2)}</p>
                <ul>
                  {analysis.investigation.findings.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
                <p className="mono">MITRE: {analysis.investigation.mapped_techniques.join(", ") || "N/A"}</p>
              </article>

              <article className="result-card">
                <h3>Response Actions</h3>
                <ul>
                  {analysis.response.actions.map((action) => (
                    <li key={action.action_id}>
                      <strong>{action.title}</strong>
                      <span>{action.reason}</span>
                    </li>
                  ))}
                </ul>
              </article>

              <article className="result-card">
                <h3>Executive Summary</h3>
                <p>{analysis.report.summary}</p>
              </article>
            </div>
          )}
        </section>
      </main>

      <section className="lower reveal delay-2">
        <article className="panel">
          <div className="panel-head">
            <h2>Knowledge Search</h2>
            <p>Query the SOC knowledge base for supporting context.</p>
          </div>
          <form onSubmit={handleKnowledgeSearch} className="inline-form">
            <input
              value={knowledgeQuery}
              onChange={(e) => setKnowledgeQuery(e.target.value)}
              placeholder="Search indicators, techniques, or tooling"
            />
            <button type="submit" disabled={knowledgeLoading}>
              {knowledgeLoading ? "Searching..." : "Search"}
            </button>
          </form>
          {knowledgeError && <p className="error">{knowledgeError}</p>}
          <div className="stack-12">
            {knowledgeResults.map((entry) => (
              <div className="result-card" key={entry.entry_id}>
                <h3>{entry.title}</h3>
                <p>{entry.content}</p>
                <p className="mono">{entry.tags.join(" · ")}</p>
              </div>
            ))}
            {!knowledgeLoading && knowledgeResults.length === 0 && (
              <p className="placeholder">Run a search to retrieve knowledge entries.</p>
            )}
          </div>
        </article>

        <article className="panel">
          <div className="panel-head">
            <h2>Playbook Catalog</h2>
            <p>Available execution guides for containment actions.</p>
          </div>

          {playbookError && <p className="error">{playbookError}</p>}

          <div className="stack-12">
            {playbooks.map((playbook) => (
              <div className="result-card" key={playbook.id}>
                <h3>{playbook.name}</h3>
                <p>{playbook.description || "No description provided."}</p>
                <p className="mono">ID: {playbook.id}</p>
              </div>
            ))}
            {!playbookError && playbooks.length === 0 && (
              <p className="placeholder">No playbooks found from the backend.</p>
            )}
          </div>
        </article>
      </section>
    </div>
  );
}
