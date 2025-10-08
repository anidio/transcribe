import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogDescription } from "./dialog.jsx"; // Corrigido: Usando a extensão .jsx
import { Button } from "./button.jsx"; // Corrigido: Usando a extensão .jsx
import { Zap, DollarSign, CheckCircle, Sparkles } from "lucide-react";
import React from 'react';

/**
 * Componente de Diálogo para Solicitação de Upgrade (Paywall).
 * Exibido quando o usuário atinge o limite de uso gratuito (limite de requisições 429).
 * * @param {object} props
 * @param {boolean} props.isOpen - Se o diálogo está aberto.
 * @param {function} props.onClose - Função para fechar o diálogo.
 */
const UpgradeDialog = ({ isOpen, onClose }) => {
    // Defina o link real para sua página de pagamento/checkout (Stripe, PagSeguro, etc.)
    const UPGRADE_LINK = "https://SEU_LINK_DE_PAGAMENTO_AQUI"; 
    
    const features = [
        "Transcrições e Resumos Ilimitados",
        "Processamento 5x Mais Rápido",
        "Acesso Prioritário a Novos Modelos de IA",
        "Suporte Premium Dedicado"
    ];

    return (
        <Dialog open={isOpen} onOpenChange={onClose}>
            <DialogContent className="sm:max-w-[425px] bg-gray-900/90 backdrop-blur-md border-pink-500/50 text-white rounded-xl shadow-2xl">
                <DialogHeader className="text-center">
                    <Zap className="h-10 w-10 text-pink-400 mx-auto mb-2 animate-pulse" />
                    <DialogTitle className="text-2xl font-bold text-cyan-400">
                        Limite Gratuito Atingido!
                    </DialogTitle>
                    <DialogDescription className="text-gray-300 mt-2">
                        Você utilizou o limite de requisições gratuitas desta hora. 
                        Faça o upgrade para a versão **Pro** e remova todas as restrições!
                    </DialogDescription>
                </DialogHeader>

                <div className="space-y-4 my-4">
                    {/* Lista de Benefícios */}
                    <div className="bg-gray-800/50 p-4 rounded-lg border border-cyan-500/30">
                        <h3 className="text-lg font-semibold text-white mb-2 flex items-center gap-2">
                            <Sparkles className="h-5 w-5 text-pink-400" />
                            Vantagens da Versão Pro:
                        </h3>
                        <ul className="space-y-2 text-sm">
                            {features.map((feature, index) => (
                                <li key={index} className="flex items-start text-gray-300">
                                    <CheckCircle className="h-4 w-4 text-green-400 flex-shrink-0 mt-0.5 mr-2" />
                                    <span>{feature}</span>
                                </li>
                            ))}
                        </ul>
                    </div>

                    {/* Botão de Upgrade Principal */}
                    <Button
                        onClick={() => window.open(UPGRADE_LINK, '_blank')}
                        className="w-full bg-gradient-to-r from-pink-600 to-purple-600 hover:from-pink-500 hover:to-purple-500 text-white text-lg py-6 shadow-lg shadow-purple-500/30 transition-all duration-300 hover:scale-[1.02]"
                    >
                        <DollarSign className="h-5 w-5 mr-2" />
                        Fazer Upgrade Agora!
                    </Button>

                    {/* Botão de Fechar */}
                    <Button
                        onClick={onClose}
                        variant="ghost"
                        className="w-full text-cyan-400 hover:bg-gray-800/50"
                    >
                        Continuar na Versão Gratuita (Aguardar)
                    </Button>
                </div>
            </DialogContent>
        </Dialog>
    );
};

export default UpgradeDialog;