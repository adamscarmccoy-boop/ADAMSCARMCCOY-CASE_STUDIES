import argparse
import os

import ollama


def load_framework_context() -> str:
    """Loads the assessment framework context from the markdown file."""
    framework_path = os.path.join(os.path.dirname(__file__), "lead_assessment_framework.md")
    try:
        with open(framework_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        print(f"Error: Could not find framework file at {framework_path}")
        return ""

def main():
    parser = argparse.ArgumentParser(
        description="Evaluate a contract lead against the H.O.R.N. Stack Assessment Framework."
    )
    parser.add_argument(
        "lead_description",
        type=str,
        help="The job description or lead details provided by the potential client."
    )

    args = parser.parse_args()

    framework_context = load_framework_context()
    if not framework_context:
        return

    print("Analyzing lead description...")

    prompt = f"""You are an expert technical consultant evaluating a potential contract lead.

    Below is your core framework, strengths, and project preferences:
    ---
    {framework_context}
    ---

    Here is the lead description provided by the potential client:
    ---
    {args.lead_description}
    ---

    Evaluate the lead against the framework and output the result EXACTLY in the following format.
    Calculate a fit score, propose a highly profitable scope based on your efficiency,
    and identify any risk flags.
    You MUST output using this EXACT tree-like character structure (using └── and ├──).
    DO NOT output plain text lists. DO NOT use markdown headers or bolding.
    Ensure you output the headers exactly as "Fit Assessment:", "Proposed Scope:",
    "Risk Flags:", and "Action:" WITHOUT any leading characters like ## or **.
    DO NOT USE BOLDING FOR HEADERS.

    Fit Assessment:
    └── Fit Score: [Score]/100 ([RATING])
        ├── [Reason 1]
        ├── [Reason 2]
        ├── [Reason 3]
        └── [Reason 4]

    Proposed Scope:
    └── [Duration] delivery (save [X] weeks = future margin)
        ├── Week 1: [Milestone]
        ├── Week 2: [Milestone]
        ├── Week 3: [Milestone]
        ├── Week 4: [Milestone]
        └── Cost: $[Total] (leave $[Buffer] buffer for client scope creep)

    Risk Flags:
    ├── [Flag 1]
    ├── [Flag 2]
    └── [Flag 3]

    Action:
    └── [Final recommendation to book call or pass, and why]
    """

    try:
        response = ollama.chat(model='gemma:2b', options={"temperature": 0.1}, messages=[
            {
                'role': 'user',
                'content': prompt,
            },
        ])
        content = response['message']['content']
        content = content.replace("**Fit Assessment:**", "Fit Assessment:")
        content = content.replace("**Proposed Scope:**", "Proposed Scope:")
        content = content.replace("**Risk Flags:**", "Risk Flags:")
        content = content.replace("**Action:**", "Action:")
        print("\n" + content)
    except Exception as e:
        print(f"Error calling Ollama: {e}")
        print("Ensure Ollama is running and the 'gemma:2b' model is installed.")

if __name__ == "__main__":
    main()
