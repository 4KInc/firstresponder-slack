"""Load a realistic demo school into the knowledge base.

Run this once to populate the knowledge base with Jefferson Elementary School data.
After loading, the AI agent will give room-specific evacuation guidance, locate
personnel by name, find nearby resources, and provide building-aware directions.

Usage:
    python -m scripts.load_demo_school
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crisis.knowledge import knowledge_base as kb


def load():
    print("Loading Jefferson Elementary School demo data...")

    # === FACILITY ===
    kb.add_facility(
        "jefferson", "Jefferson Elementary School",
        address="1200 Oak Street, Nashville, TN 37203",
        floors=2, capacity=450,
    )

    # === ZONES ===
    # Floor 1
    kb.add_zone("east-wing-f1", "jefferson", "East Wing - Floor 1", floor=1,
                zone_type="classrooms", primary_exit="Door 3 (East Exit)",
                alternate_exit="Door 7 (Gym Exit)", shelter_location="Interior hallway A",
                capacity=120, notes="Rooms 101-108, closest to east entrance")
    kb.add_zone("west-wing-f1", "jefferson", "West Wing - Floor 1", floor=1,
                zone_type="classrooms", primary_exit="Door 1 (West Exit)",
                alternate_exit="Door 5 (Cafeteria Exit)", shelter_location="Interior hallway B",
                capacity=120, notes="Rooms 109-116")
    kb.add_zone("admin-f1", "jefferson", "Main Office / Admin", floor=1,
                zone_type="administrative", primary_exit="Door 2 (Main Entrance)",
                alternate_exit="Door 1 (West Exit)", shelter_location="Principal's inner office",
                capacity=15, notes="Front office, principal, counselor, nurse")
    kb.add_zone("cafeteria", "jefferson", "Cafeteria", floor=1,
                zone_type="common", primary_exit="Door 5 (Cafeteria Exit)",
                alternate_exit="Door 6 (Kitchen Loading Dock)", shelter_location="Kitchen freezer room",
                capacity=200, notes="Also used as assembly hall")
    kb.add_zone("gym", "jefferson", "Gymnasium", floor=1,
                zone_type="common", primary_exit="Door 7 (Gym Exit)",
                alternate_exit="Door 8 (Field Exit)", shelter_location="Locker rooms (interior)",
                capacity=300, notes="PE classes, assemblies")

    # Floor 2
    kb.add_zone("east-wing-f2", "jefferson", "East Wing - Floor 2", floor=2,
                zone_type="classrooms", primary_exit="East Stairwell to Door 3",
                alternate_exit="Central Stairwell to Door 2", shelter_location="Interior hallway C",
                capacity=120, notes="Rooms 201-208")
    kb.add_zone("west-wing-f2", "jefferson", "West Wing - Floor 2", floor=2,
                zone_type="classrooms", primary_exit="West Stairwell to Door 1",
                alternate_exit="Central Stairwell to Door 2", shelter_location="Interior hallway D",
                capacity=120, notes="Rooms 209-216, includes science lab (Room 215)")
    kb.add_zone("library", "jefferson", "Library / Media Center", floor=2,
                zone_type="common", primary_exit="Central Stairwell to Door 2",
                alternate_exit="West Stairwell to Door 1", shelter_location="Library storage room (interior, no windows)",
                capacity=60, notes="Floor 2, center of building")

    # === ROOMS ===
    rooms = [
        # Floor 1 - East Wing
        ("101", "east-wing-f1", "Room 101", 1, "classroom", 25, ["Mrs. Rodriguez"]),
        ("102", "east-wing-f1", "Room 102", 1, "classroom", 25, ["Mr. Chen"]),
        ("103", "east-wing-f1", "Room 103", 1, "classroom", 25, ["Ms. Williams"]),
        ("104", "east-wing-f1", "Room 104", 1, "classroom", 25, ["Mrs. Davis"]),
        ("105", "east-wing-f1", "Room 105", 1, "classroom", 25, ["Mr. Okafor"]),
        ("106", "east-wing-f1", "Room 106", 1, "classroom", 25, ["Ms. Garcia"]),
        ("107", "east-wing-f1", "Room 107", 1, "classroom", 25, ["Mrs. Lee"]),
        ("108", "east-wing-f1", "Room 108", 1, "classroom", 25, ["Nurse Sarah"]),
        # Floor 1 - West Wing
        ("109", "west-wing-f1", "Room 109", 1, "classroom", 25, ["Mr. Brown"]),
        ("110", "west-wing-f1", "Room 110", 1, "classroom", 25, ["Ms. Taylor"]),
        ("111", "west-wing-f1", "Room 111", 1, "classroom", 25, ["Mrs. White"]),
        ("112", "west-wing-f1", "Room 112", 1, "classroom", 25, ["Mr. Scott"]),
        ("113", "west-wing-f1", "Room 113", 1, "art_room", 30, ["Ms. Ahmed"]),
        ("114", "west-wing-f1", "Room 114", 1, "music_room", 30, ["Mr. Rivera"]),
        # Floor 2 - East Wing
        ("201", "east-wing-f2", "Room 201", 2, "classroom", 25, ["Mrs. Nguyen"]),
        ("202", "east-wing-f2", "Room 202", 2, "classroom", 25, ["Mr. Patel"]),
        ("203", "east-wing-f2", "Room 203", 2, "classroom", 25, ["Ms. Clark"]),
        ("204", "east-wing-f2", "Room 204", 2, "classroom", 25, ["Mrs. Thompson"]),
        ("205", "east-wing-f2", "Room 205", 2, "classroom", 25, ["Mr. Kim"]),
        # Floor 2 - West Wing
        ("209", "west-wing-f2", "Room 209", 2, "classroom", 25, ["Ms. Johnson"]),
        ("210", "west-wing-f2", "Room 210", 2, "classroom", 25, ["Mr. Martinez"]),
        ("215", "west-wing-f2", "Room 215 - Science Lab", 2, "laboratory", 25, ["Dr. Franklin"]),
    ]
    for room_id, zone_id, name, floor, rtype, cap, personnel in rooms:
        kb.add_room(room_id, "jefferson", name, floor, zone_id, rtype, cap, personnel)

    # === PERSONNEL (45 staff) ===
    staff = [
        # Admin
        ("p001", "Principal Johnson", "U_PRINCIPAL", "Principal", "Administration", "admin-f1", 1,
         "615-555-0101", "Mark Johnson", "615-555-0102", "", False, True, False, True, "Incident Commander"),
        ("p002", "VP Martinez", "U_VP", "Vice Principal", "Administration", "admin-f1", 1,
         "615-555-0103", "Rosa Martinez", "615-555-0104", "", False, True, False, False, "Communications Lead"),
        ("p003", "Maria Santos", "U_MARIA", "Office Admin", "Administration", "admin-f1", 1,
         "615-555-0105", "Carlos Santos", "615-555-0106", "", False, False, False, False, ""),
        ("p004", "Nurse Sarah", "U_NURSE", "School Nurse", "Health", "108", 1,
         "615-555-0107", "David Park", "615-555-0108", "Asthma inhaler in office", False, True, True, False, "Medical Lead"),

        # East Wing F1 Teachers
        ("p005", "Mrs. Rodriguez", "U_RODRIGUEZ", "3rd Grade Teacher", "Teaching", "101", 1,
         "615-555-0110", "Jose Rodriguez", "615-555-0111", "", False, False, False, True, "Floor Warden - East F1"),
        ("p006", "Mr. Chen", "U_CHEN", "3rd Grade Teacher", "Teaching", "102", 1,
         "615-555-0112", "Wei Chen", "615-555-0113", "", False, False, False, False, ""),
        ("p007", "Ms. Williams", "U_WILLIAMS", "4th Grade Teacher", "Teaching", "103", 1,
         "615-555-0114", "James Williams", "615-555-0115", "", False, True, False, False, ""),
        ("p008", "Mrs. Davis", "U_DAVIS", "4th Grade Teacher", "Teaching", "104", 1,
         "615-555-0116", "Robert Davis", "615-555-0117", "Uses wheelchair — elevator required for evacuation", True, False, False, False, ""),
        ("p009", "Mr. Okafor", "U_OKAFOR", "5th Grade Teacher", "Teaching", "105", 1,
         "615-555-0118", "Ada Okafor", "615-555-0119", "", False, False, False, False, ""),
        ("p010", "Ms. Garcia", "U_GARCIA", "5th Grade Teacher", "Teaching", "106", 1,
         "615-555-0120", "Luis Garcia", "615-555-0121", "", False, True, True, False, ""),
        ("p011", "Mrs. Lee", "U_LEE", "ESL Teacher", "Teaching", "107", 1,
         "615-555-0122", "Kevin Lee", "615-555-0123", "", False, False, False, False, ""),

        # West Wing F1 Teachers
        ("p012", "Mr. Brown", "U_BROWN", "3rd Grade Teacher", "Teaching", "109", 1,
         "615-555-0124", "Linda Brown", "615-555-0125", "", False, False, False, True, "Floor Warden - West F1"),
        ("p013", "Ms. Taylor", "U_TAYLOR", "4th Grade Teacher", "Teaching", "110", 1,
         "615-555-0126", "Chris Taylor", "615-555-0127", "", False, False, False, False, ""),
        ("p014", "Mrs. White", "U_WHITE", "5th Grade Teacher", "Teaching", "111", 1,
         "615-555-0128", "Tom White", "615-555-0129", "", False, False, False, False, ""),
        ("p015", "Mr. Scott", "U_SCOTT", "5th Grade Teacher", "Teaching", "112", 1,
         "615-555-0130", "Karen Scott", "615-555-0131", "", False, True, False, False, ""),
        ("p016", "Ms. Ahmed", "U_AHMED", "Art Teacher", "Teaching", "113", 1,
         "615-555-0132", "Omar Ahmed", "615-555-0133", "", False, False, False, False, ""),
        ("p017", "Mr. Rivera", "U_RIVERA", "Music Teacher", "Teaching", "114", 1,
         "615-555-0134", "Sofia Rivera", "615-555-0135", "", False, False, False, False, ""),

        # East Wing F2 Teachers
        ("p018", "Mrs. Nguyen", "U_NGUYEN", "6th Grade Teacher", "Teaching", "201", 2,
         "615-555-0136", "Minh Nguyen", "615-555-0137", "", False, False, False, True, "Floor Warden - East F2"),
        ("p019", "Mr. Patel", "U_PATEL", "6th Grade Teacher", "Teaching", "202", 2,
         "615-555-0138", "Priya Patel", "615-555-0139", "", False, False, False, False, ""),
        ("p020", "Ms. Clark", "U_CLARK", "7th Grade Teacher", "Teaching", "203", 2,
         "615-555-0140", "Nancy Clark", "615-555-0141", "", False, True, True, False, ""),
        ("p021", "Mrs. Thompson", "U_THOMPSON", "7th Grade Teacher", "Teaching", "204", 2,
         "615-555-0142", "John Thompson", "615-555-0143", "Knee replacement — limited mobility on stairs", True, False, False, False, ""),
        ("p022", "Mr. Kim", "U_KIM", "8th Grade Teacher", "Teaching", "205", 2,
         "615-555-0144", "Susan Kim", "615-555-0145", "", False, False, False, False, ""),

        # West Wing F2 Teachers
        ("p023", "Ms. Johnson", "U_JOHNSON", "6th Grade Teacher", "Teaching", "209", 2,
         "615-555-0146", "Mike Johnson", "615-555-0147", "", False, False, False, True, "Floor Warden - West F2"),
        ("p024", "Mr. Martinez", "U_MARTINEZ", "7th Grade Teacher", "Teaching", "210", 2,
         "615-555-0148", "Ana Martinez", "615-555-0149", "", False, False, False, False, ""),
        ("p025", "Dr. Franklin", "U_FRANKLIN", "Science Teacher", "Teaching", "215", 2,
         "615-555-0150", "Eleanor Franklin", "615-555-0151", "", False, True, False, False, ""),

        # Library
        ("p026", "Ms. Jackson", "U_JACKSON", "Librarian", "Library", "library", 2,
         "615-555-0152", "Marcus Jackson", "615-555-0153", "", False, False, False, False, ""),

        # Support Staff
        ("p027", "Coach Williams", "U_COACH", "PE Teacher / Coach", "Athletics", "gym", 1,
         "615-555-0154", "Pat Williams", "615-555-0155", "", False, True, True, False, ""),
        ("p028", "Custodian Frank", "U_FRANK", "Head Custodian", "Facilities", "west-wing-f1", 1,
         "615-555-0156", "Betty Franklin", "615-555-0157", "", False, False, False, False, "Knows all utility shutoffs"),
        ("p029", "Cafeteria Rosa", "U_ROSA", "Cafeteria Manager", "Food Services", "cafeteria", 1,
         "615-555-0158", "Miguel Rosa", "615-555-0159", "", False, True, False, False, ""),
        ("p030", "Security Dave", "U_SECURITY", "Security Officer", "Security", "admin-f1", 1,
         "615-555-0160", "Sarah Davis", "615-555-0161", "", False, True, True, False, "Radio channel: Security 1"),
        ("p031", "Tech Jordan", "U_TECH", "IT Coordinator", "Technology", "library", 2,
         "615-555-0162", "Taylor Jordan", "615-555-0163", "", False, False, False, False, "Controls PA system and camera feeds"),

        # Counselors
        ("p032", "Mrs. Evans", "U_EVANS", "School Counselor", "Counseling", "admin-f1", 1,
         "615-555-0164", "Greg Evans", "615-555-0165", "", False, True, False, False, "Crisis counseling trained"),

        # Paraprofessionals / Aides
        ("p033", "Ms. Cooper", "U_COOPER", "Special Ed Aide", "Special Education", "east-wing-f1", 1,
         "615-555-0166", "James Cooper", "615-555-0167", "", False, True, True, False, ""),
        ("p034", "Mr. Hughes", "U_HUGHES", "Special Ed Aide", "Special Education", "east-wing-f2", 2,
         "615-555-0168", "Linda Hughes", "615-555-0169", "", False, False, False, False, ""),
    ]

    for s in staff:
        kb.add_person(
            person_id=s[0], name=s[1], slack_user_id=s[2], role=s[3], department=s[4],
            default_location=s[5], floor=s[6], phone=s[7],
            emergency_contact_name=s[8], emergency_contact_phone=s[9],
            medical_notes=s[10], mobility_limitations=s[11],
            trained_first_aid=s[12], trained_cpr=s[13], is_floor_warden=s[14],
            evacuation_role=s[15],
        )

    # === EMERGENCY RESOURCES ===
    resources = [
        ("jefferson", "aed", "Hallway B outside Room 112, mounted on wall", 1, "west-wing-f1"),
        ("jefferson", "aed", "Main office lobby, next to front desk", 1, "admin-f1"),
        ("jefferson", "aed", "Gym entrance, left side of double doors", 1, "gym"),
        ("jefferson", "first_aid_kit", "Nurse's office (Room 108)", 1, "east-wing-f1"),
        ("jefferson", "first_aid_kit", "Main office, behind reception counter", 1, "admin-f1"),
        ("jefferson", "first_aid_kit", "Cafeteria kitchen, on wall by service window", 1, "cafeteria"),
        ("jefferson", "first_aid_kit", "Library front desk, bottom drawer", 2, "library"),
        ("jefferson", "first_aid_kit", "Gym equipment room", 1, "gym"),
        ("jefferson", "trauma_kit", "Security office (inside admin area), locked cabinet", 1, "admin-f1"),
        ("jefferson", "fire_extinguisher", "East hallway F1, between rooms 104 and 105", 1, "east-wing-f1"),
        ("jefferson", "fire_extinguisher", "West hallway F1, between rooms 111 and 112", 1, "west-wing-f1"),
        ("jefferson", "fire_extinguisher", "East hallway F2, between rooms 203 and 204", 2, "east-wing-f2"),
        ("jefferson", "fire_extinguisher", "West hallway F2, near room 215 (science lab)", 2, "west-wing-f2"),
        ("jefferson", "fire_extinguisher", "Cafeteria kitchen", 1, "cafeteria"),
        ("jefferson", "fire_extinguisher", "Gym storage room", 1, "gym"),
        ("jefferson", "emergency_phone", "Main office front desk — direct line to 911", 1, "admin-f1"),
        ("jefferson", "emergency_phone", "Gym office — Coach Williams' desk phone", 1, "gym"),
    ]
    for fac, rtype, loc, floor, zone in resources:
        kb.add_emergency_resource(fac, rtype, loc, floor, zone)

    # === EVACUATION ROUTES ===
    routes = [
        ("jefferson", "East Wing F1 Primary", "Door 3 (East Exit)",
         "East hallway → Door 3 (east side of building) → parking lot",
         "east-wing-f1", "standard", ["east-entrance"]),
        ("jefferson", "East Wing F1 Alternate", "Door 7 (Gym Exit)",
         "East hallway → through gym corridor → Door 7 → athletic field",
         "east-wing-f1", "standard", []),
        ("jefferson", "West Wing F1 Primary", "Door 1 (West Exit)",
         "West hallway → Door 1 (west side) → staff parking lot",
         "west-wing-f1", "standard", []),
        ("jefferson", "West Wing F1 Alternate", "Door 5 (Cafeteria Exit)",
         "West hallway → through cafeteria → Door 5 → bus loop",
         "west-wing-f1", "standard", []),
        ("jefferson", "East Wing F2 Primary", "Door 3 (East Exit)",
         "East hallway F2 → East Stairwell (end of hall) → Door 3 → parking lot",
         "east-wing-f2", "standard", ["east-entrance"]),
        ("jefferson", "East Wing F2 Alternate", "Door 2 (Main Entrance)",
         "East hallway F2 → Central Stairwell → main lobby → Door 2 → front circle drive",
         "east-wing-f2", "standard", []),
        ("jefferson", "West Wing F2 Primary", "Door 1 (West Exit)",
         "West hallway F2 → West Stairwell → Door 1 → staff parking lot",
         "west-wing-f2", "standard", []),
        ("jefferson", "Library Route", "Door 2 (Main Entrance)",
         "Library → Central Stairwell → main lobby → Door 2",
         "library", "standard", []),
        ("jefferson", "Cafeteria Primary", "Door 5 (Cafeteria Exit)",
         "Cafeteria main doors → Door 5 → bus loop",
         "cafeteria", "standard", []),
        ("jefferson", "Gym Primary", "Door 7 (Gym Exit)",
         "Gym main doors → Door 7 → athletic field",
         "gym", "standard", []),
        ("jefferson", "Gym Alternate", "Door 8 (Field Exit)",
         "Gym → back corridor → Door 8 → playing fields (furthest from building)",
         "gym", "standard", []),
        # Accessible routes
        ("jefferson", "East Wing F2 Elevator Route", "Door 2 (Main Entrance)",
         "East hallway F2 → Elevator (mid-hall) → Floor 1 → main lobby → Door 2. KEY: elevator key in main office.",
         "east-wing-f2", "wheelchair_accessible", []),
        ("jefferson", "West Wing F2 Elevator Route", "Door 1 (West Exit)",
         "West hallway F2 → Elevator (mid-hall) → Floor 1 → west corridor → Door 1. KEY: elevator key in main office.",
         "west-wing-f2", "wheelchair_accessible", []),
    ]
    for fac, name, to_exit, desc, from_zone, access, blocked in routes:
        kb.add_evacuation_route(fac, name, to_exit, desc, from_zone, access, blocked)

    # === ASSEMBLY POINTS ===
    kb.add_assembly_point("ap-field", "jefferson", "Athletic Field (Primary)",
                          "Behind the gym, past the track — 500ft from building", 500, True,
                          notes="Primary rally point for all evacuations. Teachers line up by class.")
    kb.add_assembly_point("ap-parking", "jefferson", "Staff Parking Lot (Alternate)",
                          "West side staff parking lot, far end near Oak Street", 200, False,
                          alternate_point_id="ap-field",
                          notes="Alternate if athletic field is compromised. Further from east entrance.")
    kb.add_assembly_point("ap-church", "jefferson", "First Baptist Church (Off-Site)",
                          "1300 Oak Street, directly across the street from school", 400, False,
                          alternate_point_id="ap-field",
                          notes="Off-site reunification point for parents. Contact: Pastor Williams 615-555-0200")

    # === UTILITY CONTROLS ===
    utilities = [
        ("jefferson", "gas", "Utility room behind cafeteria kitchen — yellow valve handle on main pipe", 1, "cafeteria",
         "Turn yellow handle 90 degrees clockwise to shut off. Requires wrench (hanging on hook next to valve).", False, ""),
        ("jefferson", "electrical", "Electrical panel room — east end of F1 hallway, gray metal door", 1, "east-wing-f1",
         "Main breaker is top-left switch (red handle). Flip DOWN to kill power to east wing.", True, "Key on custodian Frank's keyring or in main office lockbox"),
        ("jefferson", "electrical", "Electrical panel — west end of F1 hallway, behind janitor's closet", 1, "west-wing-f1",
         "Main breaker is top-left switch. Flip DOWN to kill power to west wing.", True, "Key on custodian Frank's keyring or in main office lockbox"),
        ("jefferson", "water", "Water main shutoff — outside north side of building, green cover in ground", 1, None,
         "Lift green cover, turn valve clockwise with water key (in custodian's closet).", False, ""),
        ("jefferson", "fire_suppression", "Sprinkler control — utility room behind cafeteria", 1, "cafeteria",
         "Do NOT shut off unless fire department instructs. Red wheel valve.", False, ""),
    ]
    for fac, utype, loc, floor, zone, instructions, req_key, key_loc in utilities:
        kb._conn.execute(
            """INSERT OR REPLACE INTO utility_controls
               (facility_id, utility_type, location_description, floor, zone_id,
                shutoff_instructions, requires_key, key_location)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (fac, utype, loc, floor, zone, instructions, int(req_key), key_loc),
        )
    kb._conn.commit()

    # === HAZMAT (Science Lab) ===
    hazmat = [
        ("jefferson", "Hydrochloric Acid (dilute)", "Corrosive", "Room 215 Science Lab, chemical cabinet", 2, "west-wing-f2",
         "500mL bottles x3", "SDS binder on lab desk", "Neutralize with baking soda. Flush with water. Ventilate room."),
        ("jefferson", "Isopropyl Alcohol", "Flammable", "Room 215 Science Lab, chemical cabinet", 2, "west-wing-f2",
         "1L bottles x2", "SDS binder on lab desk", "Keep away from ignition sources. Ventilate. Absorb spill with sand."),
        ("jefferson", "Acetone", "Flammable", "Room 215 Science Lab, flammable storage cabinet (yellow)", 2, "west-wing-f2",
         "500mL bottle x1", "SDS binder on lab desk", "Do NOT use water. Absorb with vermiculite. Ventilate."),
        ("jefferson", "Natural Gas", "Flammable", "Cafeteria kitchen — gas range and ovens", 1, "cafeteria",
         "Piped supply", "N/A", "Shut off yellow valve in utility room. Evacuate. Do NOT use electrical switches."),
    ]
    for fac, name, hclass, loc, floor, zone, qty, sds, contain in hazmat:
        kb._conn.execute(
            """INSERT INTO hazmat_locations
               (facility_id, material_name, hazard_class, location_description, floor, zone_id,
                quantity, sds_location, containment_instructions)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (fac, name, hclass, loc, floor, zone, qty, sds, contain),
        )
    kb._conn.commit()

    # === NEARBY EMERGENCY SERVICES ===
    services = [
        ("hospital", "Vanderbilt University Medical Center", "1211 Medical Center Dr, Nashville, TN 37232",
         "615-322-5000", 3.2, 8, "Level I", True),
        ("hospital", "TriStar Centennial Medical Center", "2300 Patterson St, Nashville, TN 37203",
         "615-342-1000", 1.8, 5, "Level II", False),
        ("trauma_center", "Vanderbilt Children's Hospital", "2200 Children's Way, Nashville, TN 37232",
         "615-936-1000", 3.4, 9, "Level I Pediatric", True),
        ("police_station", "Metro Nashville Police - Central Precinct", "601 Korean Veterans Blvd",
         "615-862-8600", 1.5, 4, "", False),
        ("fire_station", "Nashville Fire Station 9", "1000 2nd Ave S",
         "615-862-5421", 0.8, 3, "", False),
        ("urgent_care", "Vanderbilt Health Walk-In Clinic", "1801 West End Ave",
         "615-322-3000", 1.2, 4, "", False),
    ]
    for stype, name, addr, phone, dist, eta, trauma, heli in services:
        kb._conn.execute(
            """INSERT INTO nearby_services
               (service_type, name, address, phone, distance_miles, eta_minutes, trauma_level, helipad)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (stype, name, addr, phone, dist, eta, trauma, int(heli)),
        )
    kb._conn.commit()

    # === DRILL HISTORY ===
    drills = [
        ("jefferson", "fire", "2026-05-15", 272, 310, 420, "east-wing-f2",
         "Room 204 (Mrs. Thompson) took 1:45 due to elevator wait. East stairwell bottleneck at F2."),
        ("jefferson", "fire", "2026-03-10", 248, 285, 415, "library",
         "Library students initially went wrong direction. Need clearer signage."),
        ("jefferson", "active-threat", "2026-04-22", 45, 180, 430, "cafeteria",
         "Lockdown achieved in 45 sec. Full accountability took 3 min. Cafeteria doors need auto-lock retrofit."),
        ("jefferson", "earthquake", "2026-02-05", 0, 420, 410, "east-wing-f1",
         "Drop/cover/hold compliance was good. Post-shaking evacuation took 7 min. Need utility shutoff training for staff."),
    ]
    for fac, dtype, date, evac, acct, part, slowest, issues in drills:
        kb.add_drill(dtype, date, evac, acct, part, slowest, issues, fac)

    # === CONTINUITY PLAN ===
    kb._conn.execute(
        """INSERT INTO continuity_plans
           (scenario_type, plan_name, trigger_conditions, actions, remote_work_capable,
            backup_facility, critical_functions, recovery_time_objective_hours)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        ("active-threat", "Active Threat Recovery Plan",
         "Any confirmed active threat on campus",
         '["Initiate lockdown immediately", "Call 911 — provide school address and threat details", "Activate parent notification system (SchoolMessenger)", "Establish reunification at First Baptist Church (1300 Oak St)", "Coordinate with Metro Nashville PD on scene", "Activate crisis counseling team within 2 hours of all-clear", "Send parent reunification instructions via SchoolMessenger and social media"]',
         False,
         "First Baptist Church, 1300 Oak Street — reunification and temporary operations",
         '["Student safety and accountability", "Parent communication and reunification", "Crisis counseling", "Law enforcement coordination"]',
         2),
    )
    kb._conn.commit()

    # Print summary
    summary = kb.get_facility_summary()
    print("\nJefferson Elementary School loaded successfully!")
    print(f"  Facilities: {summary['facilities']}")
    print(f"  Zones: {summary['zones']}")
    print(f"  Rooms: {summary['rooms']}")
    print(f"  Personnel: {summary['personnel']}")
    print(f"    - First Aid trained: {summary['first_aid_trained']}")
    print(f"    - CPR trained: {summary['cpr_trained']}")
    print(f"    - Mobility limited: {summary['mobility_limited']}")
    print(f"    - Floor Wardens: {summary['floor_wardens']}")
    print(f"  Emergency Resources: {summary['emergency_resources']}")
    print(f"  Evacuation Routes: {summary['evacuation_routes']}")
    print(f"  Assembly Points: {summary['assembly_points']}")
    print(f"  Utility Controls: {summary['utility_controls']}")
    print(f"  Hazmat Locations: {summary['hazmat_locations']}")
    print(f"  Nearby Services: {summary['nearby_services']}")
    print(f"  Drills Recorded: {summary['drills_recorded']}")
    print(f"  Continuity Plans: {summary['continuity_plans']}")


if __name__ == "__main__":
    load()
