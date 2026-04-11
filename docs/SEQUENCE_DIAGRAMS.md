# Sequence Diagrams

Mermaid sequence diagrams for the three primary adoption modes. See [ADOPTION_GUIDE.md](ADOPTION_GUIDE.md) for context on when to use each mode.

---

## 1. contextweaver-Only Routing (No Kernel)

Used when you want smart tool routing but provide your own execution layer.

```mermaid
sequenceDiagram
    participant Caller
    participant contextweaver
    participant YourExecutor as Your Execution Layer
    participant LLM

    Caller->>contextweaver: compile_context(state, candidate_tools)
    contextweaver->>LLM: prompt with ChoiceCard(s)
    LLM-->>contextweaver: selected item ID
    contextweaver-->>Caller: RoutingDecision(selected_item_id)

    Caller->>YourExecutor: execute(selected_item_id, args)
    YourExecutor-->>Caller: Frame (you produce this)
    Caller->>contextweaver: ingest_frame(Frame)
    contextweaver-->>Caller: updated context
```

**What you own:** Your execution layer must produce a `Frame`. The Frame contract is defined in this spec. contextweaver will not accept raw tool output.

---

## 2. Kernel-Only Execution (External Router)

Used when you want safe, auditable execution but provide your own routing layer.

```mermaid
sequenceDiagram
    participant Caller
    participant YourRouter as Your Router
    participant AgentKernel as agent-kernel
    participant PolicyEngine as Policy Engine
    participant Tool
    participant Firewall
    participant AuditLog as Audit Log

    Caller->>YourRouter: route(state)
    YourRouter-->>Caller: RoutingDecision

    Caller->>AgentKernel: execute(RoutingDecision, CapabilityToken)
    AgentKernel->>PolicyEngine: authorize(capability_id, token)
    PolicyEngine-->>AgentKernel: PolicyDecision(allow)
    AgentKernel->>AuditLog: TraceEvent(capability_authorized)

    AgentKernel->>Tool: invoke(args)
    Tool-->>AgentKernel: raw_output

    AgentKernel->>Firewall: filter(raw_output)
    Firewall-->>AgentKernel: Frame + optional Handle
    AgentKernel->>AuditLog: TraceEvent(capability_executed)

    AgentKernel-->>Caller: Frame
```

**What you own:** Your router must produce a `RoutingDecision`. The RoutingDecision contract is defined in this spec.

---

## 3. Full Stack (contextweaver → agent-kernel → ChainWeaver Flow)

Used when you want the complete ecosystem for complex, multi-step agentic workflows.

```mermaid
sequenceDiagram
    participant Caller
    participant ChainWeaver
    participant contextweaver
    participant AgentKernel as agent-kernel
    participant PolicyEngine as Policy Engine
    participant Tool
    participant Firewall
    participant HandleStore as Handle Store
    participant AuditLog as Audit Log
    participant LLM

    Caller->>ChainWeaver: start_flow(flow_id, input)

    loop For each step in DAG
        ChainWeaver->>contextweaver: compile_context(state, candidate_tools)
        contextweaver->>LLM: prompt with ChoiceCard(s)
        LLM-->>contextweaver: selected item ID
        contextweaver-->>ChainWeaver: RoutingDecision

        ChainWeaver->>AgentKernel: execute(RoutingDecision, CapabilityToken)
        AgentKernel->>PolicyEngine: authorize(capability_id, token)
        PolicyEngine-->>AgentKernel: PolicyDecision(allow)
        AgentKernel->>AuditLog: TraceEvent(capability_authorized)

        AgentKernel->>Tool: invoke(args)
        Tool-->>AgentKernel: raw_output

        AgentKernel->>Firewall: filter(raw_output)
        Firewall->>HandleStore: store_artifact(raw_output)
        HandleStore-->>Firewall: Handle
        Firewall-->>AgentKernel: Frame + Handle
        AgentKernel->>AuditLog: TraceEvent(capability_executed, firewall_applied)

        AgentKernel-->>ChainWeaver: Frame
        ChainWeaver->>contextweaver: ingest_frame(Frame)
    end

    ChainWeaver-->>Caller: flow_result
```

**Key observations:**

- Raw output never leaves agent-kernel; only `Frame` and `Handle` references are returned.
- Each step is independently authorized via a `CapabilityToken`.
- contextweaver never interacts with agent-kernel directly; ChainWeaver mediates.
- The audit log receives a `TraceEvent` for every authorization and execution.
