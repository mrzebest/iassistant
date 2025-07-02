import os
import requests
import json
from openai import OpenAI
from dotenv import load_dotenv

# Charger la clé API depuis le fichier .env
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# URL du backend EasyCampus
BASE_URL = "https://backend-production-ecb4.up.railway.app"

# Fonctions API
def get_all_events():
    return requests.get(f"{BASE_URL}/events/").json()

def get_all_mentoring():
    return requests.get(f"{BASE_URL}/mentoring/").json()

def get_all_users():
    return requests.get(f"{BASE_URL}/users/").json()

def get_all_classrooms():
    return requests.get(f"{BASE_URL}/classrooms/").json()

def get_affluence_overview():
    return requests.get(f"{BASE_URL}/presences/analytics/overview").json()

# Fonction principale appelée par app.py
def ask_gpt_with_context(question: str) -> str:
    try:
        events = get_all_events()
        mentoring = get_all_mentoring()
        users = get_all_users()
        classrooms = get_all_classrooms()
        affluence = get_affluence_overview()
    except Exception as e:
        return f"Erreur lors de la récupération des données : {str(e)}"

    # Événements
    event_context = "\n".join([
        f"- {e['title']} ({e['date_start']} → {e['date_end']}) à {e['place']} | Catégorie : {e['category']}"
        for e in events
    ])

    # Mentoring
    mentoring_context = "\n".join([
        f"- Sujet : {m['subject']}, Description : {m['description']}, Mentor : {m['mentor']['name']} ({m['mentor']['level']})"
        for m in mentoring
    ])

    # Étudiants
    users_context = "\n".join([
        f"- {u['name']} ({u['email']}, niveau : {u['level']})"
        for u in users
    ])

    # Salles
    classrooms_context = "\n".join([
        f"- {c['name']} (capacité : {c['capacity']})"
        for c in classrooms
    ])

    # Affluence (overview)
    stats = affluence["statistics"]
    overview_summary = (
        f"Présences totales : {stats['total_presences']}, "
        f"absences : {stats['total_absences']}, "
        f"taux de présence global : {stats['presence_rate']}%."
    )

    daily = "\n".join([
        f"- {d['date']} : {d['count']} présences"
        for d in affluence.get("daily_affluence", [])
    ])

    by_salle = "\n".join([
        f"- {salle['classroom_name']} : {salle['presence_count']} présents "
        f"(capacité : {salle['capacity']}, {salle['occupancy_percentage']}% d’occupation)"
        for salle in affluence.get("classroom_affluence", [])
    ])

    # Contexte complet donné à GPT
    prompt = f"""
Événements :
{event_context}

Mentoring :
{mentoring_context}

Étudiants :
{users_context}

Salles :
{classrooms_context}

Affluence :
{overview_summary}

Présence quotidienne :
{daily}

Présence par salle :
{by_salle}

Question : {question}
"""

    # Appel à OpenAI
    response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=[
            {"role": "system", "content": "Tu es un assistant universitaire francophone. Réponds de façon claire et concise en français, uniquement en utilisant les données fournies."},
            {"role": "user", "content": prompt}
        ],
        temperature=0.3,
        max_tokens=700
    )

    return response.choices[0].message.content.strip()
