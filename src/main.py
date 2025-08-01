from src.assistants.legal_chatbot import LegalChatbot

if __name__ == "__main__":
    print("Assistant juridique démarré. Tapez 'exit' pour quitter.")
    chatbot = LegalChatbot()
    chatbot.run()

