"use client";

import { useEffect, useMemo, useRef, useState, createContext, useContext } from "react";
import { TourProvider, useTour } from "@reactour/tour";
import { AlertCircle, CheckCircle2, Loader2, Send, ChevronUp, Settings, FileDown } from "lucide-react";

import { DatasetMetrics } from "@/components/data/DatasetMetrics";
import { DataChart } from "@/components/data/DataChart";
import { PlotlyChart } from "@/components/data/PlotlyChart";
import { EvidenceTable } from "@/components/data/EvidenceTable";
import { MiniBarChart } from "@/components/data/MiniBarChart";
import { AppHeader } from "@/components/layout/AppHeader";
import { MarkdownView } from "@/components/report/MarkdownView";
import { Button } from "@/components/ui/Button";
import { Field, SelectInput, TextInput } from "@/components/ui/Field";
import {
  askAgent,
  askAgentStream,
  getDatasetOverview,
  getProviders,
  saveProvider,
} from "@/features/agent/api-client";
import { CLOUD_MODE, PROVIDERS, QUICK_QUESTIONS } from "@/features/agent/constants";
import { formatOllamaMode, getOllamaBaseUrl } from "@/lib/ollama";
import type {
  ChatResponse,
  DatasetOverview,
  OllamaMode,
  ProviderName,
  ProvidersResponse,
  ReportChart,
  ReportMetadata,
} from "@/types/api";

type Theme = "light" | "dark";
export const ThemeContext = createContext<{
  theme: Theme;
}>({
  theme: "light",
});

type Message = {
  id: string;
  question: string;
  response: ChatResponse;
  streamingAnswer?: string;
};

const TOUR_STEPS = [
  {
    selector: "[data-tour='platform-intro']",
    content:
      "Esta plataforma permite consultar datos operativos de Rappi con un agente de IA, revisar evidencia, detectar insights y generar reportes ejecutivos.",
  },
  {
    selector: "[data-tour='dataset-metrics']",
    content:
      "Estos indicadores resumen la cobertura del dataset: países, zonas, métricas y volumen analítico disponible.",
  },
  {
    selector: "[data-tour='llm-config']",
    content:
      "Primero configurá el proveedor LLM. Elegí OpenAI, Anthropic, Gemini u Ollama si está habilitado localmente.",
  },
  {
    selector: "[data-tour='api-key']",
    content:
      "Pegá la API key del proveedor y guardala. Se almacena cifrada y se limpia automáticamente cuando cerrás la sesión.",
  },
  {
    selector: "[data-tour='demo-questions']",
    content:
      "Usá estas preguntas demo para probar rankings, comparaciones, diagnósticos y tendencias sin tener que escribir desde cero.",
  },
  {
    selector: "[data-tour='chat-panel']",
    content:
      "Acá conversás con el agente. El backend guarda un history_id para que el modelo recuerde el contexto de la conversación.",
  },
  {
    selector: "[data-tour='chat-input']",
    content:
      "Escribí una pregunta operativa y enviála. El agente devuelve respuesta, tabla de evidencia, gráficos y la consulta técnica.",
  },
  {
    selector: "[data-tour='report-tab']",
    content:
      "En Executive report podés generar un informe completo con anomalías, tendencias, oportunidades, gráficos y recomendaciones. Luego podés exportarlo como PDF con gráficos o como Markdown sin gráficos.",
  },
];

