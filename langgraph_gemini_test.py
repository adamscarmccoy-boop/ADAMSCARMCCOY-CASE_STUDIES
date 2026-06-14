"""
LangGraph & Google-GenAI SDK Integration Test
===============================================
A stateful, multi-turn orchestrator that runs the Gemini API via the modern
google-genai SDK inside a LangGraph workflow. Exposes local repo inspection tools.
"""

import os
import sys
import asyncio
from typing import Annotated, List, Literal, Dict, Any, Union
import operator
from dotenv import load_dotenv

# Ensure stdout uses UTF-8 to prevent encoding crashes on Windows console
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# Load env (GEMINI_API_KEY)
load_dotenv()

from google import genai
from google.genai import types
from langgraph.graph import StateGraph, START, END
from typing_extensions import TypedDict

# ─── 1. TOOL DEFINITIONS ──────────────────────────────────────────────────────

def list_workspace_files() -> dict:
    """List all Python files in the current folder.
    
    Returns:
        dict: A list of python filenames.
    """
    files = [f for f in os.listdir(".") if f.endswith(".py")]
    return {"status": "success", "files": files}

def view_file_preview(filename: str) -> dict:
    """Read the first 15 lines of a python file to inspect its code.
    
    Args:
        filename: The name of the file to preview.
        
    Returns:
        dict: The content preview or error.
    """
    if not os.path.exists(filename):
        return {"status": "error", "message": f"File '{filename}' not found."}
    try:
        with open(filename, "r", encoding="utf-8", errors="ignore") as f:
            lines = [f.readline() for _ in range(15)]
        return {"status": "success", "filename": filename, "preview": "".join(lines)}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# Registry mapping tool names to actual functions for routing
TOOLS_REGISTRY = {
    "list_workspace_files": list_workspace_files,
    "view_file_preview": view_file_preview,
}

# ─── 2. STATE DEFINITIONS ─────────────────────────────────────────────────────

class AgentState(TypedDict):
    # LangGraph statefully accumulates conversation turns here
    messages: Annotated[List[types.Content], operator.add]

# ─── 3. NORMALIZER HELPER ─────────────────────────────────────────────────────

def normalize_messages(messages: List[Union[types.Content, dict, Any]]) -> List[types.Content]:
    """Convert any incoming dicts or LangChain formats to google-genai Content types."""
    normalized = []
    for msg in messages:
        if isinstance(msg, types.Content):
            normalized.append(msg)
        elif isinstance(msg, dict):
            role = msg.get("role", "user")
            # Map 'assistant' to 'model'
            if role == "assistant":
                role = "model"
            content = msg.get("content", "")
            normalized.append(types.Content(
                role=role,
                parts=[types.Part.from_text(text=content)]
            ))
        elif hasattr(msg, "content"):  # LangChain compatibility
            role = "user"
            if msg.__class__.__name__ == "AIMessage":
                role = "model"
            normalized.append(types.Content(
                role=role,
                parts=[types.Part.from_text(text=msg.content)]
            ))
    return normalized

# ─── 4. NODE DEFINITIONS ──────────────────────────────────────────────────────

async def call_gemini_agent(state: AgentState) -> dict:
    """Node that statelessly executes Gemini with the messages history."""
    client = genai.Client()
    
    # Normalize state history
    contents = normalize_messages(state["messages"])
    
    # Configure Gemini with tools and system prompt
    config = types.GenerateContentConfig(
        system_instruction=(
            "You are the LangGraph-Gemini Bridge. Your job is to inspect the local "
            "codebase directory. Use your tools to check what files are present "
            "and inspect their contents. Keep your reports structured and clear."
        ),
        temperature=0.0,  # Deterministic tool calling
        tools=[list_workspace_files, view_file_preview]
    )
    
    # Call the model
    # Note: we use gemini-2.5-flash for fast local iterations
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=contents,
        config=config
    )
    
    # Extract candidate response content (which may contain text and/or function_call parts)
    model_content = response.candidates[0].content
    
    # Ensure role is set to 'model' for state storage
    if not model_content.role:
        model_content.role = "model"
        
    return {
        "messages": [model_content]
    }

