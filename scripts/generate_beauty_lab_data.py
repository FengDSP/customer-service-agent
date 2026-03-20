#!/usr/bin/env python3
"""Generate synthetic test data for Beauty Lab."""

import csv
import random
import os
from datetime import datetime, timedelta

random.seed(42)

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "beauty_lab")

# --- Staff with service expertise ratings (1-5 stars) ---

STAFF = [
    {
        "staff_id": "STF-001", "name": "Lily Chen", "role": "Senior Esthetician",
        "specialties": "Facial,Hair & Scalp", "working_days": "Mon;Tue;Wed;Thu;Fri",
        "working_hours": "10:00-18:00",
        "expertise": {
            "Facial": 5, "Hair & Scalp": 4, "Eyelash": 2, "Manicure": 1,
            "best_services": "RF Anti-aging V-shape & Lifting Treatment;MTS Nano Stem Cell Anti-aging Skincare;Magnetic Glow Skin Treatment",
            "good_at": "Strong hands - excellent at firm/deep massage and pressure-based facials. Great with RF and MTS micro-needling devices. Very thorough extractions. Good at explaining skin conditions to clients. Handles acne-prone and tough skin well. Scalp massage during head treatments is very relaxing.",
            "not_good_at": "Not the best with gentle/delicate touch - some clients with sensitive skin find her pressure too strong. Struggles with the Hydrafacial machine (tends to rush the suction steps). Not great at relaxation-focused treatments where soft touch matters. Can be a bit clinical and less chatty - some clients find her too quiet.",
            "bio": "8 years experience in advanced facial treatments. RF and MTS specialist. Known for thorough deep-cleaning facials and anti-aging treatments. Clients with acne or aging concerns love her."
        }
    },
    {
        "staff_id": "STF-002", "name": "Emma Wang", "role": "Esthetician",
        "specialties": "Facial,Hair & Scalp", "working_days": "Tue;Wed;Thu;Fri;Sat",
        "working_hours": "10:00-18:00",
        "expertise": {
            "Facial": 4, "Hair & Scalp": 5, "Eyelash": 1, "Manicure": 1,
            "best_services": "Hair & Scalp Revitalization with LED Lights;Herbal Hair & Scalp Refreshment;The Head Retreat;Algae Vitalizer Detox",
            "good_at": "Best scalp therapist on the team - clients with hair loss or dandruff specifically request her. Extremely knowledgeable about herbal ingredients and scalp conditions. Gentle and soothing touch perfect for sensitive scalps. Great at LED light therapy sessions. Excellent with algae and detox facials. Very warm personality - clients feel comfortable and relaxed.",
            "not_good_at": "Not confident with high-tech facial machines like RF or MTS devices - prefers manual and herbal treatments. Slower pace - appointments sometimes run 10-15 min over. Not strong enough for clients who want deep-pressure massage. Avoids doing extractions when possible. Gold facial and luxury treatments are not her strength.",
            "bio": "6 years specializing in scalp health and hair restoration. Trichology certified. Go-to person for hair loss, dandruff, and sensitive scalp issues. Clients see visible improvement in hair density after her LED sessions."
        }
    },
    {
        "staff_id": "STF-003", "name": "Mia Zhang", "role": "Lash Technician",
        "specialties": "Eyelash,Manicure", "working_days": "Mon;Wed;Thu;Fri;Sat",
        "working_hours": "10:00-18:00",
        "expertise": {
            "Facial": 1, "Hair & Scalp": 1, "Eyelash": 5, "Manicure": 3,
            "best_services": "Design Lashes;Classic Lashes",
            "good_at": "Best lash artist in the salon - her Design Lashes are stunning and last the longest. Incredibly precise and symmetrical application. Great at custom lash mapping for different eye shapes. Very fast without sacrificing quality - finishes full sets 15 min ahead of schedule. Can do volume, mega-volume, and wispy hybrid styles. Also decent at basic gel manicures.",
            "not_good_at": "Only does lashes and basic nails - cannot do any facial or scalp services. Nail art skills are limited to simple designs (not custom art level). Not very talkative during appointments - some clients find her too focused/quiet. Struggles with clients who have very sparse natural lashes. Not great at lash removal - sometimes pulls too hard.",
            "bio": "5 years as a lash artist. Specializes in volume and mega-volume sets. Award-winning lash designer. Clients travel from across the Bay Area for her Design Lashes."
        }
    },
    {
        "staff_id": "STF-004", "name": "Sophia Liu", "role": "Nail Artist",
        "specialties": "Manicure,Eyelash", "working_days": "Tue;Thu;Fri;Sat;Sun",
        "working_hours": "11:00-19:00",
        "expertise": {
            "Facial": 1, "Hair & Scalp": 1, "Eyelash": 3, "Manicure": 5,
            "best_services": "Custom Design;Cat Eye;Single Color",
            "good_at": "The nail art queen - can create any custom design clients bring in from Instagram or Pinterest. Cat eye gel technique is flawless. Very creative and suggests designs clients love. Great at shaping and cuticle care. Nails last 3-4 weeks without chipping. Fun personality - clients enjoy chatting with her. Also trained in classic lash application as backup.",
            "not_good_at": "Classic lash work is average - not as precise or long-lasting as Mia's. Cannot do Design Lashes (volume/mega-volume). No facial or scalp training at all. Sometimes runs late because she spends extra time perfecting custom designs. Can be chatty which some clients find distracting when they want quiet time.",
            "bio": "7 years nail art experience. Instagram-famous for intricate custom designs. Clients bring her photos from social media and she recreates them perfectly. Also backup lash tech for classic sets."
        }
    },
    {
        "staff_id": "STF-005", "name": "Olivia Lin", "role": "Senior Esthetician",
        "specialties": "Facial,Hair & Scalp", "working_days": "Mon;Tue;Wed;Sat;Sun",
        "working_hours": "10:00-18:00",
        "expertise": {
            "Facial": 5, "Hair & Scalp": 3, "Eyelash": 2, "Manicure": 1,
            "best_services": "24K Radiance Luxury Gold Facial;Personalized Ampoule Infusion Skincare;Perfect Glow Treatment;Hydrafacial Platinum",
            "good_at": "The luxury facial specialist - 24K Gold Facial and ampoule treatments are her signature. Best on the team with the Hydrafacial machine - knows all the boosters and customization options. Incredibly gentle touch perfect for sensitive skin clients. Creates a spa-like relaxing atmosphere. Great at skin analysis and recommending the right treatment plan. Upsells naturally without being pushy.",
            "not_good_at": "Not great at deep-pressure massage - her touch is too light for clients wanting firm pressure. Avoids MTS micro-needling (not confident with needles). RF treatments are adequate but not her strength - Lily is better. Scalp treatments are basic - Emma is much better for hair loss concerns. Sometimes over-recommends premium/expensive treatments when simpler options would work.",
            "bio": "10 years in luxury skincare. Former lead esthetician at a 5-star hotel spa. The go-to for Hydrafacial, gold facials, and pamper-focused experiences. Clients who want to feel indulged request her."
        }
    },
]

