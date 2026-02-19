# AI Continuous Improvement Workflow

This document outlines the standard operating procedure (SOP) for handling Non-Conformities (NCs) and driving continuous improvement in the EngIAConfig AI system.

## 1. Detect
**Goal:** Identify issues before they impact a large number of users.
**Sources:**
- **Automated Monitoring:** Spikes in latency, 4xx/5xx error rates (monitored via `metrics.yaml`).
- **User Feedback:** "Thumbs down" ratings or specific bug reports.
- ** Quarterly Audit:** Issues found during the `ai_audit_checklist.md` review.
- **Log Review:** Security flags or sanitized PII found in logs.

**Action:**
- Log the issue in `nc_ia_tracker.csv`.
- Assign a **Severity** (Low/Medium/High/Critical).
- Assign an **Owner**.

## 2. Analyse
**Goal:** Understand *why* the issue occurred, not just *what* happened.
**Method:** "5 Whys" Root Cause Analysis.
**Questions:**
- Was it a prompt issue?
- Was it a model limitation?
- Was it bad context data?
- Was it a software bug?

**Action:**
- Document the **Root Cause** in `nc_ia_tracker.csv`.

## 3. Correct
**Goal:** Implement a fix that prevents recurrence.
**Types of Fixes:**
- **Prompt Engineering:** Adjusting the System Prompt or Schema.
- **Code Fix:** Patching the `ChatAgent` logic (e.g., better sanitization).
- **Knowledge Base:** Updating the context retrieval system.
- **Training:** Fine-tuning the model (long-term).

**Action:**
- Implement the **Corrective Action**.
- Update the status to `In-Progress` -> `Resolved`.

## 4. Verify
**Goal:** Ensure the fix actually works and doesn't introduce regressions.
**Method:**
- Run `test_robustness.py` to ensure no regression in safety/stability.
- Manual verification of the specific failing scenario.
- Monitor `metrics.yaml` for 24-48 hours.

**Action:**
- Update **Verification Date** and Status to `Closed` in `nc_ia_tracker.csv`.

---
**Review Cycle:** This workflow is reviewed quarterly as part of the AI Audit.
