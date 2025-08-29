import { useState, useEffect } from 'react';
import { ChatService } from '@/services/chatService';

export function useApiHealth() {
  const [isHealthy, setIsHealthy] = useState<boolean | null>(null);
  const [isChecking, setIsChecking] = useState(true);
  const [lastCheck, setLastCheck] = useState<Date | null>(null);

  const checkHealth = async () => {
    setIsChecking(true);
    try {
      const isConnected = await ChatService.testBackendConnection();
      setIsHealthy(isConnected);
      setLastCheck(new Date());
    } catch (error) {
      console.error('Health check failed:', error);
      setIsHealthy(false);
    } finally {
      setIsChecking(false);
    }
  };

  useEffect(() => {
    checkHealth();
    
    const interval = setInterval(checkHealth, 300000);
    
    return () => clearInterval(interval);
  }, []);

  return {
    isHealthy,
    isChecking,
    lastCheck,
    checkHealth
  };
}
