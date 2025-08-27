// src/app/page.tsx
'use client';

import React, { useState } from 'react';
import { useChat } from '@/hooks/useChat';
import { useApiHealth } from '@/hooks/useApi';
import { Header } from '@/components/layout/Header';
import { Sidebar } from '@/components/layout/Sidebar';
import { ChatInterface } from '@/components/chat/ChatInterface';
import { Footer } from '@/components/layout/Footer';
import { Button } from '@/components/ui/Button';
import { Menu, X, AlertTriangle } from 'lucide-react';

export default function HomePage() {
  const [sidebarOpen, setSidebarOpen] = useState(false);
  
  // Hooks personnalisés
  const {
    messages,
    conversations,
    currentConversationId,
    isLoading,
    error,
    sendMessage,
    startNewConversation,
    loadConversation,
    deleteConversation, // <-- AJOUTÉ
    clearError
  } = useChat();

  const { isHealthy: isApiHealthy, isChecking } = useApiHealth();

  // Gestion de la sidebar mobile
  const toggleSidebar = () => setSidebarOpen(!sidebarOpen);
  const closeSidebar = () => setSidebarOpen(false);

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      
      {/* Header */}
      <Header 
        isApiHealthy={isApiHealthy}
        conversationCount={conversations.length}
      />

      {/* Alerte si API indisponible */}
      {!isChecking && !isApiHealthy && (
        <div className="bg-yellow-50 border-b border-yellow-200 p-3">
          <div className="max-w-7xl mx-auto flex items-center gap-3">
            <AlertTriangle size={18} className="text-yellow-600" />
            <p className="text-sm text-yellow-800">
              <strong>Service temporairement indisponible.</strong> 
              Vérifiez que votre serveur FastAPI fonctionne sur le port 8000.
            </p>
          </div>
        </div>
      )}

      {/* Contenu principal */}
      <div className="flex-1 flex overflow-hidden">
        
        {/* Bouton mobile pour ouvrir sidebar */}
        <Button
          variant="ghost"
          size="sm"
          onClick={toggleSidebar}
          className="lg:hidden fixed top-20 left-4 z-40 bg-white shadow-md border border-slate-200"
        >
          {sidebarOpen ? <X size={18} /> : <Menu size={18} />}
        </Button>

        {/* Overlay mobile */}
        {sidebarOpen && (
          <div 
            className="fixed inset-0 bg-black bg-opacity-25 z-40 lg:hidden"
            onClick={closeSidebar}
          />
        )}

        {/* Sidebar */}
        <Sidebar
          conversations={conversations}
          currentConversationId={currentConversationId}
          onSelectConversation={(id) => {
            loadConversation(id);
            closeSidebar();
          }}
          onNewConversation={() => {
            startNewConversation();
            closeSidebar();
          }}
          onDeleteConversation={(id) => {
            deleteConversation(id);
            closeSidebar();
          }}
          isOpen={sidebarOpen}
        />

        {/* Zone de chat principale */}
        <main className="flex-1 flex flex-col min-w-0">
          <ChatInterface
            messages={messages}
            onSendMessage={sendMessage}
            isLoading={isLoading}
            error={error}
            onClearError={clearError}
            currentConversationId={currentConversationId}
          />
        </main>
      </div>

      {/* Footer */}
      <Footer />
    </div>
  );
}
