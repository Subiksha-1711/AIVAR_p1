
import { useState } from "react";
import "./App.css";
import Chat from "./components/Chat";
import { selectWorkspace } from "./services/api.js";

function App() {
  const [workspace, setWorkspace] = useState("");

  const handleSelectWorkspace = async () => {
    try {
      const data = await selectWorkspace();
      setWorkspace(data.folder);
    } catch (error) {
      console.error("Workspace Error:", error);
      alert(error.response?.data?.detail || error.message);
    }
  };

  return (
    <div className="app">
      <header className="header">
        <h2>AI Coding Agent</h2>
        <span>Powered by Groq AI</span>
      </header>

      <main className="main-container">
        <aside className="sidebar">
          <h3>Workspace</h3>

          <button
            className="workspace-btn"
            onClick={handleSelectWorkspace}
          >
            Select Workspace
          </button>

          {workspace && (
            <p className="empty-text">{workspace}</p>
          )}

          <h3>Files</h3>
          <p className="empty-text">No files loaded</p>
        </aside>

        <Chat />

        <section className="editor-section">
          <h3>Code Editor</h3>
          <div className="editor-placeholder">
            Select a file to view its code
          </div>

          <h3>Execution Output</h3>
          <div className="output-placeholder">
            Program output will appear here
          </div>
        </section>
      </main>
    </div>
  );
}

export default App;
