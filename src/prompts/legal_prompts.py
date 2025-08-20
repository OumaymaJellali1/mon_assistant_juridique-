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
# === NOUVEAUX PROMPTS EXTRACTÉS ===

def get_detection_prompt(question: str) -> str:
    return f"""Analyze this user message and classify it into ONE category:

GREETING: "Hello", "Good morning", "Bonjour", "Hi", "Hey", "Salut", etc.
THANKS: "Thank you", "Thanks", "Merci", "Thx", etc.  
LEGAL_QUESTION: Any request for legal information, advice, clarification, or documents
OTHER: Everything else (small talk, unclear messages)

User message: "{question}"

Respond with ONLY the category name: GREETING, THANKS, LEGAL_QUESTION, or OTHER"""

def get_simple_response_prompt(message_type: str, question: str) -> str:
    return f"""The user sent a {message_type} message: "{question}"

Generate an appropriate, brief, and friendly response:

- If GREETING: Welcome them warmly and offer legal assistance in their language
- If THANKS: Acknowledge politely and invite more questions in their language  
- If OTHER: Redirect politely to legal topics

Detect the user's language (French, English, Arabic, etc.) and respond in the SAME language.
Keep it brief (2-3 sentences maximum) and professional."""

def get_reformulation_prompt(query: str, previous_attempts: list = None) -> str:
    previous_attempts = previous_attempts or []
    
    context_info = ""
    if previous_attempts:
        context_info = f"\n\nTentatives précédentes à éviter:\n" + "\n".join(f"- {attempt}" for attempt in previous_attempts)
    
    return f"""Tu es un expert en recherche juridique. Reformule cette question pour améliorer la recherche documentaire.

INSTRUCTIONS:
- Utilise des termes juridiques précis et variés
- Préserve le sens exact de la question
- Réponds dans la même langue que la question
- Propose une approche différente des tentatives précédentes{context_info}

QUESTION ORIGINALE: {query}

Réponds uniquement avec UNE reformulation optimale."""

def get_synthesis_prompt(question: str, context: str, sources: list = None) -> str:
    sources = sources or []
    
    sources_info = ""
    if sources:
        sources_info = "\n\n=== INFORMATIONS SUR LES SOURCES ===\n"
        for i, source in enumerate(sources, 1):
            sources_info += f"{i}. {source.get('source', 'Inconnu')} (Page {source.get('page', 'N/A')}) - Qualité: {source.get('quality', 0):.2f}\n"
    
    return f"""Expert legal assistant.

CRITICAL INSTRUCTION - READ FIRST:
DETECT the user's query language and respond in EXACTLY that same language.
Examples: User writes in english → You respond in english | French → You respond in French | User writes in Arabic → You respond in Arabic 
This applies to EVERY word of your response. NO mixing languages.

LANGUAGE MATCHING:
1. First, identify the query language
2. Respond 100% in that detected language
3. Use appropriate legal terminology for that language
4. Maintain professional tone in that language

MESSAGE TYPES:
• Greeting → Polite response + offer help (SAME LANGUAGE AS GREETING)
• Thanks → Acknowledgment + availability (SAME LANGUAGE AS THANKS)
• Farewell → Polite closure + signal continued availability (SAME LANGUAGE AS FAREWELL)
• Legal question → Complete structured response (SAME LANGUAGE AS QUESTION)
• Other → Redirect to legal topics (SAME LANGUAGE AS MESSAGE)

LEGAL RESPONSE STRUCTURE:
1. **Main Response** (no inline citations)
2. **Important Clarifications**
3. **Special Cases** (if applicable)
**Conclusion:** [Summary + limitations]
**Sources:** [Document.pdf, Page XX]

RULES:
- Response based ONLY on provided context
- Citations ONLY at end of response
- Professional tone adapted to language
- Signal limitations/nuances
- If insufficient context: clearly mention it
- Never use external knowledge outside of the provided documents.

QUESTION: {question}
CONTEXT: {context}
{sources_info}

RESPONSE:"""

# Templates de prompts pour réutilisation
DETECTION_PROMPT_TEMPLATE = PromptTemplate(
    input_variables=["question"],
    template="""Analyze this user message and classify it into ONE category:

GREETING: "Hello", "Good morning", "Bonjour", "Hi", "Hey", "Salut", etc.
THANKS: "Thank you", "Thanks", "Merci", "Thx", etc.  
LEGAL_QUESTION: Any request for legal information, advice, clarification, or documents
OTHER: Everything else (small talk, unclear messages)

User message: "{question}"

Respond with ONLY the category name: GREETING, THANKS, LEGAL_QUESTION, or OTHER"""
)

SIMPLE_RESPONSE_TEMPLATE = PromptTemplate(
    input_variables=["message_type", "question"],
    template="""The user sent a {message_type} message: "{question}"

Generate an appropriate, brief, and friendly response:

- If GREETING: Welcome them warmly and offer legal assistance in their language
- If THANKS: Acknowledge politely and invite more questions in their language  
- If OTHER: Redirect politely to legal topics

Detect the user's language (French, English, Arabic, etc.) and respond in the SAME language.
Keep it brief (2-3 sentences maximum) and professional."""
)

REFORMULATION_TEMPLATE = PromptTemplate(
    input_variables=["query", "previous_attempts"],
    template="""Tu es un expert en recherche juridique. Reformule cette question pour améliorer la recherche documentaire.

INSTRUCTIONS:
- Utilise des termes juridiques précis et variés
- Préserve le sens exact de la question
- Réponds dans la même langue que la question
- Propose une approche différente des tentatives précédentes{previous_attempts}

QUESTION ORIGINALE: {query}

Réponds uniquement avec UNE reformulation optimale."""
)

SYNTHESIS_TEMPLATE = PromptTemplate(
    input_variables=["question", "context", "sources_info"],
    template="""Expert legal assistant.

CRITICAL INSTRUCTION - READ FIRST:
DETECT the user's query language and respond in EXACTLY that same language.
Examples: User writes in english → You respond in english | French → You respond in French | User writes in Arabic → You respond in Arabic 
This applies to EVERY word of your response. NO mixing languages.

LANGUAGE MATCHING:
1. First, identify the query language
2. Respond 100% in that detected language
3. Use appropriate legal terminology for that language
4. Maintain professional tone in that language

MESSAGE TYPES:
• Greeting → Polite response + offer help (SAME LANGUAGE AS GREETING)
• Thanks → Acknowledgment + availability (SAME LANGUAGE AS THANKS)
• Farewell → Polite closure + signal continued availability (SAME LANGUAGE AS FAREWELL)
• Legal question → Complete structured response (SAME LANGUAGE AS QUESTION)
• Other → Redirect to legal topics (SAME LANGUAGE AS MESSAGE)

LEGAL RESPONSE STRUCTURE:
1. **Main Response** (no inline citations)
2. **Important Clarifications**
3. **Special Cases** (if applicable)
**Conclusion:** [Summary + limitations]
**Sources:** [Document.pdf, Page XX]

RULES:
- Response based ONLY on provided context
- Citations ONLY at end of response
- Professional tone adapted to language
- Signal limitations/nuances
- If insufficient context: clearly mention it
- Never use external knowledge outside of the provided documents.

QUESTION: {question}
CONTEXT: {context}
{sources_info}

RESPONSE:"""
)