export function OperationsDashboard() {
  const [overview, setOverview] = useState<DatasetOverview | null>(null);
  const [providers, setProviders] = useState<ProvidersResponse | null>(null);
  const [provider, setProvider] = useState<ProviderName>("openai");
  const [ollamaMode, setOllamaMode] = useState<OllamaMode>("local");
  const [model, setModel] = useState("gpt-4o-mini");
  const [apiKey, setApiKey] = useState("");
  const [useLlm, setUseLlm] = useState(true);
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [conversationHistoryId, setConversationHistoryId] = useState<string | null>(null);
  const [report, setReport] = useState("");
  const [reportMetadata, setReportMetadata] = useState<Omit<ReportMetadata, "type"> | null>(null);
  const [reportCharts, setReportCharts] = useState<ReportChart["chart"][]>([]);
  const [activeTab, setActiveTab] = useState<"ask" | "report" | "guide">("ask");
  const [status, setStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [theme, setTheme] = useState<Theme>("light");
  const [providerCollapsed, setProviderCollapsed] = useState(false);
  const [demoQuestionsCollapsed, setDemoQuestionsCollapsed] = useState(false);

  useEffect(() => {
    document.documentElement.classList.toggle("dark", theme === "dark");
  }, [theme]);

  useEffect(() => {
    void loadInitialData();
  }, []);

  useEffect(() => {
    function clearKeysOnExit() {
      clearProviderKeysBestEffort();
    }

    window.addEventListener("pagehide", clearKeysOnExit);
    window.addEventListener("beforeunload", clearKeysOnExit);
    return () => {
      window.removeEventListener("pagehide", clearKeysOnExit);
      window.removeEventListener("beforeunload", clearKeysOnExit);
    };
  }, []);

  function toggleTheme() {
    setTheme((prev) => (prev === "light" ? "dark" : "light"));
  }

  const isDark = theme === "dark";

  const baseUrl = useMemo(() => {
    return provider === "ollama" ? getOllamaBaseUrl(ollamaMode) : null;
  }, [ollamaMode, provider]);

  async function loadInitialData() {
    try {
      const [overviewData, providerData] = await Promise.all([
        getDatasetOverview(),
        getProviders(),
      ]);
      setOverview(overviewData);
      setProviders(providerData);

      const selectableSavedProvider = providerData.saved.find((item) =>
        PROVIDERS.includes(item.provider as ProviderName)
      );
      if (selectableSavedProvider) {
        const savedProvider = selectableSavedProvider;
        setProvider(savedProvider.provider as ProviderName);
        setModel(savedProvider.model);
        setProviderCollapsed(true);
      } else {
        setModel(resolveModelForProvider(providerData, "openai"));
      }
    } catch (requestError) {
      setError(formatError(requestError));
    }
  }

  async function handleSaveProvider() {
    setStatus(null);
    setError(null);
    try {
      const needsKey = provider !== "ollama" || ollamaMode === "cloud";
      if (needsKey && !apiKey.trim()) {
        setError("Paste an API key before saving this provider.");
        return;
      }
      await saveProvider({
        provider,
        model,
        api_key: needsKey ? apiKey : undefined,
        base_url: baseUrl ?? undefined,
        preserve_existing_key: !(provider === "ollama" && ollamaMode === "local"),
      });
      const savedModel = model;
      setApiKey("");
      setStatus("Provider configuration saved encrypted in SQLite.");
      const providerData = await getProviders();
      setProviders(providerData);
      setModel(savedModel);
    } catch (requestError) {
      setError(formatError(requestError));
    }
  }

  async function handleAsk(nextQuestion = question) {
    if (!nextQuestion.trim()) {
      return;
    }
    setLoading(true);
    setError(null);
    
    const messageId = crypto.randomUUID();
    
    if (useLlm) {
      // Create a placeholder message for streaming
      const placeholderResponse: ChatResponse = {
        answer: "",
        table: [],
        columns: [],
        suggestions: [],
        metadata: {},
        query: "",
      };
      
      setMessages((current) => [
        ...current,
        {
          id: messageId,
          question: nextQuestion,
          response: placeholderResponse,
          streamingAnswer: "",
        },
      ]);
      
      setQuestion("");
      
      try {
        await askAgentStream(
          {
            question: nextQuestion,
            history_id: conversationHistoryId,
            provider: provider,
            model: model,
            base_url: baseUrl,
            require_llm: useLlm,
          },
          (chunk) => {
            if (chunk.type === "history") {
              setConversationHistoryId(chunk.history_id);
            } else if (chunk.type === "table") {
              // Update the message with table data
              setMessages((current) =>
                current.map((msg) =>
                  msg.id === messageId
                    ? {
                        ...msg,
                        response: {
                          ...msg.response,
                          table: chunk.table as Record<string, unknown>[],
                          columns: chunk.columns || [],
                          suggestions: chunk.suggestions || [],
                          query: chunk.query || "",
                        },
                      }
                    : msg
                )
              );
            } else if (chunk.type === "chunk") {
              // Append streaming content
              setMessages((current) =>
                current.map((msg) =>
                  msg.id === messageId
                    ? {
                        ...msg,
                        streamingAnswer: (msg.streamingAnswer || "") + (chunk.content || ""),
                      }
                    : msg
                )
              );
            } else if (chunk.type === "error") {
              setError(chunk.error || "Unknown error");
            }
          }
        );
        
        // Finalize: move streaming answer to response
        setMessages((current) =>
          current.map((msg) => {
            if (msg.id === messageId && msg.streamingAnswer) {
              return {
                ...msg,
                response: {
                  ...msg.response,
                  answer: msg.streamingAnswer,
                },
                streamingAnswer: undefined,
              };
            }
            return msg;
          })
        );
      } catch (requestError) {
        setError(formatError(requestError));
        // Remove the placeholder message on error
        setMessages((current) => current.filter((msg) => msg.id !== messageId));
      } finally {
        setLoading(false);
      }
    } else {
      // Non-streaming mode (without LLM)
      try {
        const response = await askAgent({
          question: nextQuestion,
          history_id: conversationHistoryId,
          provider: null,
          model: null,
          base_url: null,
          require_llm: false,
        });
        if (response.history_id) {
          setConversationHistoryId(response.history_id);
        }
        setMessages((current) => [
          ...current,
          {
            id: messageId,
            question: nextQuestion,
            response,
          },
        ]);
        setQuestion("");
      } catch (requestError) {
        setError(formatError(requestError));
      } finally {
        setLoading(false);
      }
    }
  }

  async function handleReport() {
    setLoading(true);
    setError(null);
    setReport("");
    setReportMetadata(null);
    setReportCharts([]);
    setActiveTab("report");

    const reportQuestion = "Genera el reporte ejecutivo con todas las anomalías, tendencias, oportunidades y análisis";

    try {
      await askAgentStream(
        {
          question: reportQuestion,
          history_id: conversationHistoryId,
          provider,
          model,
          base_url: baseUrl,
          require_llm: useLlm,
        },
        (chunk) => {
          if (chunk.type === "history") {
            setConversationHistoryId(chunk.history_id);
          } else if (chunk.type === "metadata") {
            setReportMetadata({
              timestamp: chunk.timestamp,
              insights_count: chunk.insights_count,
              query_info: chunk.query_info,
            });
          } else if (chunk.type === "chart" && chunk.chart) {
            setReportCharts((prev) => [...prev, chunk.chart]);
          } else if (chunk.type === "chunk" && typeof chunk.content === "string") {
            setReport((current) => current + chunk.content);
          } else if (chunk.type === "error") {
            setError(chunk.error || "Unknown error");
          }
        },
      );
    } catch (requestError) {
      setError(formatError(requestError));
    } finally {
      setLoading(false);
    }
  }

  function handleExportReport() {
    setActiveTab("report");
    window.requestAnimationFrame(() => {
      window.print();
    });
  }

  function handleExportReportMarkdown() {
    if (!report) {
      return;
    }
    const markdown = buildReportMarkdown(report, reportMetadata);
    const filename = `executive-report-${new Date().toISOString().slice(0, 10)}.md`;
    downloadTextFile(filename, markdown, "text/markdown;charset=utf-8");
  }

  const savedProvider = providers?.saved.find((item) => item.provider === provider);
  const keyIsConfigured =
    provider === "ollama" && ollamaMode === "local"
      ? true
      : Boolean(savedProvider?.has_api_key);

  return (
    <ThemeContext.Provider value={{ theme }}>
      <TourProvider
        steps={TOUR_STEPS}
        nextButton={({ currentStep, setCurrentStep, setIsOpen, stepsLength }) => {
          const isLastStep = currentStep === stepsLength - 1;
          return (
            <button
              className="rounded-lg bg-[image:var(--accent-gradient)] px-3 py-2 text-sm font-bold text-white"
              onClick={() => {
                if (isLastStep) {
                  setIsOpen(false);
                  setCurrentStep(0);
                  return;
                }
                setCurrentStep((step) => step + 1);
              }}
              type="button"
            >
              {isLastStep ? "Finalizar" : "Siguiente"}
            </button>
          );
        }}
        prevButton={({ currentStep, setCurrentStep }) => (
          <button
            className="rounded-lg border border-[var(--border)] bg-[var(--surface)] px-3 py-2 text-sm font-semibold text-[var(--foreground)] disabled:cursor-not-allowed disabled:opacity-40"
            disabled={currentStep === 0}
            onClick={() => setCurrentStep((step) => Math.max(step - 1, 0))}
            type="button"
          >
            Anterior
          </button>
        )}
        styles={{
          popover: (base) => ({
            ...base,
            backgroundColor: theme === "dark" ? "#1f1f1f" : "#ffffff",
            borderRadius: 8,
            color: theme === "dark" ? "#f3f4f6" : "#1f1f1f",
          }),
          badge: (base) => ({
            ...base,
            background: "linear-gradient(135deg, #ff3b30 0%, #ff7a1a 100%)",
          }),
        }}
      >
      <main className="page-shell">
        <div className="no-print">
          <div data-tour="platform-intro">
            <AppHeader theme={theme} onToggleTheme={toggleTheme} />
          </div>
          <div data-tour="dataset-metrics">
            <DatasetMetrics overview={overview} loading={!overview && !error} />
          </div>
        </div>

      <div className="grid min-w-0 gap-4 lg:grid-cols-[360px_minmax(0,1fr)]">
        <aside className="no-print space-y-4">
          <section className="panel p-4" data-tour="llm-config">
            <div className="mb-3 flex items-center justify-between">
              <h2 className="text-lg font-bold">LLM provider</h2>
              <button
                className="flex items-center gap-1 rounded p-1 text-sm hover:bg-gray-100 dark:hover:bg-gray-800"
                onClick={() => setProviderCollapsed(!providerCollapsed)}
              >
                {providerCollapsed ? (
                  <>
                    <Settings size={16} />
                    <span className="text-xs">Configurar</span>
                  </>
                ) : (
                  <>
                    <ChevronUp size={16} />
                  </>
                )}
              </button>
            </div>
            {providerCollapsed || !providers?.saved.length ? null : (
              <div className={`mb-3 rounded-lg border p-3 text-sm ${isDark ? 'border-[#7a2a1a] bg-[#3a2018]' : 'border-[#ffd1bc] bg-[#fff0e7]'}`}>
                <div className={`flex items-center gap-2 font-medium ${isDark ? 'text-orange-200' : 'text-[#9a3412]'}`}>
                  <CheckCircle2 className="text-[var(--accent)]" size={16} />
                  Provider configurado
                </div>
                <p className={`mt-1 text-xs ${isDark ? 'text-orange-200' : 'text-[#9a3412]'}`}>
                  {provider} - {model}
                </p>
              </div>
            )}
            {!providerCollapsed ? (
              <div className="space-y-3">
                <Field label="Provider">
                  <SelectInput
                    value={provider}
                    onChange={(event) => {
                      const nextProvider = event.target.value as ProviderName;
                      setProvider(nextProvider);
                      if (providers) {
                        setModel(resolveModelForProvider(providers, nextProvider));
                      }
                    }}
                  >
                    {PROVIDERS.map((item) => (
                      <option key={item} value={item}>
                        {item}
                      </option>
                    ))}
                  </SelectInput>
                </Field>

                {provider === "ollama" && !CLOUD_MODE ? (
                  <Field label="Ollama mode">
                    <SelectInput
                      value={ollamaMode}
                      onChange={(event) =>
                        setOllamaMode(event.target.value as OllamaMode)
                      }
                    >
                      <option value="local">{formatOllamaMode("local")}</option>
                      <option value="cloud">{formatOllamaMode("cloud")}</option>
                    </SelectInput>
                  </Field>
                ) : null}

                {baseUrl ? (
                  <Field label="Base URL">
                    <TextInput disabled value={baseUrl} />
                  </Field>
                ) : null}

                <Field label="Model">
                  <TextInput value={model} onChange={(event) => setModel(event.target.value)} />
                </Field>

                <div data-tour="api-key">
                <Field
                  label="API key"
                  help={
                    provider === "ollama" && ollamaMode === "local"
                      ? "Local Ollama does not require a key."
                      : "Stored encrypted with Fernet in SQLite."
                  }
                >
                  <TextInput
                    disabled={provider === "ollama" && ollamaMode === "local"}
                    placeholder="Paste key and save"
                    type="password"
                    value={apiKey}
                    onChange={(event) => setApiKey(event.target.value)}
                  />
                </Field>
                </div>

                <label className="flex items-center gap-2 text-sm">
                  <input
                    checked={useLlm}
                    type="checkbox"
                    onChange={(event) => setUseLlm(event.target.checked)}
                  />
                  Use LangGraph LLM agent
                </label>

                <Button className="w-full" onClick={handleSaveProvider} variant="primary">
                  Save encrypted provider config
                </Button>

                <div className="text-theme-muted flex items-center gap-2 text-sm">
                  {keyIsConfigured ? (
                    <CheckCircle2 className="text-[var(--accent)]" size={16} />
                  ) : (
                    <AlertCircle className="text-[#c67821]" size={16} />
                  )}
                  {keyIsConfigured ? "Provider ready" : "API key not configured"}
                </div>
                {CLOUD_MODE ? (
                  <p className="text-theme-muted text-xs">
                    Cloud mode enabled: local Ollama is disabled.
                  </p>
                ) : null}
              </div>
            ) : null}
          </section>

          <div className="panel max-h-[60dvh] overflow-y-auto p-4" data-tour="demo-questions">
            <div className="mb-3 flex items-center justify-between">
              <h2 className="text-lg font-bold">Demo questions</h2>
              <button
                className="flex items-center gap-1 rounded p-1 text-sm hover:bg-[var(--accent-soft)]"
                onClick={() => setDemoQuestionsCollapsed(!demoQuestionsCollapsed)}
              >
                {demoQuestionsCollapsed ? (
                  <>
                    <Settings size={16} />
                    <span className="text-xs">Mostrar</span>
                  </>
                ) : (
                  <ChevronUp size={16} />
                )}
              </button>
            </div>
            {!demoQuestionsCollapsed ? (
              <div className="space-y-4">
                {Object.entries(QUICK_QUESTIONS).map(([group, questions]) => (
                  <div key={group}>
                    <h3 className="mb-2 text-sm font-bold text-[var(--accent)]">{group}</h3>
                    <div className="space-y-2">
                      {questions.map((item) => (
                        <button
                          className="focus-ring w-full rounded-lg border border-[var(--border)] bg-[var(--surface)] px-3 py-2 text-left text-sm text-[var(--foreground)] hover:border-[var(--accent)]"
                          key={item}
                          onClick={() => void handleAsk(item)}
                        >
                          {item}
                        </button>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            ) : null}
          </div>
        </aside>

        <section className="panel min-w-0 min-h-[720px] p-4">
          <div className="no-print mb-4 flex flex-wrap gap-2 border-b border-[var(--border)] pb-3">
            <TabButton active={activeTab === "ask"} onClick={() => setActiveTab("ask")}>
              Ask the agent
            </TabButton>
            <TabButton
              active={activeTab === "report"}
              onClick={() => setActiveTab("report")}
              tourId="report-tab"
            >
              Executive report
            </TabButton>
            <TabButton
              active={activeTab === "guide"}
              onClick={() => setActiveTab("guide")}
            >
              Demo guide
            </TabButton>
          </div>

          {status ? <StatusMessage tone="success">{status}</StatusMessage> : null}
          {error ? <StatusMessage tone="error">{error}</StatusMessage> : null}

          {activeTab === "ask" ? (
            <ChatPanel
              loading={loading}
              messages={messages}
              question={question}
              setMessages={setMessages}
              onClearHistory={() => setConversationHistoryId(null)}
              setQuestion={setQuestion}
              onAsk={() => void handleAsk()}
            />
          ) : null}

          {activeTab === "report" ? (
            <div className="report-print-area min-w-0 space-y-4">
              <div className="flex min-w-0 flex-wrap items-center justify-between gap-3">
                <div className="min-w-0">
                  <h2 className="text-xl font-bold">Executive report</h2>
                  <p className="text-theme-muted text-sm">
                    {reportMetadata
                      ? `Generado el ${new Date(reportMetadata.timestamp).toLocaleString()} - ${reportMetadata.insights_count} insights - ${reportMetadata.query_info?.total_zones || 0} zonas - ${reportMetadata.query_info?.time_period || ''}`
                      : "Generado por IA con análisis de anomalías, tendencias y oportunidades."}
                  </p>
                </div>
                <div className="no-print flex flex-wrap gap-2" data-tour="report-actions">
                  <Button
                    className="inline-flex items-center gap-2"
                    disabled={!report && reportCharts.length === 0}
                    onClick={handleExportReport}
                  >
                    <FileDown size={17} />
                    Export PDF
                  </Button>
                  <Button
                    className="inline-flex items-center gap-2"
                    disabled={!report}
                    onClick={handleExportReportMarkdown}
                  >
                    <FileDown size={17} />
                    Export MD
                  </Button>
                  <Button disabled={loading} onClick={() => void handleReport()} variant="primary">
                    {loading ? "Generating..." : "Generate report now"}
                  </Button>
                </div>
              </div>
              {reportMetadata?.query_info?.technical_query ? (
                <section className="no-print rounded-lg border border-[var(--border)] bg-[var(--surface)] p-3 text-[var(--foreground)]">
                  <h3 className="mb-2 text-sm font-semibold">Consulta técnica del informe</h3>
                  <pre className="overflow-x-auto rounded-lg border border-[var(--border)] bg-[var(--background)] p-3 text-xs text-[var(--foreground)]">
                    <code>{reportMetadata.query_info.technical_query}</code>
                  </pre>
                </section>
              ) : null}
              {reportCharts.length > 0 && (
                <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
                  {reportCharts.map((chart, idx) => (
                    <div key={idx} className="rounded-lg border border-[var(--border)] p-3">
                      <h3 className="mb-2 text-sm font-semibold">{chart.title}</h3>
                      <PlotlyChart data={chart.data as Record<string, unknown>} title={chart.title} />
                    </div>
                  ))}
                </div>
              )}
              {report ? (
                <div className="report-markdown max-h-[70vh] min-w-0 overflow-y-auto overflow-x-hidden rounded-lg border border-[var(--border)] bg-[var(--surface)] p-4 text-[var(--foreground)]">
                  <MarkdownView markdown={report} />
                </div>
              ) : (
                <p className="no-print text-theme-muted rounded-lg bg-[var(--background)] p-4 text-sm">
                  Generate the report when you want to review executive insights.
                </p>
              )}
            </div>
          ) : null}

          {activeTab === "guide" ? <DemoGuide /> : null}
        </section>
      </div>
    </main>
      <TourLauncher />
      </TourProvider>
    </ThemeContext.Provider>
  );
}

function ChatPanel({
  loading,
  messages,
  question,
  setMessages,
  onClearHistory,
  setQuestion,
  onAsk,
}: {
  loading: boolean;
  messages: Message[];
  question: string;
  setMessages: (messages: Message[]) => void;
  onClearHistory: () => void;
  setQuestion: (value: string) => void;
  onAsk: () => void;
}) {
  const { theme } = useContext(ThemeContext);
  const isDark = theme === "dark";
  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (loading && messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [loading, messagesEndRef]);

  return (
    <div
      className={`flex h-[60dvh] min-h-[420px] flex-col overflow-hidden ${isDark ? 'bg-gray-900' : 'bg-gray-100'}`}
      data-tour="chat-panel"
    >
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {!messages.length ? (
          <p className={`text-theme-muted rounded-lg p-4 text-sm ${isDark ? 'bg-gray-800' : 'bg-gray-100'}`}>
            Start with a demo question from the sidebar or type your own.
          </p>
        ) : (
          messages.map((message) => (
            <div key={message.id} className="space-y-3">
              <div className={`rounded-lg p-3 ${isDark ? 'border border-[#7a2a1a] bg-[#3a2018]' : 'border border-[#ff4f2e] bg-[#fff0e7]'}`}>
                <p className="text-sm font-semibold text-[var(--accent)]">
                  You: {message.question}
                </p>
              </div>
              <article className={`min-w-0 overflow-hidden rounded-lg border p-4 ${isDark ? 'border-gray-700 bg-gray-800' : 'border-gray-200 bg-white'}`} key={message.id}>
                <div className="text-theme mb-4 min-w-0 text-sm leading-6">
                  <MarkdownView markdown={message.streamingAnswer || message.response.answer} />
                  {loading && message.streamingAnswer !== undefined && (
                    <span className="animate-pulse">▊</span>
                  )}
                </div>
                <ResponseMetadata metadata={message.response.metadata} />
                <div className="grid gap-4 xl:grid-cols-2">
                  <EvidenceTable
                    columns={message.response.columns}
                    rows={message.response.table}
                    query={message.response.query}
                  />
                  <DataChart
                    columns={message.response.columns}
                    rows={message.response.table}
                  />
                  <MiniBarChart
                    columns={message.response.columns}
                    rows={message.response.table}
                  />
                </div>
              </article>
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      <div
        className={`flex gap-2 p-4 border-t ${isDark ? 'border-gray-700 bg-gray-800' : 'border-gray-200 bg-white'}`}
        data-tour="chat-input"
      >
        <TextInput
          placeholder="Ask about rankings, trends, comparisons or problematic zones"
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter") {
              onAsk();
            }
          }}
        />
        <Button disabled={loading} onClick={onAsk} variant="primary">
          {loading ? <Loader2 className="animate-spin" size={17} /> : <Send size={17} />}
        </Button>
        <Button
          disabled={!messages.length}
          onClick={() => {
            setMessages([]);
            onClearHistory();
          }}
        >
          Clear
        </Button>
      </div>
    </div>
  );
}

function DemoGuide() {
  return (
    <div className="text-theme space-y-4 text-sm">
      <h2 className="text-xl font-bold">Demo script</h2>
      <ol className="list-decimal space-y-2 pl-5">
        <li>Show dataset coverage at the top.</li>
        <li>Ask for top Lead Penetration zones.</li>
        <li>Compare Perfect Orders in Mexico by zone type.</li>
        <li>Show Gross Profit UE trend in Chapinero.</li>
        <li>Ask for high Lead Penetration and low Perfect Orders.</li>
        <li>Generate the executive report.</li>
      </ol>
      <h2 className="text-xl font-bold">Positioning</h2>
      <p>
        The UI uses Next.js and React. LangGraph coordinates planning and response
        writing with the selected LLM provider, while pandas tools keep the evidence
        auditable.
      </p>
    </div>
  );
}

function ResponseMetadata({
  metadata,
}: {
  metadata: Record<string, unknown>;
}) {
  const provider = typeof metadata.provider === "string" ? metadata.provider : null;
  const model = typeof metadata.model === "string" ? metadata.model : null;
  if (!provider && !model) {
    return null;
  }

  return (
    <p className="text-theme mb-4 rounded-lg bg-[var(--accent-soft)] px-3 py-2 text-xs font-semibold">
      Running with {provider ?? "unknown provider"} / {model ?? "unknown model"}
    </p>
  );
}

function TourLauncher() {
  const { setIsOpen } = useTour();

  useEffect(() => {
    const tourWasSeen = window.localStorage.getItem("rappi-tour-seen") === "true";
    if (!tourWasSeen) {
      window.localStorage.setItem("rappi-tour-seen", "true");
      window.requestAnimationFrame(() => setIsOpen(true));
    }
  }, [setIsOpen]);

  return (
    <button
      className="no-print fixed bottom-5 right-5 z-50 rounded-lg bg-[image:var(--accent-gradient)] px-4 py-3 text-sm font-bold text-white shadow-lg"
      onClick={() => setIsOpen(true)}
      type="button"
    >
      Guía rápida
    </button>
  );
}

function TabButton({
  active,
  children,
  onClick,
  tourId,
}: {
  active: boolean;
  children: string;
  onClick: () => void;
  tourId?: string;
}) {
  const { theme } = useContext(ThemeContext);
  const isDark = theme === "dark";

  return (
    <button
      className={`focus-ring px-4 py-2 text-sm font-semibold ${
        active
          ? "bg-[image:var(--accent-gradient)] text-white"
          : `border text-theme ${isDark ? 'border-gray-600 bg-gray-800' : 'border-gray-300 bg-white'}`
      }`}
      data-tour={tourId}
      onClick={onClick}
    >
      {children}
    </button>
  );
}

function StatusMessage({
  children,
  tone,
}: {
  children: string;
  tone: "success" | "error";
}) {
  const { theme } = useContext(ThemeContext);
  const isDark = theme === "dark";

  const className =
    tone === "success"
      ? `mb-3 rounded-lg border p-3 text-sm ${isDark ? 'border-[#7a2a1a] bg-[#3a2018] text-orange-200' : 'border-[#ffd1bc] bg-[#fff0e7] text-[#9a3412]'}`
      : `mb-3 rounded-lg border p-3 text-sm ${isDark ? 'border-red-800 bg-red-950 text-red-200' : 'border-[#f0c5b4] bg-[#fff3ef] text-[#8b3519]'}`;
  return <p className={className}>{children}</p>;
}

function formatError(error: unknown): string {
  return error instanceof Error ? error.message : "Unexpected error";
}

function buildReportMarkdown(
  report: string,
  metadata: Omit<ReportMetadata, "type"> | null,
): string {
  const lines = [report.trim()];
  const technicalQuery = metadata?.query_info?.technical_query;
  if (technicalQuery) {
    lines.push(
      "",
      "## Consulta técnica del informe",
      "",
      "```text",
      technicalQuery,
      "```",
    );
  }
  return `${lines.join("\n")}\n`;
}

function downloadTextFile(filename: string, content: string, type: string) {
  const blob = new Blob([content], { type });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

function clearProviderKeysBestEffort() {
  const payload = JSON.stringify({ reason: "client_exit" });
  if (navigator.sendBeacon) {
    const blob = new Blob([payload], { type: "application/json" });
    navigator.sendBeacon("/api/providers/clear", blob);
    return;
  }

  void fetch("/api/providers/clear", {
    method: "POST",
    body: payload,
    headers: { "Content-Type": "application/json" },
    keepalive: true,
  }).catch(() => {
    // Page unload cleanup is best effort.
  });
}

function resolveModelForProvider(
  providers: ProvidersResponse,
  provider: ProviderName,
): string {
  const savedProvider = providers.saved.find((item) => item.provider === provider);
  return savedProvider?.model ?? providers.defaultModels[provider];
}
