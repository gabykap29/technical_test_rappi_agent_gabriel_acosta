"use client";

import { useEffect, useMemo, useState } from "react";
import { AlertCircle, CheckCircle2, Loader2, Send } from "lucide-react";

import { DatasetMetrics } from "@/components/data/DatasetMetrics";
import { EvidenceTable } from "@/components/data/EvidenceTable";
import { MiniBarChart } from "@/components/data/MiniBarChart";
import { AppHeader } from "@/components/layout/AppHeader";
import { MarkdownView } from "@/components/report/MarkdownView";
import { Button } from "@/components/ui/Button";
import { Field, SelectInput, TextInput } from "@/components/ui/Field";
import {
  askAgent,
  getDatasetOverview,
  getExecutiveReport,
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

type Message = {
  id: string;
  question: string;
  response: ChatResponse;
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

  const baseUrl = useMemo(() => {
    return provider === "ollama" ? getOllamaBaseUrl(ollamaMode) : null;
  }, [ollamaMode, provider]);

  useEffect(() => {
    void loadInitialData();
  }, []);

  useEffect(() => {
    const defaultModel = providers?.defaultModels[provider];
    if (defaultModel) {
      setModel(defaultModel);
    }
  }, [provider, providers]);

  async function loadInitialData() {
    try {
      const [overviewData, providerData] = await Promise.all([
        getDatasetOverview(),
        getProviders(),
      ]);
      setOverview(overviewData);
      setProviders(providerData);
      setModel(providerData.defaultModels.openai);
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
      setApiKey("");
      setStatus("Provider configuration saved encrypted in SQLite.");
      const providerData = await getProviders();
      setProviders(providerData);
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
    try {
      const response = await askAgent({
        question: nextQuestion,
        provider: useLlm ? provider : null,
        model: useLlm ? model : null,
        base_url: useLlm ? baseUrl : null,
        require_llm: useLlm,
      });
      setMessages((current) => [
        ...current,
        {
          id: crypto.randomUUID(),
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

  async function handleReport() {
    setLoading(true);
    setError(null);
    try {
      const response = await getExecutiveReport();
      setReport(response.markdown);
      setActiveTab("report");
    } catch (requestError) {
      setError(formatError(requestError));
    } finally {
      setLoading(false);
    }
  }

  const savedProvider = providers?.saved.find((item) => item.provider === provider);
  const keyIsConfigured =
    provider === "ollama" && ollamaMode === "local"
      ? true
      : Boolean(savedProvider?.has_api_key);

  return (
    <main className="page-shell">
      <AppHeader />
      <DatasetMetrics overview={overview} loading={!overview && !error} />

      <div className="grid gap-4 lg:grid-cols-[360px_1fr]">
        <aside className="space-y-4">
          <section className="panel p-4">
            <h2 className="mb-3 text-lg font-bold">LLM provider</h2>
            <div className="space-y-3">
              <Field label="Provider">
                <SelectInput
                  value={provider}
                  onChange={(event) => setProvider(event.target.value as ProviderName)}
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

              <div className="flex items-center gap-2 text-sm text-[#53625b]">
                {keyIsConfigured ? (
                  <CheckCircle2 className="text-[#16834f]" size={16} />
                ) : (
                  <AlertCircle className="text-[#c67821]" size={16} />
                )}
                {keyIsConfigured ? "Provider ready" : "API key not configured"}
              </div>
            </div>
          </section>

          <section className="panel p-4">
            <h2 className="mb-3 text-lg font-bold">Demo questions</h2>
            <div className="space-y-4">
              {Object.entries(QUICK_QUESTIONS).map(([group, questions]) => (
                <div key={group}>
                  <h3 className="mb-2 text-sm font-bold text-[#315246]">{group}</h3>
                  <div className="space-y-2">
                    {questions.map((item) => (
                      <button
                        className="focus-ring w-full rounded-lg border border-[#d9e4dd] bg-white px-3 py-2 text-left text-sm hover:border-[#16834f]"
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
          <div className="mb-4 flex flex-wrap gap-2 border-b border-[#d9e4dd] pb-3">
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
                  <p className="text-sm text-[#66746d]">
                    Auto-generated from anomalies, trends, benchmarks and opportunities.
                  </p>
                </div>
                <Button disabled={loading} onClick={handleReport} variant="primary">
                  {loading ? "Generating..." : "Generate report now"}
                </Button>
              </div>
              {report ? (
                <div className="rounded-lg border border-[#d9e4dd] bg-white p-4">
                  <MarkdownView markdown={report} />
                </div>
              ) : (
                <p className="rounded-lg bg-[#f1f6f3] p-4 text-sm text-[#53625b]">
                  Generate the report when you want to review executive insights.
                </p>
              )}
            </div>
          ) : null}

          {activeTab === "guide" ? <DemoGuide /> : null}
        </section>
      </div>
    </main>
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
        <p className="rounded-lg bg-[#f1f6f3] p-4 text-sm text-[#53625b]">
          Start with a demo question from the sidebar or type your own.
        </p>
      ) : null}

      <div className="space-y-4">
        {messages.map((message) => (
          <article className="rounded-lg border border-[#d9e4dd] bg-white p-4" key={message.id}>
            <p className="mb-3 text-sm font-semibold text-[#315246]">
              {message.question}
            </p>
            <p className="mb-4 text-sm leading-6 text-[#29342f]">
              {message.response.answer}
            </p>
            <div className="grid gap-4 xl:grid-cols-2">
              <EvidenceTable
                columns={message.response.columns}
                rows={message.response.table}
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
    <div className="space-y-4 text-sm text-[#29342f]">
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

function TabButton({
  active,
  children,
  onClick,
}: {
  active: boolean;
  children: string;
  onClick: () => void;
}) {
  return (
    <button
      className={`focus-ring px-4 py-2 text-sm font-semibold ${
        active
          ? "bg-[#16834f] text-white"
          : "border border-[#cbd9d1] bg-white text-[#315246]"
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
  const className =
    tone === "success"
      ? "mb-3 rounded-lg border border-[#badbc7] bg-[#edf8f1] p-3 text-sm text-[#235a3a]"
      : "mb-3 rounded-lg border border-[#f0c5b4] bg-[#fff3ef] p-3 text-sm text-[#8b3519]";
  return <p className={className}>{children}</p>;
}

function formatError(error: unknown): string {
  return error instanceof Error ? error.message : "Unexpected error";
}
