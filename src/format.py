# Ai generated

import json
from google import genai
# from huggingface_hub import InferenceClient

# ===== CONFIG =====
SR = 16000                                 # sample rate from body.py
MODEL_SIZE = "base"                        # tiny / base / small / medium / large-v3
DEVICE = "cpu"                             # or "cuda" if GPU is available
COMPUTE_TYPE = "int8"                      # "float16"/"int8_float16"/"int8" etc.

# ==== Kb and LLM ==== 

# ---------------------------------------------------------
# 0) Load Knowledge Base 
# ---------------------------------------------------------
with open("kb.json") as f:
    faq_data = json.load(f)

client = genai.Client()

# ---------------------------------------------------------
# 1) Slightly improved intent classification
# ---------------------------------------------------------
def classify_intent(query):
    q = query.lower()

    # who queries → faculty/contact lookup
    if any(w in q for w in ["who is", "faculty", "professor", "prof", "contact", "email"]):
        return "contact"

    # where / location navigation queries
    if any(w in q for w in ["where is", "locate", "find", "location", "room", "lab"]):
        return "directory"

    # greeting
    if any(word in q for word in ["hello", "hi", "hey"]):
        return "greeting"

    # closing
    if "thank" in q or "bye" in q:
        return "close"

    # hours / timing
    if any(w in q for w in ["open", "close", "when", "hours"]):
        return "hours"

    return "out_of_scope"

# ---------------------------------------------------------
# 2) Utility: fuzzy match helper (broader matching)
# ---------------------------------------------------------
def fuzzy_match(q, text):
    """Loose fuzzy matching for names, rooms, labs."""
    q = q.lower()
    text = text.lower()
    return q in text or text in q or any(w in text for w in q.split())

# ---------------------------------------------------------
# 3) Improved directory lookup (rooms + labs together)
# ---------------------------------------------------------
def lookup_directory(query):
    q = query.lower()
    candidates = []

    # rooms
    for room_id, info in faq_data.get("rooms", {}).items():
        entry_text = f"{room_id} {info['name']} {info['location']}"
        if fuzzy_match(q, entry_text):
            candidates.append(f"{info['name']} is located at {info['location']}.")

    # labs
    for lab_id, info in faq_data.get("labs", {}).items():
        entry_text = f"{lab_id} {info['name']} {info['location']}"
        if fuzzy_match(q, entry_text):
            candidates.append(f"{info['name']} is located at {info['location']}.")

    # If multiple → LLM chooses the best one
    if candidates:
        return " ".join(candidates)

    return None

# ---------------------------------------------------------
# 4) Improved contact lookup (fuzzy on name + office + email)
# ---------------------------------------------------------
def lookup_contact(query):
    q = query.lower()
    candidates = []

    for cid, info in faq_data.get("contacts", {}).items():
        entry_text = f"{info['name']} {info['email']} {info['office']}"
        if fuzzy_match(q, entry_text):
            candidates.append(
                f"{info['name']} sits in {info['office']}. Email: {info['email']}."
            )

    if candidates:
        return " ".join(candidates)

    return None


# ---------------------------------------------------------
# 5) Hours unchanged but slightly more flexible
# ---------------------------------------------------------
def lookup_hours(query):
    q = query.lower()
    for place, hours in faq_data.get("hours", {}).items():
        if place in q:
            return f"The {place} is open {hours}."
    return None


# ---------------------------------------------------------
# 6) Updated LLM formatter (now supports out-of-scope free replies)
# ---------------------------------------------------------
def format_reply(intent, lookup_result=None, user_query=None):

    # Normal KB-backed replies
    if intent != "out_of_scope" and lookup_result:
        prompt = (
            f"User asked about {intent}. Info: {lookup_result}. "
            f"Reply politely in one natural sentence using ONLY the info given."
        )
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"You are NAO, the receptionist robot. {prompt}"
        )
        return response.text

    # OUT OF SCOPE — NEW LOGIC
    if intent == "out_of_scope":
        # Provide the KB context to restrict hallucinations
        kb_context = json.dumps({
            "rooms": list(faq_data["rooms"].values()),
            "labs": list(faq_data["labs"].values()),
            "contacts": list(faq_data["contacts"].values()),
            "hours": faq_data["hours"],
        })

        prompt = (
            "You are NAO, the receptionist robot at IIIT-Delhi. "
            "The user asked something outside the strict FAQ categories. "
            "Respond politely and helpfully using general knowledge of a receptionist, "
            "but DO NOT invent specific factual details that are not present in the building KB.\n\n"
            f"Building Knowledge Base:\n{kb_context}\n\n"
            f"User Query: {user_query}\n"
            "Provide a friendly, short receptionist-style response."
        )

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        return response.text

    # If no lookup result for in-scope queries
    return "Sorry, I don’t know that. Please ask about rooms, labs, faculty, contacts, or hours."

# ---------------------------------------------------------
# 7) Final combined pipeline
# ---------------------------------------------------------
def plan_reply(q: str):

    if q.lower() in ["quit", "exit"]:
        return q

    intent = classify_intent(q)

    if intent == "greeting":
        reply = format_reply("greeting", "Hello! Welcome to IIIT Delhi.")
        return reply, intent

    elif intent == "close":
        reply = format_reply("End Conversation", "Goodbye! Ask again if you need anything.")
        return reply, intent

    elif intent == "directory":
        result = lookup_directory(q)
        reply = format_reply("directory", result)
        return reply, intent

    elif intent == "hours":
        result = lookup_hours(q)
        reply = format_reply("hours", result)
        return reply, intent

    elif intent == "contact":
        result = lookup_contact(q)
        reply = format_reply("contact", result)
        return reply, intent

    # NEW: Out-of-scope → LLM general receptionist reply
    else:
        reply = format_reply("out_of_scope", user_query=q)
        return reply, intent
