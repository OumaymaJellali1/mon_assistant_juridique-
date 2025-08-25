// src/components/layout/Footer.tsx
import React from 'react';
import { Scale, ExternalLink } from 'lucide-react';

export function Footer() {
  return (
    <footer className="bg-slate-900 text-white py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          
          {/* Branding */}
          <div className="flex flex-col">
            <div className="flex items-center gap-2 mb-3">
              <Scale size={20} />
              <span className="font-bold text-lg">SmartBanker Legal</span>
            </div>
            <p className="text-slate-400 text-sm">
              Assistant juridique intelligent basé sur la législation tunisienne.
              Technologie d'IA avancée pour des conseils juridiques précis.
            </p>
          </div>

          {/* Avertissements légaux */}
          <div>
            <h4 className="font-semibold mb-3">⚖️ Avertissement Juridique</h4>
            <ul className="text-slate-400 text-sm space-y-1">
              <li>• Informations à titre indicatif uniquement</li>
              <li>• Ne remplace pas un conseil juridique personnalisé</li>
              <li>• Consultez un avocat pour vos besoins spécifiques</li>
              <li>• Basé sur la législation tunisienne</li>
            </ul>
          </div>

          {/* Contact et ressources */}
          <div>
            <h4 className="font-semibold mb-3">Ressources</h4>
            <ul className="text-slate-400 text-sm space-y-2">
              <li>
                <a href="#" className="hover:text-white transition-colors flex items-center gap-1">
                  Guide d'utilisation <ExternalLink size={12} />
                </a>
              </li>
              <li>
                <a href="#" className="hover:text-white transition-colors flex items-center gap-1">
                  Textes de loi <ExternalLink size={12} />
                </a>
              </li>
              <li>
                <a href="#" className="hover:text-white transition-colors flex items-center gap-1">
                  Support technique <ExternalLink size={12} />
                </a>
              </li>
            </ul>
          </div>
        </div>
        
        <div className="border-t border-slate-800 mt-8 pt-6 text-center text-slate-400 text-sm">
          <p>&copy; 2025 SmartBanker Legal AI. Développé avec FastAPI, LangGraph et Next.js.</p>
        </div>
      </div>
    </footer>
  );
}