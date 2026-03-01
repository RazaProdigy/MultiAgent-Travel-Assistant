import React from "react";
import { CheckCircle, Calendar, Users, Clock, DollarSign } from "lucide-react";

export default function BookingConfirmation({ booking }) {
  if (!booking) return null;

  return (
    <div
      className="bg-white rounded-lg p-5 border-t-4 border-[#25D366] shadow-lg"
      data-testid="booking-confirmation"
    >
      <div className="flex flex-col items-center text-center mb-4">
        <CheckCircle className="text-[#25D366] mb-2" size={48} strokeWidth={1.5} />
        <h3 className="font-heading text-xl font-bold text-gray-900">Booking Confirmed!</h3>
        {booking.booking_id && (
          <p className="text-xs text-gray-400 mt-1">ID: {booking.booking_id.slice(0, 8)}</p>
        )}
      </div>

      <div className="space-y-2.5 text-sm">
        <div className="flex items-center gap-2 text-gray-700">
          <Calendar size={16} className="text-[#075E54] flex-shrink-0" />
          <span className="font-medium">{booking.activity_name}</span>
        </div>
        <div className="flex items-center gap-2 text-gray-600">
          <Clock size={16} className="text-[#075E54] flex-shrink-0" />
          <span>{booking.variation_name} — {booking.time_slot}</span>
        </div>
        <div className="flex items-center gap-2 text-gray-600">
          <Users size={16} className="text-[#075E54] flex-shrink-0" />
          <span>{booking.group_size} {booking.group_size === 1 ? "person" : "people"}</span>
        </div>
        <div className="flex items-center gap-2 text-gray-600">
          <DollarSign size={16} className="text-[#075E54] flex-shrink-0" />
          <span className="font-bold text-[#075E54]">{booking.total_price} {booking.currency || "AED"}</span>
        </div>
        {booking.customer_name && (
          <div className="text-gray-500 text-xs mt-2">
            Booked for: <span className="font-medium text-gray-700">{booking.customer_name}</span>
          </div>
        )}
      </div>
    </div>
  );
}