# --- Services (unchanged from existing, loaded for reference) ---

SERVICES = [
    ("SVC-001", "Facial", "Hydrafacial Signature", 30, 199.00),
    ("SVC-002", "Facial", "Hydrafacial Deluxe", 45, 299.00),
    ("SVC-003", "Facial", "Hydrafacial Platinum", 60, 399.00),
    ("SVC-004", "Facial", "AQUA PEEL Deep Cleaning & Hydrating Facial", 60, 180.00),
    ("SVC-005", "Facial", "Vital Glow Face Relaxation", 75, 220.00),
    ("SVC-006", "Facial", "Personalized Ampoule Infusion Skincare", 90, 280.00),
    ("SVC-007", "Facial", "Algae Vitalizer Detox", 90, 260.00),
    ("SVC-008", "Facial", "Magnetic Glow Skin Treatment", 90, 250.00),
    ("SVC-009", "Facial", "Perfect Glow Treatment", 90, 240.00),
    ("SVC-010", "Facial", "Multivita Antioxidant Treatment", 90, 270.00),
    ("SVC-011", "Facial", "24K Radiance Luxury Gold Facial", 90, 350.00),
    ("SVC-012", "Facial", "RF Anti-aging V-shape & Lifting Treatment", 90, 320.00),
    ("SVC-013", "Facial", "MTS Nano Acne-free Glow Treatment", 90, 290.00),
    ("SVC-014", "Facial", "MTS Nano Hyaluronic Radiance Therapy", 90, 290.00),
    ("SVC-015", "Facial", "MTS Nano Salmon DNA Rejuvenation", 90, 310.00),
    ("SVC-016", "Facial", "MTS Nano Stem Cell Anti-aging Skincare", 90, 330.00),
    ("SVC-017", "Facial", "Skin Revival Treatment", 90, 230.00),
    ("SVC-018", "Hair & Scalp", "The Head Retreat", 60, 150.00),
    ("SVC-019", "Hair & Scalp", "Herbal Hair & Scalp Refreshment", 75, 180.00),
    ("SVC-020", "Hair & Scalp", "Hair & Scalp Intensive Nourishment and Restoration", 90, 220.00),
    ("SVC-021", "Hair & Scalp", "Hair & Scalp Revitalization with LED Lights", 110, 280.00),
    ("SVC-022", "Eyelash", "Classic Lashes", 60, 120.00),
    ("SVC-023", "Eyelash", "Design Lashes", 90, 180.00),
    ("SVC-024", "Manicure", "Single Color", 30, 45.00),
    ("SVC-025", "Manicure", "Cat Eye", 45, 65.00),
    ("SVC-026", "Manicure", "Custom Design", 60, 85.00),
]

# Service category -> service IDs
CAT_SERVICES = {}
for sid, cat, *_ in SERVICES:
    CAT_SERVICES.setdefault(cat, []).append(sid)

