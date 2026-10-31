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
  ArrowRight,
  Download
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
  const [activeCheckpoint, setActiveCheckpoint] = useState(null);

  // New Employee Form State
  const [newEmpName, setNewEmpName] = useState('');
  const [newEmpDept, setNewEmpDept] = useState('Engineering');
  const [newEmpRole, setNewEmpRole] = useState('Software Engineer');
  const [showAddModal, setShowAddModal] = useState(false);
  const [uploadStatus, setUploadStatus] = useState('');

  // Interactive Checkpoint Configuration States
  const [selectedHardware, setSelectedHardware] = useState('MacBook Pro 14" M3 Pro');
  const [assetTagInput, setAssetTagInput] = useState('ASSET-2024-9182');
  const [privilegeTier, setPrivilegeTier] = useState('Developer Privileged (MFA Enforced)');
  const [selectedTeam, setSelectedTeam] = useState('Platform Engineering');
  const [selectedManager, setSelectedManager] = useState('Kiran Rao');
  const [selectedBuddy, setSelectedBuddy] = useState('Ananya Singh');
  const [deskInput, setDeskInput] = useState('Floor 4, Tech Wing, Desk #ENG-402');
  const [workMode, setWorkMode] = useState('Hybrid (3 Days Office)');

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
    const empId = selectedEmp.employee_id || selectedEmp.id;
    const fetchDetails = async () => {
      try {
        const res = await fetch(`${API_BASE}/employees/${empId}`);
        if (res.ok) {
          const data = await res.json();
          setEmpDetail(data);
          setTrainingTasks(data.training_tasks || []);
          setDocuments(data.documents || []);
        }

        const logRes = await fetch(`${API_BASE}/onboarding/${empId}/logs`);
        if (logRes.ok) {
          const ldata = await logRes.json();
          setAuditLogs(ldata.logs || []);
        }

        // Check if employee has an active pending checkpoint
        const appRes = await fetch(`${API_BASE}/approvals?status=Pending`);
        if (appRes.ok) {
          const pendingList = await appRes.json();
          const match = pendingList.find((a) => a.employee_id === empId);
          if (match) {
            setActiveCheckpoint(match);
            if (match.approval_type === 'IT Access') {
              setPipelineStage(3);
            } else if (match.approval_type === 'Team Allocation') {
              setPipelineStage(4);
            }
          } else if (selectedEmp.onboarding_status === 'completed') {
            setPipelineStage(6);
            setActiveCheckpoint(null);
          }
        }
      } catch (err) {
        console.error(err);
      }
    };
    fetchDetails();
  }, [selectedEmp]);

  // Run End-to-End Pipeline with Active Human-in-the-Loop Checkpoint Pausing
  const runPipeline = async (emp) => {
    const target = emp || selectedEmp || employees[0];
    if (!target) return;
    setPipelineRunning(true);
    setPipelineStage(1);
    setActiveCheckpoint(null);
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
        // Step 1: Start -> Step 2: OCR & Doc check
        setTimeout(() => setPipelineStage(2), 600);

        // Step 2 -> Step 3: IT Provisioning
        setTimeout(() => {
          setPipelineLogs(result.audit_trail || []);
          setPipelineStage(3);

          if (result.is_paused) {
            // HALT ON SCREEN! Do NOT proceed until human authorizes!
            setPipelineRunning(false);
            setActiveCheckpoint(result.active_checkpoint);
            loadData();
          } else {
            // If already authorized, continue through remaining steps
            setTimeout(() => setPipelineStage(4), 600);
            setTimeout(() => setPipelineStage(5), 1200);
            setTimeout(() => {
              setPipelineStage(6);
              setPipelineRunning(false);
              setActiveCheckpoint(null);
              loadData();
            }, 1800);
          }
        }, 1300);
      } else {
        setPipelineRunning(false);
      }
    } catch (e) {
      console.error(e);
      setPipelineRunning(false);
    }
  };

  // Handle Approvals with automatic workflow resumption
  const handleApprovalAction = async (approvalId, action, customData = {}) => {
    try {
      setPipelineRunning(true);
      const res = await fetch(`${API_BASE}/approvals/${approvalId}/action`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          action,
          approver: customData.approver || 'HR / IT Governance Lead',
          notes: customData.notes || `Human intervention actioned as ${action}`,
          ...customData
        }),
      });
      if (res.ok) {
        const data = await res.json();
        await loadData();

        if (data.pipeline) {
          const pipe = data.pipeline;
          setPipelineLogs(pipe.audit_trail || []);

          if (pipe.is_paused) {
            // Advanced to next stage, but paused at the subsequent Checkpoint (e.g. Stage 4 Manager Sign-off)
            setPipelineStage(4);
            setActiveCheckpoint(pipe.active_checkpoint);
            setPipelineRunning(false);
          } else {
            // Pipeline reached 100% completion!
            setPipelineStage(5);
            setTimeout(() => {
              setPipelineStage(6);
              setActiveCheckpoint(null);
              setPipelineRunning(false);
              loadData();
            }, 900);
          }
        } else {
          setActiveCheckpoint(null);
          setPipelineRunning(false);
        }
      } else {
        setPipelineRunning(false);
      }
    } catch (e) {
      console.error(e);
      setPipelineRunning(false);
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

  // Handle File Upload (Single or Batch Multi-file)
  const handleFileUpload = async (files, docType = 'auto') => {
    const fileList = files instanceof FileList || Array.isArray(files) ? Array.from(files) : (files ? [files] : []);
    if (fileList.length === 0) return;

    if (!selectedEmp) {
      alert('Please select a candidate first.');
      return;
    }
    const empId = selectedEmp.employee_id || selectedEmp.id;
    setUploadStatus(`Uploading & verifying ${fileList.length} document(s)...`);

    const formData = new FormData();
    fileList.forEach((f) => formData.append('files', f));
    formData.append('employee_id', empId);
    formData.append('doc_type', docType);

    try {
      const res = await fetch(`${API_BASE}/documents/upload`, {
        method: 'POST',
        body: formData,
      });
      if (res.ok) {
        const data = await res.json();
        setDocuments(data.documents || []);
        setUploadStatus(`Successfully processed ${fileList.length} document(s) with PyMuPDF OCR & LLM!`);
        await loadData();
        setTimeout(() => setUploadStatus(''), 4500);
      } else {
        const errData = await res.json().catch(() => ({}));
        setUploadStatus(`Upload error: ${errData.detail || 'Server error'}`);
      }
    } catch (err) {
      console.error(err);
      setUploadStatus('Upload failed. Check backend connection.');
    }
  };

  // Auto-Generate Authentic KYC Documents Pack for Selected Candidate
  const handleGenerateDemoDocs = async () => {
    if (!selectedEmp) {
      alert('Please select a candidate first.');
      return;
    }
    const empId = selectedEmp.employee_id || selectedEmp.id;
    const empName = selectedEmp.employee_name || selectedEmp.name;
    setUploadStatus(`Generating authentic KYC document suite for ${empName}...`);
    try {
      const res = await fetch(`${API_BASE}/documents/${empId}/generate-demo-pack`, {
        method: 'POST',
      });
      if (res.ok) {
        const data = await res.json();
        setDocuments(data || []);
        setUploadStatus(`All 4 KYC documents generated & verified with PyMuPDF OCR for ${empName}!`);
        await loadData();
        setTimeout(() => setUploadStatus(''), 5000);
      } else {
        setUploadStatus('Failed to generate demo documents.');
      }
    } catch (err) {
      console.error(err);
      setUploadStatus('Error connecting to backend server.');
    }
  };

  // Handle HR Sign-off Override on Flagged Document
  const handleHROverride = async (docId) => {
    if (!docId) return;
    try {
      const res = await fetch(`${API_BASE}/documents/${docId}/hr-override`, {
        method: 'POST',
      });
      if (res.ok) {
        const data = await res.json();
        setDocuments((prev) =>
          prev.map((d) => (d.id === docId ? data.document : d))
        );
        setUploadStatus('Document manually verified and approved via HR Sign-Off!');
        await loadData();
        setTimeout(() => setUploadStatus(''), 4500);
      } else {
        alert('Failed to apply HR sign-off override.');
      }
    } catch (err) {
      console.error(err);
      alert('Error connecting to backend server.');
    }
  };

  // Handle Create Employee
  const handleCreateEmployee = async (e) => {
    e.preventDefault();
    if (!newEmpName.trim()) return;
    try {
      const res = await fetch(`${API_BASE}/employees`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          employee_name: newEmpName.trim(),
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
      } else {
        const errorData = await res.json().catch(() => ({}));
        alert(`Failed to add candidate: ${errorData.detail || 'Server error'}`);
      }
    } catch (err) {
      console.error(err);
      alert('Error connecting to backend server. Please verify backend is running on port 8000.');
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
                    activeCheckpoint && (activeCheckpoint.approval_type === 'IT Access' || activeCheckpoint.task === 'it_provisioning')
                      ? 'paused'
                      : pipelineStage === 3
                      ? 'active'
                      : pipelineStage > 3
                      ? 'completed'
                      : ''
                  }`}
                >
                  <div className="step-circle">
                    {activeCheckpoint && (activeCheckpoint.approval_type === 'IT Access' || activeCheckpoint.task === 'it_provisioning')
                      ? '⏸️'
                      : '3'}
                  </div>
                  <div className="step-label">
                    {activeCheckpoint && (activeCheckpoint.approval_type === 'IT Access' || activeCheckpoint.task === 'it_provisioning')
                      ? 'IT Gate (Paused)'
                      : 'IT Provisioning'}
                  </div>
                </div>

                <div
                  className={`pipeline-step ${
                    activeCheckpoint && (activeCheckpoint.approval_type === 'Team Allocation' || activeCheckpoint.task === 'team_allocation')
                      ? 'paused'
                      : pipelineStage === 4
                      ? 'active'
                      : pipelineStage > 4
                      ? 'completed'
                      : ''
                  }`}
                >
                  <div className="step-circle">
                    {activeCheckpoint && (activeCheckpoint.approval_type === 'Team Allocation' || activeCheckpoint.task === 'team_allocation')
                      ? '⏸️'
                      : '4'}
                  </div>
                  <div className="step-label">
                    {activeCheckpoint && (activeCheckpoint.approval_type === 'Team Allocation' || activeCheckpoint.task === 'team_allocation')
                      ? 'Manager Gate (Paused)'
                      : 'Team Allocation'}
                  </div>
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

              {/* ── Active Human-in-the-Loop Checkpoint Intervention Banner ── */}
              {activeCheckpoint && (
                <div className="hitl-checkpoint-banner">
                  <div className="hitl-checkpoint-top">
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                      <div className="hitl-pulsing-badge">
                        <ShieldAlert size={22} color="#f59e0b" />
                      </div>
                      <div>
                        <div className="hitl-badge-label">
                          HUMAN INTERVENTION REQUIRED · PIPELINE PAUSED
                        </div>
                        <h4 style={{ margin: '4px 0 0 0', fontSize: '16px', color: 'white' }}>
                          {activeCheckpoint.title}
                        </h4>
                      </div>
                    </div>
                    <span className="hitl-tag">
                      Checkpoint ID: {activeCheckpoint.approval_id}
                    </span>
                  </div>

                  <p style={{ margin: '12px 0', fontSize: '13.5px', color: 'var(--text-muted)' }}>
                    {activeCheckpoint.description}
                  </p>

                  {/* Interactive IT Provisioning Controls */}
                  {(activeCheckpoint.task === 'it_provisioning' || activeCheckpoint.approval_type === 'IT Access') && (
                    <div style={{ margin: '14px 0', padding: '12px 14px', background: 'rgba(15, 23, 42, 0.75)', borderRadius: '8px', border: '1px solid rgba(59, 130, 246, 0.3)' }}>
                      <div style={{ fontSize: '12px', fontWeight: 600, color: '#38bdf8', marginBottom: '10px' }}>
                        ⚙️ CONFIGURE IT PROVISIONING ASSETS & SECURITY TIERS:
                      </div>
                      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', marginBottom: '10px' }}>
                        <div>
                          <label style={{ fontSize: '11px', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>Hardware Model</label>
                          <select
                            value={selectedHardware}
                            onChange={(e) => setSelectedHardware(e.target.value)}
                            style={{ width: '100%', padding: '6px 10px', background: 'var(--card-bg)', color: 'white', border: '1px solid var(--card-border)', borderRadius: '6px', fontSize: '12px' }}
                          >
                            <option value='MacBook Pro 16" M3 Max (36GB, 1TB SSD)'>MacBook Pro 16" M3 Max (36GB, 1TB SSD)</option>
                            <option value='MacBook Pro 14" M3 Pro (18GB, 512GB SSD)'>MacBook Pro 14" M3 Pro (18GB, 512GB SSD)</option>
                            <option value='MacBook Air 15" M2 (16GB, 512GB SSD)'>MacBook Air 15" M2 (16GB, 512GB SSD)</option>
                            <option value="Lenovo ThinkPad X1 Carbon Gen 12 (32GB, 1TB)">Lenovo ThinkPad X1 Carbon Gen 12 (32GB, 1TB)</option>
                            <option value="Dell Precision 5680 Workstation (64GB, 2TB)">Dell Precision 5680 Workstation (64GB, 2TB)</option>
                          </select>
                        </div>
                        <div>
                          <label style={{ fontSize: '11px', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>Asset Tag & Serial #</label>
                          <input
                            type="text"
                            value={assetTagInput}
                            onChange={(e) => setAssetTagInput(e.target.value)}
                            style={{ width: '100%', padding: '6px 10px', background: 'var(--card-bg)', color: 'white', border: '1px solid var(--card-border)', borderRadius: '6px', fontSize: '12px' }}
                          />
                        </div>
                      </div>
                      <div>
                        <label style={{ fontSize: '11px', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>Access Privilege Tier</label>
                        <select
                          value={privilegeTier}
                          onChange={(e) => setPrivilegeTier(e.target.value)}
                          style={{ width: '100%', padding: '6px 10px', background: 'var(--card-bg)', color: 'white', border: '1px solid var(--card-border)', borderRadius: '6px', fontSize: '12px' }}
                        >
                          <option value="Developer Privileged (MFA Enforced)">Developer Privileged (MFA Enforced)</option>
                          <option value="Standard Business User">Standard Business User</option>
                          <option value="Cloud Infrastructure Admin (Zero Trust)">Cloud Infrastructure Admin (Zero Trust)</option>
                        </select>
                      </div>
                    </div>
                  )}

                  {/* Interactive Team Allocation Controls */}
                  {(activeCheckpoint.task === 'team_allocation' || activeCheckpoint.approval_type === 'Team Allocation') && (
                    <div style={{ margin: '14px 0', padding: '12px 14px', background: 'rgba(15, 23, 42, 0.75)', borderRadius: '8px', border: '1px solid rgba(16, 185, 129, 0.3)' }}>
                      <div style={{ fontSize: '12px', fontWeight: 600, color: '#34d399', marginBottom: '10px' }}>
                        👥 CONFIGURE SQUAD PLACEMENT & BUDDY ALLOCATION:
                      </div>
                      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px', marginBottom: '10px' }}>
                        <div>
                          <label style={{ fontSize: '11px', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>Assigned Squad / Team</label>
                          <select
                            value={selectedTeam}
                            onChange={(e) => setSelectedTeam(e.target.value)}
                            style={{ width: '100%', padding: '6px 10px', background: 'var(--card-bg)', color: 'white', border: '1px solid var(--card-border)', borderRadius: '6px', fontSize: '12px' }}
                          >
                            <option value="Platform Engineering">Platform Engineering</option>
                            <option value="Core Infrastructure">Core Infrastructure</option>
                            <option value="Product Experience">Product Experience</option>
                            <option value="Billing & Payments">Billing & Payments</option>
                          </select>
                        </div>
                        <div>
                          <label style={{ fontSize: '11px', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>Assigned Peer Buddy</label>
                          <select
                            value={selectedBuddy}
                            onChange={(e) => setSelectedBuddy(e.target.value)}
                            style={{ width: '100%', padding: '6px 10px', background: 'var(--card-bg)', color: 'white', border: '1px solid var(--card-border)', borderRadius: '6px', fontSize: '12px' }}
                          >
                            <option value="Ananya Singh (Staff Engineer)">Ananya Singh (Staff Engineer)</option>
                            <option value="Rohan Verma (Principal Architect)">Rohan Verma (Principal Architect)</option>
                            <option value="Divya Nair (Tech Lead)">Divya Nair (Tech Lead)</option>
                          </select>
                        </div>
                      </div>
                      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '10px' }}>
                        <div>
                          <label style={{ fontSize: '11px', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>Work Mode</label>
                          <select
                            value={workMode}
                            onChange={(e) => setWorkMode(e.target.value)}
                            style={{ width: '100%', padding: '6px 10px', background: 'var(--card-bg)', color: 'white', border: '1px solid var(--card-border)', borderRadius: '6px', fontSize: '12px' }}
                          >
                            <option value="Hybrid (3 Days Office)">Hybrid (3 Days Office)</option>
                            <option value="Full Remote">Full Remote</option>
                            <option value="Onsite Bengaluru HQ">Onsite Bengaluru HQ</option>
                          </select>
                        </div>
                        <div>
                          <label style={{ fontSize: '11px', color: 'var(--text-muted)', display: 'block', marginBottom: '4px' }}>Office Desk Location</label>
                          <input
                            type="text"
                            value={deskInput}
                            onChange={(e) => setDeskInput(e.target.value)}
                            style={{ width: '100%', padding: '6px 10px', background: 'var(--card-bg)', color: 'white', border: '1px solid var(--card-border)', borderRadius: '6px', fontSize: '12px' }}
                          />
                        </div>
                      </div>
                    </div>
                  )}

                  {activeCheckpoint.checklist && activeCheckpoint.checklist.length > 0 && (
                    <div className="hitl-checklist-box">
                      <div style={{ fontSize: '12px', fontWeight: 600, color: 'var(--text-muted)', marginBottom: '8px' }}>
                        REQUIRED SAFETY & COMPLIANCE CHECKS:
                      </div>
                      {activeCheckpoint.checklist.map((item, idx) => (
                        <div key={idx} className="hitl-check-item">
                          <CheckCircle2 size={15} color="#10b981" />
                          <span>{item}</span>
                        </div>
                      ))}
                    </div>
                  )}

                  <div className="hitl-action-footer">
                    <button
                      className="btn-primary hitl-approve-btn"
                      onClick={() => {
                        const isIT = activeCheckpoint.task === 'it_provisioning' || activeCheckpoint.approval_type === 'IT Access';
                        const payload = isIT ? {
                          laptop_model: selectedHardware,
                          asset_tag: assetTagInput,
                          privilege_tier: privilegeTier,
                        } : {
                          assigned_team: selectedTeam,
                          reporting_manager: selectedManager,
                          peer_buddy: selectedBuddy,
                          desk_location: deskInput,
                          work_mode: workMode,
                        };
                        handleApprovalAction(activeCheckpoint.approval_id, 'Approved', payload);
                      }}
                    >
                      <UserCheck size={16} />
                      Authorize & Proceed to Next Agent →
                    </button>
                    <button
                      className="btn-secondary hitl-reject-btn"
                      onClick={() => handleApprovalAction(activeCheckpoint.approval_id, 'Rejected')}
                    >
                      Reject Request
                    </button>
                  </div>
                </div>
              )}

              {/* ── Finished Celebration Banner ── */}
              {pipelineStage >= 6 && !activeCheckpoint && (
                <div className="hitl-success-banner">
                  <CheckCircle2 size={24} color="#10b981" />
                  <div>
                    <strong style={{ display: 'block', fontSize: '15px', color: 'white' }}>
                      Onboarding Fully Completed with Human Governance!
                    </strong>
                    <span style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
                      All AI agent proposals were verified and authorized by human approvers.
                    </span>
                  </div>
                </div>
              )}

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
                    <strong>{selectedEmp?.employee_name || selectedEmp?.name || 'No Candidate Selected'}</strong>
                  </p>
                </div>
                <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
                  <select
                    style={{
                      background: 'var(--card-bg)',
                      color: 'white',
                      border: '1px solid var(--card-border)',
                      padding: '8px 12px',
                      borderRadius: '8px',
                      fontSize: '13px',
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
                    onClick={handleGenerateDemoDocs}
                    style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '13px' }}
                  >
                    <FileCheck size={15} />
                    ⚡ Auto-Generate All 4 KYC Docs
                  </button>
                </div>
              </div>

              {/* Upload Dropzone with Multi-File Batch Support */}
              <div className="dropzone" style={{ marginBottom: '24px' }}>
                <input
                  type="file"
                  id="doc-upload-input"
                  multiple
                  style={{ display: 'none' }}
                  onChange={(e) => handleFileUpload(e.target.files, 'auto')}
                  accept=".pdf,.png,.jpg,.jpeg"
                />
                <label htmlFor="doc-upload-input" style={{ cursor: 'pointer', display: 'block' }}>
                  <Upload size={34} color="var(--primary)" style={{ marginBottom: '8px' }} />
                  <div style={{ fontWeight: 600, fontSize: '15px' }}>
                    Drop ALL candidate PDF documents at once or click to browse
                  </div>
                  <div style={{ fontSize: '12.5px', color: 'var(--text-muted)', marginTop: '4px' }}>
                    Select 1 to 4 files together. Automatically classifies Aadhaar Card, Degree Certificate, Offer Letter, and Bank Details via PyMuPDF OCR.
                  </div>
                </label>
                {uploadStatus && (
                  <div
                    style={{
                      marginTop: '12px',
                      fontSize: '13px',
                      fontWeight: 600,
                      color: '#a5b4fc',
                      background: 'rgba(99, 102, 241, 0.12)',
                      padding: '8px 14px',
                      borderRadius: '6px',
                      display: 'inline-block',
                    }}
                  >
                    {uploadStatus}
                  </div>
                )}
              </div>

              {/* Document Results Grid */}
              <div className="grid-2">
                {[
                  { id: 'aadhar_card', title: 'Aadhaar Identification', short: 'Aadhaar', sampleId: 'UID-4892' },
                  { id: 'degree_certificate', title: 'Educational Degree Certificate', short: 'Degree', sampleId: 'DEG-2022' },
                  { id: 'offer_letter_signed', title: 'Countersigned Offer Letter', short: 'Offer Letter', sampleId: 'APP-2024' },
                  { id: 'bank_details', title: 'Banking Details & Cheque', short: 'Bank Cheque', sampleId: 'HDFC-5010' },
                ].map((item) => {
                  const match = documents.find((d) => d.name === item.id || d.doc_name === item.id);
                  const meta = match?.metadata_fields || {};
                  const isOverridden = Boolean(meta.hr_manual_override);
                  const hasDiscrepancy = Boolean(match?.issues && match.issues.some((i) => !i.startsWith('[HR Manual Override]')));
                  const isVerified = Boolean(match?.readable && match?.name_match && (!hasDiscrepancy || isOverridden));
                  const isMismatch = Boolean(match?.readable && (!match?.name_match || (hasDiscrepancy && !isOverridden)));

                  return (
                    <div className="doc-card" key={item.id} style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
                      <div>
                        <div className="doc-card-header">
                          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                            <FileCheck size={18} color={isVerified ? '#10b981' : 'var(--primary)'} />
                            <strong>{item.title}</strong>
                          </div>
                          <span className={`status-pill ${isVerified ? 'passed' : isMismatch ? 'warning' : 'pending'}`}>
                            {isVerified ? (isOverridden ? 'Verified [HR Override]' : 'Verified [KYC Passed]') : isMismatch ? (match?.name_match ? 'KYC Discrepancy' : 'Name Mismatch') : 'Pending Upload'}
                          </span>
                        </div>

                        <div style={{ fontSize: '12.5px', color: 'var(--text-muted)', lineHeight: '1.7' }}>
                          <div>
                            Document Type:{' '}
                            <span style={{ color: 'white', fontWeight: 500 }}>
                              {match?.type || match?.doc_type || 'KYC Document'}
                            </span>
                          </div>
                          <div>
                            Candidate Name Match:{' '}
                            <span style={{ color: match?.name_match ? '#34d399' : match?.readable ? '#f87171' : 'var(--text-dim)', fontWeight: 600 }}>
                              {match?.name_match ? 'Validated ✓' : match?.readable ? 'Mismatch ✗' : 'Awaiting Match'}
                            </span>
                          </div>
                          <div>
                            Extracted Name:{' '}
                            <span style={{ color: 'white' }}>
                              {match?.extracted_name || 'Not detected yet'}
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
                              {match?.llm_used ? 'Gemini AI' : 'PyMuPDF Rule-Based OCR'}
                            </span>
                          </div>
                        </div>

                        {/* Structural KYC Metadata Checklist */}
                        {meta && Object.keys(meta).length > 0 && (
                          <div
                            style={{
                              marginTop: '10px',
                              padding: '8px 10px',
                              background: 'rgba(255, 255, 255, 0.03)',
                              borderRadius: '6px',
                              border: '1px solid var(--border-color)',
                              fontSize: '11.5px',
                            }}
                          >
                            <div style={{ fontWeight: 600, color: '#93c5fd', marginBottom: '5px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                              <span>Enterprise KYC Field Verification</span>
                              {isOverridden && (
                                <span style={{ color: '#10b981', fontSize: '10px', fontWeight: 600 }}>✓ HR Authorized</span>
                              )}
                            </div>
                            <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '3px', color: 'var(--text-muted)' }}>
                              {item.id === 'aadhar_card' && (
                                <>
                                  <div>UIDAI No: <strong style={{ color: meta.aadhaar_number ? 'white' : '#f87171' }}>{meta.display_id || meta.aadhaar_number || 'Missing / Invalid'}</strong></div>
                                  <div>Authority: <span style={{ color: meta.authority?.includes('Verified') ? '#86efac' : '#f87171' }}>{meta.authority || 'UIDAI Standard'}</span></div>
                                  <div>DOB on Record: <span style={{ color: 'white' }}>{meta.dob || 'Verified'}</span></div>
                                </>
                              )}
                              {item.id === 'degree_certificate' && (
                                <>
                                  <div>Institution: <strong style={{ color: meta.institution?.includes('Unrecognized') ? '#f87171' : 'white' }}>{meta.institution || 'Accredited University'}</strong></div>
                                  <div>Qualification: <span style={{ color: '#86efac' }}>{meta.degree_title || 'Degree Validated'}</span></div>
                                  <div>Graduation Year: <span style={{ color: 'white' }}>{meta.grad_year || 'Verified'}</span></div>
                                  <div>Academic Standing: <span style={{ color: '#c084fc' }}>{meta.performance || 'Passed in Honors'}</span></div>
                                </>
                              )}
                              {item.id === 'offer_letter_signed' && (
                                <>
                                  <div>Corporate Entity: <strong style={{ color: meta.employer?.includes('Unknown') ? '#f87171' : 'white' }}>{meta.employer || 'EnterpriseFlow AI'}</strong></div>
                                  <div>Offered Role: <span style={{ color: '#86efac' }}>{meta.role || 'Designation Match'}</span></div>
                                  <div>Signature Audit: <span style={{ color: meta.signature_status?.includes('Unsigned') ? '#f87171' : '#38bdf8' }}>{meta.signature_status || 'Digitally Signed'}</span></div>
                                </>
                              )}
                              {item.id === 'bank_details' && (
                                <>
                                  <div>Scheduled Bank: <strong style={{ color: meta.bank_name?.includes('Unrecognized') ? '#f87171' : 'white' }}>{meta.bank_name || 'Commercial Bank'}</strong></div>
                                  <div>Account No: <span style={{ color: meta.account_number?.includes('Not') ? '#f87171' : '#86efac' }}>{meta.account_number || 'Validated'}</span></div>
                                  <div>RBI IFSC Code: <span style={{ color: meta.ifsc_code?.includes('Invalid') ? '#f87171' : '#38bdf8' }}>{meta.ifsc_code || 'Format Valid'}</span></div>
                                </>
                              )}
                            </div>
                          </div>
                        )}

                        {match?.issues && match.issues.length > 0 && (
                          <div
                            style={{
                              background: isOverridden ? 'rgba(16, 185, 129, 0.1)' : 'var(--danger-bg)',
                              color: isOverridden ? '#34d399' : '#f87171',
                              padding: '8px',
                              borderRadius: '6px',
                              fontSize: '11px',
                              marginTop: '8px',
                            }}
                          >
                            {isOverridden ? 'HR Resolution:' : 'Verification Issues:'} {match.issues.join(', ')}
                          </div>
                        )}
                      </div>

                      {/* Individual Card Upload Action & HR Override */}
                      <div
                        style={{
                          marginTop: '14px',
                          paddingTop: '10px',
                          borderTop: '1px solid var(--card-border)',
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'center',
                          gap: '8px',
                          flexWrap: 'wrap',
                        }}
                      >
                        <label
                          className="btn-secondary"
                          style={{
                            padding: '6px 12px',
                            fontSize: '12px',
                            cursor: 'pointer',
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '6px',
                          }}
                        >
                          <Upload size={13} />
                          Upload {item.short}
                          <input
                            type="file"
                            style={{ display: 'none' }}
                            accept=".pdf,.png,.jpg,.jpeg"
                            onChange={(e) => handleFileUpload(e.target.files, item.id)}
                          />
                        </label>

                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                          {match && isMismatch && (
                            <button
                              type="button"
                              onClick={() => handleHROverride(match.id)}
                              className="btn-secondary"
                              style={{
                                padding: '5px 10px',
                                fontSize: '11px',
                                color: '#fbbf24',
                                borderColor: 'rgba(251, 191, 36, 0.4)',
                                background: 'rgba(251, 191, 36, 0.1)',
                                display: 'inline-flex',
                                alignItems: 'center',
                                gap: '5px',
                                cursor: 'pointer',
                              }}
                              title="HR officer manual sign-off override"
                            >
                              <ShieldAlert size={12} /> HR Sign-Off
                            </button>
                          )}

                          {isVerified && (
                            <span style={{ fontSize: '11px', color: '#10b981', display: 'flex', alignItems: 'center', gap: '4px' }}>
                              <CheckCircle2 size={13} /> Ready
                            </span>
                          )}
                        </div>
                      </div>
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
