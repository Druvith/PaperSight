"""Populate GemmaSight database with realistic test data for demos.

Usage:
    PYTHONPATH=src uv run python scripts/populate_db.py
"""

import sys
sys.path.insert(0, "src")

from gemmasight.database import init_db, insert_patient

# Realistic patient records covering all priority levels and common rural presentations
PATIENTS = [
    {
        "extracted": {
            "patient_name": "Ramesh Iyer",
            "age": "67",
            "gender": "Male",
            "chief_complaint": "chest-pain radiating to left arm",
            "duration": "15 minutes",
            "allergies": "None known",
            "medications": "Aspirin 75mg",
            "referred_by": "Ambulance",
        },
        "triage": {
            "priority": "red",
            "priority_label": "Immediate",
            "wait_time": "0 min",
            "action": "See now — life-threatening",
            "matched_rules": ["R01"],
            "matched_descriptions": ["Chest pain — possible cardiac emergency"],
            "escalated": False,
            "escalation_reason": "",
        },
    },
    {
        "extracted": {
            "patient_name": "Anil Kumar",
            "age": "54",
            "gender": "Male",
            "chief_complaint": "difficulty-breathing",
            "duration": "2 hours",
            "allergies": "None",
            "medications": "Salbutamol inhaler",
            "referred_by": "ASHA worker",
        },
        "triage": {
            "priority": "red",
            "priority_label": "Immediate",
            "wait_time": "0 min",
            "action": "See now — life-threatening",
            "matched_rules": ["R02"],
            "matched_descriptions": ["Respiratory distress — possible airway compromise"],
            "escalated": False,
            "escalation_reason": "",
        },
    },
    {
        "extracted": {
            "patient_name": "Leela Nair",
            "age": "29",
            "gender": "Female",
            "chief_complaint": "severe-headache and neck stiffness",
            "duration": "1 day",
            "allergies": "None",
            "medications": "Paracetamol",
            "referred_by": "Self",
        },
        "triage": {
            "priority": "red",
            "priority_label": "Immediate",
            "wait_time": "0 min",
            "action": "See now — life-threatening",
            "matched_rules": ["R08"],
            "matched_descriptions": ["Severe headache with neck stiffness — possible meningitis"],
            "escalated": False,
            "escalation_reason": "",
        },
    },
    {
        "extracted": {
            "patient_name": "Maya Raman",
            "age": "43",
            "gender": "Female",
            "chief_complaint": "high-fever and chills",
            "duration": "3 days",
            "allergies": "Penicillin",
            "medications": "Metformin",
            "referred_by": "ASHA worker",
        },
        "triage": {
            "priority": "yellow",
            "priority_label": "Priority",
            "wait_time": "< 30 min",
            "action": "See soon — serious",
            "matched_rules": ["Y01"],
            "matched_descriptions": ["Fever — possible sepsis, malaria, or typhoid"],
            "escalated": False,
            "escalation_reason": "",
        },
    },
    {
        "extracted": {
            "patient_name": "Sara Dsouza",
            "age": "8",
            "gender": "Female",
            "chief_complaint": "vomiting and abdominal-pain",
            "duration": "6 hours",
            "allergies": "None",
            "medications": "ORS sachets",
            "referred_by": "Mother",
        },
        "triage": {
            "priority": "yellow",
            "priority_label": "Priority",
            "wait_time": "< 30 min",
            "action": "See soon — serious",
            "matched_rules": ["Y02"],
            "matched_descriptions": [
                "Vomiting — dehydration and electrolyte risk",
            ],
            "escalated": False,
            "escalation_reason": "",
        },
    },
    {
        "extracted": {
            "patient_name": "Suresh Patel",
            "age": "58",
            "gender": "Male",
            "chief_complaint": "fall from ladder, leg pain",
            "duration": "30 minutes",
            "allergies": "None",
            "medications": "Amlodipine",
            "referred_by": "Coworker",
        },
        "triage": {
            "priority": "red",
            "priority_label": "Immediate",
            "wait_time": "0 min",
            "action": "See now — life-threatening",
            "matched_rules": ["R12"],
            "matched_descriptions": ["Major trauma — fracture or crush injury"],
            "escalated": False,
            "escalation_reason": "",
        },
    },
    {
        "extracted": {
            "patient_name": "Meena Kumari",
            "age": "72",
            "gender": "Female",
            "chief_complaint": "fall and hip-pain",
            "duration": "3 hours",
            "allergies": "None known",
            "medications": "Calcium supplements",
            "referred_by": "Family member",
        },
        "triage": {
            "priority": "red",
            "priority_label": "Immediate",
            "wait_time": "0 min",
            "action": "See now — life-threatening",
            "matched_rules": ["R13"],
            "matched_descriptions": ["Fall in elderly patient — high risk for hip fracture or intracranial bleed"],
            "escalated": False,
            "escalation_reason": "",
        },
    },
    {
        "extracted": {
            "patient_name": "Sunita Rao",
            "age": "26",
            "gender": "Female",
            "chief_complaint": "abdominal-pain and bleeding during pregnancy",
            "duration": "1 hour",
            "allergies": "None",
            "medications": "Iron tablets",
            "referred_by": "ANM",
        },
        "triage": {
            "priority": "red",
            "priority_label": "Immediate",
            "wait_time": "0 min",
            "action": "See now — life-threatening",
            "matched_rules": ["R11"],
            "matched_descriptions": ["Obstetric emergency — maternal and fetal risk"],
            "escalated": False,
            "escalation_reason": "",
        },
    },
    {
        "extracted": {
            "patient_name": "Lakshmi Devi",
            "age": "34",
            "gender": "Female",
            "chief_complaint": "high-fever and severe-headache",
            "duration": "2 days",
            "allergies": "Sulfa drugs",
            "medications": "Paracetamol",
            "referred_by": "ASHA worker",
        },
        "triage": {
            "priority": "yellow",
            "priority_label": "Priority",
            "wait_time": "< 30 min",
            "action": "See soon — serious",
            "matched_rules": ["Y01"],
            "matched_descriptions": ["Fever — possible sepsis, malaria, or typhoid"],
            "escalated": False,
            "escalation_reason": "",
        },
    },
    {
        "extracted": {
            "patient_name": "Aarav Sharma",
            "age": "4",
            "gender": "Male",
            "chief_complaint": "cough and fever",
            "duration": "5 days",
            "allergies": "None",
            "medications": "Vitamin D drops",
            "referred_by": "Mother",
        },
        "triage": {
            "priority": "red",
            "priority_label": "Immediate",
            "wait_time": "0 min",
            "action": "See now — life-threatening",
            "matched_rules": ["Y04", "Y01"],
            "matched_descriptions": [
                "Persistent cough — possible pneumonia or TB",
                "Fever — possible sepsis, malaria, or typhoid",
            ],
            "escalated": True,
            "escalation_reason": "Pediatric escalation (age 4 < 5)",
        },
    },
    {
        "extracted": {
            "patient_name": "Rajesh Gupta",
            "age": "45",
            "gender": "Male",
            "chief_complaint": "wound on hand, bleeding",
            "duration": "20 minutes",
            "allergies": "None",
            "medications": "None",
            "referred_by": "Self",
        },
        "triage": {
            "priority": "yellow",
            "priority_label": "Priority",
            "wait_time": "< 30 min",
            "action": "See soon — serious",
            "matched_rules": ["Y06"],
            "matched_descriptions": ["Minor trauma — wound, sprain, or soft tissue injury"],
            "escalated": False,
            "escalation_reason": "",
        },
    },
    {
        "extracted": {
            "patient_name": "Fatima Begum",
            "age": "62",
            "gender": "Female",
            "chief_complaint": "diarrhea and vomiting",
            "duration": "1 day",
            "allergies": "None",
            "medications": "ORS",
            "referred_by": "Daughter",
        },
        "triage": {
            "priority": "red",
            "priority_label": "Immediate",
            "wait_time": "0 min",
            "action": "See now — life-threatening",
            "matched_rules": ["Y03", "Y02"],
            "matched_descriptions": [
                "Diarrhea — dehydration and infectious cause",
                "Vomiting — dehydration and electrolyte risk",
            ],
            "escalated": True,
            "escalation_reason": "Elderly escalation (age 62 > 60)",
        },
    },
    {
        "extracted": {
            "patient_name": "Kavita Nair",
            "age": "19",
            "gender": "Female",
            "chief_complaint": "skin rash and itching",
            "duration": "2 days",
            "allergies": "Dust",
            "medications": "Cetirizine",
            "referred_by": "Self",
        },
        "triage": {
            "priority": "yellow",
            "priority_label": "Priority",
            "wait_time": "< 30 min",
            "action": "See soon — serious",
            "matched_rules": ["Y05"],
            "matched_descriptions": ["Rash — possible measles, dengue, or allergic reaction"],
            "escalated": False,
            "escalation_reason": "",
        },
    },
    {
        "extracted": {
            "patient_name": "Venkatesh Rao",
            "age": "35",
            "gender": "Male",
            "chief_complaint": "follow-up for diabetes",
            "duration": "N/A",
            "allergies": "None",
            "medications": "Metformin",
            "referred_by": "Dr. Patel",
        },
        "triage": {
            "priority": "green",
            "priority_label": "Non-urgent",
            "wait_time": "< 120 min",
            "action": "Queue — stable",
            "matched_rules": ["G01"],
            "matched_descriptions": ["Routine follow-up — stable chronic condition"],
            "escalated": False,
            "escalation_reason": "",
        },
    },
    {
        "extracted": {
            "patient_name": "Baby Priya",
            "age": "2",
            "gender": "Female",
            "chief_complaint": "minor cut on finger",
            "duration": "10 minutes",
            "allergies": "None",
            "medications": "None",
            "referred_by": "Mother",
        },
        "triage": {
            "priority": "yellow",
            "priority_label": "Priority",
            "wait_time": "< 30 min",
            "action": "See soon — serious",
            "matched_rules": ["G02"],
            "matched_descriptions": ["Minor superficial injury — no systemic concern"],
            "escalated": True,
            "escalation_reason": "Pediatric escalation (age 2 < 5)",
        },
    },
    {
        "extracted": {
            "patient_name": "Joseph Thomas",
            "age": "55",
            "gender": "Male",
            "chief_complaint": "prescription refill for BP medication",
            "duration": "N/A",
            "allergies": "None",
            "medications": "Amlodipine",
            "referred_by": "Self",
        },
        "triage": {
            "priority": "green",
            "priority_label": "Non-urgent",
            "wait_time": "< 120 min",
            "action": "Queue — stable",
            "matched_rules": ["G03"],
            "matched_descriptions": ["Medication refill — no acute complaint"],
            "escalated": False,
            "escalation_reason": "",
        },
    },
    {
        "extracted": {
            "patient_name": "Geeta Sharma",
            "age": "28",
            "gender": "Female",
            "chief_complaint": "eye pain and redness",
            "duration": "1 day",
            "allergies": "None",
            "medications": "None",
            "referred_by": "Self",
        },
        "triage": {
            "priority": "yellow",
            "priority_label": "Priority",
            "wait_time": "< 30 min",
            "action": "See soon — serious",
            "matched_rules": ["Y09"],
            "matched_descriptions": ["Eye complaint — possible infection, foreign body, or glaucoma"],
            "escalated": False,
            "escalation_reason": "",
        },
    },
]


def main():
    db = init_db()
    counts = {"red": 0, "yellow": 0, "green": 0, "blue": 0}

    for patient in PATIENTS:
        insert_patient(db, patient["extracted"], patient["triage"])
        counts[patient["triage"]["priority"]] += 1

    print("Database populated successfully!")
    print(f"  Red:      {counts['red']:>2} patients")
    print(f"  Yellow:   {counts['yellow']:>2} patients")
    print(f"  Green:    {counts['green']:>2} patients")
    print(f"  Blue:     {counts['blue']:>2} patients")
    print(f"  Total:    {sum(counts.values()):>2} patients")


if __name__ == "__main__":
    main()
