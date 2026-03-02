import React, { useState, useEffect } from "react";
import { useParams, useSearchParams } from "react-router-dom";
import axios from "axios";
import { Send, CheckCircle, AlertTriangle, MessageSquare, ArrowLeft } from "lucide-react";

// Use explicit backend URL; fallback so "Reply to Customer" link from email works when env is missing (e.g. dev)
const BACKEND_URL =
  process.env.REACT_APP_BACKEND_URL ||
  (typeof window !== "undefined" && `${window.location.protocol}//${window.location.hostname}:8001`);
const API = BACKEND_URL ? `${BACKEND_URL}/api` : "/api";

export default function SupervisorPanel() {
  const { sessionId } = useParams();
  const [searchParams] = useSearchParams();
  const queryFromEmail = searchParams.get("query") || "";

  const [reply, setReply] = useState("");
  const [sending, setSending] = useState(false);
  const [sent, setSent] = useState(false);
  const [error, setError] = useState("");
  const [conversation, setConversation] = useState([]);
  const [loadingConvo, setLoadingConvo] = useState(true);

  // Load conversation context
  useEffect(() => {
    async function loadConversation() {
      if (!sessionId) {
        setLoadingConvo(false);
        return;
      }
      try {
        const res = await axios.get(`${API}/conversations/${sessionId}`);
        setConversation(res.data.messages || []);
      } catch {
        setConversation([]);
      } finally {
        setLoadingConvo(false);
      }
    }
    loadConversation();
  }, [sessionId]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    const text = reply.trim();
    if (!text || !sessionId) return;

    setSending(true);
    setError("");

    try {
      await axios.post(`${API}/supervisor/reply`, {
        session_id: sessionId,
        message: text,
      });
      setSent(true);
      setReply("");
    } catch (err) {
      setError("Failed to send reply. Please try again.");
    } finally {
      setSending(false);
    }
  };

  // Get escalation messages for context
  const escalationMsgs = conversation.filter(
    (m) => m.type === "escalation" || (m.data && m.data.type === "escalation")
  );
  const recentUserMsgs = conversation
    .filter((m) => m.role === "user")
    .slice(-5);

  if (!sessionId) {
    return (
      <div className="min-h-screen bg-[#f0f2f5] flex items-center justify-center p-6" data-testid="supervisor-panel">
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8 max-w-md text-center">
          <AlertTriangle className="mx-auto text-amber-500 mb-4" size={48} />
          <h2 className="text-lg font-semibold text-gray-900 mb-2">Invalid or missing session</h2>
          <p className="text-sm text-gray-600 mb-4">
            Use the "Reply to Customer" link from the escalation email to open this panel with the correct session.
          </p>
          <a
            href="/"
            className="inline-flex items-center gap-2 bg-[#075E54] text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-[#054c44]"
            data-testid="back-to-chat"
          >
            <ArrowLeft size={18} />
            Back to chat
          </a>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#f0f2f5]" data-testid="supervisor-panel">
      {/* Header */}
      <div className="bg-[#075E54] text-white px-6 py-4 shadow-md">
        <div className="max-w-2xl mx-auto flex items-center gap-3">
          <a href="/" className="hover:opacity-80 transition-opacity" data-testid="back-to-chat">
            <ArrowLeft size={24} />
          </a>
          <div>
            <h1 className="text-xl font-semibold">Supervisor Panel</h1>
            <p className="text-sm text-white/70">
              Session: {sessionId.slice(0, 12)}...
            </p>
          </div>
        </div>
      </div>

      <div className="max-w-2xl mx-auto p-6 space-y-6">
        {/* Escalation Context */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden" data-testid="escalation-context">
          <div className="bg-amber-50 border-b border-amber-200 px-5 py-3 flex items-center gap-2">
            <AlertTriangle size={18} className="text-amber-600" />
            <h2 className="text-sm font-semibold text-amber-800">Escalation Details</h2>
          </div>
          <div className="p-5 space-y-4">
            {queryFromEmail && (
              <div>
                <p className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-1">Customer Request</p>
                <p className="text-sm text-gray-800 bg-gray-50 rounded-lg p-3">{queryFromEmail}</p>
              </div>
            )}

            {loadingConvo ? (
              <p className="text-sm text-gray-400">Loading conversation context...</p>
            ) : (
              <>
                {recentUserMsgs.length > 0 && (
                  <div>
                    <p className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-2">
                      Recent Customer Messages
                    </p>
                    <div className="space-y-2">
                      {recentUserMsgs.map((m) => (
                        <div key={m.id} className="flex items-start gap-2">
                          <MessageSquare size={14} className="text-[#075E54] mt-0.5 flex-shrink-0" />
                          <p className="text-sm text-gray-700">{m.content}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {escalationMsgs.length > 0 && (
                  <div>
                    <p className="text-xs font-medium text-gray-500 uppercase tracking-wider mb-2">
                      Escalation Reason
                    </p>
                    {escalationMsgs.map((m) => (
                      <div key={m.id} className="bg-amber-50 rounded-lg p-3 text-sm text-amber-800">
                        {m.data?.message || m.content || "Activity/variation unavailable"}
                      </div>
                    ))}
                  </div>
                )}
              </>
            )}
          </div>
        </div>

        {/* Reply Form */}
        {sent ? (
          <div
            className="bg-white rounded-xl shadow-sm border border-green-200 p-6 text-center"
            data-testid="reply-success"
          >
            <CheckCircle className="text-[#25D366] mx-auto mb-3" size={48} />
            <h3 className="text-lg font-semibold text-gray-900 mb-1">Reply Sent Successfully</h3>
            <p className="text-sm text-gray-500 mb-4">
              Your response has been relayed to the customer in their chat session.
            </p>
            <button
              onClick={() => setSent(false)}
              className="bg-[#075E54] text-white px-6 py-2 rounded-lg text-sm font-medium hover:bg-[#054c44] transition-colors"
              data-testid="send-another-reply"
            >
              Send Another Reply
            </button>
          </div>
        ) : (
          <form
            onSubmit={handleSubmit}
            className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden"
            data-testid="supervisor-reply-form"
          >
            <div className="px-5 py-3 border-b border-gray-100">
              <h2 className="text-sm font-semibold text-gray-800">Your Reply to Customer</h2>
              <p className="text-xs text-gray-500 mt-0.5">
                This message will appear in the customer's chat session
              </p>
            </div>
            <div className="p-5">
              <textarea
                value={reply}
                onChange={(e) => setReply(e.target.value)}
                placeholder="Type your response to the customer..."
                rows={5}
                className="w-full border border-gray-200 rounded-lg px-4 py-3 text-sm text-gray-900 placeholder-gray-400 resize-none focus:outline-none focus:ring-2 focus:ring-[#075E54]/20 focus:border-[#075E54]"
                data-testid="supervisor-reply-input"
                disabled={sending}
              />
              {error && (
                <p className="text-sm text-red-500 mt-2" data-testid="reply-error">{error}</p>
              )}
              <button
                type="submit"
                disabled={!reply.trim() || sending}
                className="mt-3 w-full bg-[#075E54] text-white py-2.5 rounded-lg font-medium text-sm hover:bg-[#054c44] transition-colors disabled:opacity-40 flex items-center justify-center gap-2"
                data-testid="supervisor-send-button"
              >
                <Send size={16} />
                {sending ? "Sending..." : "Send Reply to Customer"}
              </button>
            </div>
          </form>
        )}

        {/* Conversation History */}
        {conversation.length > 0 && (
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden" data-testid="conversation-history">
            <div className="px-5 py-3 border-b border-gray-100">
              <h2 className="text-sm font-semibold text-gray-800">Full Conversation History</h2>
            </div>
            <div className="p-5 space-y-3 max-h-96 overflow-y-auto">
              {conversation.map((m) => (
                <div
                  key={m.id}
                  className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}
                >
                  <div
                    className={`max-w-[80%] rounded-lg px-3 py-2 text-sm ${
                      m.role === "user"
                        ? "bg-[#d9fdd3] text-gray-900"
                        : m.role === "supervisor"
                        ? "bg-blue-50 text-blue-900 border border-blue-200"
                        : "bg-gray-100 text-gray-800"
                    }`}
                  >
                    <p className="text-[10px] font-semibold text-gray-500 mb-0.5 capitalize">
                      {m.role}
                    </p>
                    <p>{m.content || m.data?.message || "..."}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
