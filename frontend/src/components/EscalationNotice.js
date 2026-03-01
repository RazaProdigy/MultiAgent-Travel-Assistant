import React from "react";
import { AlertTriangle, Mail, ExternalLink, MailX } from "lucide-react";

export default function EscalationNotice({ data }) {
  const emailSent = data?.email_sent === true;

  return (
    <div
      className="bg-amber-50 border border-amber-200 rounded-lg p-4 shadow-sm"
      data-testid="escalation-notice"
    >
      <div className="flex items-center gap-2 mb-2">
        <AlertTriangle className="text-amber-500" size={20} />
        <span className="text-sm font-semibold text-amber-800">Escalated to Supervisor</span>
      </div>
      <p className="text-sm text-amber-700 leading-relaxed">
        {data?.message || "Your request has been escalated to a human supervisor. You'll receive a response shortly."}
      </p>
      <div className="mt-2 space-y-1.5">
        {emailSent ? (
          <div className="flex items-center gap-1.5 text-xs text-amber-600">
            <Mail size={12} />
            <span>Email notification sent to the support team</span>
          </div>
        ) : (
          <div className="flex items-center gap-1.5 text-xs text-amber-500">
            <MailX size={12} />
            <span>Email notification pending — supervisor will be notified via the panel</span>
          </div>
        )}
      </div>
    </div>
  );
}