# Staff expertise weights per category (for appointment generation)
STAFF_CAT_WEIGHT = {}
for s in STAFF:
    for cat in ["Facial", "Hair & Scalp", "Eyelash", "Manicure"]:
        STAFF_CAT_WEIGHT[(s["staff_id"], cat)] = s["expertise"][cat]

# --- Name pools ---

FIRST_NAMES = [
    "Jessica", "Karen", "Michelle", "Sarah", "Linda", "Amy", "Rachel", "Grace",
    "Tina", "Nancy", "Diana", "Wendy", "Jennifer", "Angela", "Christine", "Helen",
    "Lisa", "Susan", "Anna", "Maria", "Catherine", "Emily", "Laura", "Victoria",
    "Christina", "Stephanie", "Nicole", "Amanda", "Melissa", "Rebecca", "Sharon",
    "Cindy", "Patricia", "Dorothy", "Janet", "Pamela", "Teresa", "Gloria",
    "Alice", "Betty", "Cynthia", "Denise", "Donna", "Frances", "Irene",
    "Jade", "Kelly", "Lily", "Monica", "Natalie", "Paula", "Rita", "Sandy",
    "Tracy", "Vivian", "Yvonne", "Zoe", "Mei", "Yuki", "Hana", "Sakura",
    "Min", "Jing", "Wei", "Xin", "Yi", "Fei", "Lan", "Ling", "Qian", "Rui",
    "Harper", "Aria", "Luna", "Ella", "Chloe", "Mila", "Avery", "Riley",
    "Nora", "Hazel", "Aurora", "Willow", "Ivy", "Violet", "Nova", "Emery",
    "Isla", "Ellie", "Paisley", "Stella", "Skylar", "Maya", "Naomi", "Elena",
    "Samantha", "Jasmine", "Evelyn", "Madeline", "Brianna", "Aaliyah",
]

LAST_NAMES = [
    "Chen", "Wang", "Zhang", "Liu", "Li", "Huang", "Wu", "Yang", "Zhou", "Xu",
    "Sun", "Ma", "Zhu", "Hu", "Lin", "Guo", "He", "Luo", "Zheng", "Liang",
    "Song", "Tang", "Han", "Feng", "Cheng", "Wei", "Xie", "Deng", "Cao", "Pan",
    "Kim", "Park", "Lee", "Choi", "Jung", "Kang", "Yoon", "Shin", "Jang", "Han",
    "Tanaka", "Yamamoto", "Suzuki", "Sato", "Watanabe", "Ito", "Nakamura",
    "Nguyen", "Tran", "Pham", "Hoang", "Vo", "Bui", "Dang", "Do",
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller",
    "Davis", "Rodriguez", "Martinez", "Anderson", "Taylor", "Thomas", "Moore",
    "Jackson", "Martin", "White", "Harris", "Thompson", "Clark", "Lewis",
    "Robinson", "Walker", "Young", "Allen", "King", "Wright", "Scott", "Hill",
]

MEMBERSHIP_TIERS = ["Bronze", "Silver", "Gold"]
TIER_WEIGHTS = [0.50, 0.35, 0.15]  # distribution

# Preload: $1000 gets 85% discount (effectively $850 in credit for $1000)
# Some customers preload, some don't
PRELOAD_AMOUNT = 1000.00
PRELOAD_CREDIT = 1000.00 / 0.85  # $1176.47 worth of services for $1000

