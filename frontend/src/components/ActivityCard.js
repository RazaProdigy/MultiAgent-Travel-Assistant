import React from "react";
import { MapPin, Clock, Users, Tag } from "lucide-react";

export default function ActivityCard({ activity, onBook, onViewDetails }) {
  if (!activity) return null;

  const priceFrom = activity.price_from || (activity.variations && activity.variations.length > 0
    ? Math.min(...activity.variations.map(v => v.price))
    : null);

  return (
    <div
      className="bg-white rounded-xl overflow-hidden shadow-md w-full mt-2 border border-gray-100 activity-image-hover"
      data-testid={`activity-card-${activity.id}`}
    >
      {activity.image && (
        <div className="overflow-hidden h-40">
          <img
            src={activity.image}
            alt={activity.name}
            className="w-full h-full object-cover transition-transform duration-500"
            loading="lazy"
          />
        </div>
      )}
      <div className="p-4 flex flex-col gap-2">
        <div className="flex items-start justify-between gap-2">
          <h3 className="font-heading text-lg font-bold text-gray-900 leading-tight">
            {activity.name}
          </h3>
          {priceFrom && (
            <span className="bg-emerald-50 text-[#075E54] font-bold px-2 py-1 rounded text-xs whitespace-nowrap flex-shrink-0">
              From {priceFrom} {activity.currency || "AED"}
            </span>
          )}
        </div>

        <p className="text-sm text-gray-600 leading-relaxed line-clamp-2">
          {activity.description}
        </p>

        {activity.category && (
          <div className="flex items-center gap-1 text-xs text-gray-500">
            <Tag size={12} />
            <span>{activity.category}</span>
          </div>
        )}

        {activity.variations && activity.variations.length > 0 && (
          <div className="flex flex-col gap-1.5 mt-1">
            {activity.variations.map((v) => (
              <div
                key={v.id}
                className="flex items-center justify-between text-xs bg-gray-50 rounded-md px-2.5 py-1.5"
              >
                <span className="text-gray-700 font-medium">{v.name}</span>
                <span className="text-[#075E54] font-bold">{v.price} AED</span>
              </div>
            ))}
          </div>
        )}

        {activity.cancellation_policy && (
          <p className="text-xs text-gray-400 mt-1 leading-relaxed">
            {activity.cancellation_policy}
          </p>
        )}

        <div className="flex gap-2 mt-2">
          {onViewDetails && (
            <button
              onClick={() => onViewDetails(activity)}
              className="flex-1 bg-gray-100 text-gray-700 py-2 rounded-md font-medium text-sm hover:bg-gray-200 transition-colors"
              data-testid={`view-details-${activity.id}`}
            >
              Details
            </button>
          )}
          {onBook && activity.available !== false && (
            <button
              onClick={() => onBook(activity)}
              className="flex-1 bg-[#075E54] text-white py-2 rounded-md font-medium text-sm hover:bg-[#054c44] transition-colors"
              data-testid={`book-activity-${activity.id}`}
            >
              Book Now
            </button>
          )}
          {activity.available === false && (
            <span className="flex-1 text-center bg-amber-50 text-amber-700 py-2 rounded-md font-medium text-xs border border-amber-200">
              Currently Unavailable
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
