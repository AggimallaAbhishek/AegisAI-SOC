import { useEffect, useMemo, useRef, useState } from "react";
import {
  analyzeAlert,
  getCaseStoreStatus,
  getHealth,
  getKpiOverview,
  getKpiTrends,
  getPlaybooks,
  getSlaOverview,
  searchKnowledge
} from "./api";

const ROLE_OPTIONS = ["admin", "manager", "analyst", "viewer"];

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

function safePercent(value) {
  if (typeof value !== "number") return "0.00";
  return value.toFixed(2);
}

export default function App() {
  const isMounted = useRef(true);

  const [health, setHealth] = useState({ status: "checking", version: "-" });
  const [lastCheck, setLastCheck] = useState(new Date().toISOString());
  const [role, setRole] = useState(() => {
    const stored = window.localStorage.getItem("aegisai_soc_role") || "analyst";
    return ROLE_OPTIONS.includes(stored) ? stored : "analyst";
  });

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

  const [kpi, setKpi] = useState(null);
  const [sla, setSla] = useState(null);
  const [trends, setTrends] = useState(null);
  const [caseStore, setCaseStore] = useState(null);
  const [phase3Loading, setPhase3Loading] = useState(false);
  const [phase3Error, setPhase3Error] = useState("");

  useEffect(() => {
    return () => {
      isMounted.current = false;
    };
  }, []);

  useEffect(() => {
    window.localStorage.setItem("aegisai_soc_role", role);
  }, [role]);

  async function loadHealthData(activeRole) {
    try {
      const data = await getHealth(activeRole);
      if (!isMounted.current) return;
      setHealth({ status: data.status, version: data.version || "-" });
    } catch {
      if (!isMounted.current) return;
      setHealth({ status: "offline", version: "-" });
    } finally {
      if (!isMounted.current) return;
      setLastCheck(new Date().toISOString());
    }
  }

  async function loadPlaybookData(activeRole) {
    try {
      const data = await getPlaybooks(activeRole);
      if (!isMounted.current) return;
      setPlaybooks(Array.isArray(data.playbooks) ? data.playbooks : []);
      setPlaybookError("");
    } catch (error) {
      if (!isMounted.current) return;
      setPlaybookError(error.message || "Failed to load playbooks");
    }
  }

  async function loadPhase3Data(activeRole, showLoader = true) {
    if (showLoader) {
      setPhase3Loading(true);
    }
    setPhase3Error("");

    try {
      const [kpiData, slaData, trendData, caseStoreData] = await Promise.all([
        getKpiOverview(30, activeRole),
        getSlaOverview(30, activeRole),
        getKpiTrends(14, activeRole),
        getCaseStoreStatus(activeRole)
      ]);

      if (!isMounted.current) return;
      setKpi(kpiData);
      setSla(slaData);
      setTrends(trendData);
      setCaseStore(caseStoreData);
    } catch (error) {
      if (!isMounted.current) return;
      setPhase3Error(error.message || "Phase 3 dashboard request failed");
    } finally {
      if (!isMounted.current) return;
      if (showLoader) {
        setPhase3Loading(false);
      }
    }
  }

  useEffect(() => {
    loadHealthData(role);
    loadPlaybookData(role);
    loadPhase3Data(role, true);

    const timer = setInterval(() => {
      loadHealthData(role);
      loadPhase3Data(role, false);
    }, 15000);

    return () => {
      clearInterval(timer);
    };
  }, [role]);

  const canAnalyze = useMemo(
    () => alertForm.host.trim() && alertForm.description.trim(),
    [alertForm]
  );

  const latestTrend = useMemo(() => {
    const rows = trends?.daily_incidents;
    if (!Array.isArray(rows) || rows.length === 0) return null;
    return rows[rows.length - 1];
  }, [trends]);

  async function handleAnalyze(event) {
    event.preventDefault();
    setAnalyzeError("");
    setAnalyzing(true);
    try {
      const payload = {
        ...alertForm,
        source: alertForm.source || "SIEM"
      };
      const data = await analyzeAlert(payload, role);
      if (!isMounted.current) return;
      setAnalysis(data);
      await loadPhase3Data(role, false);
    } catch (error) {
      if (!isMounted.current) return;
      setAnalyzeError(error.message || "Failed to analyze alert");
    } finally {
      if (!isMounted.current) return;
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
      const data = await searchKnowledge(query, role);
      if (!isMounted.current) return;
      setKnowledgeResults(Array.isArray(data.results) ? data.results : []);
    } catch (error) {
      if (!isMounted.current) return;
      setKnowledgeError(error.message || "Knowledge search failed");
    } finally {
      if (!isMounted.current) return;
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
        <p className="eyebrow">Step 9 Frontend + Automation</p>
        <h1>AegisAI SOC Mission Panel</h1>
        <p>
          Unified incident workflow for alert intake, triage interpretation, and response actioning.
        </p>
        <div className="status-row">
          <span className={`health-pill ${health.status === "ok" ? "up" : "down"}`}>
            API {health.status === "ok" ? "online" : "offline"}
          </span>
          <span className="mono">v{health.version}</span>
          <span className="mono">Role: {role}</span>
          <span className="mono">KPI source: {kpi?.data_source || "loading"}</span>
          <span className="mono">Last check: {prettyTime(lastCheck)}</span>
        </div>

        <div className="role-toolbar">
          <label className="role-control">
            SOC Request Role
            <select value={role} onChange={(event) => setRole(event.target.value)}>
              {ROLE_OPTIONS.map((item) => (
                <option key={item} value={item}>
                  {item}
                </option>
              ))}
            </select>
          </label>
        </div>
      </header>

      <section className="phase3-grid reveal delay-1">
        <article className="panel metric-panel">
          <div className="panel-head">
            <h2>Phase 3 KPI</h2>
            <p>Live dashboard telemetry from the backend case store.</p>
          </div>

          {phase3Error && <p className="error">{phase3Error}</p>}

          {!kpi && phase3Loading && <p className="placeholder">Loading KPI and SLA telemetry...</p>}

          {kpi && (
            <div className="metric-cards">
              <div className="result-card metric-card">
                <h3>Total Incidents</h3>
                <p className="metric-value">{kpi.total_incidents}</p>
                <p className="mono">Resolved: {kpi.resolved_incidents}</p>
                <p className="mono">Critical: {kpi.critical_incidents}</p>
              </div>

              <div className="result-card metric-card">
                <h3>Automation Rate</h3>
                <p className="metric-value">{safePercent(kpi.automation_rate_percent)}%</p>
                <p className="mono">False Positive: {safePercent(kpi.false_positive_rate_percent)}%</p>
                <p className="mono">Window: {kpi.window_days} days</p>
              </div>

              <div className="result-card metric-card">
                <h3>SLA Compliance</h3>
                <p className="metric-value">{safePercent(sla?.compliance_percent)}%</p>
                <p className="mono">Within SLA: {sla?.within_sla || 0}</p>
                <p className="mono">Breaches: {sla?.breaches || 0}</p>
              </div>

              <div className="result-card metric-card">
                <h3>Trend Snapshot</h3>
                {latestTrend ? (
                  <>
                    <p className="metric-value">{latestTrend.incidents}</p>
                    <p className="mono">Date: {latestTrend.date}</p>
                    <p className="mono">
                      Critical: {latestTrend.critical} | Resolved: {latestTrend.resolved}
                    </p>
                  </>
                ) : (
                  <p className="placeholder">No trend records in selected window.</p>
                )}
              </div>

              <div className="result-card metric-card metric-wide">
                <h3>Case Store Status</h3>
                <p className="mono">
                  configured={String(Boolean(caseStore?.configured))} | driver_available=
                  {String(Boolean(caseStore?.driver_available))} | ready={String(Boolean(caseStore?.ready))}
                </p>
                <p className="mono">request_role={caseStore?.request_role || role}</p>
              </div>
            </div>
          )}
        </article>
      </section>

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
                <span className="mono">Case: {analysis.case_id || "N/A"}</span>
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

              {analysis.automation && (
                <article className="result-card">
                  <h3>Automation Delivery</h3>
                  <p className="mono">Jira: {analysis.automation.jira?.status || "unknown"}</p>
                  {analysis.automation.jira?.ticket_key && (
                    <p className="mono">
                      Ticket: {analysis.automation.jira.ticket_key}
                      {analysis.automation.jira.issue_url && (
                        <>
                          {" "}
                          (
                          <a href={analysis.automation.jira.issue_url} target="_blank" rel="noreferrer">
                            open
                          </a>
                          )
                        </>
                      )}
                    </p>
                  )}
                  {analysis.automation.jira?.error && (
                    <p className="mono">Jira error: {analysis.automation.jira.error}</p>
                  )}

                  <p className="mono">Slack: {analysis.automation.slack?.status || "unknown"}</p>
                  {analysis.automation.slack?.error && (
                    <p className="mono">Slack error: {analysis.automation.slack.error}</p>
                  )}
                </article>
              )}
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
