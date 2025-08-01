
def get_title_prompt(text_chunk: str) -> str:
    return f"""Donne un seul titre clair, court et précis qui résume ce texte juridique suivant.

Texte :
{text_chunk}

Titre :"""

def get_split_prompt(text: str) -> str:
    return f"""Découpe ce texte juridique en plusieurs sections de taille raisonnable,
en respectant les paragraphes. Utilise ce séparateur :
=== Section ===

Texte :
{text}
"""
def get_base_chat_prompt(question: str, context_str: str, history_str: str, lang: str) -> str:
    lang_instruction = {
        "fr": "IMPORTANT : Réponds uniquement en français.",
        "en": "IMPORTANT: Answer only in English."
    }.get(lang, "IMPORTANT: Answer in the same language as the question.")

    return f"""{lang_instruction}

Tu es un assistant juridique intelligent et conversationnel, semblable à ChatGPT.

Tu peux répondre en français ou en anglais selon la langue de la question.

{history_str}

Ta mission est de répondre **avec clarté, politesse et précision**, comme un expert juridique.

En te basant **uniquement sur les extraits ci-dessous**, réponds à la question. Si les extraits sont insuffisants, indique-le avec bienveillance.

Ta réponse doit :
- Être bien structurée, **numérotée sans sauter de points**
- Citer une **source (page + document)** pour chaque fait
- Employer un ton clair, professionnel, direct

### Question :
{question}

### Contexte :
{context_str}

### Réponse :
"""

def get_enrichment_notes(question: str, context_concat: str, lang: str) -> str:
    LEGAL_KEYWORDS = [
        "article", "loi", "circulaire", "chapitre", "service",
        "établissement", "disposition", "règlementation"
    ]
    ACCESS_KEYWORDS = [
        "accès minimum", "droit d'accès", "compte gratuit",
        "ouverture obligatoire", "exclusion bancaire", "accès aux services bancaires"
    ]

    enrichissements = []
    if len(context_concat) < 300:
        enrichissements.append("Ajoute plus d'explications juridiques." if lang == 'fr' else "Add more legal explanation.")
    if not any(kw in context_concat for kw in LEGAL_KEYWORDS):
        enrichissements.append("Utilise un vocabulaire juridique adapté." if lang == 'fr' else "Use legal vocabulary (e.g. law, article, regulation).")
    if any(m in question.lower() for m in ACCESS_KEYWORDS) and not any(m in context_concat for m in ACCESS_KEYWORDS):
        enrichissements.append("Mentionne l'accès aux services bancaires si pertinent." if lang == 'fr' else "Mention access to banking services if relevant.")
    if enrichissements:
        return "\n\n" + "\n".join(f"NOTE : {e}" for e in enrichissements)
    return ""
