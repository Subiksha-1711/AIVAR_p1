# AI Coding Agent

An AI-powered coding assistant that helps developers manage project files, generate and edit code, execute Python programs, and automatically fix eligible coding errors using natural language instructions.

The project uses **React.js** for the frontend, **FastAPI** for the backend, and **Groq API** for AI-powered responses and tool calling.

## Features

- **AI-Powered Coding Assistance:** Interact with the coding agent using natural language instructions.
- **Workspace Selection:** Select a local project folder for the agent to work with.
- **File Management:** List and read files from the selected workspace.
- **File Creation:** Generate new files based on user instructions, with user approval.
- **File Editing:** Modify existing project files with user approval.
- **Python Code Execution:** Run Python programs and view their output or errors, with user approval.
- **Automatic Error Correction:** Detect errors in eligible Python programs, attempt to correct them, and run the programs again. The agent allows a maximum of two automatic correction attempts per task.
- **Prompt Improvement:** Improve user prompts before sending them to the AI agent.
- **Conversation History:** Maintain recent conversation context during the current backend session.

## Technology Stack

### Frontend
- React.js
- Vite
- JavaScript
- CSS
- Axios

### Backend
- Python
- FastAPI
- Uvicorn
- Groq API
- Python-dotenv

## Project Structure

```text
AI-Coding-Agent/
│
├── backend/
│   ├── main.py
│   ├── .env
│   └── ...
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── services/
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── package.json
│   └── ...
│
├── .gitignore
└── README.md
```

## How It Works

1. The user selects a local project workspace.
2. The user sends a coding instruction through the React frontend.
3. The FastAPI backend sends the instruction to the Groq API.
4. The AI agent decides which available tools are needed.
5. The backend performs the requested file operations or Python execution, subject to user approval.
6. The agent examines execution results and can attempt to fix eligible Python errors.
7. The response is returned to the frontend.

## Setup and Installation

### 1. Clone the Repository

```bash
git clone https://github.com/Subiksha-1711/AIVAR_p1.git
cd AIVAR_p1
```

### 2. Backend Setup

Open a terminal inside the backend folder:

```bash
cd backend
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it on Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Install the required backend dependencies used by the project.

Create a `.env` file inside the backend folder and configure your Groq API key using the environment variable name expected by the backend code.

Start the backend:

```bash
python -m uvicorn main:app --reload
```

Backend API documentation:

```text
http://127.0.0.1:8000/docs
```

### 3. Frontend Setup

Open another terminal:

```bash
cd frontend
```

Install dependencies:

```bash
npm install
```

Start the frontend:

```bash
npm run dev
```

Open the local URL displayed by Vite in your browser.

## Available Agent Tools

The AI agent uses the following tools:

- `list_files` – Lists files in the selected workspace.
- `read_file` – Reads the contents of a file.
- `create_file` – Creates a new file.
- `edit_file` – Modifies an existing file.
- `run_code` – Executes Python programs.

## Security

- API keys are stored in the backend environment file.
- The `.env` file is excluded from Git using `.gitignore`.
- File operations are restricted to the selected workspace.
- User approval is required for file creation, editing, and code execution.
- Python code execution is not sandboxed. Only run trusted code.

## Limitations

- Conversation history is maintained in backend memory and is not permanently stored.
- Interactive Python programs requiring user input are not automatically executed.
- Automatic debugging is limited to two correction attempts per task.
- The backend must be running for the frontend to communicate with the AI agent.

## Future Enhancements

- Improved workspace and file explorer interface.
- Enhanced code editing experience.
- Persistent conversation storage.
- Additional programming language execution support.

---

**AI Coding Agent** – An AI-powered assistant for code generation, file management, execution, and debugging.