async def execute_tools(state: AgentState) -> dict:
    """Node that executes requested tool calls and appends the outputs to history."""
    last_message = state["messages"][-1]
    tool_responses = []
    
    for part in last_message.parts:
        if part.function_call:
            call = part.function_call
            print(f"⚙️  [WORKFLOW EXECUTOR] Running tool '{call.name}' with args: {call.args}")
            
            tool_func = TOOLS_REGISTRY.get(call.name)
            if tool_func:
                try:
                    result = tool_func(**call.args)
                except Exception as e:
                    result = {"status": "error", "message": str(e)}
            else:
                result = {"status": "error", "message": f"Tool '{call.name}' not registered."}
                
            # Build function response part
            tool_responses.append(
                types.Part.from_function_response(
                    name=call.name,
                    response={"result": result}
                )
            )
            
    # Function responses are wrapped in a role='user' message
    response_content = types.Content(role="user", parts=tool_responses)
    
    return {
        "messages": [response_content]
    }

# ─── 5. ROUTING CONDITIONAL ───────────────────────────────────────────────────

def should_continue(state: AgentState) -> Literal["tools", "end"]:
    """Determines whether to call a tool or end the turn."""
    last_message = state["messages"][-1]
    if last_message.parts and any(p.function_call for p in last_message.parts):
        return "tools"
    return "end"

# ─── 6. COMPILE WORKFLOW ──────────────────────────────────────────────────────

def build_workflow() -> StateGraph:
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("agent", call_gemini_agent)
    workflow.add_node("tools", execute_tools)
    
    # Set entry point
    workflow.set_entry_point("agent")
    
    # Add conditional edge
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            "end": END
        }
    )
    
    # Add edge from tools back to agent
    workflow.add_edge("tools", "agent")
    
    return workflow.compile()

app = build_workflow()

# ─── 7. MULTI-TURN TEST RUNNER ────────────────────────────────────────────────

async def run_multi_turn_test():
    print("🚀 [START] Stateful LangGraph & google-genai Multi-Turn Test")
    print("=" * 70)
    
    # Turn 1: List the workspace files
    turn_1_query = types.Content(
        role="user",
        parts=[types.Part.from_text(text="Please list the Python files in this folder.")]
    )
    
    print("\n👤 User (Turn 1): 'Please list the Python files in this folder.'")
    state = {"messages": [turn_1_query]}
    
    # Invoke LangGraph workflow
    state = await app.ainvoke(state)
    
    # Display agent response
    last_msg = state["messages"][-1]
    agent_text = "".join(p.text for p in last_msg.parts if p.text)
    print(f"\n🤖 Agent (Turn 1):\n{agent_text}")
    print("-" * 70)
    
    # Turn 2: Inspect a specific file dynamically based on the previous result
    turn_2_query = types.Content(
        role="user",
        parts=[types.Part.from_text(text="Great. Can you show me the first 15 lines of update_nb.py?")]
    )
    
    print("\n👤 User (Turn 2): 'Great. Can you show me the first 15 lines of update_nb.py?'")
    # LangGraph will statefully append this message to the previous message array
    state["messages"].append(turn_2_query)
    
    # Invoke LangGraph workflow with updated history state
    state = await app.ainvoke(state)
    
    # Display final agent response
    last_msg = state["messages"][-1]
    agent_text = "".join(p.text for p in last_msg.parts if p.text)
    print(f"\n🤖 Agent (Turn 2):\n{agent_text}")
    print("=" * 70)
    print("✅ [COMPLETE] Multi-Turn Workflow Execution Successful.")

if __name__ == "__main__":
    asyncio.run(run_multi_turn_test())
