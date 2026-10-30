import React, { useState, useEffect } from 'react';
import {
  LayoutDashboard,
  Play,
  Users,
  FileCheck,
  Laptop,
  GraduationCap,
  ShieldAlert,
  Activity,
  History,
  CheckCircle2,
  Clock,
  AlertTriangle,
  Upload,
  RefreshCw,
  ExternalLink,
  ChevronRight,
  UserCheck,
  Building2,
  Mail,
  Compass,
  ArrowRight
} from 'lucide-react';
import './style.css';

const API_BASE = '/api';

export default function App() {
  const [activeTab, setActiveTab] = useState('Dashboard');
  const [employees, setEmployees] = useState([]);
  const [selectedEmp, setSelectedEmp] = useState(null);
  const [empDetail, setEmpDetail] = useState(null);
  const [approvals, setApprovals] = useState([]);
  const [agents, setAgents] = useState([]);
  const [trainingTasks, setTrainingTasks] = useState([]);
  const [documents, setDocuments] = useState([]);
  const [auditLogs, setAuditLogs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [pipelineRunning, setPipelineRunning] = useState(false);
  const [pipelineLogs, setPipelineLogs] = useState([]);
  const [pipelineStage, setPipelineStage] = useState(0);

  // New Employee Form State
  const [newEmpName, setNewEmpName] = useState('');
  const [newEmpDept, setNewEmpDept] = useState('Engineering');
  const [newEmpRole, setNewEmpRole] = useState('Software Engineer');
  const [showAddModal, setShowAddModal] = useState(false);
  const [uploadStatus, setUploadStatus] = useState('');

  // Initial Data Fetching
  const loadData = async () => {
    try {
      // Fetch Employees
      const resEmps = await fetch(`${API_BASE}/employees`);
      if (resEmps.ok) {
        const data = await resEmps.json();
        setEmployees(data);
        if (!selectedEmp && data.length > 0) {
          setSelectedEmp(data[0]);
        }
      }

      // Fetch Approvals
      const resApps = await fetch(`${API_BASE}/approvals`);
      if (resApps.ok) {
        const data = await resApps.json();
        setApprovals(data);
      }

      // Fetch Agent Status
      const resAgents = await fetch(`${API_BASE}/agents/status`);
      if (resAgents.ok) {
        const data = await resAgents.json();
        setAgents(data);
      }
    } catch (e) {
      console.log('Using local fallback state if API not reachable yet:', e);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  // Fetch employee specific details when selectedEmp changes
  useEffect(() => {
    if (!selectedEmp) return;
    const fetchDetails = async () => {
      try {
        const res = await fetch(`${API_BASE}/employees/${selectedEmp.employee_id || selectedEmp.id}`);
        if (res.ok) {
          const data = await res.json();
          setEmpDetail(data);
          setTrainingTasks(data.training_tasks || []);
          setDocuments(data.documents || []);
        }

        const logRes = await fetch(`${API_BASE}/onboarding/${selectedEmp.employee_id || selectedEmp.id}/logs`);
        if (logRes.ok) {
          const ldata = await logRes.json();
          setAuditLogs(ldata.logs || []);
        }
      } catch (err) {
        console.error(err);
      }
    };
    fetchDetails();
  }, [selectedEmp]);

  // Run End-to-End Pipeline
  const runPipeline = async (emp) => {
    const target = emp || selectedEmp || employees[0];
    if (!target) return;
    setPipelineRunning(true);
    setPipelineStage(1);
    setPipelineLogs([
      `[Supervisor Orchestrator] Initializing onboarding workflow for ${target.employee_name || target.name}...`,
    ]);

    try {
      const payload = {
        employee_id: target.employee_id || target.id,
        employee_name: target.employee_name || target.name,
        department: target.department || 'Engineering',
        designation: target.role || 'Software Engineer',
      };

      const res = await fetch(`${API_BASE}/pipeline/run-full`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (res.ok) {
        const result = await res.json();
        // Simulate step progression for rich UX
        setTimeout(() => setPipelineStage(2), 600);
        setTimeout(() => setPipelineStage(3), 1200);
        setTimeout(() => setPipelineStage(4), 1800);
        setTimeout(() => setPipelineStage(5), 2400);
        setTimeout(() => {
          setPipelineStage(6);
          setPipelineLogs(result.audit_trail || []);
          setPipelineRunning(false);
          loadData();
        }, 3000);
      } else {
        setPipelineRunning(false);
      }
    } catch (e) {
      console.error(e);
      setPipelineRunning(false);
    }
  };

  // Handle Approvals
  const handleApprovalAction = async (approvalId, action) => {
    try {
      const res = await fetch(`${API_BASE}/approvals/${approvalId}/action`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action, approver: 'HR Supervisor', notes: `Actioned as ${action}` }),
      });
      if (res.ok) {
        loadData();
      }
    } catch (e) {
      console.error(e);
    }
  };

  // Handle Task Update
  const handleTaskStatusChange = async (taskId, newStatus) => {
    if (!selectedEmp) return;
    const empId = selectedEmp.employee_id || selectedEmp.id;
    try {
      const res = await fetch(`${API_BASE}/training/${empId}/tasks/${taskId}`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: newStatus }),
      });
      if (res.ok) {
        setTrainingTasks((old) =>
          old.map((t) => (t.id === taskId ? { ...t, status: newStatus } : t))
        );
      }
    } catch (e) {
      console.error(e);
    }
  };

  // Handle File Upload
  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setUploadStatus(`Uploading ${file.name}...`);
    const formData = new FormData();
    formData.append('file', file);
    if (selectedEmp) {
      formData.append('employee_id', selectedEmp.employee_id || selectedEmp.id);
    }
    try {
      const res = await fetch(`${API_BASE}/documents/upload`, {
        method: 'POST',
        body: formData,
      });
      if (res.ok) {
        setUploadStatus(`Successfully uploaded ${file.name}. Triggering verification...`);
        setTimeout(() => {
          runPipeline(selectedEmp);
          setUploadStatus('');
        }, 1200);
      }
    } catch (err) {
      setUploadStatus('Upload failed. Check backend connection.');
    }
  };

  // Handle Create Employee
  const handleCreateEmployee = async (e) => {
    e.preventDefault();
    if (!newEmpName) return;
    try {
      const res = await fetch(`${API_BASE}/employees`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          employee_name: newEmpName,
          department: newEmpDept,
          role: newEmpRole,
        }),
      });
      if (res.ok) {
        const created = await res.json();
        setShowAddModal(false);
        setNewEmpName('');
        await loadData();
        setSelectedEmp(created);
        runPipeline(created);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const pendingApprovalsCount = approvals.filter((a) => a.status === 'Pending').length;
  const completedEmployeesCount = employees.filter(
    (e) => e.progress === 100 || e.onboarding_status === 'completed'
  ).length;

  return (
    <div className="app">
      {/* ── Sidebar Navigation ── */}
      <aside className="sidebar">
        <div className="brand">
          EnterpriseFlow AI
          <span>Unified Multi-Agent System</span>
        </div>

        <div className="nav-label">Core Pipeline</div>
        <button
          className={`nav-item ${activeTab === 'Dashboard' ? 'active' : ''}`}
          onClick={() => setActiveTab('Dashboard')}
        >
          <LayoutDashboard size={18} />
          Dashboard
        </button>

        <button
          className={`nav-item ${activeTab === 'Live Pipeline' ? 'active' : ''}`}
          onClick={() => setActiveTab('Live Pipeline')}
        >
          <Play size={18} />
          Live Pipeline
          {pipelineRunning && <span className="online-indicator" />}
        </button>

        <div className="nav-label" style={{ marginTop: '16px' }}>
          Agent Operations
        </div>
        <button
          className={`nav-item ${activeTab === 'Employees' ? 'active' : ''}`}
          onClick={() => setActiveTab('Employees')}
        >
          <Users size={18} />
          Employees
        </button>

        <button
          className={`nav-item ${activeTab === 'Document Verification' ? 'active' : ''}`}
          onClick={() => setActiveTab('Document Verification')}
        >
          <FileCheck size={18} />
          Doc Verification
        </button>

        <button
          className={`nav-item ${activeTab === 'IT & Hardware' ? 'active' : ''}`}
          onClick={() => setActiveTab('IT & Hardware')}
        >
          <Laptop size={18} />
          IT Provisioning
        </button>

        <button
          className={`nav-item ${activeTab === 'Training' ? 'active' : ''}`}
          onClick={() => setActiveTab('Training')}
        >
          <GraduationCap size={18} />
          Training & LMS
        </button>

        <button
          className={`nav-item ${activeTab === 'Human Approvals' ? 'active' : ''}`}
          onClick={() => setActiveTab('Human Approvals')}
        >
          <ShieldAlert size={18} />
          HITL Approvals
          {pendingApprovalsCount > 0 && (
            <span className="count-badge">{pendingApprovalsCount}</span>
          )}
        </button>

        <button
          className={`nav-item ${activeTab === 'AI Agents' ? 'active' : ''}`}
          onClick={() => setActiveTab('AI Agents')}
        >
          <Activity size={18} />
          Agent Registry
        </button>

        <button
          className={`nav-item ${activeTab === 'Audit Logs' ? 'active' : ''}`}
          onClick={() => setActiveTab('Audit Logs')}
        >
          <History size={18} />
          Audit Trails
        </button>

        <div className="sidebar-bottom">
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span className="online-indicator" />
            <span>FastAPI + LangGraph Online</span>
          </div>
          <div style={{ fontSize: '11px', color: 'var(--text-dim)', marginTop: '6px' }}>
            Port 8000 · 4 Agents Synced
          </div>
        </div>
      </aside>

      {/* ── Main Workspace ── */}
      <main className="main">
        {/* Top Header */}
        <header className="topbar">
          <div>
            <div className="topbar-sub">TrizenHR Automation Platform</div>
            <h1>{activeTab}</h1>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <button className="btn-secondary" onClick={loadData}>
              <RefreshCw size={14} style={{ marginRight: '6px' }} />
              Refresh
            </button>
            <button
              className="btn-primary"
              onClick={() => runPipeline(selectedEmp)}
              disabled={pipelineRunning}
            >
              <Play size={14} />
              {pipelineRunning ? 'Pipeline Executing...' : 'Run Pipeline'}
            </button>
          </div>
        </header>

        {/* ── 1. DASHBOARD TAB ── */}
        {activeTab === 'Dashboard' && (
          <div>
            {/* Quick Stats Grid */}
            <div className="stats-grid">
              <div className="stat-card">
                <div className="stat-header">
                  <span>Total Employees</span>
                  <Users size={18} color="#6366f1" />
                </div>
                <div className="stat-value">{employees.length}</div>
                <div className="stat-sub">Across 5 departments</div>
              </div>

              <div className="stat-card">
                <div className="stat-header">
                  <span>Completed Onboarding</span>
                  <CheckCircle2 size={18} color="#10b981" />
                </div>
                <div className="stat-value">{completedEmployeesCount}</div>
                <div className="stat-sub">Ready for Day 1</div>
              </div>

              <div className="stat-card">
                <div className="stat-header">
                  <span>Pending Approvals</span>
                  <ShieldAlert size={18} color="#f59e0b" />
                </div>
                <div className="stat-value">{pendingApprovalsCount}</div>
                <div className="stat-sub">Awaiting manager / IT sign-off</div>
              </div>

              <div className="stat-card">
                <div className="stat-header">
                  <span>AI Worker Agents</span>
                  <Activity size={18} color="#ec4899" />
                </div>
                <div className="stat-value">{agents.length || 6}</div>
                <div className="stat-sub">All systems operational</div>
              </div>
            </div>

            {/* Employee Directory Panel */}
            <div className="panel">
              <div className="panel-header">
                <h3>Employee Onboarding Pipeline</h3>
                <button className="btn-secondary" onClick={() => setShowAddModal(true)}>
                  + Register Candidate
                </button>
              </div>
              <p className="panel-sub">
                Live status of multi-agent onboarding tasks across all enrolled candidates.
              </p>

              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th>Candidate</th>
                      <th>Department & Role</th>
                      <th>Status</th>
                      <th>Progress</th>
                      <th>Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {employees.map((emp) => (
                      <tr key={emp.employee_id || emp.id}>
                        <td>
                          <div className="emp-name-cell">
                            <div
                              className="avatar-badge"
                              style={{ background: emp.avatar_color || '#6366f1' }}
                            >
                              {emp.avatar || 'EP'}
                            </div>
                            <div>
                              <div style={{ fontWeight: 600 }}>{emp.employee_name || emp.name}</div>
                              <small style={{ color: 'var(--text-dim)' }}>
                                {emp.employee_id || emp.id} · {emp.email}
                              </small>
                            </div>
                          </div>
                        </td>
                        <td>
                          <div style={{ fontWeight: 500 }}>{emp.department}</div>
                          <small style={{ color: 'var(--text-muted)' }}>{emp.role}</small>
                        </td>
                        <td>
                          <span className={`status-pill ${emp.onboarding_status}`}>
                            {emp.onboarding_status.replace('_', ' ')}
                          </span>
                        </td>
                        <td>
                          <div className="progress-bar">
                            <div className="progress-track">
                              <div
                                className="progress-fill"
                                style={{ width: `${emp.progress || 0}%` }}
                              />
                            </div>
                            <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                              {emp.progress || 0}%
                            </span>
                          </div>
                        </td>
                        <td>
                          <button
                            className="btn-secondary"
                            style={{ padding: '6px 12px', fontSize: '12px' }}
                            onClick={() => {
                              setSelectedEmp(emp);
                              setActiveTab('Live Pipeline');
                              runPipeline(emp);
                            }}
                          >
                            Launch Pipeline
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* AI Agent Status Grid */}
            <div className="panel">
              <div className="panel-header">
                <h3>Active Agent Workforce</h3>
              </div>
              <div className="grid-3">
                {agents.map((ag) => (
                  <div className="agent-card" key={ag.name}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <Activity size={18} color="var(--primary)" />
                      <div style={{ fontWeight: 600, fontSize: '13.5px' }}>{ag.name}</div>
                    </div>
                    <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{ag.role}</div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span className="status-pill active">{ag.status}</span>
                      <small style={{ color: 'var(--text-dim)' }}>{ag.type}</small>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* ── 2. LIVE PIPELINE VISUALIZER TAB ── */}
        {activeTab === 'Live Pipeline' && (
          <div>
            <div className="panel">
              <div className="panel-header">
                <div>
                  <h3>Interactive LangGraph Pipeline Runner</h3>
                  <p className="panel-sub" style={{ margin: 0 }}>
                    Target Employee:{' '}
                    <strong>
                      {selectedEmp ? selectedEmp.employee_name || selectedEmp.name : 'None Selected'}
                    </strong>{' '}
                    ({selectedEmp?.department} · {selectedEmp?.role})
                  </p>
                </div>
                <div style={{ display: 'flex', gap: '10px' }}>
                  <select
                    style={{
                      background: 'var(--card-bg)',
                      color: 'white',
                      border: '1px solid var(--card-border)',
                      padding: '8px 12px',
                      borderRadius: '8px',
                    }}
                    value={selectedEmp?.employee_id || selectedEmp?.id || ''}
                    onChange={(e) => {
                      const found = employees.find(
                        (emp) => (emp.employee_id || emp.id) === e.target.value
                      );
                      if (found) setSelectedEmp(found);
                    }}
                  >
                    {employees.map((e) => (
                      <option key={e.employee_id || e.id} value={e.employee_id || e.id}>
                        {e.employee_name || e.name} ({e.department})
                      </option>
                    ))}
                  </select>
                  <button
                    className="btn-primary"
                    onClick={() => runPipeline(selectedEmp)}
                    disabled={pipelineRunning}
                  >
                    <Play size={14} />
                    {pipelineRunning ? 'Executing...' : 'Start Execution'}
                  </button>
                </div>
              </div>

              {/* Graphical Step Bar */}
              <div className="pipeline-bar">
                <div className="pipeline-line">
                  <div
                    className="pipeline-line-fill"
                    style={{ width: `${Math.min(100, (pipelineStage / 6) * 100)}%` }}
                  />
                </div>

                <div className={`pipeline-step ${pipelineStage >= 1 ? 'completed' : ''}`}>
                  <div className="step-circle">1</div>
                  <div className="step-label">Init State</div>
                </div>

                <div
                  className={`pipeline-step ${
                    pipelineStage === 2 ? 'active' : pipelineStage > 2 ? 'completed' : ''
                  }`}
                >
                  <div className="step-circle">2</div>
                  <div className="step-label">OCR & Doc Check</div>
                </div>

                <div
                  className={`pipeline-step ${
                    pipelineStage === 3 ? 'active' : pipelineStage > 3 ? 'completed' : ''
                  }`}
                >
                  <div className="step-circle">3</div>
                  <div className="step-label">IT Provisioning</div>
                </div>

                <div
                  className={`pipeline-step ${
                    pipelineStage === 4 ? 'active' : pipelineStage > 4 ? 'completed' : ''
                  }`}
                >
                  <div className="step-circle">4</div>
                  <div className="step-label">Team Allocation</div>
                </div>

                <div
                  className={`pipeline-step ${
                    pipelineStage === 5 ? 'active' : pipelineStage > 5 ? 'completed' : ''
                  }`}
                >
                  <div className="step-circle">5</div>
                  <div className="step-label">Training & Day 1</div>
                </div>

                <div className={`pipeline-step ${pipelineStage >= 6 ? 'completed' : ''}`}>
                  <div className="step-circle">🎉</div>
                  <div className="step-label">Finished</div>
                </div>
              </div>

              {/* Live Console Output */}
              <div style={{ marginTop: '24px' }}>
                <div
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    marginBottom: '8px',
                  }}
                >
                  <span style={{ fontSize: '12px', fontWeight: 700, color: 'var(--text-muted)' }}>
                    AGENT TELEMETRY CONSOLE
                  </span>
                  <span style={{ fontSize: '11px', color: 'var(--text-dim)' }}>
                    {pipelineLogs.length} events logged
                  </span>
                </div>
                <div className="terminal-card">
                  {pipelineLogs.length === 0 ? (
                    <div style={{ color: 'var(--text-dim)', fontStyle: 'italic' }}>
                      Click "Start Execution" above to run the multi-agent graph.
                    </div>
                  ) : (
                    pipelineLogs.map((log, i) => (
                      <div className="terminal-line" key={i}>
                        <span className="term-time">&gt;</span>
                        <span
                          className={`term-msg ${
                            typeof log === 'string' && log.includes('GATE')
                              ? 'term-gate'
                              : typeof log === 'string' && log.includes('completed')
                              ? 'term-success'
                              : typeof log === 'string' && log.includes('Error')
                              ? 'term-err'
                              : ''
                          }`}
                        >
                          {typeof log === 'string' ? log : JSON.stringify(log)}
                        </span>
                      </div>
                    ))
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ── 3. EMPLOYEES DIRECTORY TAB ── */}
        {activeTab === 'Employees' && (
          <div>
            <div className="panel">
              <div className="panel-header">
                <h3>Employee Directory & Profiles</h3>
                <button className="btn-primary" onClick={() => setShowAddModal(true)}>
                  + New Employee
                </button>
              </div>

              <div className="grid-2">
                {employees.map((emp) => (
                  <div
                    key={emp.employee_id || emp.id}
                    className="doc-card"
                    style={{
                      cursor: 'pointer',
                      border:
                        (selectedEmp?.employee_id || selectedEmp?.id) === (emp.employee_id || emp.id)
                          ? '2px solid var(--primary)'
                          : '1px solid var(--card-border)',
                    }}
                    onClick={() => setSelectedEmp(emp)}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
                      <div
                        className="avatar-badge"
                        style={{
                          background: emp.avatar_color || '#6366f1',
                          width: '44px',
                          height: '44px',
                          fontSize: '16px',
                        }}
                      >
                        {emp.avatar || 'EP'}
                      </div>
                      <div style={{ flex: 1 }}>
                        <div style={{ fontWeight: 700, fontSize: '15px' }}>
                          {emp.employee_name || emp.name}
                        </div>
                        <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                          {emp.role} · {emp.department}
                        </div>
                        <div style={{ fontSize: '11px', color: 'var(--text-dim)', marginTop: '2px' }}>
                          {emp.email}
                        </div>
                      </div>
                      <span className={`status-pill ${emp.onboarding_status}`}>
                        {emp.onboarding_status}
                      </span>
                    </div>

                    <div
                      style={{
                        display: 'grid',
                        gridTemplateColumns: '1fr 1fr',
                        gap: '8px',
                        fontSize: '12px',
                        marginTop: '8px',
                        padding: '10px',
                        background: 'rgba(0,0,0,0.2)',
                        borderRadius: '8px',
                      }}
                    >
                      <div>
                        <span style={{ color: 'var(--text-dim)' }}>Manager: </span>
                        <strong>{emp.manager || 'Priya Sharma'}</strong>
                      </div>
                      <div>
                        <span style={{ color: 'var(--text-dim)' }}>Buddy: </span>
                        <strong>{emp.buddy || 'Rohan Verma'}</strong>
                      </div>
                      <div>
                        <span style={{ color: 'var(--text-dim)' }}>Team: </span>
                        <span>{emp.team || 'Core Team'}</span>
                      </div>
                      <div>
                        <span style={{ color: 'var(--text-dim)' }}>Desk: </span>
                        <span>{emp.desk || '3rd Floor East'}</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* ── 4. DOCUMENT VERIFICATION TAB ── */}
        {activeTab === 'Document Verification' && (
          <div>
            <div className="panel">
              <div className="panel-header">
                <div>
                  <h3>Document Verification Hub (PyMuPDF OCR + Gemini LLM)</h3>
                  <p className="panel-sub" style={{ margin: 0 }}>
                    Viewing verification results for:{' '}
                    <strong>{selectedEmp?.employee_name || selectedEmp?.name}</strong>
                  </p>
                </div>
              </div>

              {/* Upload Dropzone */}
              <div className="dropzone" style={{ marginBottom: '24px' }}>
                <input
                  type="file"
                  id="doc-upload-input"
                  style={{ display: 'none' }}
                  onChange={handleFileUpload}
                  accept=".pdf,.png,.jpg,.jpeg"
                />
                <label htmlFor="doc-upload-input" style={{ cursor: 'pointer' }}>
                  <Upload size={32} color="var(--primary)" style={{ marginBottom: '8px' }} />
                  <div style={{ fontWeight: 600 }}>Drop candidate PDF documents here or click to browse</div>
                  <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '4px' }}>
                    Supports Aadhaar Card, Degree Certificate, Offer Letter, Bank Details
                  </div>
                </label>
                {uploadStatus && (
                  <div style={{ marginTop: '12px', fontSize: '13px', color: '#a5b4fc' }}>
                    {uploadStatus}
                  </div>
                )}
              </div>

              {/* Document Results Grid */}
              <div className="grid-2">
                {[
                  { id: 'aadhar_card', title: 'Aadhaar Identification' },
                  { id: 'degree_certificate', title: 'Educational Degree Certificate' },
                  { id: 'offer_letter_signed', title: 'Countersigned Offer Letter' },
                  { id: 'bank_details', title: 'Banking Details & Cheque' },
                ].map((item) => {
                  const match = documents.find((d) => d.name === item.id || d.doc_name === item.id);
                  return (
                    <div className="doc-card" key={item.id}>
                      <div className="doc-card-header">
                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          <FileCheck size={18} color="var(--primary)" />
                          <strong>{item.title}</strong>
                        </div>
                        <span className={`status-pill ${match?.readable ? 'passed' : 'pending'}`}>
                          {match?.readable ? 'Verified [OCR]' : 'Pending'}
                        </span>
                      </div>

                      <div style={{ fontSize: '12.5px', color: 'var(--text-muted)' }}>
                        <div>
                          Document Type:{' '}
                          <span style={{ color: 'white' }}>{match?.type || 'KYC Record'}</span>
                        </div>
                        <div>
                          Name Match:{' '}
                          <span style={{ color: match?.name_match ? '#34d399' : '#f87171' }}>
                            {match?.name_match ? 'Validated' : 'Awaiting Match'}
                          </span>
                        </div>
                        <div>
                          Confidence Score:{' '}
                          <span style={{ textTransform: 'capitalize', color: 'white' }}>
                            {match?.confidence || 'High'}
                          </span>
                        </div>
                        <div>
                          Extraction Engine:{' '}
                          <span style={{ color: '#c084fc' }}>
                            {match?.llm_used ? 'Gemini AI' : 'Rule-Based OCR'}
                          </span>
                        </div>
                      </div>

                      {match?.issues && match.issues.length > 0 && (
                        <div
                          style={{
                            background: 'var(--danger-bg)',
                            color: '#f87171',
                            padding: '8px',
                            borderRadius: '6px',
                            fontSize: '11px',
                          }}
                        >
                          Issues: {match.issues.join(', ')}
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        )}

        {/* ── 5. IT & HARDWARE TAB ── */}
        {activeTab === 'IT & Hardware' && (
          <div>
            <div className="panel">
              <div className="panel-header">
                <div>
                  <h3>IT Provisioning & Asset Inventory</h3>
                  <p className="panel-sub" style={{ margin: 0 }}>
                    Allocated to:{' '}
                    <strong>{selectedEmp?.employee_name || selectedEmp?.name}</strong> (
                    {selectedEmp?.department})
                  </p>
                </div>
              </div>

              <div className="grid-2">
                {/* Hardware Spec Card */}
                <div className="asset-card">
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <Laptop size={20} color="var(--blue)" />
                    <strong>Allocated Laptop Hardware</strong>
                  </div>
                  <div style={{ fontSize: '20px', fontWeight: 700, margin: '8px 0' }}>
                    {empDetail?.it_assets?.laptop_model || 'MacBook Pro 14" M3 Pro'}
                  </div>
                  <div style={{ fontSize: '12px', color: 'var(--text-muted)', lineHeight: '1.8' }}>
                    <div>
                      RAM:{' '}
                      <strong style={{ color: 'white' }}>
                        {empDetail?.it_assets?.specs?.ram || '18 GB Unified'}
                      </strong>
                    </div>
                    <div>
                      Storage:{' '}
                      <strong style={{ color: 'white' }}>
                        {empDetail?.it_assets?.specs?.storage || '512 GB SSD'}
                      </strong>
                    </div>
                    <div>
                      Operating System:{' '}
                      <strong style={{ color: 'white' }}>
                        {empDetail?.it_assets?.specs?.os || 'macOS Sonoma'}
                      </strong>
                    </div>
                    <div>
                      Peripherals:{' '}
                      <span style={{ color: 'white' }}>
                        {empDetail?.it_assets?.specs?.extras?.join(', ') ||
                          'Dell 27" 4K Monitor, Magic Keyboard & Mouse'}
                      </span>
                    </div>
                    <div>
                      Procurement Ticket ID:{' '}
                      <span style={{ fontFamily: 'var(--mono-font)', color: '#818cf8' }}>
                        {empDetail?.it_assets?.master_ticket || 'HW-609121'}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Software Access Card */}
                <div className="asset-card">
                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                    <Compass size={20} color="var(--purple)" />
                    <strong>Software Access Licenses</strong>
                  </div>
                  <div
                    style={{
                      display: 'grid',
                      gridTemplateColumns: '1fr 1fr',
                      gap: '8px',
                      marginTop: '8px',
                    }}
                  >
                    {[
                      { name: 'Slack', tier: 'Pro' },
                      { name: 'GitHub', tier: 'Enterprise' },
                      { name: 'Jira', tier: 'Standard' },
                      { name: 'Confluence', tier: 'Standard' },
                      { name: 'Tailscale VPN', tier: 'Teams' },
                      { name: 'AWS Console', tier: 'IAM Access' },
                    ].map((sw) => (
                      <div
                        key={sw.name}
                        style={{
                          background: 'rgba(0,0,0,0.2)',
                          padding: '8px',
                          borderRadius: '6px',
                          fontSize: '12px',
                        }}
                      >
                        <div style={{ fontWeight: 600 }}>{sw.name}</div>
                        <small style={{ color: 'var(--text-dim)' }}>{sw.tier}</small>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ── 6. TRAINING & LMS TAB ── */}
        {activeTab === 'Training' && (
          <div>
            <div className="panel">
              <div className="panel-header">
                <div>
                  <h3>Training & Orientation Checklist</h3>
                  <p className="panel-sub" style={{ margin: 0 }}>
                    Day 1 activities for:{' '}
                    <strong>{selectedEmp?.employee_name || selectedEmp?.name}</strong>
                  </p>
                </div>
              </div>

              <div>
                {trainingTasks.map((t) => (
                  <div
                    key={t.id}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      padding: '12px 0',
                      borderBottom: '1px solid var(--card-border)',
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                      <GraduationCap size={18} color="var(--primary)" />
                      <div>
                        <div style={{ fontWeight: 600, fontSize: '13.5px' }}>{t.title}</div>
                        <small style={{ color: 'var(--text-dim)' }}>Category: {t.category}</small>
                      </div>
                    </div>

                    <select
                      value={t.status}
                      onChange={(e) => handleTaskStatusChange(t.id, e.target.value)}
                      style={{
                        background: 'var(--card-bg)',
                        color: 'white',
                        border: '1px solid var(--card-border)',
                        padding: '6px 12px',
                        borderRadius: '6px',
                        fontSize: '12px',
                      }}
                    >
                      <option value="Pending">Pending</option>
                      <option value="In progress">In progress</option>
                      <option value="Completed">Completed</option>
                    </select>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* ── 7. HUMAN APPROVALS TAB ── */}
        {activeTab === 'Human Approvals' && (
          <div>
            <div className="panel">
              <div className="panel-header">
                <div>
                  <h3>Human-in-the-Loop Approval Queue</h3>
                  <p className="panel-sub" style={{ margin: 0 }}>
                    Review agent decisions requiring human authority before pipeline progresses.
                  </p>
                </div>
              </div>

              <div className="grid-2">
                {approvals.map((app) => (
                  <div className="approval-card" key={app.approval_id}>
                    <div className="approval-card-header">
                      <div>
                        <strong>{app.title}</strong>
                        <div style={{ fontSize: '11px', color: 'var(--text-dim)' }}>
                          Candidate: {app.employee_name} · Agent: {app.agent}
                        </div>
                      </div>
                      <span className={`status-pill ${app.status.toLowerCase()}`}>
                        {app.status}
                      </span>
                    </div>

                    <p style={{ fontSize: '12.5px', color: 'var(--text-muted)' }}>
                      {app.description}
                    </p>

                    <div style={{ marginTop: '8px' }}>
                      <div
                        style={{
                          fontSize: '11px',
                          fontWeight: 700,
                          color: 'var(--text-dim)',
                          marginBottom: '4px',
                        }}
                      >
                        SUPERVISOR CHECKLIST
                      </div>
                      {app.checklist &&
                        app.checklist.map((chk, i) => (
                          <div className="checklist-item" key={i}>
                            <CheckCircle2 size={13} color="var(--success)" />
                            <span>{chk}</span>
                          </div>
                        ))}
                    </div>

                    {app.status === 'Pending' && (
                      <div
                        style={{
                          display: 'flex',
                          gap: '10px',
                          marginTop: '12px',
                          paddingTop: '12px',
                          borderTop: '1px solid var(--card-border)',
                        }}
                      >
                        <button
                          className="btn-approve"
                          onClick={() => handleApprovalAction(app.approval_id, 'Approved')}
                        >
                          Approve Sign-Off
                        </button>
                        <button
                          className="btn-reject"
                          onClick={() => handleApprovalAction(app.approval_id, 'Rejected')}
                        >
                          Reject
                        </button>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* ── 8. AI AGENTS TAB ── */}
        {activeTab === 'AI Agents' && (
          <div>
            <div className="panel">
              <div className="panel-header">
                <h3>Multi-Agent System Architecture</h3>
              </div>
              <div className="grid-3">
                {agents.map((ag) => (
                  <div className="agent-card" key={ag.name}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                      <Activity size={20} color="var(--primary)" />
                      <strong>{ag.name}</strong>
                    </div>
                    <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{ag.role}</div>
                    <div
                      style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        marginTop: '10px',
                      }}
                    >
                      <span className="status-pill active">{ag.status}</span>
                      <small style={{ color: 'var(--text-dim)' }}>{ag.type}</small>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* ── 9. AUDIT LOGS TAB ── */}
        {activeTab === 'Audit Logs' && (
          <div>
            <div className="panel">
              <div className="panel-header">
                <div>
                  <h3>Permanent Audit Trail (PostgreSQL / SQLite)</h3>
                  <p className="panel-sub" style={{ margin: 0 }}>
                    Detailed actions and system events for:{' '}
                    <strong>{selectedEmp?.employee_name || selectedEmp?.name}</strong>
                  </p>
                </div>
              </div>

              <div>
                {auditLogs.map((log) => (
                  <div
                    key={log.log_id}
                    style={{
                      display: 'flex',
                      alignItems: 'flex-start',
                      gap: '14px',
                      padding: '12px 0',
                      borderBottom: '1px solid rgba(255, 255, 255, 0.04)',
                    }}
                  >
                    <History size={16} color="var(--primary)" style={{ marginTop: '3px' }} />
                    <div style={{ flex: 1 }}>
                      <div style={{ fontSize: '13px', fontWeight: 600 }}>{log.action}</div>
                      <div style={{ fontSize: '11px', color: 'var(--text-dim)', marginTop: '2px' }}>
                        Agent: <span style={{ color: '#818cf8' }}>{log.agent}</span> · Time:{' '}
                        {new Date(log.timestamp).toLocaleTimeString()}
                      </div>
                    </div>
                    <span className={`status-pill ${log.status}`}>{log.status}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </main>

      {/* ── Add Employee Modal ── */}
      {showAddModal && (
        <div className="modal-overlay">
          <div className="modal-content">
            <h3 style={{ marginBottom: '16px' }}>Register New Candidate</h3>
            <form onSubmit={handleCreateEmployee}>
              <div style={{ marginBottom: '14px' }}>
                <label style={{ display: 'block', fontSize: '12px', color: 'var(--text-muted)', marginBottom: '4px' }}>
                  Full Name
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Maya Chen"
                  value={newEmpName}
                  onChange={(e) => setNewEmpName(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '10px',
                    background: 'var(--card-bg)',
                    border: '1px solid var(--card-border)',
                    borderRadius: '8px',
                    color: 'white',
                  }}
                />
              </div>

              <div style={{ marginBottom: '14px' }}>
                <label style={{ display: 'block', fontSize: '12px', color: 'var(--text-muted)', marginBottom: '4px' }}>
                  Department
                </label>
                <select
                  value={newEmpDept}
                  onChange={(e) => setNewEmpDept(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '10px',
                    background: 'var(--card-bg)',
                    border: '1px solid var(--card-border)',
                    borderRadius: '8px',
                    color: 'white',
                  }}
                >
                  <option value="Engineering">Engineering</option>
                  <option value="Design">Design</option>
                  <option value="Finance">Finance</option>
                  <option value="Human Resources">Human Resources</option>
                  <option value="Sales">Sales</option>
                </select>
              </div>

              <div style={{ marginBottom: '20px' }}>
                <label style={{ display: 'block', fontSize: '12px', color: 'var(--text-muted)', marginBottom: '4px' }}>
                  Role / Designation
                </label>
                <input
                  type="text"
                  required
                  placeholder="e.g. Senior Frontend Engineer"
                  value={newEmpRole}
                  onChange={(e) => setNewEmpRole(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '10px',
                    background: 'var(--card-bg)',
                    border: '1px solid var(--card-border)',
                    borderRadius: '8px',
                    color: 'white',
                  }}
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px' }}>
                <button type="button" className="btn-secondary" onClick={() => setShowAddModal(false)}>
                  Cancel
                </button>
                <button type="submit" className="btn-primary">
                  Save & Launch Onboarding
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
