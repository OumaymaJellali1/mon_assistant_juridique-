import React from 'react';
import { Scale, ExternalLink } from 'lucide-react';

export function Footer() {
  return (
    <footer className="bg-slate-900 text-white py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
  <div className="flex flex-col">
    <div className="flex items-center gap-2 mb-3">
      <Scale size={20} />
      <span className="font-bold text-lg">SmartBanker</span>
    </div>
    <p className="text-slate-400 text-sm">
      un agent conversationnel intelligent conçu pour interagir avec les services bancaires et offrir une assistance financière en temps réel
    </p>
  </div>

  <div>
    <h4 className="font-semibold mb-3">⚖️ Informations Importantes</h4>
    <ul className="text-slate-400 text-sm space-y-1">
      <li>• Informations à titre indicatif uniquement</li>
      <li>• Ne remplace pas un conseil bancaire personnalisé</li>
      <li>• Basé sur la législation tunisienne</li>
    </ul>
  </div>
</div>

      </div>
    </footer>
  );
}