
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from groq import Groq
from dotenv import load_dotenv
from pathlib import Path
from tkinter import filedialog, messagebox
import tkinter as tk
import subprocess
import sys
import json
import os
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

app = FastAPI(title="AI Coding Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

WORKSPACE = None
conversation_history = []

MAX_TOOL_ITERATIONS = 8
MAX_HISTORY_MESSAGES = 6


# -------------------- REQUEST MODELS --------------------

class ChatRequest(BaseModel):
    message: str
    improve_prompt: bool = False


class ReadFileRequest(BaseModel):
    filename: str


class CreateFileRequest(BaseModel):
    filename: str
    content: str


class EditFileRequest(BaseModel):
    filename: str
    content: str


class RunCodeRequest(BaseModel):
    filename: str


# -------------------- HOME --------------------

@app.get("/")
def home():
    return {
        "message": "AI Coding Agent Backend is running!"
    }


# -------------------- PROMPT IMPROVER --------------------

@app.post("/improve-prompt")
def improve_prompt(request: ChatRequest):

    try:
        api_key = os.getenv("GROQ_API_KEY")
        model = os.getenv("GROQ_MODEL")

        if not api_key or not model:
            raise HTTPException(
                status_code=500,
                detail="Groq API key or model is missing."
            )

        client = Groq(api_key=api_key)

        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": """
You are an expert programming prompt engineer.

Your task is to improve vague programming instructions.

Rules:
1. Understand the user's original intention.
2. Make the instruction clear and specific.
3. Include relevant technical details when appropriate.
4. Do not change the user's original intention.
5. Do not invent unnecessary requirements.
6. Return only the improved prompt.
"""
                },
                {
                    "role": "user",
                    "content": request.message
                }
            ]
        )

        return {
            "original_prompt": request.message,
            "improved_prompt": response.choices[0].message.content
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# -------------------- AGENT PROMPT IMPROVEMENT --------------------

def get_improved_prompt(client, model, original_prompt):

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": """
You are an expert programming prompt engineer.

Improve the user's programming instruction.

Rules:
1. Preserve the user's original intention.
2. Make the instruction clear and specific.
3. Do not add unnecessary features.
4. Do not assume a technology stack unless the user specified one.
5. Do not invent requirements or constraints.
6. Keep the improved prompt focused on what the user asked.
7. Return only the improved prompt, without an introduction.
"""
            },
            {
                "role": "user",
                "content": original_prompt
            }
        ]
    )

    improved = response.choices[0].message.content

    if not improved:
        raise HTTPException(
            status_code=500,
            detail="The prompt improver returned an empty response."
        )

    return improved.strip()


# -------------------- NORMAL CHAT --------------------

@app.post("/chat")
def chat(request: ChatRequest):

    try:
        api_key = os.getenv("GROQ_API_KEY")
        model = os.getenv("GROQ_MODEL")

        if not api_key or not model:
            raise HTTPException(
                status_code=500,
                detail="Groq API key or model is missing from .env."
            )

        client = Groq(api_key=api_key)

        response = client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful programming assistant."
                },
                {
                    "role": "user",
                    "content": request.message
                }
            ]
        )

        return {
            "response": response.choices[0].message.content
        }

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# -------------------- WORKSPACE SELECTION --------------------

@app.post("/select-workspace")
async def select_workspace():

    global WORKSPACE

    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)

    try:
        folder = filedialog.askdirectory(
            title="Select your project folder"
        )
    finally:
        root.destroy()

    if not folder:
        return {
            "message": "No folder selected"
        }

    WORKSPACE = Path(folder).resolve()

    conversation_history.clear()

    return {
        "message": "Workspace selected successfully",
        "folder": str(WORKSPACE)
    }


# -------------------- SAFE FILE PATH --------------------

def get_safe_path(filename):

    if WORKSPACE is None:
        raise HTTPException(
            status_code=400,
            detail="Please select a workspace first."
        )

    if not filename or not filename.strip():
        raise HTTPException(
            status_code=400,
            detail="Filename cannot be empty."
        )

    file_path = (WORKSPACE / filename).resolve()

    try:
        file_path.relative_to(WORKSPACE)
    except ValueError:
        raise HTTPException(
            status_code=403,
            detail="Access outside the workspace is not allowed."
        )

    return file_path


def check_protected_file(file_path):

    if file_path.name == ".env" or file_path.name.startswith(".env."):
        raise HTTPException(
            status_code=403,
            detail="Access to environment secret files is not allowed."
        )


# -------------------- LIST FILES --------------------

@app.get("/list-files")
def list_files():

    if WORKSPACE is None:
        raise HTTPException(
            status_code=400,
            detail="Please select a workspace first."
        )

    ignored = {
        "venv",
        ".venv",
        ".git",
        "node_modules",
        "__pycache__"
    }

    files = []

    for path in WORKSPACE.rglob("*"):

        relative_path = path.relative_to(WORKSPACE)

        if any(part in ignored for part in relative_path.parts):
            continue

        if path.is_file():

            try:
                path.resolve().relative_to(WORKSPACE)
            except ValueError:
                continue

            files.append(str(relative_path))

    return {
        "workspace": str(WORKSPACE),
        "files": files
    }


# -------------------- READ FILE --------------------

@app.post("/read-file")
def read_file(request: ReadFileRequest):

    print("READ FILE REQUEST:", request.filename)

    file_path = get_safe_path(request.filename)

    check_protected_file(file_path)

    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail="File not found."
        )

    if not file_path.is_file():
        raise HTTPException(
            status_code=400,
            detail="The selected path is not a file."
        )

    if file_path.stat().st_size > 1_000_000:
        raise HTTPException(
            status_code=413,
            detail="File is too large to read."
        )

    try:
        content = file_path.read_text(encoding="utf-8")

        print("FILE CONTENT LENGTH:", len(content))

        max_chars = 3000

        if len(content) > max_chars:
            content = content[:max_chars] + "\n\n[File content truncated.]"

        result = {
            "filename": request.filename,
            "content": content
        }

        print("READ FILE RESULT:", result)

        return result

    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400,
            detail="This file is not a readable UTF-8 text file."
        )


# -------------------- CREATE FILE --------------------

@app.post("/create-file")
def create_file(request: CreateFileRequest):

    file_path = get_safe_path(request.filename)

    check_protected_file(file_path)

    if file_path.exists():
        raise HTTPException(
            status_code=409,
            detail="File already exists. Cannot overwrite it."
        )

    if not file_path.parent.exists():
        raise HTTPException(
            status_code=404,
            detail="Parent directory does not exist."
        )

    try:
        with file_path.open("x", encoding="utf-8") as file:
            file.write(request.content)

        return {
            "message": "File created successfully.",
            "filename": request.filename
        }

    except OSError as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# -------------------- EDIT FILE --------------------

@app.post("/edit-file")
def edit_file(request: EditFileRequest):

    file_path = get_safe_path(request.filename)

    check_protected_file(file_path)

    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail="File not found."
        )

    if not file_path.is_file():
        raise HTTPException(
            status_code=400,
            detail="The selected path is not a file."
        )

    try:
        file_path.write_text(
            request.content,
            encoding="utf-8"
        )

        return {
            "message": "File updated successfully.",
            "filename": request.filename
        }

    except OSError as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# -------------------- RUN PYTHON CODE --------------------

@app.post("/run-code")
def run_code(request: RunCodeRequest):

    file_path = get_safe_path(request.filename)

    check_protected_file(file_path)

    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail="File not found."
        )

    if not file_path.is_file():
        raise HTTPException(
            status_code=400,
            detail="The selected path is not a file."
        )

    if file_path.suffix.lower() != ".py":
        raise HTTPException(
            status_code=400,
            detail="Only Python files can be executed."
        )

    try:
        result = subprocess.run(
            [sys.executable, str(file_path)],
            cwd=str(WORKSPACE),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=10
        )

        return {
            "filename": request.filename,
            "success": result.returncode == 0,
            "output": result.stdout,
            "error": result.stderr,
            "return_code": result.returncode,
            "message": (
                "Program executed successfully."
                if result.returncode == 0
                else "Program execution failed."
            )
        }

    except subprocess.TimeoutExpired:
        raise HTTPException(
            status_code=408,
            detail="Execution timed out after 10 seconds."
        )

    except OSError as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# -------------------- USER APPROVAL --------------------

def confirm_file_change(action, filename):

    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)

    try:
        approved = messagebox.askyesno(
            "AI Coding Agent Approval",
            f"Allow AI to {action} this file?\n\n{filename}",
            parent=root
        )

        return approved

    finally:
        root.destroy()


# -------------------- GROQ TOOL DEFINITIONS --------------------

AGENT_TOOLS = [

    {
        "type": "function",
        "function": {
            "name": "list_files",
            "description": "List all files in the selected project workspace.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read the contents of a file in the selected project workspace.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "Relative path of the file to read."
                    }
                },
                "required": ["filename"]
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "create_file",
            "description": "Create a new file inside the selected workspace.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string"
                    },
                    "content": {
                        "type": "string"
                    }
                },
                "required": ["filename", "content"]
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "edit_file",
            "description": "Replace the contents of an existing file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string"
                    },
                    "content": {
                        "type": "string"
                    }
                },
                "required": ["filename", "content"]
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "run_code",
            "description": "Execute a Python file inside the selected workspace.",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string"
                    }
                },
                "required": ["filename"]
            }
        }
    }

]


# -------------------- EXECUTE AGENT TOOLS --------------------

def execute_agent_tool(tool_name, arguments):

    if tool_name == "list_files":
        return list_files()

    elif tool_name == "read_file":

        request = ReadFileRequest(
            filename=arguments["filename"]
        )

        return read_file(request)

    elif tool_name == "create_file":

        filename = arguments["filename"]

        if not confirm_file_change("create", filename):
            return {
                "message": "File creation rejected by user."
            }

        request = CreateFileRequest(
            filename=filename,
            content=arguments["content"]
        )

        return create_file(request)

    elif tool_name == "edit_file":

        filename = arguments["filename"]

        if not confirm_file_change("edit", filename):
            return {
                "message": "File editing rejected by user."
            }

        request = EditFileRequest(
            filename=filename,
            content=arguments["content"]
        )

        return edit_file(request)

    elif tool_name == "run_code":

        filename = arguments["filename"]

        if not confirm_file_change("execute", filename):
            return {
                "message": "Code execution rejected by user."
            }

        request = RunCodeRequest(
            filename=filename
        )

        return run_code(request)

    else:

        return {
            "error": f"Unknown tool: {tool_name}"
        }


# -------------------- CONVERSATION HISTORY --------------------

def save_conversation(user_message, assistant_message):

    conversation_history.append({
        "role": "user",
        "content": user_message
    })

    conversation_history.append({
        "role": "assistant",
        "content": assistant_message or ""
    })

    if len(conversation_history) > MAX_HISTORY_MESSAGES:
        del conversation_history[:-MAX_HISTORY_MESSAGES]


@app.post("/clear-history")
def clear_history():

    conversation_history.clear()

    return {
        "message": "Conversation history cleared successfully."
    }


# -------------------- AI AGENT --------------------

@app.post("/agent")
async def run_agent(request: ChatRequest):

    if WORKSPACE is None:
        raise HTTPException(
            status_code=400,
            detail="Please select a workspace first."
        )

    api_key = os.getenv("GROQ_API_KEY")
    model = os.getenv("GROQ_MODEL")

    if not api_key or not model:
        raise HTTPException(
            status_code=500,
            detail="Groq API key or model is missing from .env."
        )

    try:

        client = Groq(api_key=api_key)

        user_message = request.message

        if request.improve_prompt:
            user_message = get_improved_prompt(
                client,
                model,
                request.message
            )

        system_prompt = """
You are an intelligent AI Coding Agent.

Your job is to understand the user's programming request
and work with their selected project workspace.

AVAILABLE TOOLS:

1. list_files:
   Lists project files.

2. read_file:
   Reads the contents of a file.

3. create_file:
   Creates a new file.

4. edit_file:
   Updates an existing file.

5. run_code:
   Executes a Python file.

RULES:

- Understand the user's request before selecting a tool.
- Use tools when actual project operations are required.
- Never invent file contents.
- Read relevant files before modifying them.
- Use relative file paths inside the selected workspace.
- Do not access environment secret files.
- File creation, editing and execution require user approval.
- If an operation is rejected, do not claim it succeeded.
- Check tool results before reporting success.
- Explain errors clearly.
- After completing the requested operations, provide a clear final response.

IMPORTANT TOOL-USAGE RULES:

- When asked to create a file, call create_file.
- When asked to edit a file, call edit_file.
- When asked to run code, call run_code.
- Never ask for approval through a chat message.
- The application displays an approval popup.
- Perform requested operations in the correct order.
- Use previous conversation messages to understand follow-up requests.
- If the user says "that file", use the file identified in the conversation.

AUTOMATIC CODE CHECKING:

- After creating or editing a Python file, check whether it can be executed automatically.
- If the program requires interactive keyboard input using input(), do not automatically execute it.
- For programs that can run automatically, use the run_code tool.
- Check the execution result.
- If execution succeeds, report the actual output.
- If execution fails, analyze the error and identify the cause.
- If the problem can be fixed, use edit_file to correct the code.
- After fixing the code, run it again to verify the correction.
- Make at most two automatic correction attempts for each task.
- Never claim that code works unless execution or testing confirms it.
- If execution times out, explain that the program may require user input or may be taking too long.
"""

        messages = [
            {
                "role": "system",
                "content": system_prompt
            }
        ] + conversation_history[-MAX_HISTORY_MESSAGES:] + [
            {
                "role": "user",
                "content": user_message
            }
        ]

        # AGENT TOOL-CALLING LOOP

        for step in range(MAX_TOOL_ITERATIONS):

            print(f"\nAgent iteration: {step + 1}")

            response = client.chat.completions.create(
                model=model,
                messages=messages,
                tools=AGENT_TOOLS,
                tool_choice="auto"
            )

            assistant_message = response.choices[0].message

            print("AI response:", assistant_message.content)
            print("Tool calls:", assistant_message.tool_calls)

            # Return final response if no tools are requested.

            if not assistant_message.tool_calls:

                save_conversation(
                    user_message,
                    assistant_message.content
                )

                return {
                    "response": assistant_message.content
                }

            # Add assistant tool-call message.

            messages.append(
                assistant_message.model_dump(
                    mode="json",
                    exclude_none=True
                )
            )

            # Execute requested tools.

            for tool_call in assistant_message.tool_calls:

                tool_name = tool_call.function.name

                print("Executing tool:", tool_name)

                try:

                    arguments = json.loads(
                        tool_call.function.arguments
                    )

                    print("Arguments:", arguments)

                    result = execute_agent_tool(
                        tool_name,
                        arguments
                    )

                except HTTPException as e:

                    result = {
                        "error": e.detail
                    }

                except (ValueError, KeyError, TypeError) as e:

                    result = {
                        "error": f"Invalid tool arguments: {str(e)}"
                    }

                except Exception as e:

                    result = {
                        "error": str(e)
                    }

                print("Tool result:", result)

                # Send tool result back to Groq.

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": tool_name,
                    "content": json.dumps(
                        result,
                        ensure_ascii=False,
                        default=str
                    )
                })

        # Tool iteration limit reached.

        messages.append({
            "role": "user",
            "content": (
                "The tool-call limit has been reached. "
                "Summarize the operations completed so far and "
                "explain any remaining work. Do not request more tools."
            )
        })

        final_response = client.chat.completions.create(
            model=model,
            messages=messages
        )

        final_message = final_response.choices[0].message

        save_conversation(
            user_message,
            final_message.content
        )

        return {
            "response": final_message.content
            or "The agent reached its tool-call limit."
        }

    except HTTPException:
        raise

    except Exception as e:

        print("Agent error:", str(e))

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
