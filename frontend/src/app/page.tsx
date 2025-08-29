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
  
  const {
    messages,
    conversations,
    currentConversationId,
    isLoading,
    error,
    sendMessage,
    startNewConversation,
    loadConversation,
    deleteConversation, 
    clearError
  } = useChat();

  const { isHealthy: isApiHealthy, isChecking } = useApiHealth();

  const toggleSidebar = () => setSidebarOpen(!sidebarOpen);
  const closeSidebar = () => setSidebarOpen(false);

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      
      <Header 
        isApiHealthy={isApiHealthy}
        conversationCount={conversations.length}
      />

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

      <div className="flex-1 flex overflow-hidden">
        
        <Button
          variant="ghost"
          size="sm"
          onClick={toggleSidebar}
          className="lg:hidden fixed top-20 left-4 z-40 bg-white shadow-md border border-slate-200"
        >
          {sidebarOpen ? <X size={18} /> : <Menu size={18} />}
        </Button>

        {sidebarOpen && (
          <div 
            className="fixed inset-0 bg-black bg-opacity-25 z-40 lg:hidden"
            onClick={closeSidebar}
          />
        )}

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

      <Footer />
    </div>
  );
}
