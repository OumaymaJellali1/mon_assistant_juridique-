import React from 'react';
import { Scale } from 'lucide-react';

export default function Loading() {
  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center">
      <div className="text-center">
        <div className="w-16 h-16 bg-slate-700 rounded-lg flex items-center justify-center mb-4 mx-auto">
          <Scale size={32} className="text-white animate-pulse" />
        </div>
        <h2 className="text-xl font-semibold text-slate-900 mb-2">SmartBanker Legal</h2>
        <p className="text-slate-600">Initialisation de l'assistant juridique...</p>
        
        <div className="mt-4 flex justify-center gap-1">
          <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
          <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
          <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
        </div>
      </div>
    </div>
  );
}