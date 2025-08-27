// src/components/chat/InputArea.tsx
import React, { useState, useRef, useEffect } from 'react';
import { Button } from '@/components/ui/Button';
import { Send } from 'lucide-react';
import { cn } from '@/utils/cn';

interface InputAreaProps {
  onSendMessage: (message: string) => void;
  isLoading: boolean;
  placeholder?: string;
}

export function InputArea({ 
  onSendMessage, 
  isLoading, 
  placeholder = "Posez votre question juridique..." 
}: InputAreaProps) {
  const [message, setMessage] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
    }
  }, [message]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!message.trim() || isLoading) return;
    
    onSendMessage(message.trim());
    setMessage('');
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <div className="bg-white border-t border-slate-200 p-4">
      <form onSubmit={handleSubmit} className="flex gap-3">
        
        <div className="flex-1 relative">
          <textarea
            ref={textareaRef}
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            disabled={isLoading}
            className={cn(
              "w-full min-h-[44px] max-h-[120px] px-4 py-3 pr-12",
              "border border-slate-300 rounded-lg resize-none",
              "focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent",
              "placeholder:text-slate-500 text-slate-900",
              "disabled:opacity-50 disabled:cursor-not-allowed",
              "transition-all duration-200"
            )}
            rows={1}
          />
          
          <div className="absolute bottom-1 right-1 text-xs text-slate-400">
            {message.length}/5000
          </div>
        </div>

        <div className="flex flex-col gap-2">
          
          <Button
            type="submit"
            variant="primary"
            size="md"
            disabled={!message.trim() || isLoading}
            isLoading={isLoading}
            className="h-[44px] w-[44px] p-0 rounded-lg"
          >
            <Send size={18} />
          </Button>
          
        </div>
      </form>
      
      <div className="mt-2 text-xs text-slate-500 text-center">
        ⚖️ Cette consultation est à titre informatif. Pour des conseils juridiques personnalisés, consultez un avocat.
      </div>
    </div>
  );
}