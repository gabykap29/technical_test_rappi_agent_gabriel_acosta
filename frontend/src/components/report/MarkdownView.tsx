import { useContext } from "react";
import ReactMarkdown from "react-markdown";
import type { Components } from "react-markdown";
import remarkGfm from "remark-gfm";
import type { ReactNode } from "react";
import { ThemeContext } from "@/features/agent/OperationsDashboard";

type MarkdownViewProps = {
  markdown: string;
};

type TagProps = {
  children?: ReactNode;
};

type CodeProps = {
  className?: string;
  children?: ReactNode;
  node?: object;
};

type LinkProps = {
  href?: string;
  children?: ReactNode;
};

export function MarkdownView({ markdown }: MarkdownViewProps) {
  const { theme } = useContext(ThemeContext);
  const isDark = theme === "dark";
  const normalizedMarkdown = normalizeMarkdown(markdown);

  if (!normalizedMarkdown) {
    return <p className="text-theme-muted text-sm">No content to display.</p>;
  }

  const components: Components = {
    h1: ({ children }: TagProps) => <h1 className="text-theme mb-3 mt-4 text-2xl font-bold">{children}</h1>,
    h2: ({ children }: TagProps) => <h2 className="text-theme mb-2 mt-4 text-xl font-bold">{children}</h2>,
    h3: ({ children }: TagProps) => <h3 className="text-theme mb-2 mt-3 text-lg font-bold">{children}</h3>,
    h4: ({ children }: TagProps) => <h4 className="text-theme mb-1 mt-2 font-semibold">{children}</h4>,
    p: ({ children }: TagProps) => <p className="text-theme mb-2 leading-6 break-words">{children}</p>,
    ul: ({ children }: TagProps) => <ul className="mb-2 list-disc pl-5 break-words">{children}</ul>,
    ol: ({ children }: TagProps) => (
      <ol className="mb-2 list-decimal pl-5 break-words">{children}</ol>
    ),
    li: ({ children }: TagProps) => <li className="mb-1 break-words">{children}</li>,
    code: ({ className, children, ...props }: CodeProps) => {
      const isInline = !className;
      return isInline ? (
        <code className={`break-words rounded px-1 py-0.5 ${isDark ? 'bg-gray-700 text-gray-200' : 'bg-gray-100'}`} {...props}>
          {children}
        </code>
      ) : (
        <code className={className} {...props}>
          {children}
        </code>
      );
    },
    pre: ({ children }: TagProps) => (
      <pre className={`mb-2 max-w-full overflow-x-auto rounded p-3 ${isDark ? 'bg-gray-700' : 'bg-gray-100'}`}>
        {children}
      </pre>
    ),
    blockquote: ({ children }: TagProps) => (
      <blockquote className="border-l-4 border-gray-300 pl-3 italic dark:border-gray-600">
        {children}
      </blockquote>
    ),
    table: ({ children }: TagProps) => (
      <div className="mb-3 max-w-full overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">{children}</table>
      </div>
    ),
    thead: ({ children }: TagProps) => (
      <thead className="bg-gray-50 dark:bg-gray-900">{children}</thead>
    ),
    tbody: ({ children }: TagProps) => (
      <tbody className="divide-y divide-gray-200 dark:divide-gray-700">{children}</tbody>
    ),
    tr: ({ children }: TagProps) => <tr className={isDark ? 'bg-gray-800' : 'bg-white'}>{children}</tr>,
    th: ({ children }: TagProps) => (
      <th className={`px-3 py-2 text-left text-xs font-semibold uppercase tracking-wider ${isDark ? 'bg-gray-700 text-gray-200' : 'bg-gray-50 text-gray-500'}`}>
        {children}
      </th>
    ),
    td: ({ children }: TagProps) => (
      <td className={`px-3 py-2 text-sm break-words ${isDark ? 'text-gray-300' : 'text-gray-700'}`}>{children}</td>
    ),
    a: ({ href, children }: LinkProps) => (
      <a
        className="break-words text-[#16834f] underline hover:text-[#126f40] dark:text-[#4ade80] dark:hover:text-[#22c55e]"
        href={href}
      >
        {children}
      </a>
    ),
    hr: () => <hr className="my-4 border-gray-200 dark:border-gray-700" />,
    strong: ({ children }: TagProps) => (
      <strong className="font-semibold">{children}</strong>
    ),
    em: ({ children }: TagProps) => <em className="italic">{children}</em>,
  };

  return (
    <article className="prose prose-sm text-theme min-w-0 max-w-full [overflow-wrap:anywhere]">
      <ReactMarkdown components={components} remarkPlugins={[remarkGfm]}>{normalizedMarkdown}</ReactMarkdown>
    </article>
  );
}

function normalizeMarkdown(markdown: string) {
  let text = markdown
    .replace(/^\uFEFF/, "")
    .replace(/\r\n/g, "\n")
    .trimStart();

  text = parseSerializedMarkdown(text);

  const escapedNewlines = text.match(/\\n/g)?.length ?? 0;
  const realNewlines = text.match(/\n/g)?.length ?? 0;
  if (escapedNewlines > realNewlines) {
    text = text
      .replace(/\\n/g, "\n")
      .replace(/\\t/g, "\t")
      .replace(/\\"/g, "\"");
  }

  text = extractMarkdownFence(text);
  text = dedentMarkdown(text);

  return text
    .replace(/^```(?:markdown|md|text)?[ \t]*\n/i, "")
    .replace(/\n```[ \t]*$/i, "")
    .trim();
}

function parseSerializedMarkdown(value: string) {
  if (looksLikeJsonString(value)) {
    try {
      const parsed = JSON.parse(value);
      if (typeof parsed === "string") {
        return parsed;
      }
    } catch {
      // Keep the original text if it is not a valid JSON string.
    }
  }

  try {
    const parsed = JSON.parse(value);
    if (parsed && typeof parsed === "object" && "markdown" in parsed) {
      const markdown = (parsed as { markdown?: unknown }).markdown;
      if (typeof markdown === "string") {
        return markdown;
      }
    }
  } catch {
    // Keep the original text if it is not a valid JSON object.
  }

  return value;
}

function extractMarkdownFence(value: string) {
  const fence = value.match(/```(?:markdown|md|text)?[ \t]*\n([\s\S]*?)\n```/i);
  if (!fence) {
    return value;
  }

  const beforeFence = value.slice(0, fence.index).trim();
  const afterFence = value.slice((fence.index ?? 0) + fence[0].length).trim();
  if (!beforeFence && !afterFence) {
    return fence[1];
  }

  return value;
}

function dedentMarkdown(value: string) {
  const lines = value.split("\n");
  const indents = lines
    .filter((line) => line.trim())
    .map((line) => line.match(/^[ \t]*/)?.[0].length ?? 0);

  if (!indents.length) {
    return value;
  }

  const smallestIndent = Math.min(...indents);
  if (smallestIndent === 0) {
    return value;
  }

  return lines
    .map((line) => line.slice(Math.min(smallestIndent, line.length)))
    .join("\n");
}

function looksLikeJsonString(value: string) {
  return value.length >= 2 && value.startsWith("\"") && value.endsWith("\"");
}
