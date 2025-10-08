import { useState, useEffect } from "react";
import "./App.css";
import axios from "axios";
import { Button } from "./components/ui/button";
import { Input } from "./components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "./components/ui/card";
import { Badge } from "./components/ui/badge";
import { Loader2, Youtube, Sparkles, FileText, Zap } from "lucide-react";
import { toast } from "sonner";
import Footer from "./components/ui/Footer.jsx";
import UpgradeDialog from "./components/ui/UpgradeDialog.jsx"; 

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;
const PRO_KEY_STORAGE_NAME = "yt-ai-pro-key"; // Nome da chave no localStorage

function App() {
  const [url, setUrl] = useState("");
  const [transcript, setTranscript] = useState("");
  const [summary, setSummary] = useState("");
  const [enrichment, setEnrichment] = useState("");
  const [loading, setLoading] = useState({
    transcribe: false,
    summarize: false,
    enrich: false
  });
  const [isUpgradeModalOpen, setIsUpgradeModalOpen] = useState(false);
  // NOVO ESTADO: Armazena a chave PRO
  const [proKey, setProKey] = useState(null);

  // Efeito 1: Carrega a chave PRO do localStorage ao iniciar
  useEffect(() => {
    const storedKey = localStorage.getItem(PRO_KEY_STORAGE_NAME);
    if (storedKey) {
      setProKey(storedKey);
    }
  }, []);

  // Efeito 2: Inicializa os blocos do AdSense após a renderização ou mudança de conteúdo
  useEffect(() => {
    // Tenta carregar o AdSense globalmente, se ele existir
    if (window.adsbygoogle && process.env.NODE_ENV === 'production') {
        try {
            (window.adsbygoogle = window.adsbygoogle || []).push({});
        } catch (error) {
            console.error("AdSense push failed:", error);
        }
    }
  }, [transcript, summary, enrichment]); // Re-renderiza ads quando novos conteúdos aparecem

  const setLoadingState = (action, state) => {
    setLoading(prev => ({ ...prev, [action]: state }));
  };

  // Função para simular a compra e salvar a chave
  const buyProVersion = (secretKey) => {
    // O MOCK_PRO_KEY DEVE SER IGUAL ao PRO_API_KEY no seu backend/.env
    const MOCK_PRO_KEY = "mngBt-Pr0-2025-a1c2d3e4f5g6h7i8j9k0-z9y8x7w6v5u4"; 

    // Simulação do sucesso da compra
    localStorage.setItem(PRO_KEY_STORAGE_NAME, MOCK_PRO_KEY);
    setProKey(MOCK_PRO_KEY);
    setIsUpgradeModalOpen(false);
    toast.success("Upgrade Pro ativado! Você já pode usar ilimitadamente.");
  };

  // NOVO: Função centralizada para chamadas à API com o cabeçalho PRO
  const handleApiCall = async (endpoint, data, action) => {
    setLoadingState(action, true);

    const headers = {};
    if (proKey) {
        headers['X-PRO-KEY'] = proKey; // Adiciona o cabeçalho PRO para bypass
    }

    try {
        const response = await axios.post(`${API}${endpoint}`, data, { headers });
        return response.data;
    } catch (error) {
        // Tratamento do limite de requisições (429)
        if (error.response?.status === 429) {
            setIsUpgradeModalOpen(true);
            toast.error(error.response?.data?.detail || "Limite de uso excedido. Faça upgrade!");
        } else {
            // Erro geral
            toast.error(error.response?.data?.detail || `Erro ao executar ${action}`);
        }
        throw error; // Propaga o erro
    } finally {
        setLoadingState(action, false);
    }
  };

  const handleTranscribe = async () => {
    if (!url.trim()) {
      toast.error("Por favor, insira uma URL do YouTube");
      return;
    }

    setSummary("");
    setEnrichment("");

    try {
      const data = await handleApiCall("/videos/transcribe", { url }, 'transcribe');
      setTranscript(data.transcript);
      toast.success("Transcrição concluída com sucesso!");
    } catch (error) {
      // O tratamento de erro está em handleApiCall, apenas ignoramos o erro aqui
    }
  };

  const handleSummarize = async () => {
    if (!transcript.trim()) {
      toast.error("Primeiro obtenha a transcrição do vídeo");
      return;
    }

    try {
      const data = await handleApiCall("/videos/summarize", { text: transcript }, 'summarize');
      setSummary(data.result);
      toast.success("Resumo gerado com sucesso!");
    } catch (error) {
      // O tratamento de erro está em handleApiCall, apenas ignoramos o erro aqui
    }
  };

  const handleEnrich = async () => {
    if (!transcript.trim()) {
      toast.error("Primeiro obtenha a transcrição do vídeo");
      return;
    }

    try {
      const data = await handleApiCall("/videos/enrich", { text: transcript }, 'enrich');
      setEnrichment(data.result);
      toast.success("Conteúdo aprimorado com sucesso!");
    } catch (error) {
      // O tratamento de erro está em handleApiCall, apenas ignoramos o erro aqui
    }
  };

  const formatMarkdown = (text) => {
    if (!text) return "";
    
    return text
      .replace(/## (.*)/g, '<h2 class="text-xl font-bold text-cyan-400 mb-3 mt-6">$1</h2>')
      .replace(/### (.*)/g, '<h3 class="text-lg font-semibold text-pink-400 mb-2 mt-4">$1</h3>')
      .replace(/\*\*(.*?)\*\*/g, '<strong class="text-cyan-300">$1</strong>')
      .replace(/\*(.*?)\*/g, '<em class="text-pink-300">$1</em>')
      .replace(/- (.*?)(?=\n|$)/g, '<li class="ml-4 text-gray-300">• $1</li>')
      .replace(/\n/g, '<br/>');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-purple-900/20 to-gray-900">
      
      {/* Paywall Dialog - Passa a função buyProVersion */}
      <UpgradeDialog isOpen={isUpgradeModalOpen} onClose={() => setIsUpgradeModalOpen(false)} onUpgrade={buyProVersion} />

      {/* Background Effects */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-cyan-500/10 rounded-full blur-3xl animate-pulse"></div>
        <div className="absolute top-3/4 right-1/4 w-96 h-96 bg-pink-500/10 rounded-full blur-3xl animate-pulse delay-1000"></div>
      </div>

      <div className="relative z-10 container mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-12">
          <div className="flex items-center justify-center gap-3 mb-4">
            <div className="p-3 bg-gradient-to-r from-cyan-500/20 to-pink-500/20 rounded-xl backdrop-blur-sm border border-cyan-500/30">
              <Youtube className="h-8 w-8 text-cyan-400" />
            </div>
            <h1 className="text-4xl md:text-5xl font-bold bg-gradient-to-r from-cyan-400 via-pink-400 to-cyan-400 bg-clip-text text-transparent">
              YT AI Processor
            </h1>
          </div>
          
          {/* Parágrafo de SEO Otimizado */}
          <p className="text-xl text-gray-300 max-w-2xl mx-auto">
            Transforme vídeos do YouTube em conteúdo estruturado com IA avançada. Use nossa ferramenta 
            <strong className="text-cyan-400"> Grátis</strong> para <strong className="text-pink-400">Transcrever</strong>, 
            <strong className="text-pink-400"> Resumir</strong> e <strong className="text-pink-400">Otimizar</strong> qualquer vídeo em português!
          </p>
        </div>

        {/* Main Content */}
        <div className="max-w-6xl mx-auto space-y-8">
          {/* Input Section */}
          <Card className="bg-gray-900/50 backdrop-blur-sm border-gray-700/50">
            <CardHeader>
              <CardTitle className="text-xl text-cyan-400 flex items-center gap-2">
                <Youtube className="h-5 w-5" />
                URL do YouTube
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex gap-3">
                <Input
                  data-testid="youtube-url-input"
                  type="url"
                  placeholder="Cole aqui a URL do vídeo do YouTube..."
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  className="flex-1 bg-gray-800/50 border-gray-600 text-white placeholder-gray-400 focus:border-cyan-500 focus:ring-cyan-500/20"
                />
                <Button
                  data-testid="transcribe-button"
                  onClick={handleTranscribe}
                  disabled={loading.transcribe}
                  className="bg-gradient-to-r from-cyan-600 to-cyan-700 hover:from-cyan-500 hover:to-cyan-600 text-white px-6 transition-all duration-200 hover:scale-105"
                >
                  {loading.transcribe ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <FileText className="h-4 w-4" />
                  )}
                  Transcrever
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* AD BLOCK 1: BANNER PRINCIPAL (Horizontal) */}
          <div data-testid="ad-placement-top" className="w-full h-auto min-h-20 bg-gray-800/70 p-1 rounded-xl border border-pink-500/30 shadow-xl text-center flex items-center justify-center">
            <ins className="adsbygoogle"
                style={{ display: 'block', width: '100%', height: '100%', minHeight: '90px' }}
                data-ad-client="ca-pub-SEU_PUBLISHER_ID"
                data-ad-slot="2693883691" 
                data-ad-format="auto"
                data-full-width-responsive="true"
                dangerouslySetInnerHTML={{ __html: '' }} 
            />
          </div>

          {/* Action Buttons */}
          {transcript && (
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Button
                data-testid="summarize-button"
                onClick={handleSummarize}
                disabled={loading.summarize}
                className="bg-gradient-to-r from-pink-600 to-pink-700 hover:from-pink-500 hover:to-pink-600 text-white px-8 py-3 text-lg transition-all duration-200 hover:scale-105"
              >
                {loading.summarize ? (
                  <Loader2 className="h-5 w-5 animate-spin mr-2" />
                ) : (
                  <Sparkles className="h-5 w-5 mr-2" />
                )}
                Resumir Conteúdo
              </Button>

              <Button
                data-testid="enrich-button"
                onClick={handleEnrich}
                disabled={loading.enrich}
                className="bg-gradient-to-r from-purple-600 to-purple-700 hover:from-purple-500 hover:to-purple-600 text-white px-8 py-3 text-lg transition-all duration-200 hover:scale-105"
              >
                {loading.enrich ? (
                  <Loader2 className="h-5 w-5 animate-spin mr-2" />
                ) : (
                  <Zap className="h-5 w-5 mr-2" />
                )}
                Aprimorar Conteúdo
              </Button>
            </div>
          )}

          {/* Results Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
            
            {/* AD BLOCK 2: CARD/SIDEBAR (Retangular) */}
            <div data-testid="ad-placement-sidebar" className={`w-full h-auto min-h-48 bg-gray-800/70 p-1 rounded-xl border border-cyan-500/30 shadow-xl text-center flex items-center justify-center 
              ${!transcript && 'lg:col-span-3 xl:col-span-3'} 
              ${transcript && !summary && !enrichment && 'lg:col-span-2 xl:col-span-2'}`}>
                <ins className="adsbygoogle"
                    style={{ display: 'block', width: '100%', height: '100%', minHeight: '250px' }}
                    data-ad-client="ca-pub-SEU_PUBLISHER_ID"
                    data-ad-slot="9653317366"
                    data-ad-format="rectangle"
                    dangerouslySetInnerHTML={{ __html: '' }} 
                />
            </div>

            {/* Transcript */}
            {transcript && (
              <Card data-testid="transcript-card" className="bg-gray-900/50 backdrop-blur-sm border-gray-700/50">
                <CardHeader>
                  <CardTitle className="text-lg text-white flex items-center gap-2">
                    <FileText className="h-5 w-5 text-green-400" />
                    Transcrição
                    <Badge variant="secondary" className="bg-green-500/20 text-green-400 border-green-500/30">
                      Original
                    </Badge>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="max-h-96 overflow-y-auto bg-gray-800/30 p-4 rounded-lg border border-gray-600/30">
                    <p data-testid="transcript-text" className="text-gray-300 text-sm leading-relaxed whitespace-pre-wrap">
                      {transcript}
                    </p>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Summary */}
            {summary && (
              <Card data-testid="summary-card" className="bg-gray-900/50 backdrop-blur-sm border-gray-700/50">
                <CardHeader>
                  <CardTitle className="text-lg text-white flex items-center gap-2">
                    <Sparkles className="h-5 w-5 text-pink-400" />
                    Resumo Inteligente
                    <Badge variant="secondary" className="bg-pink-500/20 text-pink-400 border-pink-500/30">
                      IA
                    </Badge>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="max-h-96 overflow-y-auto bg-gray-800/30 p-4 rounded-lg border border-gray-600/30">
                    <div 
                      data-testid="summary-text"
                      className="text-gray-300 text-sm leading-relaxed prose prose-invert max-w-none"
                      dangerouslySetInnerHTML={{ __html: formatMarkdown(summary) }}
                    />
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Enrichment */}
            {enrichment && (
              <Card data-testid="enrichment-card" className="bg-gray-900/50 backdrop-blur-sm border-gray-700/50 lg:col-span-2 xl:col-span-1">
                <CardHeader>
                  <CardTitle className="text-lg text-white flex items-center gap-2">
                    <Zap className="h-5 w-5 text-purple-400" />
                    Conteúdo Aprimorado
                    <Badge variant="secondary" className="bg-purple-500/20 text-purple-400 border-purple-500/30">
                      Enhanced
                    </Badge>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="max-h-96 overflow-y-auto bg-gray-800/30 p-4 rounded-lg border border-gray-600/30">
                    <div 
                      data-testid="enrichment-text"
                      className="text-gray-300 text-sm leading-relaxed prose prose-invert max-w-none"
                      dangerouslySetInnerHTML={{ __html: formatMarkdown(enrichment) }}
                    />
                  </div>
                </CardContent>
              </Card>
            )}
          </div>

          {/* Status Info / CTA Otimizado para SEO/Branding */}
          <div className="text-center mt-8">
            <p className="text-gray-400 text-sm">
              <span className="text-white font-semibold mr-1">Potencializado por IA.</span> 
              Precisa de uma ferramenta como essa?
              <a 
                href="[LINK DO SEU SITE DE DESENVOLVIMENTO DE SOFTWARE]" 
                target="_blank" 
                rel="noopener noreferrer" 
                className="text-cyan-400 font-bold hover:text-pink-400 transition-colors duration-200 ml-1"
              >
                Fale com a MangueBit Code sobre desenvolvimento de software.
              </a>
            </p>
          </div>
        </div>
      </div>
      
      {/* Footer */}
      <Footer /> 

    </div>
  );
}

export default App;