// src/components/chat/ConversationList.tsx
import React from 'react';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { cn } from '@/utils/cn';
import { Plus, MessageSquare, Clock } from 'lucide-react';
import type { Conversation } from '@/types/chat';
import { Scale } from 'lucide-react';

interface ConversationListProps {
  conversations: Conversation[];
  currentConversationId?: string;
  onSelectConversation: (id: string) => void;
  onNewConversation: () => void;
}

export function ConversationList({
  conversations,
  currentConversationId,
  onSelectConversation,
  onNewConversation
}: ConversationListProps) {
  
  const formatDate = (date: Date) => {
    const now = new Date();
    const diffHours = Math.abs(now.getTime() - date.getTime()) / 36e5;
    
    if (diffHours < 1) {
      return 'Il y a quelques minutes';
    } else if (diffHours < 24) {
      return `Il y a ${Math.floor(diffHours)}h`;
    } else {
      return date.toLocaleDateString('fr-FR', { 
        day: 'numeric', 
        month: 'short' 
      });
    }
  };

  return (
    <div className="h-full bg-slate-50 border-r border-slate-200 flex flex-col">
      
      {/* Header */}
      <div className="p-4 border-b border-slate-200 bg-white">
        <div className="flex items-center justify-between mb-3">
          <h2 className="font-semibold text-slate-900 flex items-center gap-2">
            <MessageSquare size={18} />
            Consultations
          </h2>
          <Badge variant="secondary">
            {conversations.length}
          </Badge>
        </div>
        
        <Button
          onClick={onNewConversation}
          variant="primary"
          size="sm"
          className="w-full"
        >
          <Plus size={16} className="mr-2" />
          Nouvelle consultation
        </Button>
      </div>

      {/* Liste des conversations */}
      <div className="flex-1 overflow-y-auto">
        {conversations.length === 0 ? (
          <div className="p-4 text-center text-slate-500">
            <MessageSquare size={32} className="mx-auto mb-2 opacity-50" />
            <p className="text-sm">Aucune consultation</p>
          </div>
        ) : (
          <div className="p-2">
            {conversations.map((conversation) => (
              <button
                key={conversation.id}
                onClick={() => onSelectConversation(conversation.id)}
                className={cn(
                  "w-full p-3 mb-2 text-left rounded-lg transition-colors",
                  "hover:bg-white hover:shadow-sm border",
                  currentConversationId === conversation.id
                    ? "bg-white border-blue-200 shadow-sm"
                    : "bg-transparent border-transparent hover:border-slate-200"
                )}
              >
                
                {/* Titre */}
                <div className="font-medium text-slate-900 text-sm mb-1 truncate">
                  {conversation.title}
                </div>
                
                {/* Dernier message */}
                {conversation.lastMessage && (
                  <div className="text-xs text-slate-600 mb-2 truncate">
                    {conversation.lastMessage}
                  </div>
                )}
                
                {/* Métadonnées */}
                <div className="flex items-center justify-between text-xs text-slate-500">
                  <div className="flex items-center gap-1">
                    <Clock size={10} />
                    <span>{formatDate(conversation.updatedAt)}</span>
                  </div>
                  
                  <Badge variant="secondary" className="text-xs">
                    {conversation.messageCount} msg
                  </Badge>
                </div>
              </button>
            ))}
          </div>
        )}
      </div>
      
      {/* Footer avec informations */}
      <div className="p-4 border-t border-slate-200 bg-white">
        <div className="text-xs text-slate-500 text-center">
          <div className="flex items-center justify-center gap-1 mb-1">
            <Scale size={12} />
            <span>SmartBanker Legal AI</span>
          </div>
          <div>Assistant juridique intelligent</div>
        </div>
      </div>
    </div>
  );
}