def generate_customers(n=200):
    customers = []
    used_names = set()

    for i in range(1, n + 1):
        while True:
            first = random.choice(FIRST_NAMES)
            last = random.choice(LAST_NAMES)
            name = f"{first} {last}"
            if name not in used_names:
                used_names.add(name)
                break

        email = f"{first.lower()}.{last.lower()}{random.randint(1,99)}@{'email.com' if random.random() > 0.3 else random.choice(['gmail.com', 'yahoo.com', 'outlook.com', 'icloud.com'])}"
        phone = f"408-555-{random.randint(1000, 9999)}"

        # Member since: between 2025-01-01 and 2026-03-15
        days_ago = random.randint(5, 450)
        member_since = (datetime(2026, 3, 20) - timedelta(days=days_ago)).strftime("%Y-%m-%d")

        tier = random.choices(MEMBERSHIP_TIERS, weights=TIER_WEIGHTS, k=1)[0]

        if tier == "Gold":
            total_visits = random.randint(10, 40)
        elif tier == "Silver":
            total_visits = random.randint(4, 15)
        else:
            total_visits = random.randint(1, 6)

        # Preloaded balance: ~30% of customers preload
        has_preload = random.random() < 0.30
        if has_preload:
            # They paid $1000, got $1176.47 credit. Some has been spent.
            initial_credit = round(PRELOAD_CREDIT, 2)
            spent = round(random.uniform(0, initial_credit * 0.8), 2)
            remaining_balance = round(initial_credit - spent, 2)
        else:
            remaining_balance = 0.00

        # ~20% get a meaningful note, 80% empty
        notes_pool = [
            # Skin concerns & treatment preferences
            "Needs acne removal - active breakouts on chin and forehead",
            "Cystic acne - wants MTS Nano Acne-free treatment series",
            "Hyperpigmentation on cheeks - looking for brightening treatments",
            "Post-sunburn skin recovery - needs gentle barrier repair",
            "Rosacea-prone - avoid harsh exfoliation and strong acids",
            "Wants anti-aging focus - fine lines around eyes and mouth",
            "Dark circles and puffiness - interested in eye area treatments",
            "Large pores on nose and cheeks - wants deep cleaning",
            "Dry flaky patches - needs intense hydration treatments",
            "Oily T-zone but dry cheeks - combination skin challenge",
            # Massage & pressure preferences
            "Likes gentle massage only - bruises easily",
            "Loves deep pressure massage - the harder the better",
            "Sensitive skin - absolutely no firm pressure during facials",
            "Wants firm extractions - doesn't mind some pain for results",
            "Prefers light relaxation-focused facials over clinical treatments",
            "Likes strong scalp massage with lots of pressure",
            # Staff preferences
            "Only books with Lily - trusts her extractions",
            "Prefers Olivia for luxury pampering facials",
            "Prefers Emma for scalp treatments - gentle touch",
            "Loyal to Mia for lashes - won't see anyone else",
            "Regular nail client with Sophia - loves her custom designs",
            "Tried Lily once - too rough. Now only books Olivia or Emma",
            "Loves Olivia's Hydrafacial technique",
            # Personality & service style preferences
            "Hates upsells - just do what was booked, nothing more",
            "Do NOT suggest upgrades or add-ons - gets annoyed",
            "Enjoys chatting during appointments - very social",
            "Prefers silence during treatments - comes to relax",
            "Wants detailed skin analysis and product recommendations after each visit",
            "Likes being educated about what products are being used",
            "Doesn't want small talk - just the treatment please",
            # Scheduling & logistics
            "Prefers morning appointments before 11am",
            "Only available on weekends",
            "Prefers evening slots - works until 5pm",
            "Frequently reschedules - confirm 48hrs in advance",
            "Always 10-15 min late - schedule buffer time",
            "Always on time and appreciates punctuality",
            # Allergies & sensitivities
            "Allergic to certain essential oils - especially lavender and tea tree",
            "Sensitive to fragrance - use fragrance-free products only",
            "Latex allergy - use nitrile gloves",
            "Allergic to adhesive in certain lash glues - use sensitive formula",
            "Cannot use products with retinol - causes severe irritation",
            "Nut allergy - check product ingredients for almond/coconut oil",
            # Hair & scalp concerns
            "Hair thinning at crown - wants LED scalp treatment series",
            "Severe dandruff - tried everything OTC, needs professional help",
            "Postpartum hair loss - very stressed about it",
            "Itchy scalp with flaking - needs herbal treatment",
            "Colored hair - avoid harsh scalp products that strip color",
            # Lash & nail preferences
            "Prefers natural-looking classic lashes - nothing dramatic",
            "Wants mega-volume dramatic lashes for events",
            "Sparse natural lashes - needs experienced lash tech",
            "Gel manicure every 3 weeks - single color only",
            "Loves intricate nail art - willing to pay extra for custom designs",
            "Cat eye gel addict - books every 3 weeks with Sophia",
            # Value & spending
            "Budget-conscious - prefers basic treatments only",
            "Price is no object - always wants the premium option",
            "Interested in prepaid package deals for savings",
            "Compares prices with other salons - price sensitive",
            "Tips generously - treat well",
            "VIP client - complimentary drinks and snacks",
            "Student - asks about discounts",
            # Misc
            "Referred by friend - first visit gift given",
            "Birthday month: special discount eligible",
            "Brings her daughter for mother-daughter appointments",
            "Takes photos of every treatment for her beauty blog",
            "Writes Yelp reviews - ensure great experience",
            "Had bad experience at previous salon - needs trust building",
            "Claustrophobic - no face covers or heavy masks",
            "Pregnant - avoid certain ingredients and essential oils",
        ]

        if random.random() < 0.25:
            notes = random.choice(notes_pool)
        else:
            notes = ""

        customers.append({
            "customer_id": f"CUS-{i:03d}",
            "name": name,
            "email": email,
            "phone": phone,
            "member_since": member_since,
            "membership_tier": tier,
            "total_visits": total_visits,
            "prepaid_balance": f"{remaining_balance:.2f}",
            "notes": notes,
        })

    return customers


def get_staff_for_service(service_id):
    """Pick a staff member weighted by expertise for the service category."""
    cat = None
    for sid, c, *_ in SERVICES:
        if sid == service_id:
            cat = c
            break

    candidates = []
    weights = []
    for s in STAFF:
        w = STAFF_CAT_WEIGHT.get((s["staff_id"], cat), 0)
        if w >= 2:  # only staff with at least some skill
            # Check if day is a working day (simplified - we'll just use the weight)
            candidates.append(s["staff_id"])
            weights.append(w ** 2)  # square to amplify expertise preference

    if not candidates:
        candidates = [s["staff_id"] for s in STAFF]
        weights = [1] * len(candidates)

    return random.choices(candidates, weights=weights, k=1)[0]


