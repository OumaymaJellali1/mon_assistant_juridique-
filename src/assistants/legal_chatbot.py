
from langdetect import detect
import time
import re
import string
from difflib import SequenceMatcher
from google.generativeai import GenerativeModel
from src.config import settings
from src.prompts.legal_prompts import get_base_chat_prompt
from src.qdrant.qdrant_client import QdrantClientWrapper
from src.qdrant.embed_model import model
from src.qdrant.qdrant import DocumentRetriever  

from google import generativeai as genai
genai.configure(api_key=settings.GEMINI_API_KEY)


class LegalChatbot:
    def __init__(self):
        self.llm = GenerativeModel(settings.GEMMA_MODEL)
        qdrant_wrapper = QdrantClientWrapper()   
        self.qdrant = DocumentRetriever(qdrant_client=qdrant_wrapper, embedder=model)


        self.conversation_history = []

        self.LEGAL_KEYWORDS = [
            "article", "loi", "circulaire", "chapitre", "service",
            "établissement", "disposition", "règlementation"
        ]
        self.ACCESS_KEYWORDS = [
            "accès minimum", "droit d'accès", "compte gratuit",
            "ouverture obligatoire", "exclusion bancaire", "accès aux services bancaires"
        ]
        self.SALUTATIONS = [
            "bonjour", "bonsoir", "salut", "hello", "hi", "yo", "bonj", "slt", "bjr",
            "bon matin", "bonne journée"
        ]
        self.REMERCIEMENTS = [
            "merci", "thanks", "thank you", "thx", "je vous remercie", "merci beaucoup",
            "merci infiniment", "grand merci", "c’est gentil"
        ]
        self.AU_REVOIR = [
            "au revoir", "bye", "a bientôt", "ciao", "à la prochaine", "à plus",
            "bonne soirée", "bonne journée", "fin de la session", "exit", "quit"
        ]

    def count_tokens(self, text):
        return len(text) // 4

    def detect_intention(self, text, expressions, seuil=0.75):
        mots = re.findall(r'\w+', text.lower())
        for mot in mots:
            if any(SequenceMatcher(None, mot, expr).ratio() > seuil for expr in expressions):
                return True
        for expr in expressions:
            if expr in text.lower():
                return True
        return False

    def filtrer_doublons_fuzzy(self, text, seuil=0.6):
        points = re.split(r'\n(?=\d+\.)', text.strip())
        uniques, contenus = [], []
        for point in points:
            contenu = re.sub(r'^\d+\.\s*', '', point).strip().lower()
            contenu = contenu.translate(str.maketrans('', '', string.punctuation))
            if any(SequenceMatcher(None, contenu, c).ratio() > seuil for c in contenus):
                continue
            contenus.append(contenu)
            uniques.append(point.strip())
        return '\n'.join(uniques)

    def enrichir_prompt_si_pertinent(self, question, contexts, prompt):
        try:
            langue = detect(question)
        except:
            langue = 'fr'
        texte_concatene = " ".join([ctx.get('Article', '') or ctx.get('titre_gemma', '') for ctx in contexts]).lower()
        enrichissements = []
        if len(texte_concatene) < 300:
            enrichissements.append("Ajoute plus d'explications juridiques." if langue == 'fr' else "Add more legal explanation.")
        if not any(kw in texte_concatene for kw in self.LEGAL_KEYWORDS):
            enrichissements.append("Utilise un vocabulaire juridique adapté." if langue == 'fr' else "Use legal vocabulary.")
        if any(m in question.lower() for m in self.ACCESS_KEYWORDS) and not any(m in texte_concatene for m in self.ACCESS_KEYWORDS):
            enrichissements.append("Mentionne l'accès aux services bancaires." if langue == 'fr' else "Mention banking access.")
        if enrichissements:
            prompt += "\n\n" + "\n".join(f"NOTE : {e}" for e in enrichissements)
        return prompt

    def build_prompt_with_history(self, question, contexts):
        try:
            lang = detect(question)
        except:
            lang = 'fr'

        context_texts = []
        total_tokens = 0
        for ctx in contexts:
            page = ctx.get('page', 'N/A')
            pdf = ctx.get('pdf', 'source inconnue')
            titre = ctx.get('titre_gemma') or ctx.get('Titre') or "Titre non spécifié"
            texte = ctx.get('Article') or " ".join(filter(None, [ctx.get('titre_gemma'), ctx.get('Loi'), ctx.get('Chapitre')]))
            bloc = f"- (Page {page}, Doc: {pdf}) {titre}\n{texte}"
            bloc_tokens = self.count_tokens(bloc)
            if total_tokens + bloc_tokens > settings.MAX_PROMPT_TOKENS:
                break
            context_texts.append(bloc)
            total_tokens += bloc_tokens

        context_str = "\n\n".join(context_texts)
        if not context_str.strip():
            context_str = "Aucun extrait pertinent trouvé." if lang == "fr" else "No relevant excerpt found."

        history_entries = []
        for i, turn in enumerate(self.conversation_history[-5:]):
            q = turn.get("question", "")
            a = turn.get("answer", "")
            if a:
                history_entries.append(f"Q{i+1}: {q}\nA{i+1}: {a}")
            else:
                history_entries.append(f"Q{i+1}: {q}")
        history_str = ""
        if history_entries:
            history_str = ("Historique des échanges :\n" if lang == "fr" else "Conversation history:\n") + "\n\n".join(history_entries)

        prompt = get_base_chat_prompt(question, context_str, history_str, lang)
        return self.enrichir_prompt_si_pertinent(question, contexts, prompt)

    def score_response(self, text):
        return {
            "length_ok": len(text) >= 150,
            "keywords_ok": any(kw in text.lower() for kw in self.LEGAL_KEYWORDS),
            "structure_ok": len(re.findall(r'^\d+\.', text, re.MULTILINE)) >= 2,
            "context_ok": not bool(re.search(r'aucune information|impossible de répondre|je ne sais pas|not enough', text.lower()))
        }

    def generate_answer(self, question, contexts, max_attempts=4):
        prompt = self.build_prompt_with_history(question, contexts)
        for attempt in range(max_attempts):
            print(f"\n=== Tentative {attempt + 1} ===")
            response = self.llm.generate_content(prompt).text.strip()
            response = self.filtrer_doublons_fuzzy(response)
            response = re.sub(r"Page\s*-?1\s*,", "Document :", response, flags=re.IGNORECASE)
            response = re.sub(r"\(Page\s*-?1\s*,", "(Document :", response, flags=re.IGNORECASE)
            response = re.sub(r"^(Voici la réponse.*?extraits fournis\.?)\s*", "", response, flags=re.I | re.DOTALL)

            if all(self.score_response(response).values()):
                return response

            try:
                lang = detect(question)
            except:
                lang = 'fr'
            prompt += "\n\n" + ("Ajoute plus de détails." if lang == 'fr' else "Add more legal details.")
            time.sleep(1)
        return "1. Désolé, les extraits ne permettent pas de répondre."

    def run(self):
        print("Assistant juridique démarré. Tapez 'exit' pour quitter.")
        while True:
            question = input("\nPose ta question juridique : ").strip()
            if not question:
                print("Veuillez saisir une question non vide.")
                continue

            try:
                question_lang = detect(question)
            except:
                question_lang = 'fr'

            if self.detect_intention(question, self.SALUTATIONS):
                print("Bonjour ! Comment puis-je vous aider ?")
                continue
            if self.detect_intention(question, self.REMERCIEMENTS):
                print("Avec plaisir ! N'hésitez pas à poser d'autres questions.")
                continue
            if self.detect_intention(question, self.AU_REVOIR, seuil=0.95):
                print("Fin de la session. Au revoir !")
                break

            contexts = self.qdrant.retrieve_documents(question)
            print("DEBUG - Contextes extraits :")
            for c in contexts:
                print(f"- (Page {c.get('page')}, Doc {c.get('pdf')}) {c.get('titre_gemma') or c.get('Titre')}")

            self.conversation_history.append({"question": question, "answer": None})

            answer = self.generate_answer(question, contexts)
            self.conversation_history[-1]["answer"] = answer

            with open("derniere_reponse.txt", "w", encoding="utf-8") as f:
                f.write(answer)

            print("\nRéponse générée :\n")
            print(answer)


