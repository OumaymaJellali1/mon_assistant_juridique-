from src.assistants.legal_chatbot import AdvancedLegalChatbot
import asyncio

async def main_async():
    """Point d'entrée principal asynchrone"""
    try:
        print("Initialisation de l'assistant juridique avancé...")
        chatbot = AdvancedLegalChatbot()
        print("Initialisation réussie!")
        
        await chatbot.run_interactive_async()
        
    except Exception as e:
        print(f"Erreur d'initialisation: {str(e)}")

def main():
    """Point d'entrée principal synchrone"""
    asyncio.run(main_async())


if __name__ == "__main__":
    main()