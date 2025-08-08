# legal_prompts_langchain.py
from langchain.prompts import PromptTemplate

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

def get_reformulate_query_prompt(original_query: str) -> str:
    return f"""
Reformule cette question juridique pour améliorer la recherche dans une base documentaire.

IMPORTANT : 
- Conserve le sens original
- Utilise la même langue que la question
- Ajoute des termes juridiques précis si nécessaire

QUESTION ORIGINALE: {original_query}

Réponds uniquement avec la requête reformulée.
"""

def get_search_expander_prompt(original_query: str) -> str:
    return f"""
Génère 3 requêtes alternatives pour cette question juridique.

IMPORTANT : 
- Utilise la même langue que la question originale
- Varie les angles d'approche
- Inclus des termes juridiques connexes

QUESTION: {original_query}

Format : Une requête par ligne, numérotée.
"""

def get_answer_synthesizer_prompt(question: str, context_str: str, history_str: str, lang: str = "auto") -> str:
    return f"""
Tu es un expert juridique qui répond à des questions avec précision et professionnalisme.

=== CONSIGNES OBLIGATOIRES ===
1. LANGUE :
   - Réponds dans la même langue que la question

2. STRUCTURE :
   - Structure en points numérotés
   - Sois concis mais complet
   - Reste strictement dans le domaine juridique

3. SOURCES :
   - Format EXACT : [NOM COMPLET DU DOCUMENT, NUMÉRO DE PAGE PRÉCIS]

4. PRÉCISION :
   - Sois concis mais complet
   - Uniquement des informations vérifiables dans le contexte fourni
   - Pas de paraphrases approximatives

=== RÈGLES DE SORTIE ===
1. Cette réponse est définitive.
2. Ne pose pas de nouvelle question dans la réponse.
3. Termine impérativement par :
   Final Answer: <ta réponse complète ici>

=== CONTEXTE DOCUMENTAIRE ===
{context_str}

=== QUESTION ===
{question}

=== HISTORIQUE ===
{history_str if history_str else "Aucun historique"}

=== RÉPONSE ATTENDUE ===
Donne la réponse finale selon les règles ci-dessus.
"""

def get_no_context_found_prompt(question: str, lang: str = "auto") -> str:
    return f"""
L'utilisateur a posé une question mais aucun document pertinent n'a été trouvé.

Question : "{question}"

Réponds dans la même langue que la question :
1. Explique poliment qu'aucune information n'a été trouvée
2. Suggeste de reformuler la question
3. Propose éventuellement des pistes de recherche
"""

def get_react_agent_prompt() -> PromptTemplate:
    """Prompt principal pour l'agent ReAct corrigé et format-safe"""
    template = (
        "Tu es un assistant juridique expert utilisant le framework ReAct. "
        "Suis scrupuleusement ces instructions :\n\n"
        "Outils disponibles :\n"
        "{tools}\n\n"
        "Noms des outils : {tool_names}\n\n"
        "Instructions IMPÉRATIVES :\n"
        "1. Format des actions :\n"
        "   - Pour utiliser un outil, ÉCRIS EXACTEMENT ceci :\n"
        "Action: nom_de_l_outil\n"
        "Action Input: \"entrée\"\n"
        "   - Ne modifie pas ce format\n"
        "   - Ne mets rien d'autre dans l'action\n\n"
        "2. Processus de raisonnement :\n"
        "   - Analyse la langue de la question (réponds dans la même langue)\n"
        "   - Identifie si c'est une question juridique ou une interaction sociale\n"
        "   - Pour les questions juridiques :\n"
        "     * Utilise d'abord 'query_reformulator' si besoin\n"
        "     * Puis 'document_search' pour trouver des sources\n"
        "     * Enfin 'answer_synthesizer' pour construire la réponse\n"
        "   - Pour les salutations/remerciements : Réponse courte et courtoise\n\n"
        "3. Règles de réponse :\n"
        "   - Structure en points numérotés\n"
        "   - Cite EXACTEMENT les sources [NOM COMPLET du document, NUMÉRO DE PAGE PRÉCIS]\n"
        "   - Sois concis mais complet\n"
        "   - Reste strictement dans le domaine juridique\n\n"
        "Historique conversationnel :\n"
        "{chat_history}\n\n"
        "Input actuel : {input}\n\n"
        "Processus de raisonnement (Thought/Action/Observation) :\n"
        "{agent_scratchpad}"
    )

    return PromptTemplate(
        template=template,
        input_variables=["tools", "tool_names", "input", "agent_scratchpad", "chat_history"]
    )

