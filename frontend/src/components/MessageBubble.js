import React from "react";
import ActivityCard from "./ActivityCard";
import BookingConfirmation from "./BookingConfirmation";
import EscalationNotice from "./EscalationNotice";
import { Check, CheckCheck } from "lucide-react";

function formatTime(timestamp) {
  if (!timestamp) return "";
  const d = new Date(timestamp);
  return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

export default function MessageBubble({ msg, onBookActivity }) {
  const isUser = msg.role === "user";
  const isSupervisor = msg.role === "supervisor";
  const isBot = msg.role === "assistant";
  const data = msg.data || {};
  const msgType = data.type || msg.type || "text";

  // Supervisor messages
  if (isSupervisor) {
    return (
      <div className="flex justify-center message-enter" data-testid="supervisor-message">
        <div className="bg-blue-50 border border-blue-200 rounded-lg px-4 py-3 max-w-[90%] shadow-sm">
          <div className="flex items-center gap-2 mb-1">
            <span className="w-2 h-2 rounded-full bg-blue-500 inline-block" />
            <span className="text-xs font-semibold text-blue-700">Supervisor Response</span>
          </div>
          <p className="text-sm text-blue-900">{msg.content}</p>
          <span className="text-[10px] text-blue-400 mt-1 block text-right">
            {formatTime(msg.timestamp)}
          </span>
        </div>
      </div>
    );
  }

  // User messages
  if (isUser) {
    return (
      <div className="flex justify-end message-enter" data-testid="user-message">
        <div className="bg-[#d9fdd3] text-gray-900 rounded-lg rounded-tr-none shadow-sm px-3 py-2 max-w-[85%] relative">
          <p className="text-sm leading-relaxed whitespace-pre-wrap">{msg.content}</p>
          <div className="flex items-center justify-end gap-1 mt-1">
            <span className="text-[10px] text-[#8696a0]">{formatTime(msg.timestamp)}</span>
            <CheckCheck size={14} className="text-blue-500" />
          </div>
        </div>
      </div>
    );
  }

  // Bot messages
  return (
    <div className="flex items-start gap-2 self-start message-enter" data-testid="bot-message">
      <div className="w-8 h-8 rounded-full overflow-hidden flex-shrink-0 mt-1">
        <img
          src="https://images.pexels.com/photos/3410596/pexels-photo-3410596.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=100&w=100"
          alt="Bot"
          className="w-full h-full object-cover"
        />
      </div>
      <div className="max-w-[85%] flex flex-col gap-2">
        {/* Text message */}
        {data.message && (
          <div className="bg-white text-gray-900 rounded-lg rounded-tl-none shadow-sm px-3 py-2">
            <p className="text-sm leading-relaxed whitespace-pre-wrap">{data.message}</p>
            <span className="text-[10px] text-[#8696a0] block text-right mt-1">
              {formatTime(msg.timestamp)}
            </span>
          </div>
        )}

        {/* Activity info card */}
        {msgType === "activity_info" && data.activity && (
          <ActivityCard
            activity={data.activity}
            onBook={onBookActivity}
          />
        )}

        {/* Activity list */}
        {msgType === "activity_list" && data.activities && (
          <div className="flex flex-col gap-2">
            {data.activities.map((act) => (
              <ActivityCard
                key={act.id}
                activity={act}
                onBook={onBookActivity}
              />
            ))}
          </div>
        )}

        {/* Booking confirmation */}
        {msgType === "booking" && data.booking && (
          <BookingConfirmation booking={data.booking} />
        )}

        {/* Escalation notice */}
        {msgType === "escalation" && (
          <EscalationNotice data={data} />
        )}
      </div>
    </div>
  );
}
