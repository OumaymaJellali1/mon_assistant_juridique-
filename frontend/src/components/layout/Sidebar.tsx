// src/components/layout/Sidebar.tsx
import React from 'react';
import { ConversationList } from '@/components/chat/ConversationList';
import type { Conversation } from '@/types/chat';
import { cn } from '@/utils/cn';

interface SidebarProps {
  conversations: Conversation[];
  currentConversationId?: string;
  onSelectConversation: (id: string) => void;
  onNewConversation: () => void;
  isOpen: boolean;
}

export function Sidebar({
  conversations,
  currentConversationId,
  onSelectConversation,
  onNewConversation,
  isOpen
}: SidebarProps) {
  return (
    <aside className={cn(
      "fixed inset-y-0 left-0 z-50 w-80 bg-white transform transition-transform duration-300 ease-in-out lg:translate-x-0 lg:static lg:inset-0",
      isOpen ? "translate-x-0" : "-translate-x-full"
    )}>
      <ConversationList
        conversations={conversations}
        currentConversationId={currentConversationId}
        onSelectConversation={onSelectConversation}
        onNewConversation={onNewConversation}
      />
    </aside>
  );
}