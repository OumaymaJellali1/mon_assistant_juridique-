// src/components/chat/ConversationList.tsx
import React, { useState } from 'react';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { cn } from '@/utils/cn';
import { Plus, MessageSquare, Clock, Trash2, MoreVertical } from 'lucide-react';
import type { Conversation } from '@/types/chat';
import { Scale } from 'lucide-react';

interface ConversationListProps {
  conversations: Conversation[];
  currentConversationId?: string;
  onSelectConversation: (id: string) => void;
  onNewConversation: () => void;
  onDeleteConversation: (id: string) => void;
}

function ConversationActions({ 
  conversationId, 
  onDelete,
  className 
}: { 
  conversationId: string; 
  onDelete: (id: string) => void;
  className?: string;
}) {
  const [showConfirm, setShowConfirm] = useState(false);

  const handleDelete = (e: React.MouseEvent) => {
    e.stopPropagation(); 
    if (showConfirm) {
      onDelete(conversationId);
      setShowConfirm(false);
    } else {
      setShowConfirm(true);
    }
  };

  const handleCancel = (e: React.MouseEvent) => {
    e.stopPropagation();
    setShowConfirm(false);
  };

  if (showConfirm) {
    return (
      <div className={cn("flex items-center gap-1", className)}>
        <button
          onClick={handleDelete}
          className="px-2 py-1 text-xs bg-red-100 text-red-700 rounded hover:bg-red-200 transition-colors"
        >
          Confirmer
        </button>
        <button
          onClick={handleCancel}
          className="px-2 py-1 text-xs bg-gray-100 text-gray-700 rounded hover:bg-gray-200 transition-colors"
        >
          Annuler
        </button>
      </div>
    );
  }

  return (
    <button
      onClick={handleDelete}
      className={cn(
        "p-1 rounded hover:bg-red-100 text-slate-400 hover:text-red-600 transition-colors opacity-0 group-hover:opacity-100",
        className
      )}
      title="Supprimer la consultation"
    >
      <Trash2 size={14} />
    </button>
  );
}

export function ConversationList({
  conversations,
  currentConversationId,
  onSelectConversation,
  onNewConversation,
  onDeleteConversation
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

      <div className="flex-1 overflow-y-auto">
        {conversations.length === 0 ? (
          <div className="p-4 text-center text-slate-500">
            <MessageSquare size={32} className="mx-auto mb-2 opacity-50" />
            <p className="text-sm">Aucune consultation</p>
          </div>
        ) : (
          <div className="p-2">
            {conversations.map((conversation) => (
              <div
                key={conversation.id}
                className={cn(
                  "group relative mb-2 rounded-lg transition-colors border",
                  currentConversationId === conversation.id
                    ? "bg-white border-blue-200 shadow-sm"
                    : "bg-transparent border-transparent hover:border-slate-200"
                )}
              >
                <div
                  className={cn(
                    "relative w-full p-3 rounded-lg transition-colors cursor-pointer",
                    "hover:bg-white hover:shadow-sm",
                    currentConversationId === conversation.id
                      ? "bg-white"
                      : "bg-transparent hover:bg-white"
                  )}
                  onClick={() => onSelectConversation(conversation.id)}
                >
                  
                  <div className="flex items-start justify-between mb-1">
                    <div className="font-medium text-slate-900 text-sm truncate pr-2 flex-1">
                      {conversation.title}
                    </div>
                    <ConversationActions
                      conversationId={conversation.id}
                      onDelete={onDeleteConversation}
                    />
                  </div>
                  
                  {conversation.lastMessage && (
                    <div className="text-xs text-slate-600 mb-2 truncate">
                      {conversation.lastMessage}
                    </div>
                  )}
                  
                  <div className="flex items-center justify-between text-xs text-slate-500">
                    <div className="flex items-center gap-1">
                      <Clock size={10} />
                      <span>{formatDate(conversation.updatedAt)}</span>
                    </div>
                    
                    <Badge variant="secondary" className="text-xs">
                      {conversation.messageCount} msg
                    </Badge>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
      
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