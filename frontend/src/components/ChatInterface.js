import React, { useState, useRef, useEffect, useCallback } from "react";
import axios from "axios";
import { Send, Phone, Video, MoreVertical, Smile } from "lucide-react";
import MessageBubble from "./MessageBubble";
import TypingIndicator from "./TypingIndicator";

const BACKEND_URL =
  process.env.REACT_APP_BACKEND_URL ||
  (typeof window !== "undefined" && `${window.location.protocol}//${window.location.hostname}:8001`);
const API = BACKEND_URL ? `${BACKEND_URL}/api` : "/api";

const AGGREGATION_DELAY = 2500; // ms to wait before sending aggregated messages

function generateSessionId() {
  return "sess-" + crypto.randomUUID();
}

export default function ChatInterface() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [pendingMessages, setPendingMessages] = useState([]);
  const [sessionId] = useState(() => {
    const stored = sessionStorage.getItem("chat_session_id");
    if (stored) return stored;
    const id = generateSessionId();
    sessionStorage.setItem("chat_session_id", id);
    return id;
  });

  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);
  const pollingRef = useRef(null);
  const aggregationTimerRef = useRef(null);
  const pendingRef = useRef([]);

  // Scroll to bottom
  const scrollToBottom = useCallback(() => {
    setTimeout(() => {
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, 100);
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading, scrollToBottom]);

  // Load conversation history on mount
  useEffect(() => {
    async function loadHistory() {
      try {
        const res = await axios.get(`${API}/conversations/${sessionId}`);
        if (res.data.messages && res.data.messages.length > 0) {
          setMessages(res.data.messages);
        } else {
          setMessages([
            {
              id: "welcome",
              role: "assistant",
              content: "",
              timestamp: new Date().toISOString(),
              type: "text",
              data: {
                type: "text",
                message:
                  "Ahlan! Welcome to the Dubai Travel Assistant. I can help you discover and book amazing activities in Dubai — from the Burj Khalifa to Desert Safaris and more. What are you looking for today?",
              },
            },
          ]);
        }
      } catch {
        setMessages([
          {
            id: "welcome",
            role: "assistant",
            content: "",
            timestamp: new Date().toISOString(),
            type: "text",
            data: {
              type: "text",
              message:
                "Ahlan! Welcome to the Dubai Travel Assistant. I can help you discover and book amazing activities in Dubai. What would you like to explore?",
            },
          },
        ]);
      }
    }
    loadHistory();
  }, [sessionId]);

  // Poll for new messages (supervisor replies); poll more often when escalation is present
  const hasEscalation = messages.some(
    (m) => m.type === "escalation" || (m.data && m.data.type === "escalation")
  );
  const pollInterval = hasEscalation ? 2000 : 5000;

  useEffect(() => {
    pollingRef.current = setInterval(async () => {
      try {
        const res = await axios.get(`${API}/conversations/${sessionId}`);
        const serverMsgs = res.data.messages || [];
        setMessages((prev) => {
          const prevIds = new Set(prev.map((m) => m.id));
          const hasNew = serverMsgs.some(
            (m) => !prevIds.has(m.id) && (m.role === "supervisor" || m.role === "assistant")
          );
          return hasNew ? serverMsgs : prev;
        });
      } catch {
        // silent
      }
    }, pollInterval);
    return () => clearInterval(pollingRef.current);
  }, [sessionId, pollInterval]);

  // Send aggregated messages to backend
  const flushPendingMessages = useCallback(async () => {
    const pending = pendingRef.current;
    if (pending.length === 0) return;

    pendingRef.current = [];
    setPendingMessages([]);

    // Combine all pending messages into one
    const combinedText = pending.map((m) => m.text).join("\n");
    setLoading(true);

    try {
      const res = await axios.post(`${API}/chat`, {
        session_id: sessionId,
        message: combinedText,
      });

      const response = res.data.response;
      const botMsg = {
        id: "b-" + Date.now(),
        role: "assistant",
        content: response.message || "",
        timestamp: new Date().toISOString(),
        type: response.type || "text",
        data: response,
      };

      setMessages((prev) => [...prev, botMsg]);
    } catch {
      const errorMsg = {
        id: "e-" + Date.now(),
        role: "assistant",
        content: "",
        timestamp: new Date().toISOString(),
        type: "text",
        data: {
          type: "text",
          message: "Sorry, I'm having trouble connecting. Please try again in a moment.",
        },
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  }, [sessionId]);

  // Send message with aggregation support
  const sendMessage = useCallback(() => {
    const text = input.trim();
    if (!text) return;

    // Add user message to UI immediately
    const userMsg = {
      id: "u-" + Date.now() + "-" + Math.random(),
      role: "user",
      content: text,
      timestamp: new Date().toISOString(),
      type: "text",
    };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");

    // If currently loading (bot is processing), add to pending queue
    // This handles "interruption" — user sends more messages while bot is thinking
    if (loading) {
      pendingRef.current.push({ text, timestamp: Date.now() });
      setPendingMessages([...pendingRef.current]);
      return;
    }

    // Add to pending queue and set/reset aggregation timer
    pendingRef.current.push({ text, timestamp: Date.now() });
    setPendingMessages([...pendingRef.current]);

    // Clear existing timer and set a new one
    if (aggregationTimerRef.current) {
      clearTimeout(aggregationTimerRef.current);
    }

    aggregationTimerRef.current = setTimeout(() => {
      flushPendingMessages();
    }, AGGREGATION_DELAY);
  }, [input, loading, flushPendingMessages]);

  // After loading finishes, check if there are queued messages
  useEffect(() => {
    if (!loading && pendingRef.current.length > 0) {
      // Small delay to let the user see the response, then process queued messages
      const timer = setTimeout(() => {
        flushPendingMessages();
      }, 500);
      return () => clearTimeout(timer);
    }
  }, [loading, flushPendingMessages]);

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const handleBookActivity = (activity) => {
    setInput(`I'd like to book ${activity.name}`);
    inputRef.current?.focus();
  };

  const hasPending = pendingMessages.length > 0 && !loading;

  return (
    <div
      className="flex flex-col h-screen max-w-md mx-auto bg-white shadow-2xl overflow-hidden relative border-x border-gray-200"
      data-testid="chat-interface"
    >
      {/* Header */}
      <div className="bg-[#075E54] text-white px-4 py-3 flex items-center gap-3 z-10 shadow-md" data-testid="chat-header">
        <div className="w-10 h-10 rounded-full overflow-hidden border-2 border-white/30 flex-shrink-0">
          <img
            src="https://images.pexels.com/photos/3410596/pexels-photo-3410596.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=100&w=100"
            alt="Dubai Travel Assistant"
            className="w-full h-full object-cover"
          />
        </div>
        <div className="flex-1 min-w-0">
          <h1 className="text-base font-semibold truncate">Dubai Travel Assistant</h1>
          <p className="text-xs text-white/70" data-testid="status-text">
            {loading ? "typing..." : hasPending ? "listening..." : "online"}
          </p>
        </div>
        <div className="flex items-center gap-4">
          <Video size={20} className="opacity-70 cursor-pointer hover:opacity-100 transition-opacity" />
          <Phone size={20} className="opacity-70 cursor-pointer hover:opacity-100 transition-opacity" />
          <MoreVertical size={20} className="opacity-70 cursor-pointer hover:opacity-100 transition-opacity" />
        </div>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto relative wa-chat-bg chat-scrollbar" data-testid="messages-area">
        <div className="relative z-10 p-4 flex flex-col gap-3">
          {/* Date chip */}
          <div className="flex justify-center mb-2">
            <span className="bg-white/80 text-[#8696a0] text-xs px-3 py-1 rounded-lg shadow-sm">
              Today
            </span>
          </div>

          {/* AI notice */}
          <div className="flex justify-center mb-2">
            <div className="bg-[#fdf8c8] text-[#54656f] text-[11px] px-3 py-1.5 rounded-md text-center max-w-[85%] leading-relaxed shadow-sm">
              Messages are powered by AI. Your bookings are confirmed instantly.
            </div>
          </div>

          {messages.map((msg) => (
            <MessageBubble key={msg.id} msg={msg} onBookActivity={handleBookActivity} />
          ))}

          {/* Aggregation indicator */}
          {hasPending && (
            <div className="flex justify-center message-enter" data-testid="aggregation-indicator">
              <span className="bg-white/80 text-[#8696a0] text-[11px] px-3 py-1 rounded-lg shadow-sm">
                Collecting your messages...
              </span>
            </div>
          )}

          {loading && <TypingIndicator />}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input Area */}
      <div className="bg-[#f0f2f5] px-3 py-2.5 flex items-end gap-2 z-10" data-testid="chat-input-area">
        <button
          className="text-[#54656f] hover:text-[#075E54] transition-colors p-1.5 flex-shrink-0"
          data-testid="emoji-button"
        >
          <Smile size={24} />
        </button>
        <div className="flex-1 bg-white rounded-3xl px-4 py-2.5 flex items-end shadow-sm">
          <textarea
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type a message"
            rows={1}
            className="flex-1 text-sm text-gray-900 placeholder-gray-400 resize-none bg-transparent outline-none max-h-32 leading-snug"
            style={{ minHeight: "20px" }}
            data-testid="chat-input"
          />
        </div>
        <button
          onClick={sendMessage}
          disabled={!input.trim()}
          className="w-10 h-10 rounded-full bg-[#075E54] text-white flex items-center justify-center flex-shrink-0 disabled:opacity-40 hover:bg-[#054c44] transition-colors"
          data-testid="send-button"
        >
          <Send size={18} />
        </button>
      </div>
    </div>
  );
}
