# legal_chatbot_langchain.py
import re
from typing import Any, Optional
from enum import Enum
from pydantic import Field

from langchain.agents import AgentExecutor, create_react_agent
from langchain.tools import BaseTool
from langchain.prompts import PromptTemplate
from langchain.memory import ConversationBufferWindowMemory
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.callbacks.manager import CallbackManagerForToolRun
from src.qdrant.qdrant_client import QdrantClientWrapper
from src.qdrant.qdrant import DocumentRetriever
from src.config import settings
from src.prompts.legal_prompts import (
    get_reformulate_query_prompt,
    get_search_expander_prompt,
    get_answer_synthesizer_prompt,
    get_react_agent_prompt
)

class DocumentSearchTool(BaseTool):
    name: str = "document_search"
    description: str = """Recherche des documents juridiques pertinents pour répondre à une question.
    Entrée: question ou requête de recherche (string)
    Sortie: liste de documents pertinents avec métadonnées"""
    document_retriever: DocumentRetriever = Field(exclude=True)
    chatbot: Any = Field(exclude=True, default=None)
    
    def _run(self, query: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        try:
            documents = self.document_retriever.retrieve_documents(query, top_k=10)
            if not documents:
                return "Aucun document pertinent trouvé."
            
            result = []
            for i, doc in enumerate(documents):
                metadata = doc.metadata
                result.append(f"Document {i+1}:")
                result.append(f"Source: {metadata.get('source', 'inconnue')}")
                result.append(f"Titre: {metadata.get('titre_gemma', 'Non spécifié')}")
                result.append(f"Contenu: {doc.page_content[:500]}...")
                result.append(f"Page: {metadata.get('page_number', 'N/A')}")
                result.append("---")
            
            search_results = "\n".join(result)
            
            if self.chatbot:
                self.chatbot.last_search_results = search_results
            
            return search_results
        except Exception as e:
            return f"Erreur de recherche: {str(e)}"

class QueryReformulatorTool(BaseTool):
    name: str = "query_reformulator"
    description: str = """Reformule une question juridique pour améliorer la recherche.
    Entrée: question originale (string)
    Sortie: question reformulée (string)"""
    llm: Any = Field(exclude=True)
    
    def _run(self, query: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        try:
            prompt = get_reformulate_query_prompt(query)
            response = self.llm.invoke(prompt)
            return response.content.strip()
        except Exception as e:
            return f"Erreur de reformulation: {str(e)}"

class SearchExpanderTool(BaseTool):
    name: str = "search_expander"
    description: str = """Génère des requêtes alternatives pour une question juridique.
    Entrée: question originale (string)
    Sortie: liste de requêtes alternatives"""
    llm: Any = Field(exclude=True)
    
    def _run(self, query: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        try:
            prompt = get_search_expander_prompt(query)
            response = self.llm.invoke(prompt)
            return response.content.strip()
        except Exception as e:
            return f"Erreur d'expansion: {str(e)}"

class AnswerSynthesizerTool(BaseTool):
    name: str = "answer_synthesizer"
    description: str = """Synthétise une réponse finale basée sur une question et le contexte documentaire trouvé.
    Entrée: La question à traiter (l'outil récupérera automatiquement le contexte des documents)
    Sortie: réponse structurée et citée"""
    llm: Any = Field(exclude=True)
    chatbot: Any = Field(exclude=True)
    
    def _run(self, question: str, run_manager: Optional[CallbackManagerForToolRun] = None) -> str:
        try:
            context = self._get_recent_context()
            history = self._get_history()
            
            prompt = get_answer_synthesizer_prompt(question, context, history, "auto")
            response = self.llm.invoke(prompt)
            
            return self.chatbot._clean_response(response.content.strip())
        except Exception as e:
            return f"Erreur de synthèse: {str(e)}"
    
    def _get_recent_context(self) -> str:
        """Récupère le contexte des documents trouvés récemment"""
        if hasattr(self.chatbot, 'last_search_results') and self.chatbot.last_search_results:
            return self.chatbot.last_search_results
        return "Aucun contexte documentaire disponible."
    
    def _get_history(self) -> str:
        if not hasattr(self.chatbot, 'conversation_history'):
            return ""
        history = self.chatbot.conversation_history[-3:]
        return "\n".join(f"Q: {q}\nA: {a}" for q, a in history if a)

class AgenticLegalChatbot:
    def __init__(self):
        # Initialisation du LLM
        self.llm = ChatGoogleGenerativeAI(
            model=settings.GEMMA_MODEL,
            google_api_key=settings.GEMINI_API_KEY,
            temperature=0.1
        )
        
        # Initialisation du client Qdrant
        self.qdrant_client = QdrantClientWrapper()
        self.embedder = settings.EMBEDDING_MODEL
        
        # Initialisation du retriever
        self.document_retriever = DocumentRetriever(
            qdrant_client=self.qdrant_client,
            embedder=self.embedder
        )
        
        # Configuration de la mémoire
        self.memory = ConversationBufferWindowMemory(
            memory_key="chat_history",
            k=5,
            return_messages=True,
            input_key="input"  
        )
        
        self.conversation_history = []
        self.last_search_results = ""  # Pour stocker les derniers résultats de recherche
        
        # Création des outils
        self.tools = [
            DocumentSearchTool(document_retriever=self.document_retriever, chatbot=self),
            QueryReformulatorTool(llm=self.llm),
            SearchExpanderTool(llm=self.llm),
            AnswerSynthesizerTool(llm=self.llm, chatbot=self)
        ]
        
        # Préparation du prompt avec les tool_names
        base_prompt = get_react_agent_prompt()
        tool_names = ", ".join([tool.name for tool in self.tools])
        final_prompt = base_prompt.partial(tool_names=tool_names)
        
        # Création de l'agent
        self.agent = create_react_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=final_prompt
        )
        
        # Création de l'exécuteur
        self.agent_executor = AgentExecutor(
        agent=self.agent,
        tools=self.tools,
        memory=self.memory,
        verbose=True,
        max_iterations=10,  
        early_stopping_method="generate",  
        handle_parsing_errors=True,
        return_intermediate_steps=True  
)

    def _clean_response(self, response: str) -> str:
        # Remplacer "Page -1" par juste le nom du document
        response = re.sub(r"Page\s*-1", "Document", response)
        # Garder "Page X" pour les autres numéros (ex: "Page 42" → "Page 42")
        response = re.sub(r"Document\s*(\d+)", r"Page \1", response)
        return response.strip()

    def process_question(self, question: str) -> str:
        try:
            # Réinitialiser les résultats de recherche
            self.last_search_results = ""
            
            result = self.agent_executor.invoke({"input": question})
            answer = self._clean_response(result["output"])
            self.conversation_history.append((question, answer))
            return answer
        except Exception as e:
            error_msg = f"Erreur: {str(e)}"
            self.conversation_history.append((question, error_msg))
            return error_msg

    def run(self):
        print("Assistant juridique prêt. Tapez 'exit' pour quitter.")
        while True:
            question = input("\nQuestion: ").strip()
            if question.lower() in ('exit', 'quit'):
                break
            if not question:
                continue
                
            response = self.process_question(question)
            print(f"\nRéponse:\n{response}")