def generate_appointments(customers, start_date, end_date):
    """Generate appointments from start_date to end_date."""
    appointments = []
    apt_id = 1001

    current = start_date
    time_slots = ["10:00", "10:30", "11:00", "11:30", "13:00", "13:30", "14:00", "14:30", "15:00", "15:30", "16:00"]

    today = datetime(2026, 3, 20).date()

    while current <= end_date:
        # Skip some days randomly (holidays, slow days)
        if current.weekday() == 6 and random.random() < 0.3:  # some Sundays closed
            current += timedelta(days=1)
            continue

        # Number of appointments per day: 4-10
        n_apts = random.randint(4, 10)

        day_slots = random.sample(time_slots, min(n_apts, len(time_slots)))

        for time_slot in day_slots:
            cust = random.choice(customers)
            service = random.choice(SERVICES)
            service_id = service[0]
            staff_id = get_staff_for_service(service_id)

            if current < today:
                # Past appointments
                status = random.choices(
                    ["completed", "cancelled", "no_show"],
                    weights=[0.82, 0.12, 0.06],
                    k=1
                )[0]
            elif current == today:
                status = random.choices(
                    ["completed", "in_progress", "confirmed"],
                    weights=[0.3, 0.2, 0.5],
                    k=1
                )[0]
            else:
                # Future appointments
                status = random.choices(
                    ["confirmed", "cancelled"],
                    weights=[0.90, 0.10],
                    k=1
                )[0]

            notes_pool = [
                "", "", "", "", "", "",  # most have no notes
                "First-time client",
                "Requested extra hydration",
                "Sensitive skin - gentle products",
                "Follow-up session",
                "Package deal - session 2 of 5",
                "Package deal - session 3 of 5",
                "Birthday treatment",
                "Referred by existing client",
                "Rescheduled from last week",
                "Prefers low music volume",
                "Late arrival - 15 min",
                "Cancelled within 24hrs - $50 fee",
                "Prepaid balance used",
                "Combo booking with friend",
            ]
            notes = random.choice(notes_pool)
            if status == "cancelled" and random.random() < 0.3:
                notes = "Cancelled within 24hrs - $50 fee"

            appointments.append({
                "appointment_id": f"APT-{apt_id}",
                "customer_id": cust["customer_id"],
                "customer_name": cust["name"],
                "customer_email": cust["email"],
                "customer_phone": cust["phone"],
                "service_id": service_id,
                "staff_id": staff_id,
                "date": current.strftime("%Y-%m-%d"),
                "time": time_slot,
                "status": status,
                "notes": notes,
            })
            apt_id += 1

        current += timedelta(days=1)

    return appointments


def write_staff():
    path = os.path.join(DATA_DIR, "staff.csv")
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "staff_id", "name", "role", "specialties", "working_days", "working_hours",
            "facial_rating", "hair_scalp_rating", "eyelash_rating", "manicure_rating",
            "best_services", "good_at", "not_good_at", "bio"
        ])
        for s in STAFF:
            writer.writerow([
                s["staff_id"], s["name"], s["role"], s["specialties"],
                s["working_days"], s["working_hours"],
                s["expertise"]["Facial"],
                s["expertise"]["Hair & Scalp"],
                s["expertise"]["Eyelash"],
                s["expertise"]["Manicure"],
                s["expertise"]["best_services"],
                s["expertise"]["good_at"],
                s["expertise"]["not_good_at"],
                s["expertise"]["bio"],
            ])
    print(f"Written {len(STAFF)} staff to {path}")


# --- Review templates inspired by real beauty salon reviews ---

# Each template is (rating, template_text) where {staff}, {service}, {date} get filled in.
# Reviews reflect real patterns: pressure complaints, machine handling, retention,
# breakouts, relaxation, communication style, etc.

