import React from "react";

export default function TypingIndicator() {
  return (
    <div className="flex items-start gap-2 self-start message-enter" data-testid="typing-indicator">
      <div className="w-8 h-8 rounded-full overflow-hidden flex-shrink-0 mt-1">
        <img
          src="https://images.pexels.com/photos/3410596/pexels-photo-3410596.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=100&w=100"
          alt="Bot"
          className="w-full h-full object-cover"
        />
      </div>
      <div className="bg-white rounded-lg rounded-tl-none shadow-sm px-4 py-3 flex items-center gap-1.5">
        <span className="typing-dot w-2 h-2 bg-gray-400 rounded-full inline-block" />
        <span className="typing-dot w-2 h-2 bg-gray-400 rounded-full inline-block" />
        <span className="typing-dot w-2 h-2 bg-gray-400 rounded-full inline-block" />
      </div>
    </div>
  );
}
