// src/components/chat/ChatInterface.tsx
import React, { useEffect, useRef } from 'react';
import { MessageBubble } from './MessageBubble';
import { InputArea } from './InputArea';
import { TypingIndicator } from './TypingIndicator';
import { Button } from '@/components/ui/Button';
import { AlertCircle, RefreshCw, Scale } from 'lucide-react';
import type { ChatMessage } from '@/types/chat';

interface ChatInterfaceProps {
  messages: ChatMessage[];
  onSendMessage: (message: string) => void;
  isLoading: boolean;
  error?: string;
  onClearError: () => void;
  currentConversationId?: string;
}

export function ChatInterface({
  messages,
  onSendMessage,
  isLoading,
  error,
  onClearError,
  currentConversationId
}: ChatInterfaceProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll vers le bas
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ 
        behavior: 'smooth',
        block: 'end'
      });
    }
  }, [messages, isLoading]);

  const isEmpty = messages.length === 0;

  return (
    <div className="flex flex-col h-full bg-slate-50">
      
      {/* Header du chat */}
      <div className="bg-white border-b border-slate-200 p-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-slate-700 rounded-lg flex items-center justify-center">
              <Scale size={20} className="text-white" />
            </div>
            <div>
              <h1 className="font-semibold text-slate-900">Assistant Juridique</h1>
              <p className="text-sm text-slate-600">
                {currentConversationId ? `Consultation #${currentConversationId.slice(-8)}` : 'Nouvelle consultation'}
              </p>
            </div>
          </div>
          
          {/* Indicateur de statut */}
          <div className="flex items-center gap-2">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
            <span className="text-xs text-slate-500">En ligne</span>
          </div>
        </div>
      </div>

      {/* Zone des messages */}
      <div className="flex-1 overflow-y-auto p-4">
        
        {/* Message d'accueil */}
        {isEmpty && (
          <div className="flex flex-col items-center justify-center h-full text-center">
            <div className="w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center mb-4">
              <Scale size={24} className="text-slate-600" />
            </div>
            
            <h3 className="text-lg font-semibold text-slate-900 mb-2">
              Bienvenue dans votre consultation juridique
            </h3>
            
            <p className="text-slate-600 max-w-md mb-6">
              Je suis votre assistant juridique intelligent. Posez-moi vos questions 
              sur le droit tunisien et je vous fournirai des informations précises 
              basées sur la législation en vigueur.
            </p>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 w-full max-w-2xl">
              {[
                "Comment la législation tunisienne protège-t-elle les données bancaires personnelles ? ",
                "Quels droits a le client face à sa banque ?",
                "Quelles règles encadrent le crédit bancaire ?",
                "Droits du travailleur en cas de Quels recours pour un client en cas de litige bancaire ?"
              ].map((example, index) => (
                <button
                  key={index}
                  onClick={() => onSendMessage(example)}
                  className="p-3 text-left bg-white border border-slate-200 rounded-lg hover:border-blue-300 hover:shadow-sm transition-all text-sm text-slate-700"
                >
                  "{example}"
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Messages */}
        {messages.map((message) => (
          <MessageBubble
            key={message.id}
            message={message}
            showTimestamp={true}
          />
        ))}

        {/* Indicateur de frappe */}
        {isLoading && <TypingIndicator />}

        {/* Ancre pour l'auto-scroll */}
        <div ref={messagesEndRef} />
      </div>

      {/* Zone d'erreur */}
      {error && (
        <div className="bg-red-50 border-t border-red-200 p-4">
          <div className="flex items-center gap-3">
            <AlertCircle size={18} className="text-red-600 flex-shrink-0" />
            <div className="flex-1">
              <p className="text-sm text-red-800 font-medium">Erreur</p>
              <p className="text-sm text-red-700">{error}</p>
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={onClearError}
              className="text-red-600 hover:text-red-700"
            >
              <RefreshCw size={16} />
            </Button>
          </div>
        </div>
      )}

      {/* Zone de saisie */}
      <InputArea
       onSendMessage={onSendMessage}
       isLoading={isLoading}
       placeholder="Écrivez votre question juridique ici..."
       />

    </div>
  );
}