REVIEW_TEMPLATES = {
    "STF-001": {  # Lily Chen - strong hands, deep pressure, good with RF/MTS, not gentle
        "positive": [
            (5, "Lily did my RF treatment and I can already see a difference in my jawline after just one session. She really knows how to use the machine and explained everything step by step. My skin felt tight and lifted. Will definitely come back for the full series."),
            (5, "Best extractions I've ever had. Lily is so thorough - she got every single clogged pore. Yes it hurt a bit but my skin was SO clear afterward. Worth it if you can handle some pressure."),
            (5, "Had the MTS Nano treatment with Lily and my skin is glowing 3 days later. She clearly knows what she's doing with the micro-needling device. Very professional and clinical approach. Not a chatty spa experience but the results speak for themselves."),
            (5, "Lily's facial massage is incredible - she uses firm pressure that really gets into the tension in my jaw and temples. I carry so much stress in my face and she works it all out. My skin looks lifted after every session."),
            (4, "Came in for the Magnetic Glow treatment with Lily. She was very thorough with the cleansing and exfoliation steps. Extractions were a bit intense but my skin has never looked this clear. She doesn't talk much but I appreciate her focus."),
            (5, "I've been seeing Lily for my acne-prone skin for 6 months now and the difference is night and day. She's not afraid to do proper extractions and her MTS treatments have really helped with my scarring. Truly an expert."),
            (4, "Lily really knows her stuff with the RF machine. She adjusts the intensity based on different areas of your face which shows real expertise. The treatment was a bit uncomfortable in some areas but the lifting results are visible immediately."),
            (5, "Scalp massage during my Head Retreat with Lily was heavenly. She has strong hands and really works out the tension. My headache was completely gone by the end. Will book again."),
        ],
        "negative": [
            (2, "I have sensitive skin and told Lily I wanted a gentle facial. But her pressure was way too strong during the massage and the extractions left my face red for two days. She's skilled but not the right fit for sensitive skin."),
            (3, "Booked a Hydrafacial with Lily and felt like she was rushing through the suction steps. The machine didn't feel like it was doing much. I've had better Hydrafacials elsewhere. She seems more comfortable with manual treatments than machine-based ones."),
            (2, "The extraction part was so painful I almost cried. I asked her to be gentler but she said she needed to apply pressure to get everything out. Left with bruise-like marks that took 4 days to fade. Not going back to her for facials."),
            (3, "Lily is clearly knowledgeable but she barely said a word during my 90-minute treatment. I had questions about my skin and felt like I was bothering her when I asked. The results were fine but I want someone warmer."),
        ],
    },
    "STF-002": {  # Emma Wang - gentle, herbal expert, great with scalp, slow, avoids machines
        "positive": [
            (5, "Emma is a miracle worker for my scalp. I've had dandruff for years and after 3 sessions with her the flaking has almost completely stopped. She really understands herbal ingredients and customized the treatment for my specific condition."),
            (5, "The LED hair treatment with Emma was the most relaxing 110 minutes of my life. She has such a gentle touch and the scalp massage was pure bliss. My hair felt lighter and shinier for a whole week afterward."),
            (5, "I was losing hair postpartum and was so stressed about it. Emma was incredibly kind and reassuring. She explained exactly what was happening and tailored a treatment plan. After 4 LED sessions I can see new growth coming in!"),
            (5, "Emma's Algae Detox facial is my favorite treatment. She's so gentle with sensitive skin - no redness or irritation afterward. The algae mask felt amazing and my skin was hydrated for days. She also gave me great product recommendations."),
            (4, "Such a warm personality! Emma made me feel so comfortable from the moment I walked in. She asked about my concerns, explained every step, and checked in throughout. My scalp has never felt this clean and healthy."),
            (5, "Came in for the Herbal Scalp Refreshment and Emma spent extra time on the areas where I had the most buildup. She's not rushed at all - really takes her time to do things right. My itchy scalp is finally under control."),
            (5, "Emma is the only esthetician I trust with my sensitive scalp. She uses just the right amount of pressure and always does a patch test first. Love that she uses natural herbal products. My hair stylist even noticed my scalp looks healthier."),
            (4, "Had the Vital Glow facial with Emma and it was lovely. Very relaxing, gentle touch, skin felt hydrated and plump. She has a calming presence that makes the whole experience feel luxurious."),
        ],
        "negative": [
            (3, "Emma is sweet but my appointment ran 20 minutes over. I had somewhere to be and she was still doing the final steps. She's thorough but needs to manage time better. Had to skip the blow dry."),
            (3, "I wanted deep extractions but Emma barely touched my clogged pores. She said she prefers not to do aggressive extractions. My skin didn't feel as clean as I'd hoped. Fine for relaxation but not for serious skin clearing."),
            (2, "Booked the Head Retreat hoping for a deep-pressure scalp massage but Emma's touch was way too light. I could barely feel it. When I asked for more pressure she tried but it still wasn't enough. Disappointing if you like firm massage."),
            (3, "Emma doesn't seem confident with the high-tech machines. I asked about RF treatment and she suggested I book with someone else. Felt like she's limited to herbal and manual treatments only."),
        ],
    },
    "STF-003": {  # Mia Zhang - best lash artist, precise, fast, quiet, struggles with sparse lashes
        "positive": [
            (5, "Mia is hands down the best lash artist in San Jose. My Design Lashes are STUNNING - perfectly symmetrical and the volume is amazing without looking fake. She finished a full set in under 2 hours which is impressive."),
            (5, "I've been going to Mia for a year now and my lashes always look incredible. The retention is amazing - they last 3-4 weeks easy. She's quiet during the appointment but I actually prefer that since I usually nap."),
            (5, "Drove 40 minutes to see Mia for volume lashes and it was worth every mile. She mapped out my eye shape first and customized the curl pattern. The result was dramatic but still natural-looking. Everyone asks me where I get them done."),
            (5, "Mia's classic lash sets are so precise. Every single lash is perfectly isolated and placed. No clumping, no stickies, no discomfort. My natural lashes are still healthy after a year of extensions with her. That says everything."),
            (4, "Got a mega-volume set from Mia for my wedding and I cried happy tears when I saw them. Absolutely gorgeous. She even stayed late to make sure they were perfect. Best lash experience I've ever had."),
            (5, "What I love about Mia is she never rushes but she's also incredibly fast. Full set in 90 minutes and they're flawless. No other lash tech I've tried comes close to her precision and symmetry."),
            (5, "My wispy hybrid set from Mia gets me compliments constantly. She really understands different lash styles and can create any look you want. The texture mapping she does is next level."),
            (4, "Mia also did my gel manicure and it was solid work. Clean application, lasted 3 weeks without chipping. Not as fancy as a nail specialist but definitely good for a basic gel set."),
        ],
        "negative": [
            (3, "Mia is talented but she barely talks. I tried to make conversation and got one-word answers. After 90 minutes of silence it felt awkward. Some people like quiet but I prefer a bit of warmth from my lash tech."),
            (2, "I have naturally very sparse and thin lashes and Mia struggled with my set. Some extensions didn't bond well and fell off within a week. She admitted my lashes were challenging but I expected better from someone with her reputation."),
            (3, "Had Mia remove my old set from another salon and she pulled a bit too hard on some lashes. Lost a few natural lashes in the process. The new set she applied was beautiful though. Just wish the removal was gentler."),
            (3, "Mia's nail work is okay but nothing special. The design I asked for was simplified - she said she doesn't do complex nail art. If you want fancy nails, book with someone else. Stick to lashes with her."),
        ],
    },
    "STF-004": {  # Sophia Liu - nail art queen, creative, chatty, average lash work
        "positive": [
            (5, "Sophia is a NAIL GENIUS. I showed her a super complicated cherry blossom design from Pinterest and she recreated it perfectly. Every nail was a tiny work of art. My friends couldn't believe they were done by hand."),
            (5, "The Cat Eye gel Sophia does is unreal - the dimension and shift in the light is mesmerizing. She takes her time to get the magnet placement just right. My nails lasted 4 weeks without a single chip."),
            (5, "I love my appointments with Sophia because she's so fun to talk to! We chat the whole time and she always suggests creative design ideas I wouldn't have thought of. Makes the whole experience enjoyable, not just the result."),
            (5, "Sophia's cuticle work is immaculate. She's so careful and gentle - never any bleeding or pain. The shaping is always perfect and symmetrical. She really cares about nail health, not just aesthetics."),
            (4, "Showed Sophia a nail design from Instagram and she not only recreated it but improved on it. She has an amazing eye for color combinations. My custom set gets compliments everywhere I go."),
            (5, "I've tried every nail tech in south San Jose and Sophia is the only one whose work lasts more than 3 weeks on me. Her prep work is thorough and the application is flawless. Worth the price every time."),
            (5, "Sophia did my bridal nails and they were absolutely stunning. French ombre with tiny pearl details. She even matched the design to my dress. So talented and creative."),
            (4, "Also got classic lashes from Sophia as a backup when Mia wasn't available. They were decent - nice and natural looking. Not as precise as Mia's but perfectly good for everyday wear."),
        ],
        "negative": [
            (3, "Sophia is great at nails but my classic lash set from her wasn't as good as Mia's. Some lashes were slightly uneven and the retention was maybe 2 weeks vs Mia's 3-4 weeks. Stick to nails with Sophia."),
            (3, "My appointment ran 30 minutes late because Sophia was perfecting the previous client's custom design. I appreciate the attention to detail but not when it makes me wait. She needs to allocate more time for complex designs."),
            (2, "Sophia talks SO much. I just wanted to relax during my manicure but she chatted the entire time without picking up on my cues that I wanted quiet. Great nails though. Just wish there was a do not disturb option."),
            (3, "Sophia can't do volume or Design Lashes - only classics. I didn't realize this when I booked and had to reschedule with Mia. The booking system should make this clearer."),
        ],
    },
    "STF-005": {  # Olivia Lin - luxury facial queen, Hydrafacial expert, gentle, upsells
        "positive": [
            (5, "Olivia's 24K Gold Facial is the most luxurious experience I've ever had. From the moment the gold mask went on I felt like royalty. My skin had a gorgeous glow for two weeks afterward. She creates such a relaxing spa atmosphere."),
            (5, "Best Hydrafacial I've ever had, hands down. Olivia knows every booster and add-on and customized my treatment perfectly. The suction was thorough but comfortable, and she took her time with each step. My pores have never been this clean."),
            (5, "Olivia did a skin analysis before my facial and recommended the Personalized Ampoule treatment instead of what I originally booked. She was right - the anti-wrinkle ampoules made a visible difference. She really knows how to match treatments to skin needs."),
            (5, "I have extremely sensitive skin and Olivia is the only esthetician who has never caused a reaction. Her touch is feather-light and she always checks in to make sure I'm comfortable. The Perfect Glow treatment left me radiant without any redness."),
            (4, "The Hydrafacial Platinum with Olivia was worth every penny. She added lymphatic drainage and a custom booster. My skin looked incredible for the next week. She explains everything she's doing which I really appreciate as a first-timer."),
            (5, "Olivia talked me through a complete skincare routine after my facial and it's transformed my at-home care. She doesn't just do the treatment - she educates you. My skin has honestly never been better since following her advice."),
            (5, "I bring my mom to see Olivia for the Gold Facial every month. She always makes us feel pampered and special. The treatment room smells amazing and she plays the most relaxing music. It's truly a luxury experience."),
            (4, "Olivia's ampoule infusion facial was deeply hydrating. She customized the 3D firming ampoule for my jawline area where I'm starting to see sagging. Gentle massage technique and very thorough product application. Felt like a 5-star spa."),
        ],
        "negative": [
            (3, "Olivia recommended I upgrade from the Signature to the Platinum Hydrafacial, then also suggested adding boosters. My bill was $200 more than I planned. The treatment was great but I felt upsold. Just do what I book please."),
            (2, "I asked Olivia for a deep massage and she could barely apply any pressure. Her touch is way too light for anyone who wants real muscle work. Great for pampering but useless for tension relief. My neck was still stiff when I left."),
            (3, "Booked an MTS treatment with Olivia but she seemed hesitant with the device. She went very shallow and I could tell she wasn't fully confident. Ended up rebooking with Lily who was much better with micro-needling."),
            (3, "Olivia pushed the Gold Facial pretty hard when I just came in for a basic cleansing facial. I know it's her specialty but it's 3x the price and I didn't need it. Sometimes simpler is better. The basic facial she did was fine but felt like she was going through the motions."),
        ],
    },
}


