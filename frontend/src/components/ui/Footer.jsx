import React from 'react';
import { Instagram } from 'lucide-react'; // Importamos o ícone necessário

const Footer = () => {
    // Definimos as cores e o estilo do seu site (Cyberpunk/Dark)
    return (
        <footer className="mt-16 py-8 border-t border-cyan-500/30 bg-gray-900/50 backdrop-blur-sm">
            <div className="container mx-auto px-4 text-center">
                
                {/* Seção Principal - MangueBit Code */}
                <p className="text-lg font-semibold text-white">
                    Este é um produto <span className="text-cyan-400">MangueBit Code</span>.
                </p>
                <p className="text-gray-400 mt-2 max-w-xl mx-auto text-sm">
                    Criamos tecnologia sob medida para simplificar processos, aumentar resultados e impulsionar o seu negócio. Fale com a gente e descubra como podemos ajudar você.
                </p>

                {/* Seção de Redes Sociais */}
                <div className="my-6">
                    <a
                        href="[LINK DO SEU INSTAGRAM]" // Substitua pelo link real
                        target="_blank"
                        rel="noopener noreferrer"
                        // Estilização com cores de destaque do tema
                        className="inline-flex items-center justify-center gap-2 text-base font-bold text-pink-400 hover:text-cyan-400 transition-colors duration-200"
                    >
                        <Instagram className="h-5 w-5" />
                        Siga-nos no Instagram!
                    </a>
                </div>

                {/* Separador Estilizado */}
                <div className="w-24 h-px mx-auto bg-pink-400/50 my-6"></div>

                {/* Informações de Contato e Copyright */}
                <p className="text-xs text-gray-400">
                    Contato: <a href="mailto:contato@manguebitcode.com" className="text-cyan-400 hover:underline">contato@manguebitcode.com</a> | (81) 99999-8888
                </p>
                <p className="text-xs text-gray-400 mt-1">
                    © {new Date().getFullYear()} MangueBit Code. Todos os direitos reservados.
                </p>
            </div>
        </footer>
    );
};

export default Footer;