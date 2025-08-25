import re
import asyncio
from typing import Any, Dict, List, Tuple, TypedDict, Annotated, Optional
from datetime import datetime

from langgraph.graph import StateGraph, END, MessagesState
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI

        
from qdrant.qdrant_client import QdrantClientWrapper
from qdrant.qdrant import DocumentRetriever
from config import settings
from prompts.legal_prompts import (
    get_detection_prompt,
    get_simple_response_prompt,
    get_reformulation_prompt,
    get_synthesis_prompt,
   
)
import json
from datetime import datetime    
# === État étendu du graphe ===
class AdvancedAgentState(MessagesState):
    question: str
    search_results: str
    reformulated_queries: List[str]
    final_answer: str
    iteration_count: int
    documents_found: bool
    search_quality_score: float
    error_messages: List[str]
    processing_time: float
    confidence_score: float
    sources: List[Dict[str, str]]
    user_preferences: Dict[str, Any]


# === Outils avancés ===
class LegalToolBox:
    """Boîte à outils spécialisée pour le domaine juridique"""
    
    def __init__(self, llm, retriever):
        self.llm = llm
        self.retriever = retriever
    
    def smart_document_search(self, query: str) -> Dict[str, Any]:
        """Recherche intelligente avec scoring et filtrage"""
        try:
            # Recherche initiale
            documents = self.retriever.retrieve_documents(query, top_k=15)
            
            if not documents:
                return {
                    "success": False,
                    "results": "Aucun document pertinent trouvé.",
                    "score": 0.0,
                    "document_count": 0,
                    "sources": []
                }
            
            # Scoring et filtrage
            scored_docs = []
            sources = []
            
            for i, doc in enumerate(documents[:10]): 
                metadata = doc.metadata
                confidence = metadata.get('score', 0.0)
                
                # Calcul du score de qualité basé sur plusieurs facteurs
                quality_score = self._calculate_quality_score(doc, query)
                
                if quality_score > 0.3:  
                    scored_docs.append((doc, quality_score))
                    sources.append({
                        "source": metadata.get('source', 'inconnue'),
                        "page": metadata.get('page', 'N/A'),
                        "title": metadata.get('titre_gemma', ''),
                        "confidence": confidence,
                        "quality": quality_score
                    })
            
            # Tri par score de qualité
            scored_docs.sort(key=lambda x: x[1], reverse=True)
            
            # Formatage des résultats
            result_text = self._format_search_results(scored_docs[:8])
            
            overall_score = sum(score for _, score in scored_docs) / len(scored_docs) if scored_docs else 0.0
            
            return {
                "success": True,
                "results": result_text,
                "score": overall_score,
                "document_count": len(scored_docs),
                "sources": sources
            }
            
        except Exception as e:
            return {
                "success": False,
                "results": f"Erreur de recherche: {str(e)}",
                "score": 0.0,
                "document_count": 0,
                "sources": []
            }
    
    def _calculate_quality_score(self, doc, query: str) -> float:
        """Calcule un score de qualité pour un document"""
        content = doc.page_content.lower()
        query_lower = query.lower()
        query_terms = query_lower.split()
        
        # Facteurs de scoring
        term_matches = sum(1 for term in query_terms if term in content)
        term_ratio = term_matches / len(query_terms) if query_terms else 0
        
        # Bonus pour les éléments juridiques
        legal_bonus = 0
        legal_keywords = ['article', 'loi', 'décret', 'ordonnance', 'code', 'tribunal', 'jurisprudence']
        legal_bonus = sum(0.1 for keyword in legal_keywords if keyword in content)
        
        # Longueur du contenu (ni trop court ni trop long)
        length_score = 1.0
        if len(content) < 100:
            length_score = 0.5
        elif len(content) > 5000:
            length_score = 0.8
        
        # Score final
        final_score = min(1.0, term_ratio + legal_bonus + (length_score * 0.2))
        return final_score
    
    def _format_search_results(self, scored_docs: List[Tuple[Any, float]]) -> str:
        """Formate les résultats de recherche avec scores"""
        result = []
        
        for i, (doc, score) in enumerate(scored_docs):
            metadata = doc.metadata
            result.append(f"\n=== Document {i+1} (Score: {score:.2f}) ===")
            result.append(f"Source: {metadata.get('source', 'inconnue')}")
            result.append(f"Page: {metadata.get('page', 'N/A')}")
            
            # Hiérarchie juridique simplifiée
            hierarchy_parts = []
            for key in ['loi', 'titre', 'chapitre', 'article']:
                value = metadata.get(key, "")
                if value and value != "Non spécifié":
                    hierarchy_parts.append(f"{key.capitalize()}: {value}")
            
            if hierarchy_parts:
                result.append("Structure: " + " | ".join(hierarchy_parts))
            
            if metadata.get('titre_gemma'):
                result.append(f"Résumé: {metadata.get('titre_gemma')}")
            
            # Contenu adaptatif selon le score
            max_length = int(600 + (score * 400))  # Plus de contenu pour les meilleurs scores
            content = doc.page_content[:max_length]
            if len(doc.page_content) > max_length:
                content += "\n[...contenu adapté selon la pertinence...]"
            
            result.append(f"Contenu:\n{content}")
            result.append("---")
        
        return "\n".join(result)

    def intelligent_query_reformulator(self, query: str, previous_attempts: List[str] = None) -> Dict[str, Any]:
     """Reformulateur intelligent qui évite les répétitions"""
     try:
        previous_attempts = previous_attempts or []
        
        # Utilisation du prompt externe
        prompt = get_reformulation_prompt(query, previous_attempts)
        
        response = self.llm.invoke([HumanMessage(content=prompt)])
        reformulated = response.content.strip()
        
        # Validation que la reformulation est différente
        is_different = all(
            self._similarity_score(reformulated, prev) < 0.8 
            for prev in previous_attempts
        )
        
        return {
            "success": True,
            "reformulated_query": reformulated,
            "is_different": is_different,
            "confidence": 0.8 if is_different else 0.4
        }
        
     except Exception as e:
        return {
            "success": False,
            "reformulated_query": query,
            "is_different": False,
            "confidence": 0.0,
            "error": str(e)
        }
    
    def _similarity_score(self, text1: str, text2: str) -> float:
        """Calcule une similarité simple entre deux textes"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        if not words1 or not words2:
            return 0.0
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        return len(intersection) / len(union)

    def advanced_answer_synthesizer(self, question: str, context: str, sources: List[Dict] = None) -> Dict[str, Any]:
     """Synthétiseur de réponse avancé avec validation"""
     try:
        sources = sources or []
        
        # Utilisation du prompt externe
        prompt = get_synthesis_prompt(question, context, sources)
        print(f" prompt used {prompt}")
        response = self.llm.invoke([HumanMessage(content=prompt)])
        answer = response.content.strip()
        
        # Validation de la qualité de la réponse
        quality_metrics = self._evaluate_answer_quality(answer, context, question)
        
        return {
            "success": True,
            "answer": answer,
            "quality_metrics": quality_metrics,
            "confidence": quality_metrics.get("overall_confidence", 0.5),
            "sources_count": len(sources)
        }
        
     except Exception as e:
        return {
            "success": False,
            "answer": f"Erreur lors de la synthèse: {str(e)}",
            "quality_metrics": {},
            "confidence": 0.0,
            "sources_count": 0
        }

    
    def _evaluate_answer_quality(self, answer: str, context: str, question: str) -> Dict[str, float]:
        """Évalue la qualité d'une réponse"""
        metrics = {}
        
        # Longueur appropriée
        length_score = 1.0
        if len(answer) < 100:
            length_score = 0.5
        elif len(answer) > 3000:
            length_score = 0.8
        metrics["length_appropriateness"] = length_score
        
        # Présence de sources
        sources_mentioned = answer.count("[") + answer.count("Sources :")
        metrics["sources_inclusion"] = min(1.0, sources_mentioned / 3)
        
        # Structure (points numérotés)
        structure_score = 0.5
        if re.search(r'\d+\.', answer):  
            structure_score += 0.3
        if "Sources :" in answer: 
            structure_score += 0.2
        metrics["structure_quality"] = min(1.0, structure_score)
        
        question_terms = set(question.lower().split())
        answer_terms = set(answer.lower().split())
        relevance = len(question_terms.intersection(answer_terms)) / len(question_terms) if question_terms else 0
        metrics["relevance"] = relevance
        
        # Score global
        overall = sum(metrics.values()) / len(metrics)
        metrics["overall_confidence"] = overall
        
        return metrics