def generate_reviews(appointments):
    """Generate reviews for completed appointments."""
    reviews = []
    review_id = 1001

    completed = [a for a in appointments if a["status"] == "completed"]

    # ~40% of completed appointments get a review
    reviewed = random.sample(completed, min(len(completed), int(len(completed) * 0.4)))

    for apt in reviewed:
        staff_id = apt["staff_id"]
        templates = REVIEW_TEMPLATES.get(staff_id, {})
        if not templates:
            continue

        # 75% positive, 25% negative
        if random.random() < 0.75:
            pool = templates.get("positive", [])
        else:
            pool = templates.get("negative", [])

        if not pool:
            continue

        rating, text = random.choice(pool)

        # Find service name
        svc_name = apt["service_id"]
        for sid, cat, name, *_ in SERVICES:
            if sid == apt["service_id"]:
                svc_name = name
                break

        # Find staff name
        staff_name = staff_id
        for s in STAFF:
            if s["staff_id"] == staff_id:
                staff_name = s["name"]
                break

        reviews.append({
            "review_id": f"REV-{review_id}",
            "appointment_id": apt["appointment_id"],
            "customer_id": apt["customer_id"],
            "customer_name": apt["customer_name"],
            "staff_id": staff_id,
            "staff_name": staff_name,
            "service_id": apt["service_id"],
            "service_name": svc_name,
            "date": apt["date"],
            "rating": rating,
            "review_text": text,
        })
        review_id += 1

    return reviews


