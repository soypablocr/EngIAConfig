# AI System Quarterly Audit Checklist

## 1. Model Performance Review
- [ ] Review `accuracy` metrics. Are we meeting the >95% target?
- [ ] Analyze `latency` trends. Has response time degraded?
- [ ] Check `fallback_rate`. Is the primary API reliable?
- [ ] Review successful vs failed configuration generations.

## 2. Security & Privacy Audit
- [ ] **Log Review:** Check application logs for any accidental PII logging (IPs, Emails).
- [ ] **Attack Attempts:** Review logs for rejected prompt injection attempts.
- [ ] **Access Control:** Verify that only authorized API keys are in use and rotated if necessary.
- [ ] **Dependency Scan:** Run `pip audit` or similar to check for vulnerabilities in AI libraries.

## 3. Data Quality & Bias
- [ ] **Bias Check:** Randomly sample 50 past interactions. checking for biased language or tone.
- [ ] **Context Relevance:** Verify that the "Form Context" injected into the prompt is accurate and useful.
- [ ] **Hallucination Check:** Review a sample of "technical explanation" responses for accuracy.

## 4. User Feedback & Satisfaction
- [ ] Review all user-submitted feedback (star ratings, comments).
- [ ] Analyze common user complaints or feature requests.
- [ ] Identify patterns in "thumbs down" responses.

## 5. Compliance & Governance
- [ ] **Policy Alignment:** Ensure AI usage still aligns with internal "AI Acceptable Use Policy".
- [ ] **Regulatory Check:** Review any new local or international regulations (e.g., EU AI Act updates) that might affect the tool.
- [ ] **Training:** Confirm that all new team members have completed the "AI Fundamentals" workshop.

---
**Audit Completed By:** ____________________
**Date:** ____________________
