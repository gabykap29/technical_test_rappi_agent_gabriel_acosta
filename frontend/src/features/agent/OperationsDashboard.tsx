"use client";

import { useEffect, useMemo, useState, createContext, useContext, type Dispatch, type SetStateAction } from "react";
import { AlertCircle, CheckCircle2, Loader2, Send, Moon, Sun, ChevronUp, ChevronDown, Settings } from "lucide-react";

import { DatasetMetrics } from "@/components/data/DatasetMetrics";
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
import { PROVIDERS, QUICK_QUESTIONS } from "@/features/agent/constants";
import { formatOllamaMode, getOllamaBaseUrl } from "@/lib/ollama";
import type {
  ChatResponse,
  DatasetOverview,
  OllamaMode,
  ProviderName,
  ProvidersResponse,
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
  const [report, setReport] = useState("");
  const [activeTab, setActiveTab] = useState<"ask" | "report" | "guide">("ask");
  const [status, setStatus] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [theme, setTheme] = useState<Theme>("light");
  const [providerCollapsed, setProviderCollapsed] = useState(false);

  useEffect(() => {
    document.documentElement.classList.toggle("dark", theme === "dark");
  }, [theme]);

  useEffect(() => {
    void loadInitialData();
  }, []);

  function toggleTheme() {
    setTheme((prev) => (prev === "light" ? "dark" : "light"));
  }

  const { theme: themeFromContext } = useContext(ThemeContext);
  const isDark = themeFromContext === "dark";

  const baseUrl = useMemo(() => {
    return provider === "ollama" ? getOllamaBaseUrl(ollamaMode) : null;
  }, [ollamaMode, provider]);

  useEffect(() => {
    void loadInitialData();
  }, []);

  async function loadInitialData() {
    try {
      const [overviewData, providerData] = await Promise.all([
        getDatasetOverview(),
        getProviders(),
      ]);
      setOverview(overviewData);
      setProviders(providerData);
      
      if (providerData.saved.length > 0) {
        const savedProvider = providerData.saved[0];
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
            provider: provider,
            model: model,
            base_url: baseUrl,
            require_llm: useLlm,
          },
          (chunk) => {
            if (chunk.type === "table") {
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
          provider: null,
          model: null,
          base_url: null,
          require_llm: false,
        });
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

  function handleReport() {
    setLoading(true);
    setError(null);
    setReport("");
    setActiveTab("report");

    const question = "Genera el reporte ejecutivo con todas las anomalías, tendencias, oportunidades y análisis";
    const messageId = crypto.randomUUID();

    setMessages((current) => [
      ...current,
      {
        id: messageId,
        question,
        response: {
          answer: "",
          table: [],
          columns: [],
          suggestions: [],
          metadata: {},
          query: "",
        },
      },
    ]);

    askAgentStream(
      {
        question,
        provider: provider,
        model: model,
        base_url: baseUrl,
        require_llm: useLlm,
      },
      (chunk) => {
        if (chunk.type === "table") {
          setReport((prev) => prev + (chunk.content || ""));
        } else if (chunk.type === "chunk") {
          setReport((prev) => prev + (chunk.content || ""));
          setLoading(false);
        } else if (chunk.type === "error") {
          setError(chunk.error || "Unknown error");
          setLoading(false);
        }
      }
    );
  }

  const savedProvider = providers?.saved.find((item) => item.provider === provider);
  const keyIsConfigured =
    provider === "ollama" && ollamaMode === "local"
      ? true
      : Boolean(savedProvider?.has_api_key);

  return (
    <ThemeContext.Provider value={{ theme }}>
      <main className="page-shell">
        <AppHeader theme={theme} onToggleTheme={toggleTheme} />
        <DatasetMetrics overview={overview} loading={!overview && !error} />

      <div className="grid gap-4 lg:grid-cols-[360px_1fr]">
        <aside className="space-y-4">
          <section className="panel p-4">
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
              <div className={`mb-3 rounded-lg border p-3 text-sm ${isDark ? 'border-green-800 bg-green-950' : 'border-[#badbc7] bg-[#edf8f1]'}`}>
                <div className={`flex items-center gap-2 font-medium ${isDark ? 'text-green-200' : 'text-green-800'}`}>
                  <CheckCircle2 className={isDark ? 'text-green-400' : 'text-[#16834f]'} size={16} />
                  Provider configurado
                </div>
                <p className={`mt-1 text-xs ${isDark ? 'text-green-300' : 'text-green-700'}`}>
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

                {provider === "ollama" ? (
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
                    <CheckCircle2 className="text-[#16834f]" size={16} />
                  ) : (
                    <AlertCircle className="text-[#c67821]" size={16} />
                  )}
                  {keyIsConfigured ? "Provider ready" : "API key not configured"}
                </div>
              </div>
            ) : null}
          </section>

          <section className="panel p-4">
            <h2 className="text-theme mb-3 text-lg font-bold">Demo questions</h2>
            <div className="space-y-4">
              {Object.entries(QUICK_QUESTIONS).map(([group, questions]) => (
                <div key={group}>
                  <h3 className={`mb-2 text-sm font-bold ${isDark ? 'text-green-400' : 'text-[#315246]'}`}>{group}</h3>
                  <div className="space-y-2">
                    {questions.map((item) => (
                      <button
                        className={`focus-ring w-full rounded-lg border px-3 py-2 text-left text-sm ${isDark ? 'border-gray-700 bg-gray-800 text-gray-200 hover:border-green-500' : 'border-[#d9e4dd] bg-white hover:border-[#16834f]'}`}
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
          </section>
        </aside>

        <section className="panel min-h-[720px] p-4">
          <div className="mb-4 flex flex-wrap gap-2 border-b border-[var(--border)] pb-3">
            <TabButton active={activeTab === "ask"} onClick={() => setActiveTab("ask")}>
              Ask the agent
            </TabButton>
            <TabButton
              active={activeTab === "report"}
              onClick={() => setActiveTab("report")}
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
              setQuestion={setQuestion}
              onAsk={() => void handleAsk()}
              onSuggestion={(suggestion) => void handleAsk(suggestion)}
            />
          ) : null}

          {activeTab === "report" ? (
            <div className="space-y-4">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <h2 className="text-xl font-bold">Executive report</h2>
                  <p className="text-theme-muted text-sm">
                    Generado por IA con análisis de anomalías, tendencias y oportunidades.
                  </p>
                </div>
                <Button disabled={loading} onClick={handleReport} variant="primary">
                  {loading ? "Generating..." : "Generate report now"}
                </Button>
              </div>
              {report ? (
                <div className={`rounded-lg border p-4 ${isDark ? "border-gray-700 bg-gray-800" : "border-[#d9e4dd] bg-white"}`}>
                  <MarkdownView markdown={report} />
                </div>
              ) : (
                <p className={`text-theme-muted rounded-lg p-4 text-sm ${isDark ? "bg-gray-800" : "bg-[#f1f6f3]"}`}>
                  Generate the report when you want to review executive insights.
                </p>
              )}
            </div>
          ) : null}

          {activeTab === "guide" ? <DemoGuide /> : null}
        </section>
      </div>
    </main>
    </ThemeContext.Provider>
  );
}

function ChatPanel({
  loading,
  messages,
  question,
  setMessages,
  setQuestion,
  onAsk,
  onSuggestion,
}: {
  loading: boolean;
  messages: Message[];
  question: string;
  setMessages: (messages: Message[]) => void;
  setQuestion: (value: string) => void;
  onAsk: () => void;
  onSuggestion: (question: string) => void;
}) {
  const { theme } = useContext(ThemeContext);
  const isDark = theme === "dark";

  return (
    <div className="space-y-4">
      <div className="flex gap-2">
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
        <Button disabled={!messages.length} onClick={() => setMessages([])}>
          Clear
        </Button>
      </div>

      {!messages.length ? (
        <p className={`text-theme-muted rounded-lg p-4 text-sm ${isDark ? 'bg-gray-800' : 'bg-[#f1f6f3]'}`}>
          Start with a demo question from the sidebar or type your own.
        </p>
      ) : null}

      <div className="space-y-4">
        {messages.map((message) => (
          <article className={`rounded-lg border p-4 ${isDark ? 'border-gray-700 bg-gray-800' : 'border-[#d9e4dd] bg-white'}`} key={message.id}>
            <p className={`mb-3 text-sm font-semibold ${isDark ? 'text-green-400' : 'text-[#315246]'}`}>
              {message.question}
            </p>
            <div className="text-theme mb-4 text-sm leading-6">
              <MarkdownView markdown={message.streamingAnswer || message.response.answer} />
              {message.streamingAnswer !== undefined && (
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
              <MiniBarChart
                columns={message.response.columns}
                rows={message.response.table}
              />
            </div>
            {message.response.suggestions.length ? (
              <div className="mt-4 flex flex-wrap gap-2">
                {message.response.suggestions.map((suggestion) => (
                  <Button
                    key={suggestion}
                    onClick={() => onSuggestion(suggestion)}
                    variant="ghost"
                  >
                    {suggestion}
                  </Button>
                ))}
              </div>
            ) : null}
          </article>
        ))}
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

function TabButton({
  active,
  children,
  onClick,
}: {
  active: boolean;
  children: string;
  onClick: () => void;
}) {
  const { theme } = useContext(ThemeContext);
  const isDark = theme === "dark";

  return (
    <button
      className={`focus-ring px-4 py-2 text-sm font-semibold ${
        active
          ? "bg-[#16834f] text-white"
          : `border text-theme ${isDark ? 'border-gray-600 bg-gray-800' : 'border-[#cbd9d1] bg-white'}`
      }`}
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
      ? `mb-3 rounded-lg border p-3 text-sm ${isDark ? 'border-green-800 bg-green-950 text-green-200' : 'border-[#badbc7] bg-[#edf8f1] text-[#235a3a]'}`
      : `mb-3 rounded-lg border p-3 text-sm ${isDark ? 'border-red-800 bg-red-950 text-red-200' : 'border-[#f0c5b4] bg-[#fff3ef] text-[#8b3519]'}`;
  return <p className={className}>{children}</p>;
}

function formatError(error: unknown): string {
  return error instanceof Error ? error.message : "Unexpected error";
}

function resolveModelForProvider(
  providers: ProvidersResponse,
  provider: ProviderName,
): string {
  const savedProvider = providers.saved.find((item) => item.provider === provider);
  return savedProvider?.model ?? providers.defaultModels[provider];
}