def write_reviews(reviews):
    path = os.path.join(DATA_DIR, "reviews.csv")
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "review_id", "appointment_id", "customer_id", "customer_name",
            "staff_id", "staff_name", "service_id", "service_name",
            "date", "rating", "review_text"
        ])
        writer.writeheader()
        writer.writerows(reviews)
    print(f"Written {len(reviews)} reviews to {path}")


def write_customers(customers):
    path = os.path.join(DATA_DIR, "customers.csv")
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "customer_id", "name", "email", "phone", "member_since",
            "membership_tier", "total_visits", "prepaid_balance", "notes"
        ])
        writer.writeheader()
        writer.writerows(customers)
    print(f"Written {len(customers)} customers to {path}")


def write_appointments(appointments):
    path = os.path.join(DATA_DIR, "appointments.csv")
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "appointment_id", "customer_id", "customer_name", "customer_email",
            "customer_phone", "service_id", "staff_id", "date", "time",
            "status", "notes"
        ])
        writer.writeheader()
        writer.writerows(appointments)
    print(f"Written {len(appointments)} appointments to {path}")


if __name__ == "__main__":
    print("Generating Beauty Lab test data...")

    customers = generate_customers(200)
    write_customers(customers)

    # Appointments: Nov 2025 to May 2026 (4 months back + 2 months forward from March 20, 2026)
    start = datetime(2025, 11, 20).date()
    end = datetime(2026, 5, 20).date()
    appointments = generate_appointments(customers, start, end)
    write_appointments(appointments)

    write_staff()

    reviews = generate_reviews(appointments)
    write_reviews(reviews)

    print("Done!")
