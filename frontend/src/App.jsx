
import { useEffect, useState } from "react";
import "./App.css";

const API_URL = "http://127.0.0.1:8000/api/disagreements/";

const reasonLabels = {
  VALUE_MISMATCH: "Value Mismatch",
  MISSING_IN_B: "Missing in B",
  ORPHAN_IN_B: "Orphan in B",
  DUPLICATE_IN_B: "Duplicate in B",
  LOCATION_MISMATCH: "Location Mismatch",
};

function App() {
  const [org, setOrg] = useState("ORG-A");
  const [reason, setReason] = useState("");
  const [sort, setSort] = useState("-value");
  const [records, setRecords] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");

  useEffect(() => {
    const controller = new AbortController();

    async function loadData() {
      setLoading(true);
      setError("");
      setRecords([]);

      const params = new URLSearchParams({ org, sort });
      if (reason) params.set("reason", reason);

      try {
        const response = await fetch(
          `${API_URL}?${params.toString()}`,
          { signal: controller.signal }
        );

        if (!response.ok) {
          throw new Error(`API returned ${response.status}`);
        }

        const data = await response.json();

        if (!Array.isArray(data.results)) {
          throw new Error("Invalid API response");
        }

        if (!controller.signal.aborted) {
          setRecords(data.results);
        }
      } catch (err) {
        if (!controller.signal.aborted) {
          setError(err.message);
        }
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      }
    }

    loadData();
    return () => controller.abort();
  }, [org, reason, sort]);

  const visibleRecords = records.filter((record) => {
    const query = search.trim().toLowerCase();
    return (
      !query ||
      record.record_id.toLowerCase().includes(query) ||
      record.location_id.toLowerCase().includes(query) ||
      record.reason.toLowerCase().includes(query)
    );
  });

  const countReason = (value) =>
    visibleRecords.filter((record) => record.reason === value).length;

  const metrics = [
    {
      label: "Total Disagreements",
      value: visibleRecords.length,
      className: "metric-teal",
      symbol: "◈",
      detail: "Records requiring review",
    },
    {
      label: "Value Mismatches",
      value: countReason("VALUE_MISMATCH"),
      className: "metric-amber",
      symbol: "≠",
      detail: "Financial discrepancies",
    },
    {
      label: "Missing Records",
      value: countReason("MISSING_IN_B"),
      className: "metric-rose",
      symbol: "⊘",
      detail: "Absent from System B",
    },
    {
      label: "Duplicate Entries",
      value: countReason("DUPLICATE_IN_B"),
      className: "metric-violet",
      symbol: "▣",
      detail: "Potential duplicate payments",
    },
  ];

  const formatAmount = (value) =>
    value === null || value === undefined
      ? "—"
      : Number(value).toLocaleString("en-IN", {
          minimumFractionDigits: 2,
          maximumFractionDigits: 2,
        });

  function exportCSV() {
    const escapeCell = (value) =>
      `"${String(value ?? "").replaceAll('"', '""')}"`;

    const headers = [
      "Record ID",
      "Location",
      "Reason",
      "System A Value",
      "System B Value",
    ];

    const rows = visibleRecords.map((record) => [
      record.record_id,
      record.location_id,
      record.reason,
      record.system_a_value,
      record.system_b_value,
    ]);

    const csv = [headers, ...rows]
      .map((row) => row.map(escapeCell).join(","))
      .join("\r\n");

    const blob = new Blob([csv], {
      type: "text/csv;charset=utf-8;",
    });

    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `dealeros-${org.toLowerCase()}-disagreements.csv`;
    link.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">D</div>
          <div>
            <strong>DealerOS</strong>
            <small>OPERATIONS SUITE</small>
          </div>
        </div>

        <div className="nav-caption">WORKSPACE</div>

        <nav className="navigation" aria-label="Main navigation">
          <a className="nav-active" href="#overview">
            <span>◈</span> Overview
          </a>
          <a href="#reconciliation">
            <span>▤</span> Reconciliation
          </a>
        </nav>

        <div className="sidebar-bottom">
          <span className="status-dot" />
          Local Development
          <small>Django REST + React</small>
        </div>
      </aside>

      <main className="main-content" id="overview">
        <header className="topbar">
          <div>
            <div className="breadcrumb">
              WORKSPACE / RECONCILIATION
            </div>
            <h1>Operations Overview</h1>
            <p>
              Monitor financial discrepancies across your systems.
            </p>
          </div>

          <div className="topbar-right">
            <span className="environment-pill">
              <span className="status-dot" />
              Development
            </span>
            <div className="avatar">DO</div>
          </div>
        </header>

        <section className="welcome-panel">
          <div>
            <div className="welcome-label">
              RECONCILIATION CONTROL CENTER
            </div>
            <h2>Financial clarity, in one place.</h2>
            <p>
              Track mismatches, identify missing records,
              and review exceptions with confidence.
            </p>
          </div>
          <div className="welcome-symbol" aria-hidden="true">
            ◈
          </div>
        </section>

        <div className="section-heading">
          <div>
            <h2>Key Metrics</h2>
            <p>
              {org} · {reason ? reasonLabels[reason] : "All reasons"}
            </p>
          </div>
        </div>

        <section className="metrics-grid" aria-label="Key metrics">
          {metrics.map((metric) => (
            <div
              className={`metric-card ${metric.className}`}
              key={metric.label}
            >
              <div className="metric-heading">
                <span>{metric.label}</span>
                <span className="metric-symbol">{metric.symbol}</span>
              </div>
              <strong>{loading ? "..." : metric.value}</strong>
              <small>{metric.detail}</small>
            </div>
          ))}
        </section>

        <section className="workspace-panel" id="reconciliation">
          <div className="panel-heading">
            <div>
              <h2>Reconciliation Workspace</h2>
              <p>
                Explore, filter, and export disagreement records.
              </p>
            </div>
            <button
              className="export-button"
              onClick={exportCSV}
              disabled={loading || !!error || visibleRecords.length === 0}
            >
              ↓ Export CSV
            </button>
          </div>

          <div className="toolbar">
            <label>
              Organization
              <select
                value={org}
                onChange={(event) => setOrg(event.target.value)}
              >
                <option value="ORG-A">ORG-A</option>
                <option value="ORG-B">ORG-B</option>
              </select>
            </label>

            <label>
              Disagreement
              <select
                value={reason}
                onChange={(event) => setReason(event.target.value)}
              >
                <option value="">All Reasons</option>
                {Object.entries(reasonLabels).map(([value, label]) => (
                  <option value={value} key={value}>
                    {label}
                  </option>
                ))}
              </select>
            </label>

            <label>
              Sort
              <select
                value={sort}
                onChange={(event) => setSort(event.target.value)}
              >
                <option value="-value">Highest Value</option>
                <option value="value">Lowest Value</option>
                <option value="record_id">Record ID</option>
                <option value="-record_id">Record ID Descending</option>
              </select>
            </label>

            <label>
              Search Records
              <input
                type="search"
                placeholder="Search ID, location, reason..."
                value={search}
                onChange={(event) => setSearch(event.target.value)}
              />
            </label>
          </div>

          <div className="table-heading">
            <h3>Disagreement Records</h3>
            <span className="count-pill">
              {loading ? "Loading" : `${visibleRecords.length} records`}
            </span>
          </div>

          {error && (
            <div className="error-banner" role="alert">
              {error}. Check the Django backend connection.
            </div>
          )}

          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>Record ID</th>
                  <th>Location</th>
                  <th>Disagreement</th>
                  <th>System A Value</th>
                  <th>System B Value</th>
                </tr>
              </thead>
              <tbody>
                {loading || visibleRecords.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="empty-state">
                      {loading
                        ? "Loading reconciliation data..."
                        : error
                          ? "Unable to load records."
                          : "No matching records found."}
                    </td>
                  </tr>
                ) : (
                  visibleRecords.map((record, index) => (
                    <tr
                      key={`${record.record_id}-${record.reason}-${index}`}
                    >
                      <td className="record-code">{record.record_id}</td>
                      <td>{record.location_id}</td>
                      <td>
                        <span
                          className={`reason-badge badge-${record.reason.toLowerCase()}`}
                        >
                          <span className="badge-dot" />
                          {reasonLabels[record.reason] || record.reason}
                        </span>
                      </td>
                      <td>{formatAmount(record.system_a_value)}</td>
                      <td>{formatAmount(record.system_b_value)}</td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </section>

        <footer className="app-footer">
          DealerOS Command Center · Reconciliation Module
          <span>Powered by Django REST API</span>
        </footer>
      </main>
    </div>
  );
}

export default App;
