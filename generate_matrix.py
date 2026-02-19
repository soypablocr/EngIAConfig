
import pandas as pd
import os

# Define the data for the competence matrix
data = {
    "Role": [
        "Developer", "Developer", "Developer", "Developer",
        "DevOps", "DevOps", "DevOps",
        "Security Engineer", "Security Engineer", "Security Engineer",
        "Project Manager", "Project Manager",
        "Architect", "Architect", "Architect"
    ],
    "Skill Area": [
        "AI Fundamentals", "Coding Assistant", "Prompt Engineering", "AI Security",
        "AIOps", "Model Deployment", "Monitoring",
        "AI Risk Management", "Adversarial AI", "Compliance",
        "AI Strategy", "Resource Management",
        "System Design", "Model Selection", "Integration"
    ],
    "Specific Competency": [
        "Understanding LLMs and Transformers", "Using Github Copilot/Cursor effectively", "Writing effective prompts for code generation", "Secure coding practices with AI",
        "Automating workflows with AI agents", "Deploying local LLMs (Ollama, etc.)", "Monitoring AI agent performance",
        "Identifying AI specific risks (hallucinations, bias)", "Detecting prompt injection attacks", "GDPR/EU AI Act compliance",
        "Identifying AI use cases", "Estimating AI compute costs",
        "Designing RAG architectures", "Choosing between Open Source vs Proprietary models", "Integrating AI APIs into existing systems"
    ],
    "Proficiency Level (1-5)": [
        3, 5, 4, 4,
        3, 4, 4,
        5, 5, 4,
        3, 3,
        5, 5, 5
    ],
    "Priority": [
        "High", "High", "High", "Critical",
        "Medium", "High", "Medium",
        "Critical", "Critical", "High",
        "Medium", "Medium",
        "Critical", "High", "High"
    ]
}

# Create a DataFrame
df = pd.DataFrame(data)

# Define the output file path
output_file = os.path.join(os.getcwd(), "competence_matrix_ia.xlsx")

# Write to Excel
try:
    df.to_excel(output_file, index=False)
    print(f"Successfully created {output_file}")
except Exception as e:
    print(f"Error creating Excel file: {e}")
