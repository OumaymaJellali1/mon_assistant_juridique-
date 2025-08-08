from src.assistants.legal_chatbot import AgenticLegalChatbot

def main():
    print("Assistant juridique agentique démarré. Tapez 'exit' pour quitter.")
    chatbot = AgenticLegalChatbot()
    try:
        chatbot.run()
    except KeyboardInterrupt:
        print("\nSession interrompue par l'utilisateur. Au revoir !")
    except Exception as e:
        print(f"Erreur inattendue : {e}")

if __name__ == "__main__":
    main()
