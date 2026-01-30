import os
import json
import requests
from openai import OpenAI
from dotenv import load_dotenv

# Chargement de la clé OpenAI depuis .env
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# URL de l'API backend
BASE_URL = "https://backend-production-3740d.up.railway.app"

# Récupération des événements
def get_all_events():
    try:
        response = requests.get(f"{BASE_URL}/events/")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}

# Récupération des mentorats
def get_all_mentoring():
    try:
        response = requests.get(f"{BASE_URL}/mentoring/")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}

# Récupération des utilisateurs (étudiants)
def get_all_users():
    try:
        response = requests.get(f"{BASE_URL}/users/")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}
    
# Récupération des salles 
def get_all_classrooms():
    try:
        response = requests.get(f"{BASE_URL}/classrooms/")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}

# récupération des affluences    
def get_affluence_overview():
    try:
        response = requests.get(f"{BASE_URL}/presences/analytics/overview")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        return {"error": str(e)}

    

# Assistant GPT avec toutes les données disponibles
def ask_gpt_with_context(question):
    events = get_all_events()
    mentoring = get_all_mentoring()
    users = get_all_users()
    classrooms = get_all_classrooms()
    affluence = get_affluence_overview()
    if "error" in affluence:
        return f"Erreur API affluence : {affluence['error']}"
    if "error" in events:
        return f"Erreur API événements : {events['error']}"
    if "error" in mentoring:
        return f"Erreur API mentoring : {mentoring['error']}"
    if "error" in users:
        return f"Erreur API utilisateurs : {users['error']}"
    if "error" in classrooms:
        return f"Erreur API salles : {classrooms['error']}"

    # Résumé des événements
    event_list = [
        f"- {e['title']} ({e['date_start']} → {e['date_end']}) à {e['place']} | Catégorie : {e['category']}"
        for e in events
    ]
    event_context = "\n".join(event_list)

    # Résumé des mentorings
    mentoring_list = [
        f"- Sujet : {m['subject']}, Description : {m['description']}, Mentor : {m['mentor']['name']} ({m['mentor']['level']})"
        for m in mentoring
    ]
    mentoring_context = "\n".join(mentoring_list)

    # Résumé des étudiants
    users_list = [
        f"- {u['name']} (niveau : {u['level']}, email : {u['email']})"
        for u in users
    ]
    users_context = "\n".join(users_list)

    # Résumé des salles de classe
    classrooms_list = [
        f"- {c['name']} (capacité : {c['capacity']})"
        for c in classrooms
    ]
    classrooms_context = "\n".join(classrooms_list)

    # Résumé global
    stats = affluence["statistics"]
    overview_summary = (
        f"Présences totales : {stats['total_presences']}, "
        f"Absences : {stats['total_absences']}, "
        f"Taux de présence global : {stats['presence_rate']}%."
    )

    # Résumé journalier
    daily = "\n".join([
        f"- {entry['date']} : {entry['count']} présences" 
        for entry in affluence["daily_affluence"]
    ])

    # Résumé par salle
    affluence_by_salle = "\n".join([
        f"- {salle['classroom_name']} : {salle['presence_count']} présents / capacité {salle['capacity']} "
        f"({salle['occupancy_percentage']}% d’occupation)"
        for salle in affluence.get("classroom_affluence", [])
    ])
    # Construction du prompt complet

    full_context = f"""
Liste des événements :
{event_context}

Liste des mentorats :
{mentoring_context}

Liste des étudiants :
{users_context}

Liste des salles :
{classrooms_context}

Statistiques globales d'affluence :
{overview_summary}

Présence quotidienne :
{daily}

Affluence par salle :
{affluence_by_salle}
"""

    messages = [
        {
            "role": "system",
            "content": (
                "Tu es un assistant universitaire. Tu as accès aux événements, mentorats, salles et étudiants. "
                "Réponds uniquement en utilisant les informations fournies, en français clair et concis."
            )
        },
        {
            "role": "user",
            "content": f"{full_context}\n\nQuestion : {question}"
        }
    ]

    response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=messages,
        temperature=0.3,
        max_tokens=700
    )

    return response.choices[0].message.content.strip()

# Interface console
if __name__ == "__main__":
    print("Ton e-Assistant ")

    while True:
        question = input("\nPose ta question (ou 'exit') : ")
        if question.lower() in ["exit", "quit"]:
            print("Fermeture de l'assistant.")
            break

        try:
            response = ask_gpt_with_context(question)
            print("\nRéponse :", response)
        except Exception as e:
            print("\nErreur :", str(e))
