# AI Governance Control Mapping

This document maps the required AI Governance Controls to the specific artifacts and tasks implemented in the EngIAConfig project.

| Control ID | Control Name | Description | Implemented Artifact / Task | Status |
| :--- | :--- | :--- | :--- | :--- |
| **A.1** | **AI Policy & Scope** | Definition of acceptable use, system scope, and limitations. | `AI-Scope-Statement.md` <br> `AI-Risk-Assessment.md` | **Implemented** |
| **A.2** | **Resources & Competency** | Ensuring the team has the necessary skills and training to build/maintain AI. | `competence_matrix_ia.xlsx` <br> `AI-Training-Plan.md` | **Implemented** |
| **A.3** | **Data Privacy** | Mechanisms to protect sensitive user data (PII) from being sent to LLMs. | `chat_agent.py` (Sanitization Guardrails) <br> `test_robustness.py` (PII Tests) | **Implemented** |
| **A.4** | **System Lifecycle** | Managing model versions, monitoring performance, and handling failures. | `chat_agent.py` (Generic Fallback & Versioning) <br> `metrics.yaml` <br> `nc_ia_tracker.csv` | **Implemented** |
| **A.5** | **Responsible Use** | Managing risks related to bias, hallucinations, and security. | `ai_audit_checklist.md` <br> `AI-Risk-Assessment.md` <br> `continuous_improvement_workflow.md` | **Implemented** |

## Audit Trail
- **Last Updated:** 2026-02-19
- **Reviewer:** AI Agent
