
import { useState } from "react";
import { sendMessage } from "../services/api.js";
import "./Chat.css";

function Chat() {
  const [improvePrompt, setImprovePrompt] = useState(false);
  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);

  const handleSend = async () => {
    if (!message.trim() || loading) return;

    const userMessage = message;

    setMessages((prev) => [
      ...prev,
      { role: "user", text: userMessage }
    ]);

    setMessage("");
    setLoading(true);

    try {
      const data = await sendMessage(userMessage, improvePrompt);

      setMessages((prev) => [
        ...prev,
        { role: "assistant", text: data.response }
      ]);
    } catch (error) {
      console.error("API Error:", error);

      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          text: error.response?.data?.detail || error.message
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="chat-section">
      <h2>AI Assistant</h2>

      <div className="chat-messages">
        {messages.length === 0 && (
          <>
            <h3>Welcome to AI Coding Agent!</h3>
            <p>How can I help you today?</p>
          </>
        )}

        {messages.map((item, index) => (
          <div key={index} className={`message ${item.role}`}>
            <strong>
              {item.role === "user" ? "You" : "AI Assistant"}
            </strong>
            <p>{item.text}</p>
          </div>
        ))}

        {loading && <p>AI is thinking...</p>}
      </div>

      <label className="prompt-option">
        <input
          type="checkbox"
          checked={improvePrompt}
          onChange={(e) => setImprovePrompt(e.target.checked)}
        />
        Improve my prompt
      </label>

      <div className="chat-input">
        <input
          type="text"
          placeholder="Enter your message..."
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") handleSend();
          }}
        />

        <button onClick={handleSend} disabled={loading}>
          {loading ? "Sending..." : "Send"}
        </button>
      </div>
    </section>
  );
}

export default Chat;
