# rlhf-worldcup-2026 🏆

An AI-powered FIFA World Cup 2026 chatbot built with **RLHF** (Reinforcement Learning from Human Feedback), **Llama 3.3 70B** via Groq, and a Flask web interface.

---

## What it does

Ask any question about the 2026 World Cup — groups, teams, players, stadiums, format — and get expert AI analysis. Every response can be rated 👍 or 👎, and the model adapts its behavior based on your feedback.

---

## Architecture

```
rlhf-worldcup-2026/
├── data/
│   ├── __init__.py
│   ├── world_cup_factuals.py   ← 48 teams, 12 groups, WC knowledge
│   └── feedback_manager.py     ← read/write rlhf_feedback.json
├── ml/
│   ├── __init__.py
│   ├── config.py               ← hyperparameters
│   ├── dataset_loader.py       ← builds preference pairs from data/
│   ├── train_reward_model.py   ← trains reward model on 👍👎 feedback
│   └── train_ppo.py            ← PPO fine-tuning loop
├── web/
│   ├── app.py                  ← Flask server + Groq API + RLHF loop
│   ├── templates/
│   │   └── index.html          ← chat interface
│   └── static/
│       ├── css/style.css       ← dark glass UI
│       └── js/app.js           ← chat logic + feedback buttons
├── .env.example                ← API key template
├── .gitignore
├── requirements.txt
└── rlhf_feedback.json          ← user feedback (auto-generated)
```

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| LLM | Llama 3.3 70B via Groq API |
| Backend | Flask (Python) |
| RLHF | TRL — RewardTrainer + PPO |
| Active Learning | modAL + scikit-learn |
| Frontend | HTML + CSS + Vanilla JS |
| Data | 48 teams · 12 groups · WC 2026 facts |

---

## How RLHF Works Here

```
1. User asks a question
         ↓
2. Llama 3.3 70B generates answer (using data/ as context)
         ↓
3. User clicks 👍 or 👎
         ↓
4. Feedback saved to rlhf_feedback.json
         ↓
5. Next Groq call reads feedback → adjusts system prompt
         ↓
6. run train_reward_model.py → reward model trained on feedback
         ↓
7. Model keeps improving with each interaction
```

---

## Quick Start

### 1. Clone the repo
```bash
git clone https://github.com/your-username/rlhf-worldcup-2026.git
cd rlhf-worldcup-2026
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Add your Groq API key
```bash
cp .env.example .env
# Edit .env and add your key: GROQ_API_KEY=gsk_...
# Get a free key at: https://console.groq.com
```

### 4. Run the chatbot
```bash
python web/app.py
```

### 5. Open in browser
```
http://localhost:5000
```

---

## RLHF Training (Optional)

After collecting feedback through the interface:

```bash
# Train reward model on your 👍👎 feedback
python ml/train_reward_model.py

# PPO fine-tuning
python ml/train_ppo.py
```

---

## Example Questions

```
"Groupe C"                              → Brazil, Morocco, Haiti, Scotland
"Analyse la France"                     → Full France profile + AI analysis
"Qui sont les favoris pour 2026 ?"      → Tournament favorites
"Explique le format de la Coupe du Monde 2026"
"Quels sont les stades ?"
"Compare le Brésil et l'Argentine"
```

---

## Dataset

All team and group data is hardcoded in `data/world_cup_factuals.py`:
- 48 teams with FIFA rank, coach, key players, play style, fun facts
- 12 group narratives
- 30+ general World Cup 2026 facts

No external datasets required to run the chatbot.

---

## Requirements

```
Python 3.9+
Groq API key (free at console.groq.com)
Internet connection (for Groq API calls)
```

---

## Project Context

Built as part of a course on **Reinforcement Learning from Human Feedback (RLHF)**, applying concepts including:
- Preference datasets (chosen vs rejected responses)
- Reward model training with TRL
- PPO fine-tuning
- Active Learning with uncertainty sampling
- Human feedback loops in production systems
