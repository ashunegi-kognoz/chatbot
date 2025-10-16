import { useState, useEffect, useRef } from "react";
import { FaArrowRight, FaArrowUp, FaChevronLeft, FaChevronRight } from "react-icons/fa";
import Markdown from "react-markdown";

const API_BASE = import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000";

  // Suggestion questions that will always be visible
  const suggestionQuestions = [
    "What kind of questions can I ask?",
    "How does the Foundational Learning Program work?",
    "How do I get started with the program?",
  ];

export default function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [uploading, setUploading] = useState(false);
  const [uploadMessage, setUploadMessage] = useState("");
  const [currentConversationId, setCurrentConversationId] = useState(null);
  const [open, setOpen] = useState(true);
  const [canScrollLeft, setCanScrollLeft] = useState(false);
  const [canScrollRight, setCanScrollRight] = useState(false);

  const messagesEndRef = useRef(null);
  const suggestionsScrollRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  // Check scroll position for suggestion buttons
  const checkScrollButtons = () => {
    if (suggestionsScrollRef.current) {
      const { scrollLeft, scrollWidth, clientWidth } = suggestionsScrollRef.current;
      setCanScrollLeft(scrollLeft > 0);
      setCanScrollRight(scrollLeft < scrollWidth - clientWidth - 1);
    }
  };

  // Scroll functions
  const scrollLeft = () => {
    if (suggestionsScrollRef.current) {
      suggestionsScrollRef.current.scrollBy({ left: -200, behavior: 'smooth' });
    }
  };

  const scrollRight = () => {
    if (suggestionsScrollRef.current) {
      suggestionsScrollRef.current.scrollBy({ left: 200, behavior: 'smooth' });
    }
  };

  // Check scroll buttons on component mount and when suggestions change
  useEffect(() => {
    checkScrollButtons();
    const handleResize = () => checkScrollButtons();
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [suggestionQuestions]);

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

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    // Check file type
    const fileExtension = file.name.split('.').pop()?.toLowerCase();
    if (fileExtension !== 'txt') {
      setError("Please upload only .txt files");
      return;
    }

    setUploading(true);
    setError("");
    setUploadMessage("");

    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch(`${API_BASE}/upload`, { method: "POST", body: formData });
      const data = await res.json();
      if (!res.ok) throw new Error(data?.detail || "Upload failed");
      setUploadMessage(`✅ ${data?.message} (${data?.chunks_added} chunks added)`);
      
      // Clear upload message after 5 seconds
      setTimeout(() => setUploadMessage(""), 5000);
    } catch (e) {
      setError(e.message);
    } finally {
      setUploading(false);
    }
  };

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
      const res = await fetch(`${API_BASE}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: userMessage,
          conversation_id: currentConversationId,
          top_k: 12,
        }),
      });
    
      const data = await res.json();
      if (!res.ok) throw new Error(data?.detail || "Request failed");
    
      // Save/refresh conversation id
      setCurrentConversationId(data.conversation_id);
      localStorage.setItem("conversationId", data.conversation_id);
    
      // Replace temp user with a final user bubble (optional), or just leave it
      setMessages(prev => {
        const filtered = prev.filter(msg => msg.id !== tempUserMessage.id);
        return [
          ...filtered,
          { id: `user-${Date.now()}`, role: "user", content: userMessage, created_at: new Date().toISOString() },
          { id: data.message_id, role: "assistant", content: data.answer, created_at: new Date().toISOString() }
        ];
      });
    } catch (e) {
      setError(e.message);
      setMessages(prev => prev.filter(msg => !msg.id.startsWith("temp-")));
    } finally {
      setLoading(false);
    }
  };

  const formatTime = (dateString) => {
    return new Date(dateString).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };



  // Handle suggestion question click
  const handleSuggestionClick = async (question) => {
    if (loading) return;

    setInput("");
    setLoading(true);
    setError("");

    const tempUserMessage = {
      id: `temp-${Date.now()}`,
      role: "user",
      content: question,
      created_at: new Date().toISOString(),
    };
    setMessages(prev => [...prev, tempUserMessage]);

    try {
      const res = await fetch(`${API_BASE}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: question,
          conversation_id: currentConversationId,
          top_k: 12,
        }),
      });
    
      const data = await res.json();
      if (!res.ok) throw new Error(data?.detail || "Request failed");
    
      // Save/refresh conversation id
      setCurrentConversationId(data.conversation_id);
      localStorage.setItem("conversationId", data.conversation_id);
    
      // Replace temp user with a final user bubble
      setMessages(prev => {
        const filtered = prev.filter(msg => msg.id !== tempUserMessage.id);
        return [
          ...filtered,
          { id: `user-${Date.now()}`, role: "user", content: question, created_at: new Date().toISOString() },
          { id: data.message_id, role: "assistant", content: data.answer, created_at: new Date().toISOString() }
        ];
      });
    } catch (e) {
      setError(e.message);
      setMessages(prev => prev.filter(msg => !msg.id.startsWith("temp-")));
    } finally {
      setLoading(false);
    }
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
            <div className="flex items-center space-x-2">
              {/* File Upload Button */}
              {/* <label 
                className={`px-3 py-1 text-xs rounded-full cursor-pointer transition-colors ${
                  uploading 
                    ? 'bg-gray-300 text-gray-500 cursor-not-allowed' 
                    : 'bg-teal-100 text-teal-600 hover:bg-teal-200'
                }`}
              >
                {uploading ? '⏳ Uploading...' : '📄 Upload TXT'}
                <input
                  type="file"
                  accept=".txt"
                  onChange={handleFileUpload}
                  disabled={uploading}
                  className="hidden"
                />
              </label>  */}
              <button
                onClick={() => setOpen(false)}
                className="text-gray-500 hover:text-gray-700"
                aria-label="Close"
              >
                ✕
              </button>
            </div>
          </div>

          {/* Messages Area */}
          <div className="relative flex-1 overflow-y-auto py-2 space-y-2 px-4 bg-white border border-teal-400 rounded-lg">
            {/* Chat Messages */}
            {messages.length === 0 ? (
              <div className="flex flex-col h-full items-center justify-center text-gray-600 mb-6">
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
            
            {/* Loading indicator */}
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
                {/* Suggestion Questions - Inside input box */}
                <div className="w-full mb-3">
                  <p className="text-xs font-medium text-gray-500 mb-2">💡 Suggestions </p>
                  <div className="relative">
                    {/* Left fade overlay */}
                    {canScrollLeft && (
                      <div className="absolute left-0 top-0 bottom-0 w-8 bg-gradient-to-r from-white to-transparent z-10 pointer-events-none" />
                    )}
                    
                    {/* Right fade overlay */}
                    {canScrollRight && (
                      <div className="absolute right-0 top-0 bottom-0 w-8 bg-gradient-to-l from-white to-transparent z-10 pointer-events-none" />
                    )}
                    
                    {/* Left scroll button */}
                    {canScrollLeft && (
                      <button
                        onClick={scrollLeft}
                        className="absolute left-1 top-1/2 transform -translate-y-[70%] z-20 bg-white border border-teal-200 rounded-full p-1.5 shadow-sm hover:bg-teal-50 transition-colors"
                        aria-label="Scroll left"
                      >
                        <FaChevronLeft className="w-3 h-3 text-teal-600" />
                      </button>
                    )}
                    
                    {/* Right scroll button */}
                    {canScrollRight && (
                      <button
                        onClick={scrollRight}
                        className="absolute right-1 top-1/2 transform -translate-y-[70%] z-20 bg-white border border-teal-200 rounded-full p-1.5 shadow-sm hover:bg-teal-50 transition-colors"
                        aria-label="Scroll right"
                      >
                        <FaChevronRight className="w-3 h-3 text-teal-600" />
                      </button>
                    )}
                    
                    <div 
                      ref={suggestionsScrollRef}
                      className="flex gap-2 overflow-x-auto pb-2 scrollbar-hide"
                      onScroll={checkScrollButtons}
                      style={{ 
                        scrollBehavior: 'smooth'
                      }}
                    >
                      {suggestionQuestions.map((question, index) => (
                        <button
                          key={index}
                          onClick={() => handleSuggestionClick(question)}
                          disabled={loading}
                          className="flex-shrink-0 px-3 py-1.5 text-xs bg-teal-50 hover:bg-teal-100 text-teal-700 border border-teal-200 rounded-full transition-colors disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap"
                        >
                          {question}
                        </button>
                      ))}
                    </div>
                  </div>
                </div>

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
                  // className="flex self-end items-center space-x-2 text-white px-4 py-2 rounded-full hover:cursor-pointer border-black border-2 disabled:opacity-50 disabled:cursor-not-allowed"
                  className="flex self-end items-center space-x-2 text-white px-4 py-2 rounded-full hover:cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {/* <span className="text-black">Send</span> */}
                  <span className="inline-flex items-center justify-center w-6 h-6 bg-teal-500 rounded-full"><FaArrowUp size={12} /></span>
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}