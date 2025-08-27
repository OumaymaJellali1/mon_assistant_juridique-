// src/components/layout/Header.tsx
import React from 'react';
import { Badge } from '@/components/ui/Badge';
import { Scale, Shield, Zap } from 'lucide-react';
import { cn } from '@/utils/cn';

interface HeaderProps {
  isApiHealthy?: boolean  | null;
  conversationCount: number;
}

export function Header({ isApiHealthy, conversationCount }: HeaderProps) {
  return (
    <header className="bg-white border-b border-slate-200 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-slate-700 to-slate-900 rounded-lg flex items-center justify-center">
              <Scale size={24} className="text-white" />
            </div>
            
            <div>
              <h1 className="text-xl font-bold text-slate-900">SmartBanker Legal</h1>
              <p className="text-sm text-slate-600">Assistant Juridique Intelligent</p>
            </div>
          </div>

          <div className="flex items-center gap-4">
            
            <div className="hidden sm:flex items-center gap-2">
              <Shield size={16} className="text-slate-500" />
              <span className="text-sm text-slate-600">
                {conversationCount} consultation{conversationCount > 1 ? 's' : ''}
              </span>
            </div>

            <div className="flex items-center gap-2">
              <div className={cn(
                "w-2 h-2 rounded-full",
                isApiHealthy ? "bg-green-500 animate-pulse" : "bg-red-500"
              )} />
              <Badge variant={isApiHealthy ? "success" : "destructive"}>
                {isApiHealthy ? "En ligne" : "Hors ligne"}
              </Badge>
            </div>

            <Badge variant="secondary" className="hidden md:inline-flex">
              v1.0.0
            </Badge>
          </div>
        </div>
      </div>
    </header>
  );
}