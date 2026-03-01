"""
Mock database of 10+ Dubai activities with variations, pricing, images, policies.
"""

DUBAI_ACTIVITIES = [
    {
        "id": "burj-khalifa",
        "name": "Burj Khalifa At The Top",
        "description": "Visit the world's tallest building and enjoy breathtaking views from the 124th and 148th floors. Experience the stunning Dubai skyline like never before.",
        "image": "https://images.pexels.com/photos/13205608/pexels-photo-13205608.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=650&w=940",
        "category": "Sightseeing",
        "variations": [
            {"id": "bk-standard", "name": "Standard (124th Floor)", "time_slots": ["09:00", "12:00", "15:00", "18:00"], "group_sizes": [1, 2, 4, 6], "price": 149, "currency": "AED"},
            {"id": "bk-prime", "name": "Prime Hours (124th Floor)", "time_slots": ["17:00", "18:00", "19:00"], "group_sizes": [1, 2, 4], "price": 224, "currency": "AED"},
            {"id": "bk-sky", "name": "SKY (148th Floor)", "time_slots": ["10:00", "14:00", "17:00"], "group_sizes": [1, 2], "price": 553, "currency": "AED"}
        ],
        "cancellation_policy": "Free cancellation up to 24 hours before the experience. No refund for cancellations within 24 hours.",
        "reschedule_policy": "Rescheduling is allowed up to 12 hours before the booked time slot, subject to availability.",
        "available": True
    },
    {
        "id": "desert-safari",
        "name": "Desert Safari Adventure",
        "description": "Experience the thrill of dune bashing, camel riding, sandboarding, and a magical BBQ dinner under the stars in the Arabian Desert.",
        "image": "https://images.pexels.com/photos/18979287/pexels-photo-18979287.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=650&w=940",
        "category": "Adventure",
        "variations": [
            {"id": "ds-morning", "name": "Morning Safari", "time_slots": ["06:00", "07:00"], "group_sizes": [2, 4, 6, 8], "price": 180, "currency": "AED"},
            {"id": "ds-evening", "name": "Evening Safari with BBQ Dinner", "time_slots": ["15:00", "16:00"], "group_sizes": [2, 4, 6, 8, 10], "price": 280, "currency": "AED"},
            {"id": "ds-overnight", "name": "Overnight Camping Safari", "time_slots": ["15:00"], "group_sizes": [2, 4, 6], "price": 450, "currency": "AED"}
        ],
        "cancellation_policy": "Free cancellation up to 48 hours before. 50% refund for cancellations between 24-48 hours. No refund within 24 hours.",
        "reschedule_policy": "Rescheduling available up to 24 hours before the booking, subject to availability.",
        "available": True
    },
    {
        "id": "dubai-marina-cruise",
        "name": "Dubai Marina Luxury Cruise",
        "description": "Sail through the stunning Dubai Marina on a luxury yacht. Enjoy gourmet dining, live entertainment, and panoramic views of the glittering skyline.",
        "image": "https://images.pexels.com/photos/3601425/pexels-photo-3601425.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=650&w=940",
        "category": "Cruise",
        "variations": [
            {"id": "mc-lunch", "name": "Lunch Cruise (2 hours)", "time_slots": ["12:00", "13:00"], "group_sizes": [2, 4, 6, 8], "price": 320, "currency": "AED"},
            {"id": "mc-sunset", "name": "Sunset Cruise (2 hours)", "time_slots": ["17:00", "18:00"], "group_sizes": [2, 4, 6], "price": 420, "currency": "AED"},
            {"id": "mc-dinner", "name": "Dinner Cruise (3 hours)", "time_slots": ["20:00"], "group_sizes": [2, 4, 6, 8, 10], "price": 550, "currency": "AED"}
        ],
        "cancellation_policy": "Full refund if cancelled 72 hours before. 50% refund for 24-72 hour cancellations. No refund within 24 hours.",
        "reschedule_policy": "Rescheduling permitted up to 48 hours before the cruise, subject to availability.",
        "available": True
    },
    {
        "id": "skydiving-palm",
        "name": "Skydiving over Palm Jumeirah",
        "description": "Take the ultimate leap of faith with a tandem skydive over the iconic Palm Jumeirah. Free-fall from 13,000 feet with unbelievable views.",
        "image": "https://images.pexels.com/photos/5035655/pexels-photo-5035655.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=650&w=940",
        "category": "Adventure",
        "variations": [
            {"id": "sd-tandem", "name": "Tandem Skydive", "time_slots": ["08:00", "10:00", "12:00", "14:00"], "group_sizes": [1, 2], "price": 1899, "currency": "AED"},
            {"id": "sd-video", "name": "Tandem + Video Package", "time_slots": ["08:00", "10:00", "12:00", "14:00"], "group_sizes": [1, 2], "price": 2499, "currency": "AED"}
        ],
        "cancellation_policy": "Free cancellation up to 48 hours before. No refund within 48 hours due to weather-dependent scheduling.",
        "reschedule_policy": "Free rescheduling allowed. Weather-related cancellations are automatically rescheduled.",
        "available": True
    },
    {
        "id": "jet-ski",
        "name": "Jet Ski Experience",
        "description": "Race across the turquoise waters of the Arabian Gulf on a high-powered jet ski with stunning views of the Burj Al Arab and Dubai skyline.",
        "image": "https://images.pexels.com/photos/4491948/pexels-photo-4491948.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=650&w=940",
        "category": "Water Sports",
        "variations": [
            {"id": "js-30min", "name": "30-Minute Ride", "time_slots": ["09:00", "11:00", "14:00", "16:00"], "group_sizes": [1, 2], "price": 350, "currency": "AED"},
            {"id": "js-60min", "name": "60-Minute Ride", "time_slots": ["09:00", "11:00", "14:00", "16:00"], "group_sizes": [1, 2], "price": 600, "currency": "AED"},
            {"id": "js-tour", "name": "Guided Tour (90 min)", "time_slots": ["10:00", "15:00"], "group_sizes": [2, 4], "price": 850, "currency": "AED"}
        ],
        "cancellation_policy": "Full refund if cancelled 24 hours before. No refund within 24 hours.",
        "reschedule_policy": "Rescheduling available up to 12 hours before the slot.",
        "available": True
    },
    {
        "id": "dubai-frame",
        "name": "Dubai Frame",
        "description": "Step inside the world's largest picture frame standing 150 meters tall. Enjoy panoramic views of old and new Dubai from the Sky Deck.",
        "image": "https://images.pexels.com/photos/15832006/pexels-photo-15832006.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=650&w=940",
        "category": "Sightseeing",
        "variations": [
            {"id": "df-general", "name": "General Admission", "time_slots": ["09:00", "11:00", "13:00", "15:00", "17:00"], "group_sizes": [1, 2, 4, 6], "price": 50, "currency": "AED"},
            {"id": "df-sunset", "name": "Sunset Experience", "time_slots": ["17:30", "18:00"], "group_sizes": [1, 2, 4], "price": 75, "currency": "AED"}
        ],
        "cancellation_policy": "Free cancellation up to 24 hours before. No refund within 24 hours.",
        "reschedule_policy": "Rescheduling allowed up to 6 hours before the visit.",
        "available": True
    },
    {
        "id": "aquaventure",
        "name": "Aquaventure Waterpark",
        "description": "The Middle East's largest waterpark at Atlantis The Palm. Over 30 slides, a 2.3km river ride, and a private beach experience.",
        "image": "https://images.pexels.com/photos/1319829/pexels-photo-1319829.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=650&w=940",
        "category": "Theme Park",
        "variations": [
            {"id": "aq-day", "name": "Full Day Pass", "time_slots": ["10:00"], "group_sizes": [1, 2, 4, 6], "price": 340, "currency": "AED"},
            {"id": "aq-vip", "name": "VIP Experience (Cabana + Fast Track)", "time_slots": ["10:00"], "group_sizes": [2, 4], "price": 890, "currency": "AED"}
        ],
        "cancellation_policy": "Free cancellation up to 48 hours before visit. 50% refund between 24-48 hours.",
        "reschedule_policy": "Rescheduling permitted up to 24 hours before, subject to date availability.",
        "available": True
    },
    {
        "id": "hot-air-balloon",
        "name": "Hot Air Balloon Ride",
        "description": "Float above the Dubai desert at sunrise in a majestic hot air balloon. Witness the golden dunes, wildlife, and spectacular sunrise views.",
        "image": "https://images.pexels.com/photos/210012/pexels-photo-210012.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=650&w=940",
        "category": "Adventure",
        "variations": [
            {"id": "hab-standard", "name": "Standard Basket", "time_slots": ["05:30"], "group_sizes": [1, 2, 4], "price": 1100, "currency": "AED"},
            {"id": "hab-exclusive", "name": "Exclusive (Falcon Show + Breakfast)", "time_slots": ["05:30"], "group_sizes": [2, 4], "price": 1600, "currency": "AED"}
        ],
        "cancellation_policy": "Free cancellation up to 72 hours before. 50% refund between 48-72 hours. No refund within 48 hours.",
        "reschedule_policy": "Free rescheduling for weather-related cancellations. Otherwise, 48 hours advance notice required.",
        "available": True
    },
    {
        "id": "old-dubai-tour",
        "name": "Old Dubai Heritage Walking Tour",
        "description": "Explore the historic heart of Dubai — Al Fahidi, Gold Souk, Spice Souk, and an Abra ride across Dubai Creek with a local guide.",
        "image": "https://images.pexels.com/photos/3581364/pexels-photo-3581364.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=650&w=940",
        "category": "Cultural",
        "variations": [
            {"id": "od-morning", "name": "Morning Tour (3 hours)", "time_slots": ["08:00", "09:00"], "group_sizes": [1, 2, 4, 6, 8], "price": 120, "currency": "AED"},
            {"id": "od-evening", "name": "Evening Tour with Street Food", "time_slots": ["17:00", "18:00"], "group_sizes": [2, 4, 6], "price": 200, "currency": "AED"}
        ],
        "cancellation_policy": "Free cancellation anytime up to 12 hours before the tour. No refund after that.",
        "reschedule_policy": "Rescheduling allowed up to 12 hours before with no extra charges.",
        "available": True
    },
    {
        "id": "dubai-miracle-garden",
        "name": "Dubai Miracle Garden",
        "description": "The world's largest natural flower garden featuring 150 million flowers in stunning structures including a life-size Emirates A380.",
        "image": "https://images.pexels.com/photos/2539076/pexels-photo-2539076.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=650&w=940",
        "category": "Sightseeing",
        "variations": [
            {"id": "mg-general", "name": "General Entry", "time_slots": ["09:00", "12:00", "15:00"], "group_sizes": [1, 2, 4, 6], "price": 55, "currency": "AED"},
            {"id": "mg-combo", "name": "Combo (Garden + Butterfly Garden)", "time_slots": ["09:00", "12:00"], "group_sizes": [1, 2, 4], "price": 90, "currency": "AED"}
        ],
        "cancellation_policy": "Free cancellation up to 24 hours before. No refund within 24 hours.",
        "reschedule_policy": "Rescheduling allowed up to 12 hours before. Season-end closures are non-refundable.",
        "available": True
    },
    {
        "id": "deep-dive-dubai",
        "name": "Deep Dive Dubai",
        "description": "Dive into the world's deepest pool at 60 meters. Perfect for certified divers and beginners with a discover scuba experience.",
        "image": "https://images.pexels.com/photos/37542/divers-underwater-ocean-swim.jpg?auto=compress&cs=tinysrgb&dpr=2&h=650&w=940",
        "category": "Adventure",
        "variations": [
            {"id": "dd-discover", "name": "Discover Scuba (Beginner)", "time_slots": ["10:00", "14:00"], "group_sizes": [1, 2], "price": 800, "currency": "AED"},
            {"id": "dd-certified", "name": "Certified Diver Experience", "time_slots": ["09:00", "11:00", "13:00", "15:00"], "group_sizes": [1, 2, 4], "price": 600, "currency": "AED"}
        ],
        "cancellation_policy": "Free cancellation up to 48 hours before. Medical certificate required. No refund within 48 hours.",
        "reschedule_policy": "Rescheduling allowed up to 24 hours before. Medical cancellations processed with doctor's note.",
        "available": True
    },
    {
        "id": "helicopter-tour",
        "name": "Helicopter Tour of Dubai",
        "description": "See Dubai from above on a thrilling helicopter ride over the Palm Jumeirah, Burj Al Arab, World Islands, and Burj Khalifa.",
        "image": "https://images.pexels.com/photos/2868257/pexels-photo-2868257.jpeg?auto=compress&cs=tinysrgb&dpr=2&h=650&w=940",
        "category": "Sightseeing",
        "variations": [
            {"id": "ht-12min", "name": "12-Minute Iconic Tour", "time_slots": ["09:00", "11:00", "14:00", "16:00"], "group_sizes": [1, 2, 3], "price": 750, "currency": "AED"},
            {"id": "ht-25min", "name": "25-Minute Grand Tour", "time_slots": ["10:00", "13:00", "15:00"], "group_sizes": [1, 2, 3], "price": 1350, "currency": "AED"}
        ],
        "cancellation_policy": "Full refund for cancellations 72 hours before. 50% refund between 24-72 hours. No refund within 24 hours.",
        "reschedule_policy": "Rescheduling available 48 hours before. Weather-related rescheduling is free.",
        "available": False
    }
]
