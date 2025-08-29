import React from 'react';
import { cn } from '@/utils/cn';
import { User, Scale, Clock, ExternalLink, FileText } from 'lucide-react';
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
  
  const renderSources = (sources: any[]) => {
    if (!sources || sources.length === 0) return null;

    return (
      <div className="mt-3 pt-3 border-t border-slate-100">
        <div className="text-xs font-medium text-slate-600 mb-2 flex items-center gap-1">
          <FileText size={12} />
          Sources utilisées :
        </div>
        <div className="space-y-1">
          {sources.map((source, index) => (
            <div key={index} className="text-xs">
              {source.url ? (
                <a
                  href={source.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 text-blue-600 hover:text-blue-800 hover:underline transition-colors"
                  title={source.title || source.document_name || 'Ouvrir la source'}
                >
                  <ExternalLink size={10} />
                  <span>
                    {source.title || source.document_name || `Source ${index + 1}`}
                  </span>
                </a>
              ) : (
                <div className="inline-flex items-center gap-1 text-slate-600">
                  <FileText size={10} />
                  <span>
                    {source.title || source.document_name || source.source || `Document ${index + 1}`}
                  </span>
                  {source.page && (
                    <span className="text-slate-500">- Page {source.page}</span>
                  )}
                </div>
              )}
              {source.relevance_score && (
                <span className="ml-2 text-slate-400">
                  ({Math.round(source.relevance_score * 100)}% pertinence)
                </span>
              )}
            </div>
          ))}
        </div>
      </div>
    );
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

        <div className={cn(
          "flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-white text-sm font-medium",
          isUser
            ? "bg-blue-600"
            : "bg-slate-700"
        )}>
          {isUser ? <User size={16} /> : <Scale size={16} />}
        </div>

        <div className="flex flex-col">

          <div className={cn(
            "px-4 py-3 rounded-lg shadow-sm border",
            isUser
              ? "bg-blue-600 text-white border-blue-600"
              : "bg-white text-slate-900 border-slate-200"
          )}>

            {!isUser && (
              <div className="flex items-center gap-2 mb-2 text-xs text-slate-500 font-medium">
                <Scale size={12} />
                <span>Assistant Bancaire</span>
              </div>
            )}

            <div className={cn(
              "whitespace-pre-wrap break-words",
              isUser ? "text-white" : "text-slate-900"
            )}>
              {message.content}
            </div>

            {!isUser && message.sources && renderSources(message.sources)}
          </div>
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