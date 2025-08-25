// src/components/chat/TypingIndicator.tsx
import React from 'react';
import { Scale } from 'lucide-react';

export function TypingIndicator() {
  return (
    <div className="flex w-full justify-start mb-4">
      <div className="flex gap-3">
        
        {/* Avatar assistant */}
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-slate-700 flex items-center justify-center text-white">
          <Scale size={16} />
        </div>

        {/* Animation de frappe */}
        <div className="bg-white border border-slate-200 rounded-lg px-4 py-3 shadow-sm">
          <div className="flex items-center gap-2">
            <div className="text-xs text-slate-500 font-medium flex items-center gap-2">
              <Scale size={12} />
              <span>Assistant Juridique</span>
            </div>
          </div>
          
          <div className="flex items-center gap-1 mt-2">
            <div className="flex gap-1">
              <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
              <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
              <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
            </div>
            <span className="text-xs text-slate-500 ml-2">Analyse en cours...</span>
          </div>
        </div>
      </div>
    </div>
  );
}
