import { useEffect, useState } from "react";
import ReactMarkdown from "react-markdown";
import type { Components } from "react-markdown";
import type { ReactNode } from "react";

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
  const [isDark, setIsDark] = useState(false);

  useEffect(() => {
    const check = () => setIsDark(document.documentElement.classList.contains("dark"));
    check();
    const obs = new MutationObserver(check);
    obs.observe(document.documentElement, { attributes: true, attributeFilter: ["class"] });
    return () => obs.disconnect();
  }, []);

  const components: Components = {
    h1: ({ children }: TagProps) => <h1 className="text-theme mb-3 mt-4 text-2xl font-bold">{children}</h1>,
    h2: ({ children }: TagProps) => <h2 className="text-theme mb-2 mt-4 text-xl font-bold">{children}</h2>,
    h3: ({ children }: TagProps) => <h3 className="text-theme mb-2 mt-3 text-lg font-bold">{children}</h3>,
    h4: ({ children }: TagProps) => <h4 className="text-theme mb-1 mt-2 font-semibold">{children}</h4>,
    p: ({ children }: TagProps) => <p className="text-theme mb-2 leading-6">{children}</p>,
    ul: ({ children }: TagProps) => <ul className="mb-2 list-disc pl-5">{children}</ul>,
    ol: ({ children }: TagProps) => (
      <ol className="mb-2 list-decimal pl-5">{children}</ol>
    ),
    li: ({ children }: TagProps) => <li className="mb-1">{children}</li>,
    code: ({ className, children, ...props }: CodeProps) => {
      const isInline = !className;
      return isInline ? (
        <code className={`rounded px-1 py-0.5 ${isDark ? 'bg-gray-700 text-gray-200' : 'bg-gray-100'}`} {...props}>
          {children}
        </code>
      ) : (
        <code className={className} {...props}>
          {children}
        </code>
      );
    },
    pre: ({ children }: TagProps) => (
      <pre className={`mb-2 overflow-x-auto rounded p-3 ${isDark ? 'bg-gray-700' : 'bg-gray-100'}`}>
        {children}
      </pre>
    ),
    blockquote: ({ children }: TagProps) => (
      <blockquote className="border-l-4 border-gray-300 pl-3 italic dark:border-gray-600">
        {children}
      </blockquote>
    ),
    table: ({ children }: TagProps) => (
      <div className="mb-3 overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">{children}</table>
      </div>
    ),
    thead: ({ children }: TagProps) => (
      <thead className="bg-gray-50 dark:bg-gray-900">{children}</thead>
    ),
    tbody: ({ children }: TagProps) => (
      <tbody className="divide-y divide-gray-200 dark:divide-gray-700">{children}</tbody>
    ),
    tr: ({ children }: TagProps) => <tr>{children}</tr>,
    th: ({ children }: TagProps) => (
      <th className="px-3 py-2 text-left text-xs font-semibold uppercase tracking-wider">
        {children}
      </th>
    ),
    td: ({ children }: TagProps) => (
      <td className="whitespace-nowrap px-3 py-2 text-sm">{children}</td>
    ),
    a: ({ href, children }: LinkProps) => (
      <a
        className="text-[#16834f] underline hover:text-[#126f40] dark:text-[#4ade80] dark:hover:text-[#22c55e]"
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
    <article className="prose prose-sm text-theme max-w-none">
      <ReactMarkdown components={components}>{markdown}</ReactMarkdown>
    </article>
  );
}
