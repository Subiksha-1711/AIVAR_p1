
import axios from "axios";

const API = axios.create({
  baseURL: "http://127.0.0.1:8000"
});

export async function sendMessage(message, improvePrompt) {
  const response = await API.post("/agent", {
    message: message,
    improve_prompt: improvePrompt
  });

  return response.data;
}

export async function selectWorkspace() {
  const response = await API.post("/select-workspace");
  return response.data;
}
