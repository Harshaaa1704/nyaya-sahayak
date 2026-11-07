import { useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { FileText, Gavel, Menu, MessageSquare, Plus, Send, ShieldCheck, Sparkles, Upload, X } from "lucide-react";

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api";
const suggestions = [
  "What is the difference between civil and criminal cases in India?",
  "What should I check before signing a rental agreement?",
  "Explain the basic steps in filing an FIR.",
];

const requestJson = async (url, options) => {
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), 60000);
  try {
    const response = await fetch(url, { ...options, signal: controller.signal });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "The request could not be completed.");
    return data;
  } catch (error) {
    if (error.name === "AbortError") {
      throw new Error("The AI provider took too long to respond. Please try again.");
    }
    throw error;
  } finally {
    window.clearTimeout(timeout);
  }
};

const createConversation = () => ({
  id: `${Date.now()}-${Math.random().toString(36).slice(2)}`,
  title: "New conversation",
  messages: [],
  document: null,
});

function App() {
  const [conversations, setConversations] = useState(() => [createConversation()]);
  const [activeConversationId, setActiveConversationId] = useState(() => conversations[0]?.id);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const fileInput = useRef(null);
  const activeConversation = conversations.find(({ id }) => id === activeConversationId) || conversations[0];
  const messages = activeConversation.messages;
  const document = activeConversation.document;

  const updateConversation = (id, update) => {
    setConversations((current) => current.map((conversation) => (
      conversation.id === id ? { ...conversation, ...update } : conversation
    )));
  };

  const sendMessage = async (text = input) => {
    const question = text.trim();
    if (!question || loading) return;
    setInput("");
    const next = [...messages, { role: "user", content: question }];
    const title = activeConversation.title === "New conversation"
      ? question.slice(0, 42) + (question.length > 42 ? "..." : "")
      : activeConversation.title;
    updateConversation(activeConversation.id, { messages: next, title });
    setLoading(true);
    try {
      const endpoint = document ? `${API_URL}/documents/${document.document_id}/chat` : `${API_URL}/chat`;
      const body = document ? { question, history: messages } : { messages: next };
      const data = await requestJson(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      const answer = document && data.references?.length
        ? `${data.answer}\n\n**Source pages:** ${data.references.join(", ")}`
        : data.answer;
      setConversations((current) => current.map((conversation) => (
        conversation.id === activeConversation.id
          ? { ...conversation, messages: [...conversation.messages, { role: "assistant", content: answer }] }
          : conversation
      )));
    } catch (error) {
      setConversations((current) => current.map((conversation) => (
        conversation.id === activeConversation.id
          ? { ...conversation, messages: [...conversation.messages, { role: "assistant", content: `**Unable to answer**\n\n${error.message}` }] }
          : conversation
      )));
    } finally { setLoading(false); }
  };

  const upload = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;
    setUploading(true);
    const form = new FormData();
    form.append("file", file);
    try {
      const data = await requestJson(`${API_URL}/documents`, { method: "POST", body: form });
      updateConversation(activeConversation.id, {
        document: data,
        messages: [{ role: "assistant", content: `I've processed **${data.filename}** (${data.pages} pages). Ask me anything about its contents.${data.has_text ? "" : "\n\nThis appears to be a scanned PDF, so selectable text was not found."}` }],
      });
    } catch (error) {
      updateConversation(activeConversation.id, {
        messages: [{ role: "assistant", content: `**Upload failed**\n\n${error.message}` }],
      });
    }
    finally { setUploading(false); event.target.value = ""; }
  };

  const newChat = () => {
    const conversation = createConversation();
    setConversations((current) => [...current, conversation]);
    setActiveConversationId(conversation.id);
    setInput("");
    setSidebarOpen(false);
  };

  const selectConversation = (id) => {
    if (loading) return;
    setActiveConversationId(id);
    setInput("");
    setSidebarOpen(false);
  };

  const removeDocument = () => updateConversation(activeConversation.id, { document: null });

  return (
    <div className="app-shell">
      <aside className={`sidebar ${sidebarOpen ? "open" : ""}`}>
        <div className="brand"><div className="brand-mark"><Gavel size={19} /></div><div><strong>Nyaya-Sahayak</strong><span>Legal clarity, simply.</span></div></div>
        <button className="new-chat" onClick={newChat}><Plus size={17} /> New conversation</button>
        <div className="conversation-list">
          <p className="conversation-label">Your conversations</p>
          {conversations.map((conversation) => (
            <button
              className={`conversation-item ${conversation.id === activeConversation.id ? "active" : ""}`}
              key={conversation.id}
              onClick={() => selectConversation(conversation.id)}
              title={conversation.title}
            >
              <MessageSquare size={15} />
              <span>{conversation.title}</span>
            </button>
          ))}
        </div>
        <div className="side-note"><ShieldCheck size={18} /><div><b>Private by design</b><span>Documents are held temporarily for this session.</span></div></div>
        <div className="sidebar-bottom"><span>Built for Indian legal information</span><span className="version">v1.0</span></div>
      </aside>
      {sidebarOpen && <button className="scrim" onClick={() => setSidebarOpen(false)} aria-label="Close menu" />}
      <main className="main">
        <header className="topbar"><button className="menu-btn" onClick={() => setSidebarOpen(true)}><Menu size={21} /></button><div className="mobile-brand"><Gavel size={18} /> Nyaya-Sahayak</div><div className="top-status"><span className="status-dot" /> AI legal assistant</div></header>
        <section className="chat-wrap">
          {messages.length === 0 ? <div className="welcome"><div className="welcome-icon"><Sparkles size={25} /></div><p className="eyebrow">WELCOME TO NYAYA-SAHAYAK</p><h1>Legal clarity,<br /><em>without the jargon.</em></h1><p className="welcome-copy">Ask questions about Indian law in plain language, or upload a legal document to understand what it says.</p><div className="suggestions">{suggestions.map((item) => <button key={item} onClick={() => sendMessage(item)}>{item}<span>→</span></button>)}</div></div>
            : <div className="messages">{messages.map((message, index) => <div className={`message-row ${message.role}`} key={`${message.role}-${index}`}><div className="avatar">{message.role === "assistant" ? <Gavel size={15} /> : "You"}</div><div className="message-content">            <ReactMarkdown remarkPlugins={[remarkGfm]}>{message.content}</ReactMarkdown></div></div>)}{loading && <div className="message-row assistant"><div className="avatar"><Gavel size={15} /></div><div className="typing"><i /><i /><i /></div></div>}</div>}
        </section>
        <div className="composer-area">
          {document && <div className="document-chip"><FileText size={16} /><span>{document.filename}</span><small>{document.pages} pages</small><button onClick={removeDocument} aria-label="Remove document"><X size={14} /></button></div>}
          <div className="composer"><textarea value={input} onChange={(event) => setInput(event.target.value)} onKeyDown={(event) => { if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); sendMessage(); } }} placeholder={document ? "Ask about this document..." : "Ask a question about Indian law..."} rows="1" /><input ref={fileInput} type="file" accept="application/pdf" onChange={upload} hidden /><button className="upload-btn" onClick={() => fileInput.current?.click()} disabled={uploading} aria-label="Upload PDF">{uploading ? <span className="spinner" /> : <Upload size={18} />}</button><button className="send-btn" onClick={() => sendMessage()} disabled={!input.trim() || loading} aria-label="Send"><Send size={17} /></button></div>
          <p className="disclaimer">Nyaya-Sahayak provides general legal information, not legal advice. Verify important matters with a qualified lawyer.</p>
        </div>
      </main>
    </div>
  );
}

export default App;
