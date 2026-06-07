import os
import sys
import re
import json
import time
from flask import Flask, request, jsonify, render_template, Response

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from data import GROUPS, TEAM_INFO, GROUP_NARRATIVES, WC_KNOWLEDGE, load_feedback, save_feedback

GROQ_API_KEY = "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"

try:
    from groq import Groq
    groq_client = Groq(api_key=GROQ_API_KEY)
    groq_client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": "ping"}],
        max_tokens=5
    )
    GROQ_READY = True
    print("[OK] Groq connecte - llama-3.3-70b-versatile pret")
except Exception as e:
    groq_client = None
    GROQ_READY = False
    print(f"[!!] Groq non disponible : {e}")

app = Flask(__name__, template_folder='templates', static_folder='static')
app.config['JSON_AS_ASCII'] = False

def get_rlhf_system_prompt():
    try:
        feedback = load_feedback()
        neg = sum(1 for f in feedback if f.get("score") == 0)
        pos = sum(1 for f in feedback if f.get("score") == 1)
        rlhf_note = ""
        if neg > 3:
            rlhf_note = f"\nRLHF: {neg} reponses mal notees - sois plus precis et complet."
        elif pos > 3:
            rlhf_note = f"\nRLHF: {pos} reponses bien notees - continue dans ce style."
    except Exception:
        rlhf_note = ""
    return (
        "Tu es un expert analyste FIFA World Cup 2026, alimente par llama-3.3-70b-versatile + RLHF.\n"
        "REGLES:\n"
        "- Reponds en francais (ou dans la langue de l utilisateur)\n"
        "- Sois precis, passionne, expert football\n"
        "- Utilise exclusivement les donnees fournies\n"
        f"- Format de reponse fluide, sans markdown complexe.{rlhf_note}"
    )

def search_local_context(query):
    query_clean = query.lower()
    m = re.search(r"groupe\s+([a-l])", query_clean)
    if m:
        letter = m.group(1).upper()
        teams = GROUPS.get(letter, [])
        narrative = GROUP_NARRATIVES.get(letter, "")
        txt = f"Donnees Officielles Groupe {letter} :\nEquipes : {', '.join(teams)}\nContexte : {narrative}\n\nDetail des equipes :\n"
        for t in teams:
            info = TEAM_INFO.get(t, {})
            txt += f"- {t} ({info.get('flag','')}) : Rang FIFA {info.get('fifa_rank')}, Selectionneur {info.get('coach')}, Style {info.get('play_style')}\n"
        return txt, "group", letter
    for team_name, info in TEAM_INFO.items():
        if team_name.lower() in query_clean:
            txt = f"Fiche Equipe : {team_name} {info.get('flag','')}\n" \
                  f"- Rang FIFA : {info.get('fifa_rank')}\n" \
                  f"- Participations : {info.get('wc_appearances')}\n" \
                  f"- Meilleur resultat : {info.get('best_result')}\n" \
                  f"- Selectionneur : {info.get('coach')}\n" \
                  f"- Joueurs cles : {', '.join(info.get('key_players',[]))}\n" \
                  f"- Style de jeu : {info.get('play_style')}\n" \
                  f"- Anecdote : {info.get('fun_fact')}\n"
            return txt, "team", team_name
    found_facts = []
    for k, v in WC_KNOWLEDGE.items():
        if k in query_clean or any(word in query_clean for word in k.split("_")):
            found_facts.append(v)
    if found_facts:
        return "Faits generaux Coupe du Monde 2026 :\n" + "\n".join(found_facts), "factual", "general"
    return "Donnees generales : " + " | ".join(list(WC_KNOWLEDGE.values())[:5]), "fallback", "all"

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/groups", methods=["GET"])
def get_groups():
    return jsonify(GROUPS)

@app.route("/api/model-status", methods=["GET"])
def status():
    samples = load_feedback()
    return Response(
        json.dumps({
            "loaded": GROQ_READY,
            "status": "ready" if GROQ_READY else "offline",
            "model": "llama-3.3-70b-versatile",
            "provider": "Groq",
            "rlhf_samples": len(samples)
        }, ensure_ascii=True),
        content_type="application/json; charset=utf-8"
    )

@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.get_json() or {}
    user_msg = data.get("message", "").strip()
    if not user_msg:
        return jsonify({"answer": "Message vide."})
    context_txt, context_type, context_id = search_local_context(user_msg)
    if not GROQ_READY:
        clean_ans = f"Mode Factuel Local (Groq non configure) :\n\n{context_txt}"
        return jsonify({
            "answer": clean_ans,
            "context_type": context_type,
            "context_id": context_id,
            "raw_data": context_txt
        })
    try:
        sys_prompt = get_rlhf_system_prompt()
        prompt_with_ctx = f"CONTEXTE OFFICIEL DISPONIBLE :\n{context_txt}\n\nQUESTION UTILISATEUR : {user_msg}"
        completion = groq_client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": prompt_with_ctx}
            ],
            temperature=0.3,
            max_tokens=800
        )
        ans = completion.choices[0].message.content
        return jsonify({
            "answer": ans,
            "context_type": context_type,
            "context_id": context_id,
            "raw_data": context_txt
        })
    except Exception as e:
        fallback_ans = f"Erreur API Groq ({e}). Retour factuel :\n\n{context_txt}"
        return jsonify({
            "answer": fallback_ans,
            "context_type": context_type,
            "context_id": context_id,
            "raw_data": context_txt
        })

@app.route("/api/feedback", methods=["POST"])
def feedback():
    try:
        data = request.get_json()
        entry = {
            "timestamp": time.time(),
            "question": data.get("question", ""),
            "answer": data.get("answer", ""),
            "score": data.get("score", 1),
            "comment": data.get("comment", "")
        }
        save_feedback(entry)
        fb = load_feedback()
        total = len(fb)
        pos = sum(1 for f in fb if f.get("score") == 1)
        return jsonify({
            "status": "saved",
            "total_feedback": total,
            "positive_rate": round(pos / total * 100, 1) if total else 0
        })
    except Exception as e:
        print(f"[feedback route error] {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    print("\n" + "="*55)
    print("  FIFA World Cup 2026 - AI Chatbot")
    print("  Model  : llama-3.3-70b-versatile (Groq)")
    print("="*55)
    app.run(host="0.0.0.0", port=5000, debug=True)
