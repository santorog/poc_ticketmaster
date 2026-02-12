# Plan : Profil utilisateur et recommandations personnalisees

## Probleme actuel

Le pipeline actuel est "aveugle" : la requete utilisateur est vectorisee telle quelle et comparee aux evenements. Aucun contexte personnel n'est pris en compte — un fan de rock et un fan de jazz obtiennent les memes resultats pour "concert a Paris".

## Approche retenue : Hybride (enrichissement query + contexte LLM)

```
Profil YAML → enrichit la requete FAISS (meilleur recall)
                                          ↓
User Query + Profil → FAISS (top_k ajuste selon openness) → candidats
                                          ↓
Candidats + Profil + Query → GPT (ranking personalise) → recommandation
```

**Pourquoi hybride ?**
- Enrichir la requete FAISS permet de remonter des events proches des gouts de l'utilisateur
- Passer le profil au LLM permet un ranking intelligent (le LLM comprend "ouvert d'esprit" mieux que FAISS)
- Le parametre `openness` controle la balance : 0 = strictement mes gouts, 1 = decouverte totale

## Fichiers a creer/modifier

### 1. `data/user_profile.py` — nouveau
- Dataclass `UserProfile` : name, city, preferred_genres, preferred_cities, openness (0.0-1.0)
- `load(path)` : charge depuis un fichier YAML
- `to_search_text()` : texte injecte dans la requete FAISS pour biaiser la recherche semantique vers les preferences
- `to_prompt_context()` : bloc de contexte injecte dans le prompt GPT

### 2. `profiles/default.yaml` — nouveau
- Exemple de profil utilisateur pre-rempli

### 3. `rag/rag_engine.py` — modifier
- `generate_response(query, profile=None)`
- Si profil present : construire une requete enrichie pour FAISS, ajuster top_k selon openness
- Passer le profil au LLM pour le ranking final

### 4. `llm/llm_client.py` — modifier
- `generate_suggestion(query, events, profile=None)`
- Si profil : ajouter un bloc "Profil de l'utilisateur" dans le prompt avec ses gouts, sa ville, son niveau d'ouverture
- Adapter l'instruction : "privilegie ses gouts mais propose aussi des decouvertes selon son ouverture d'esprit"

### 5. `app.py` — modifier
- Charger le profil au demarrage (`--profile profiles/default.yaml`)
- Passer le profil a travers tout le pipeline

### 6. `requirements.txt` — ajouter `pyyaml`

## Format du profil (`profiles/default.yaml`)

```yaml
name: "Santiago"
city: "Paris"
preferred_genres:
  - Rock
  - Jazz
  - Chanson Francaise
preferred_cities:
  - Paris
  - Bordeaux
  - Lyon
openness: 0.7  # 0.0 = strict, 1.0 = tres ouvert
```

## Comment `openness` affecte le pipeline

| openness | Requete FAISS | top_k | Comportement LLM |
|----------|---------------|-------|-------------------|
| 0.0 | Fortement enrichie avec les genres/villes preferes | 5 | "Recommande uniquement dans ses gouts" |
| 0.5 | Legerement enrichie | 10 | "Privilegie ses gouts mais propose 1 decouverte" |
| 1.0 | Requete brute (pas d'enrichissement) | 15 | "Propose un maximum de diversite et de decouverte" |

## Ce qui n'est PAS dans ce plan (iterations futures)

- Historique des evenements avec avis (necessite un flow de feedback)
- Enrichissement des descriptions d'evenements via GPT
- Filtre par distance geographique
- Multi-utilisateurs
