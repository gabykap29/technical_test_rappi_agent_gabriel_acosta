type MarkdownViewProps = {
  markdown: string;
};

export function MarkdownView({ markdown }: MarkdownViewProps) {
  return (
    <article className="space-y-3 text-sm leading-6 text-[#29342f]">
      {markdown.split("\n").map((line, index) => {
        if (line.startsWith("# ")) {
          return (
            <h1 className="text-2xl font-bold" key={index}>
              {line.slice(2)}
            </h1>
          );
        }
        if (line.startsWith("## ")) {
          return (
            <h2 className="pt-3 text-xl font-bold" key={index}>
              {line.slice(3)}
            </h2>
          );
        }
        if (line.startsWith("### ")) {
          return (
            <h3 className="pt-2 text-lg font-bold" key={index}>
              {line.slice(4)}
            </h3>
          );
        }
        if (line.startsWith("#### ")) {
          return (
            <h4 className="font-semibold" key={index}>
              {line.slice(5)}
            </h4>
          );
        }
        if (line.startsWith("- ")) {
          return (
            <p className="pl-3" key={index}>
              {line}
            </p>
          );
        }
        if (!line.trim()) {
          return <div className="h-1" key={index} />;
        }
        return <p key={index}>{line}</p>;
      })}
    </article>
  );
}