# === Graphe avancé ===
class AdvancedLegalChatbot:
    """Chatbot juridique avancé avec LangGraph"""
    
    def __init__(self):
        # LLM avec configuration optimisée
        self.llm = ChatGoogleGenerativeAI(
            model=settings.GEMMA_MODEL,
            google_api_key=settings.GEMINI_API_KEY,
            temperature=0.1,
            max_tokens=4000
        )
        
        # Retriever
        self.qdrant_client = QdrantClientWrapper()
        self.document_retriever = DocumentRetriever(
            qdrant_client=self.qdrant_client,
            embedder=settings.EMBEDDING_MODEL
        )
        
        # Boîte à outils
        self.toolbox = LegalToolBox(self.llm, self.document_retriever)
        
        # Historique enrichi
        self.conversation_history = []
        self.performance_metrics = []
        
        # Graphe avec checkpointing
        self.memory = MemorySaver()
        self.graph = self._build_advanced_graph()
    
    def _build_advanced_graph(self) -> StateGraph:
        """Construit le graphe avec décision LLM intelligente"""
        workflow = StateGraph(AdvancedAgentState)
        
        # Nœuds du workflow
        workflow.add_node("initialize", self._initialize_processing)
        workflow.add_node("detect_type", self._detect_message_type_with_llm)  
        workflow.add_node("generate_simple_response", self._generate_simple_response_node)  
        workflow.add_node("smart_search", self._smart_search_node)
        workflow.add_node("evaluate_results", self._evaluate_results_node)
        workflow.add_node("reformulate_intelligently", self._intelligent_reformulation_node)
        workflow.add_node("synthesize_advanced", self._advanced_synthesis_node)
        workflow.add_node("finalize_response", self._finalize_response_node)
        
        # Point d'entrée
        workflow.set_entry_point("initialize")
        
        workflow.add_edge("initialize", "detect_type")
        
        workflow.add_conditional_edges(
            "detect_type",
            self._decide_flow_after_detection,
            {
                "generate_simple_response": "generate_simple_response",
                "smart_search": "smart_search"
            }
        )
        
        # Flux pour réponses simples
        workflow.add_edge("generate_simple_response", END)
        
        workflow.add_edge("smart_search", "evaluate_results")
        
        workflow.add_conditional_edges(
            "evaluate_results",
            self._decide_next_action,
            {
                "reformulate": "reformulate_intelligently",
                "synthesize": "synthesize_advanced",
                "end_failure": END
            }
        )
        
        workflow.add_edge("reformulate_intelligently", "smart_search")
        workflow.add_edge("synthesize_advanced", "finalize_response")
        workflow.add_edge("finalize_response", END)
        
        return workflow.compile(checkpointer=self.memory)
    
    # === Nœuds du graphe ===
    
    def _initialize_processing(self, state: AdvancedAgentState) -> AdvancedAgentState:
        """Initialise le traitement avec timestamp et configuration"""
        start_time = datetime.now()
        
        return {
            **state,
            "processing_time": start_time.timestamp(),
            "iteration_count": 0,
            "reformulated_queries": [],
            "error_messages": [],
            "sources": [],
            "search_quality_score": 0.0,
            "confidence_score": 0.0,
            "user_preferences": {},
            "messages": state.get("messages", []) + [
                AIMessage(content="Initialisation du traitement...")
            ]
        }
    
    def _detect_message_type_with_llm(self, state: AdvancedAgentState) -> AdvancedAgentState:
     """Utilise le LLM pour détecter le type de message"""
     try:
        # Utilisation du prompt externe
        detection_prompt = get_detection_prompt(state['question'])
        
        response = self.llm.invoke([HumanMessage(content=detection_prompt)])
        message_type = response.content.strip().upper()
        
        # Validation de la réponse
        valid_types = ["GREETING", "THANKS", "LEGAL_QUESTION", "OTHER"]
        if message_type not in valid_types:
            message_type = "LEGAL_QUESTION" 
        
        print(f"Type de message détecté par LLM: {message_type}")
        
        return {
            **state,
            "user_preferences": {"message_type": message_type},
            "messages": state.get("messages", []) + [
                AIMessage(content=f"Type détecté: {message_type}")
            ]
        }
        
     except Exception as e:
        print(f"Erreur de détection: {str(e)}")
        return {
            **state,
            "user_preferences": {"message_type": "LEGAL_QUESTION"},
            "error_messages": state.get("error_messages", []) + [f"Erreur de détection: {str(e)}"]
        }

    def _decide_flow_after_detection(self, state: AdvancedAgentState) -> str:
        """Décide du flux basé sur le type détecté par le LLM"""
        message_type = state.get("user_preferences", {}).get("message_type", "LEGAL_QUESTION")
        
        print(f"Décision de flux pour type: {message_type}")
        
        if message_type in ["GREETING", "THANKS", "OTHER"]:
            return "generate_simple_response"
        else:
            return "smart_search"

    def _generate_simple_response_node(self, state: AdvancedAgentState) -> AdvancedAgentState:
     """Génère une réponse simple avec le LLM pour salutations/remerciements"""
     try:
        message_type = state.get("user_preferences", {}).get("message_type", "OTHER")
        
        # Utilisation du prompt externe
        simple_prompt = get_simple_response_prompt(message_type, state['question'])
        
        response = self.llm.invoke([HumanMessage(content=simple_prompt)])
        simple_answer = response.content.strip()
        
        print(f"Réponse simple générée pour {message_type}")
        
        return {
            **state,
            "final_answer": simple_answer,
            "confidence_score": 1.0,
            "processing_time": (datetime.now().timestamp() - 
                              state.get("processing_time", datetime.now().timestamp())),
            "sources": [],
            "messages": state.get("messages", []) + [
                AIMessage(content=f"Réponse simple générée")
            ]
        }
        
     except Exception as e:
        print(f"Erreur génération simple: {str(e)}")
        # Réponse par défaut en cas d'erreur
        default_response = "Hello! I'm your legal assistant. How can I help you with your legal questions today?\n\nBonjour ! Je suis votre assistant juridique. Comment puis-je vous aider ?"
        
        return {
            **state,
            "final_answer": default_response,
            "confidence_score": 0.5,
            "error_messages": state.get("error_messages", []) + [f"Erreur génération simple: {str(e)}"]
        }
    
    def _smart_search_node(self, state: AdvancedAgentState) -> AdvancedAgentState:
        """Recherche intelligente avec scoring"""
        print("Début de la recherche documentaire...")
        
        # Déterminer la requête à utiliser
        if state.get("reformulated_queries"):
            query = state["reformulated_queries"][-1]
            search_type = f"Recherche reformulée (tentative {state['iteration_count'] + 1})"
        else:
            query = state["question"]
            search_type = "Recherche initiale"
        
        # Exécuter la recherche intelligente
        search_result = self.toolbox.smart_document_search(query)
        
        # Mise à jour de l'état
        new_state = {
            **state,
            "search_results": search_result.get("results", ""),
            "documents_found": search_result.get("success", False),
            "search_quality_score": search_result.get("score", 0.0),
            "sources": search_result.get("sources", []),
            "messages": state.get("messages", []) + [
                AIMessage(content=f"{search_type}: {search_result.get('document_count', 0)} documents trouvés (Score: {search_result.get('score', 0.0):.2f})")
            ]
        }
        
        # Ajouter les erreurs si nécessaire
        if not search_result.get("success", False):
            error_msg = f"Échec de recherche: {search_result.get('results', 'Erreur inconnue')}"
            new_state["error_messages"] = state.get("error_messages", []) + [error_msg]
        
        return new_state
    
    def _evaluate_results_node(self, state: AdvancedAgentState) -> AdvancedAgentState:
        """Évalue la qualité des résultats obtenus"""
        quality_score = state.get("search_quality_score", 0.0)
        documents_found = state.get("documents_found", False)
        iteration_count = state.get("iteration_count", 0)
        
        confidence_factors = []
        
        if documents_found:
            confidence_factors.append(quality_score)
        
        if len(state.get("sources", [])) > 0:
            confidence_factors.append(min(1.0, len(state["sources"]) / 5))  # Bonus pour plusieurs sources
        
        if iteration_count == 0:  # Bonus pour succès au premier essai
            confidence_factors.append(0.2)
        
        overall_confidence = sum(confidence_factors) / len(confidence_factors) if confidence_factors else 0.0
        
        return {
            **state,
            "confidence_score": overall_confidence,
            "messages": state.get("messages", []) + [
                AIMessage(content=f"Évaluation: Confiance {overall_confidence:.2f}, Documents: {documents_found}, Qualité: {quality_score:.2f}")
            ]
        }
    
    def _intelligent_reformulation_node(self, state: AdvancedAgentState) -> AdvancedAgentState:
        """Reformule intelligemment la requête"""
        previous_queries = [state["question"]] + state.get("reformulated_queries", [])
        
        # Reformulation intelligente
        reformulation_result = self.toolbox.intelligent_query_reformulator(
            query=state["question"],
            previous_attempts=previous_queries
        )
        
        new_reformulated_queries = state.get("reformulated_queries", [])
        
        if reformulation_result.get("success", False):
            new_query = reformulation_result["reformulated_query"]
            new_reformulated_queries.append(new_query)
            message = f"Reformulation: '{new_query}' (Confiance: {reformulation_result.get('confidence', 0):.2f})"
        else:
            error_msg = f"Échec de reformulation: {reformulation_result.get('error', 'Erreur inconnue')}"
            new_state_errors = state.get("error_messages", []) + [error_msg]
            message = f"Problème de reformulation, nouvelle tentative..."
            
        return {
            **state,
            "reformulated_queries": new_reformulated_queries,
            "iteration_count": state.get("iteration_count", 0) + 1,
            "messages": state.get("messages", []) + [AIMessage(content=message)]
        }
    
    def _advanced_synthesis_node(self, state: AdvancedAgentState) -> AdvancedAgentState:
        """Synthèse avancée de la réponse"""
        # Synthèse avec contexte enrichi
        synthesis_result = self.toolbox.advanced_answer_synthesizer(
            question=state["question"],
            context=state.get("search_results", ""),
            sources=state.get("sources", [])
        )
        
        if synthesis_result.get("success", False):
            final_answer = synthesis_result["answer"]
            quality_metrics = synthesis_result.get("quality_metrics", {})
            synthesis_confidence = synthesis_result.get("confidence", 0.5)
            
            # Nettoyage de la réponse
            cleaned_answer = self._clean_response(final_answer)
            
            message = f"Synthèse terminée (Confiance: {synthesis_confidence:.2f})"
        else:
            cleaned_answer = f"Erreur de synthèse: {synthesis_result.get('answer', 'Impossible de générer une réponse')}"
            quality_metrics = {}
            synthesis_confidence = 0.0
            message = "Échec de la synthèse"
        
        return {
            **state,
            "final_answer": cleaned_answer,
            "confidence_score": max(state.get("confidence_score", 0), synthesis_confidence),
            "messages": state.get("messages", []) + [AIMessage(content=message)]
        }
    
    def _finalize_response_node(self, state: AdvancedAgentState) -> AdvancedAgentState:
        """Finalise la réponse avec métriques"""
        # Calcul du temps de traitement
        start_time = state.get("processing_time", datetime.now().timestamp())
        processing_duration = datetime.now().timestamp() - start_time
        
        # Compilation des métriques finales
        final_metrics = {
            "processing_time": processing_duration,
            "iterations": state.get("iteration_count", 0),
            "documents_found": len(state.get("sources", [])),
            "confidence": state.get("confidence_score", 0.0),
            "search_quality": state.get("search_quality_score", 0.0),
            "errors": len(state.get("error_messages", []))
        }
        
        # Message de finalisation
        metrics_summary = f"Traité en {processing_duration:.1f}s, {final_metrics['iterations']} itérations, {final_metrics['documents_found']} sources, confiance: {final_metrics['confidence']:.2f}"
        
        return {
            **state,
            "processing_time": processing_duration,
            "messages": state.get("messages", []) + [
                AIMessage(content=metrics_summary)
            ]
        }
    
    def _decide_next_action(self, state: AdvancedAgentState) -> str:
        """Décide de l'action suivante basée sur l'état"""
        documents_found = state.get("documents_found", False)
        quality_score = state.get("search_quality_score", 0.0)
        iteration_count = state.get("iteration_count", 0)
        confidence = state.get("confidence_score", 0.0)
        
        # Si on a de bons résultats, on synthétise
        if documents_found and (quality_score > 0.4 or confidence > 0.5):
            return "synthesize"
        
        # Si on n'a pas trouvé grand chose et qu'on peut encore essayer
        if not documents_found or quality_score < 0.3:
            if iteration_count < 3:  
                return "reformulate"
        
        # Si on a quelque chose de moyen, on essaye de synthétiser quand même
        if documents_found and iteration_count < 3:
            return "synthesize"
        
        # Sinon, échec
        return "end_failure"
    
    def _clean_response(self, response: str) -> str:
        """Nettoie et améliore la réponse finale"""
        # Corrections de base
        response = re.sub(r"Page\s*-1", "Document", response)
        
        # Amélioration du formatage
        response = re.sub(r"\n{3,}", "\n\n", response)  # Pas plus de 2 retours à la ligne
        response = response.strip()
        
        # Ajout d'émojis pour améliorer la lisibilité
        if "Sources :" in response:
            response = response.replace("Sources :", "\nSources consultées :")
        
        return response
    
    # === Interface publique ===
    
    async def process_question_async(self, question: str, config: Optional[Dict] = None) -> str:
        """Traite une question de manière asynchrone"""
        try:
            # Configuration par défaut
            config = config or {"configurable": {"thread_id": "default"}}
            
            # État initial
            initial_state = AdvancedAgentState(
                messages=[HumanMessage(content=question)],
                question=question,
                search_results="",
                reformulated_queries=[],
                final_answer="",
                iteration_count=0,
                documents_found=False,
                search_quality_score=0.0,
                error_messages=[],
                processing_time=0.0,
                confidence_score=0.0,
                sources=[],
                user_preferences={}
            )
            
            # Exécution du graphe
            final_state = await self.graph.ainvoke(initial_state, config)
            sources = final_state.get("sources", [])

            # Récupération de la réponse
            print(f"messages {final_state}")
            final_answer = final_state.get("final_answer", "Aucune réponse générée")
            
            # Sauvegarde de l'historique avec métriques
            self._save_to_history(question, final_answer, final_state)
            
            return {
    "answer": final_answer,
    "sources": sources,
    "confidence": final_state.get("confidence_score", 0.0),
    "processing_time": final_state.get("processing_time", 0.0)
}

            
        except Exception as e:
            error_msg = f"Erreur lors du traitement: {str(e)}"
            self.conversation_history.append((question, error_msg, {"error": True}))
            return error_msg
    
    def process_question(self, question: str, config: Optional[Dict] = None) -> str:
        """Version synchrone du traitement"""
        return asyncio.run(self.process_question_async(question, config))
    
    def _save_to_history(self, question: str, answer: str, state: Dict) -> None:
        """Sauvegarde enrichie dans l'historique"""
        metrics = {
            "processing_time": state.get("processing_time", 0),
            "confidence": state.get("confidence_score", 0),
            "sources_count": len(state.get("sources", [])),
            "iterations": state.get("iteration_count", 0),
            "timestamp": datetime.now().isoformat()
        }
        
        self.conversation_history.append((question, answer, metrics))
        self.performance_metrics.append(metrics)
    
    # === Interface interactive simplifiée ===
    
    async def run_interactive_async(self):
        """Mode interactif asynchrone"""
        print("Assistant Juridique LangGraph Avancé - Prêt!")
        print("Commandes spéciales:")
        print("  'metrics' : Statistiques de performance")
        print("  'history' : Historique détaillé")
        print("  'export' : Exporter l'historique")
        print("  'exit' : Quitter")
        print("-" * 60)
        
        while True:
            try:
                user_input = input("\nQuestion (ou commande): ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ['exit', 'quit', 'bye']:
                    print("Au revoir!")
                    break
                
                if user_input.lower() == 'metrics':
                    self._show_performance_metrics()
                    continue
                
                if user_input.lower() == 'history':
                    self._show_detailed_history()
                    continue
                
                if user_input.lower() == 'export':
                    self._export_history()
                    continue
                
                # Mode normal (unique option)
                print(f"\nTraitement de: '{user_input}'")
                response = await self.process_question_async(user_input)
                print(f"\nRéponse:\n{response}")
                print("-" * 60)
                
            except KeyboardInterrupt:
                print("\n\nArrêt demandé. Au revoir!")
                break
            except Exception as e:
                print(f"\nErreur inattendue: {str(e)}")
    
    def _show_performance_metrics(self):
        """Affiche les métriques de performance"""
        if not self.performance_metrics:
            print("Aucune métrique disponible.")
            return
        
        metrics = self.performance_metrics
        print(f"\nMétriques de Performance ({len(metrics)} sessions)")
        print("-" * 50)
        
        avg_time = sum(m.get("processing_time", 0) for m in metrics) / len(metrics)
        avg_confidence = sum(m.get("confidence", 0) for m in metrics) / len(metrics)
        avg_sources = sum(m.get("sources_count", 0) for m in metrics) / len(metrics)
        avg_iterations = sum(m.get("iterations", 0) for m in metrics) / len(metrics)
        
        print(f"Temps moyen: {avg_time:.2f}s")
        print(f"Confiance moyenne: {avg_confidence:.2f}")
        print(f"Sources moyennes: {avg_sources:.1f}")
        print(f"Itérations moyennes: {avg_iterations:.1f}")
        
        # Distribution des performances
        high_confidence = sum(1 for m in metrics if m.get("confidence", 0) > 0.7)
        print(f"Sessions haute confiance: {high_confidence}/{len(metrics)} ({100*high_confidence/len(metrics):.1f}%)")
    
    def _show_detailed_history(self):
        """Affiche l'historique détaillé avec métriques"""
        if not self.conversation_history:
            print("Aucun historique disponible.")
            return
        
        print(f"\nHistorique Détaillé ({len(self.conversation_history)} conversations)")
        print("=" * 70)
        
        for i, (question, answer, metrics) in enumerate(self.conversation_history[-5:], 1):
            print(f"\n{i}. Question: {question}")
            
            # Métriques de la session
            confidence = metrics.get("confidence", 0)
            processing_time = metrics.get("processing_time", 0)
            sources = metrics.get("sources_count", 0)
            
            print(f"   Confiance: {confidence:.2f} | Temps: {processing_time:.1f}s | Sources: {sources}")
            
            # Aperçu de la réponse
            answer_preview = answer[:200] + "..." if len(answer) > 200 else answer
            print(f"   Réponse: {answer_preview}")
            print("-" * 50)
        
        if len(self.conversation_history) > 5:
            print(f"\n... et {len(self.conversation_history) - 5} conversations plus anciennes.")
    
    def _export_history(self):
        """Exporte l'historique en JSON"""
        if not self.conversation_history:
            print("Aucun historique à exporter.")
            return
    
        
        export_data = {
            "export_date": datetime.now().isoformat(),
            "total_conversations": len(self.conversation_history),
            "conversations": []
        }
        
        for question, answer, metrics in self.conversation_history:
            export_data["conversations"].append({
                "question": question,
                "answer": answer,
                "metrics": metrics
            })
        
        filename = f"legal_chat_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            print(f"Historique exporté vers: {filename}")
        except Exception as e:
            print(f"Erreur d'export: {str(e)}")
    
    def run_interactive(self):
        """Version synchrone du mode interactif"""
        asyncio.run(self.run_interactive_async())
