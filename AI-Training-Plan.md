# AI Training Plan

## Overview
This document outlines the training plan to upskill the engineering and product teams on Artificial Intelligence, focusing on fundamentals and security.

## Workshop 1: AI Fundamentals for Engineering

**Objective:**  
To provide a solid understanding of Generative AI concepts, tools, and practical applications in software development.

**Target Audience:**  
Developers, QA, DevOps, Product Managers.

**Duration:**  
4 Hours (Half-day)

**Prerequisites:**  
- Basic understanding of software development.
- GitHub account.

**Agenda:**

| Time | Topic | Description |
| :--- | :--- | :--- |
| 09:00 - 09:45 | **Introduction to GenAI** | What are LLMs? How do Transformers work (high level)? Key terminology (Tokens, Context Window, Temperature). |
| 09:45 - 10:30 | **Prompt Engineering** | Zero-shot, Few-shot, Chain-of-Thought. Best practices for writing effective prompts. |
| 10:30 - 10:45 | *Break* | |
| 10:45 - 11:45 | **AI Coding Assistants** | Hands-on lab with GitHub Copilot/Cursor. Generating code, explaining code, refactoring, and generating tests. |
| 11:45 - 12:45 | **Local LLMs** | Introduction to Ollama/LM Studio. Running models locally for privacy. Privacy considerations with public AI tools. |
| 12:45 - 13:00 | **Q&A** | Open discussion. |

**Resources:**
- [DeepLearning.AI: ChatGPT Prompt Engineering for Developers](https://www.deeplearning.ai/short-courses/chatgpt-prompt-engineering-for-developers/)
- [Ollama Documentation](https://ollama.com/)

---

## Workshop 2: AI Security & Risk Management

**Objective:**  
To understand the specific security risks associated with AI/LLMs and how to mitigate them in our applications and workflows.

**Target Audience:**  
Security Engineers, Seniors Developers, Architects, DevOps.

**Duration:**  
4 Hours (Half-day)

**Prerequisites:**  
- Completion of "AI Fundamentals" workshop.

**Agenda:**

| Time | Topic | Description |
| :--- | :--- | :--- |
| 14:00 - 14:45 | **OWASP Top 10 for LLMs** | Overview of the top security risks: Prompt Injection, Insecure Output Handling, Training Data Poisoning, etc. |
| 14:45 - 15:45 | **Prompt Injection** | Deep dive into prompt injection attacks (Direct & Indirect). Hands-on lab: "Jailbreaking" a sample app. |
| 15:45 - 16:00 | *Break* | |
| 16:00 - 17:00 | **Secure AI Development** | Implementing Guardrails (Input/Output validation). Sanitization strategies. Human-in-the-loop patterns. |
| 17:00 - 17:45 | **Data Privacy & Compliance** | PII handling. EU AI Act overview. Corporate policies for using third-party AI services. |
| 17:45 - 18:00 | **Wrap-up** | Review of key takeaways and actionable security checklist. |

**Resources:**
- [OWASP Top 10 for Large Language Model Applications](https://owasp.org/www-project-top-10-for-large-language-model-applications/)
- [Lakera Gandalf (Prompt Injection Game)](https://gandalf.lakera.ai/)
