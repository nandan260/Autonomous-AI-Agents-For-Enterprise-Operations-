from langgraph.graph import END, START, StateGraph

from .document_verification import document_verification_agent
from .it_provisioning import it_provisioning_agent
from .monitoring import monitoring_agent
from .state import AgentState, create_initial_state
from .team_allocation import team_allocation_agent
from .training import training_agent

DOCUMENT_VERIFICATION = "document_verification"
IT_PROVISIONING = "it_provisioning"
TEAM_ALLOCATION = "team_allocation"
TRAINING = "training"
FINALIZE = "finalize"

TASKS: tuple[tuple[str, str], ...] = (
    (DOCUMENT_VERIFICATION, "documents_verified"),
    (IT_PROVISIONING, "it_provisioned"),
    (TEAM_ALLOCATION, "team_allocated"),
    (TRAINING, "training_assigned"),
)

TASK_IDS: tuple[str, ...] = tuple(task_id for task_id, _ in TASKS)


def receive_onboarding(state: AgentState) -> AgentState:
    audit_log = list(state.get("audit_log") or [])
    audit_log.append(
        f"[Orchestrator] Initialized onboarding pipeline for {state.get('employee_name')} "
        f"({state.get('employee_id')}) - Dept: {state.get('department')}"
    )
    return {**state, "audit_log": audit_log}


def check_onboarding_progress(state: AgentState) -> dict[str, bool]:
    return {task_id: bool(state.get(flag)) for task_id, flag in TASKS}


def identify_incomplete_tasks(state: AgentState) -> list[str]:
    progress = check_onboarding_progress(state)
    return [task_id for task_id in TASK_IDS if not progress[task_id]]


def assign_tasks(state: AgentState) -> AgentState:
    incomplete = identify_incomplete_tasks(state)
    audit_log = list(state.get("audit_log") or [])
    if incomplete:
        audit_log.append(f"[Orchestrator] Queued stages for execution: {incomplete}")
    return {**state, "audit_log": audit_log}


def track_tasks(state: AgentState) -> AgentState:
    incomplete = identify_incomplete_tasks(state)
    completed = [t for t in TASK_IDS if t not in incomplete]
    audit_log = list(state.get("audit_log") or [])
    audit_log.append(f"[Orchestrator] Stages finalized: Completed={completed}, Incomplete={incomplete}")
    return {**state, "audit_log": audit_log}


def _run_node_wrapper(task_id: str, agent_fn):
    def node(state: AgentState) -> AgentState:
        updated = agent_fn(state)
        audit_log = list(updated.get("audit_log") or [])
        audit_log.append(f"[Orchestrator] Completed stage: {task_id}")
        return {**updated, "audit_log": audit_log}
    return node


def build_orchestrator_graph():
    """Build LangGraph workflow pipeline with sequential fallback routing."""
    workflow = StateGraph(AgentState)

    workflow.add_node("start_orchestrator", receive_onboarding)
    workflow.add_node(DOCUMENT_VERIFICATION, _run_node_wrapper(DOCUMENT_VERIFICATION, document_verification_agent))
    workflow.add_node(IT_PROVISIONING, _run_node_wrapper(IT_PROVISIONING, it_provisioning_agent))
    workflow.add_node(TEAM_ALLOCATION, _run_node_wrapper(TEAM_ALLOCATION, team_allocation_agent))
    workflow.add_node(TRAINING, _run_node_wrapper(TRAINING, training_agent))
    workflow.add_node(FINALIZE, track_tasks)
    workflow.add_node("monitoring", monitoring_agent)

    # Workflow Edges: sequential execution pipeline across all specialized agents
    workflow.add_edge(START, "start_orchestrator")
    workflow.add_edge("start_orchestrator", DOCUMENT_VERIFICATION)
    workflow.add_edge(DOCUMENT_VERIFICATION, IT_PROVISIONING)
    workflow.add_edge(IT_PROVISIONING, TEAM_ALLOCATION)
    workflow.add_edge(TEAM_ALLOCATION, TRAINING)
    workflow.add_edge(TRAINING, FINALIZE)
    workflow.add_edge(FINALIZE, "monitoring")
    workflow.add_edge("monitoring", END)

    return workflow.compile()


def run_onboarding(
    employee_id: str,
    employee_name: str,
    department: str = "Engineering",
    designation: str = "Software Engineer",
    joining_date: str = "",
    upload_folder: str = "",
) -> AgentState:
    """Entry point: execute the full multi-agent onboarding graph."""
    graph = build_orchestrator_graph()
    initial_state = create_initial_state(
        employee_id=employee_id,
        employee_name=employee_name,
        department=department,
        designation=designation,
        joining_date=joining_date,
        upload_folder=upload_folder,
    )
    return graph.invoke(initial_state)
