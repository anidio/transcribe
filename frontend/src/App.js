import { useState } from "react";
import "./App.css";
import axios from "axios";
import { Button } from "./components/ui/button";
import { Input } from "./components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "./components/ui/card";
import { Badge } from "./components/ui/badge";
import { Loader2, Youtube, Sparkles, FileText, Zap } from "lucide-react";
import { toast } from "sonner";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

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

  const setLoadingState = (action, state) => {
    setLoading(prev => ({ ...prev, [action]: state }));
  };

  const handleTranscribe = async () => {
    if (!url.trim()) {
      toast.error("Por favor, insira uma URL do YouTube");
      return;
    }

    setLoadingState('transcribe', true);
    setSummary("");
    setEnrichment("");

    try {
      const response = await axios.post(`${API}/videos/transcribe`, { url });
      setTranscript(response.data.transcript);
      toast.success("Transcrição concluída com sucesso!");
    } catch (error) {
      console.error("Erro na transcrição:", error);
      toast.error(error.response?.data?.detail || "Erro ao transcrever vídeo");
    } finally {
      setLoadingState('transcribe', false);
    }
  };

  const handleSummarize = async () => {
    if (!transcript.trim()) {
      toast.error("Primeiro obtenha a transcrição do vídeo");
      return;
    }

    setLoadingState('summarize', true);

    try {
      const response = await axios.post(`${API}/videos/summarize`, { text: transcript });
      setSummary(response.data.result);
      toast.success("Resumo gerado com sucesso!");
    } catch (error) {
      console.error("Erro no resumo:", error);
      toast.error(error.response?.data?.detail || "Erro ao gerar resumo");
    } finally {
      setLoadingState('summarize', false);
    }
  };

  const handleEnrich = async () => {
    if (!transcript.trim()) {
      toast.error("Primeiro obtenha a transcrição do vídeo");
      return;
    }

    setLoadingState('enrich', true);

    try {
      const response = await axios.post(`${API}/videos/enrich`, { text: transcript });
      setEnrichment(response.data.result);
      toast.success("Conteúdo aprimorado com sucesso!");
    } catch (error) {
      console.error("Erro no aprimoramento:", error);
      toast.error(error.response?.data?.detail || "Erro ao aprimorar conteúdo");
    } finally {
      setLoadingState('enrich', false);
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
          <p className="text-xl text-gray-300 max-w-2xl mx-auto">
            Transforme vídeos do YouTube em conteúdo estruturado com IA avançada
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

          {/* Status Info */}
          <div className="text-center mt-8">
            <p className="text-gray-400 text-sm">
              Powered by Gemini 2.5 Flash • GPT-4o • Claude 3.5 Sonnet
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;