import { useState, useEffect, useRef } from "react";
import { FaArrowRight } from "react-icons/fa";
import Markdown from "react-markdown";

const API_BASE = import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000";

export default function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  // const [uploading, setUploading] = useState(false);
  const [uploadMessage, setUploadMessage] = useState("");
  const [currentConversationId, setCurrentConversationId] = useState(null);
  const [open, setOpen] = useState(true);

  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  useEffect(() => {
    const savedId = localStorage.getItem("conversationId");
    if (savedId) {
      setCurrentConversationId(savedId);
      fetch(`${API_BASE}/conversations/${savedId}/messages`)
        .then(res => res.json())
        .then(data => {
          if (Array.isArray(data)) {
            setMessages(data.map(m => ({
              id: m.id,
              role: m.role,
              content: m.content,
              created_at: m.created_at
            })));
          }
        })
        .catch(() => { });
    }
  }, []);

  // const handleFileUpload = async (event) => {
  //   const file = event.target.files[0];
  //   if (!file) return;

  //   setUploading(true);
  //   setError("");
  //   setUploadMessage("");

  //   const formData = new FormData();
  //   formData.append("file", file);

  //   try {
  //     const res = await fetch(`${API_BASE}/upload`, { method: "POST", body: formData });
  //     const data = await res.json();
  //     if (!res.ok) throw new Error(data?.detail || "Upload failed");
  //     setUploadMessage(`✅ ${data?.message} (${data?.chunks_added} chunks added)`);
  //   } catch (e) {
  //     setError(e.message);
  //   } finally {
  //     setUploading(false);
  //   }
  // };

  const sendMessage = async () => {
    if (!input.trim() || loading) return;

    const userMessage = input.trim();
    setInput("");
    setLoading(true);
    setError("");

    const tempUserMessage = {
      id: `temp-${Date.now()}`,
      role: "user",
      content: userMessage,
      created_at: new Date().toISOString(),
    };
    setMessages(prev => [...prev, tempUserMessage]);

    try {
      const res = await fetch(`${API_BASE}/chat/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: userMessage,
          conversation_id: currentConversationId,
          top_k: 5,
        }),
      });

      if (!res.ok) throw new Error("Request failed");

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let conversationId = null;
      let userMessageId = null;
      let assistantMessageId = null;
      let assistantContent = "";
      let tempAssistantMessageId = `temp-assistant-${Date.now()}`;

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));

              if (data.conversation_id) {
                conversationId = data.conversation_id;
                userMessageId = data.user_message_id;
                setCurrentConversationId(conversationId);
                localStorage.setItem("conversationId", conversationId);

                setMessages(prev => {
                  const filtered = prev.filter(msg => msg.id !== tempUserMessage.id);
                  return [
                    ...filtered,
                    { id: userMessageId, role: "user", content: userMessage, created_at: new Date().toISOString() }
                  ];
                });
              }

              if (data.content !== undefined) {
                if (data.done) {
                  assistantMessageId = data.message_id;
                  setMessages(prev => {
                    const filtered = prev.filter(msg => msg.id !== tempAssistantMessageId);
                    return [
                      ...filtered,
                      { id: assistantMessageId, role: "assistant", content: assistantContent, created_at: new Date().toISOString() }
                    ];
                  });
                } else {
                  assistantContent += data.content;
                  setMessages(prev => {
                    const filtered = prev.filter(msg => msg.id !== tempAssistantMessageId);
                    return [
                      ...filtered,
                      { id: tempAssistantMessageId, role: "assistant", content: assistantContent, created_at: new Date().toISOString() }
                    ];
                  });
                }
              }
            } catch (e) {
              console.error("Error parsing stream data:", e);
            }
          }
        }
      }
    } catch (e) {
      setError(e.message);
      setMessages(prev => prev.filter(msg =>
        !msg.id.startsWith("temp-") && !msg.id.startsWith("temp-assistant-")
      ));
    } finally {
      setLoading(false);
    }
  };

  const formatTime = (dateString) => {
    return new Date(dateString).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <div className="fixed inset-0 pointer-events-none">
      {/* Launcher when closed */}
      {!open && (
        <button
          onClick={() => setOpen(true)}
          className="pointer-events-auto fixed bottom-6 right-6 bg-teal-500 text-white rounded-full shadow-lg px-4 py-3 font-semibold hover:bg-teal-600"
        >
          <p>🤖 Ask Me</p>
        </button>
      )}

      {/* Chat Widget */}
      {open && (
        <div className="px-6 py-10 pointer-events-auto fixed right-0 w-full sm:w-[50vw] lg:w-[30vw] h-screen bg-white rounded-2xl shadow-xl flex flex-col overflow-hidden">
          {/* Header */}
          <div className="flex items-center justify-between px-4 py-3 border-b border-teal-100">
            <div className="flex items-center space-x-2">
              <img src="/assets/ai_small_stars.svg" alt="ai small stars" />              
              <h2 className="text-teal-500 font-semibold">Ask Me Anything!</h2>
            </div>
            <button
              onClick={() => setOpen(false)}
              className="text-gray-500 hover:text-gray-700"
              aria-label="Close"
            >
              ✕
            </button>
          </div>

          {/* Messages Area */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-white border border-teal-400 rounded-lg">
            {messages.length === 0 ? (
              <div className="h-full flex flex-col items-center justify-center text-gray-600">
                <img src="/assets/ai_stars.svg" alt="ai stars" className="self-start pl-6" />
                <p className="text-lg font-medium">Hi, What can I help you with?</p>
              </div>
            ) : (
              messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[80%] px-4 py-2 rounded-2xl ${message.role === 'user'
                        ? 'bg-teal-500 text-white rounded-br-sm'
                        : 'bg-white border border-gray-200 rounded-bl-sm'
                      }`}
                  >
                    <Markdown>{message.content}</Markdown>
                    <div className={`text-[11px] mt-1 ${message.role === 'user' ? 'text-teal-100' : 'text-gray-400'}`}>
                      {formatTime(message.created_at)}
                    </div>
                  </div>
                </div>
              ))
            )}
            {loading && (
              <div className="flex justify-start">
                <div className="bg-white border border-gray-200 px-4 py-2 rounded-2xl">
                  <div className="flex space-x-1">
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                    <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <div className="border-t border-teal-100 py-2">
            {error && <div className="text-red-600 text-xs mb-2">{error}</div>}
            {uploadMessage && <div className="text-green-600 text-xs mb-2">{uploadMessage}</div>}

            <div className="flex items-end">
              <div className="p-4 rounded-lg flex flex-col justify-between items-center w-full border border-teal-400 ">
                <textarea
                  rows={2}
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyUp={(e) => e.key === 'Enter' && !e.shiftKey && sendMessage()}
                  placeholder="Type here..."
                  className="w-full resize-none px-3 py-2 focus:outline-none focus:border-none"
                  disabled={loading}
                />
                <button
                  onClick={sendMessage}
                  disabled={loading || !input.trim()}
                  className="flex self-end items-center space-x-2 text-white px-4 py-2 rounded-full hover:cursor-pointer border-black border-2 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <span className="text-black">Send</span>
                  <span className="inline-flex items-center justify-center w-6 h-6 bg-teal-500 rounded-full"><FaArrowRight size={12} /></span>
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}