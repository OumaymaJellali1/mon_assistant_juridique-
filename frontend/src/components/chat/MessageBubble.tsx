// src/components/chat/MessageBubble.tsx
import React from 'react';
import { cn } from '@/utils/cn';
import { User, Scale, Clock } from 'lucide-react';
import type { ChatMessage } from '@/types/chat';

interface MessageBubbleProps {
  message: ChatMessage;
  showTimestamp?: boolean;
}

export function MessageBubble({ message, showTimestamp = true }: MessageBubbleProps) {
  const isUser = message.role === 'user';
  
  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('fr-FR', { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  return (
    <div className={cn(
      "flex w-full mb-4",
      isUser ? "justify-end" : "justify-start"
    )}>
      <div className={cn(
        "flex max-w-[80%] gap-3",
        isUser ? "flex-row-reverse" : "flex-row"
      )}>
        
        {/* Avatar */}
        <div className={cn(
          "flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-white text-sm font-medium",
          isUser 
            ? "bg-blue-600" 
            : "bg-slate-700"
        )}>
          {isUser ? <User size={16} /> : <Scale size={16} />}
        </div>

        {/* Contenu du message */}
        <div className="flex flex-col">
          
          {/* Bubble du message */}
          <div className={cn(
            "px-4 py-3 rounded-lg shadow-sm border",
            isUser 
              ? "bg-blue-600 text-white border-blue-600" 
              : "bg-white text-slate-900 border-slate-200"
          )}>
            
            {/* Role indicator pour l'assistant */}
            {!isUser && (
              <div className="flex items-center gap-2 mb-2 text-xs text-slate-500 font-medium">
                <Scale size={12} />
                <span>Assistant Juridique</span>
              </div>
            )}
            
            {/* Contenu */}
            <div className={cn(
              "whitespace-pre-wrap break-words",
              isUser ? "text-white" : "text-slate-900"
            )}>
              {message.content}
            </div>
          </div>

          {/* Timestamp */}
          {showTimestamp && (
            <div className={cn(
              "flex items-center gap-1 mt-1 text-xs text-slate-500",
              isUser ? "justify-end" : "justify-start"
            )}>
              <Clock size={10} />
              <span>{formatTime(message.timestamp)}</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}