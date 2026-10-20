"use client";
import { useState, type ReactNode } from "react";
import { Copy, Check, Code2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { safeWebUrl } from "@/lib/urls";
import { toast } from "sonner";
function CodeBlock({ code, language }: { code: string; language: string }) {
  const [copied, setCopied] = useState(false);
  const copy = async () => {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      setTimeout(() => setCopied(false), 1800);
    } catch {
      toast.error("Could not copy code");
    }
  };
  return (
    <div className="my-5 overflow-hidden rounded-xl border border-border bg-background">
      <div className="flex items-center justify-between border-b border-border bg-muted/50 px-4 py-2">
        <span className="flex items-center gap-2 text-[11px] text-muted-foreground">
          <Code2 className="size-3.5" />
          {language || "Code"}
        </span>
        <Button
          variant="ghost"
          size="sm"
          className="h-6 gap-1.5 px-2 text-[10px]"
          onClick={copy}
        >
          {copied ? <Check className="size-3" /> : <Copy className="size-3" />}
          {copied ? "Copied" : "Copy code"}
        </Button>
      </div>
      <pre className="overflow-x-auto p-4 text-xs leading-7 text-zinc-300">
        <code>{code}</code>
      </pre>
    </div>
  );
}
function inline(text: string): ReactNode {
  return text
    .split(/(\[[^\]]+\]\(https?:\/\/[^\s)]+\)|\*\*[^*]+\*\*|`[^`]+`)/g)
    .map((part, index) => {
      if (part.startsWith("**") && part.endsWith("**"))
        return (
          <strong key={index} className="font-semibold text-foreground">
            {part.slice(2, -2)}
          </strong>
        );
      if (part.startsWith("`"))
        return (
          <code
            key={index}
            className="rounded-md border border-border bg-muted px-1.5 py-0.5 font-mono text-[0.85em] text-primary"
          >
            {part.slice(1, -1)}
          </code>
        );
      const match = part.match(/^\[([^\]]+)\]\(([^)]+)\)$/);
      const url = match && safeWebUrl(match[2]);
      return match && url ? (
        <a
          key={index}
          href={url.href}
          target="_blank"
          rel="noopener noreferrer"
          className="text-primary underline decoration-primary/30 underline-offset-4 hover:decoration-primary"
        >
          {match[1]}
        </a>
      ) : (
        part
      );
    });
}
export function MarkdownContent({ content }: { content: string }) {
  const lines = content.trim().split("\n");
  const result: ReactNode[] = [];
  for (let index = 0; index < lines.length; index++) {
    const line = lines[index];
    if (!line.trim()) continue;
    if (line.startsWith("```")) {
      const language = line.slice(3).trim();
      const code: string[] = [];
      while (++index < lines.length && !lines[index].startsWith("```"))
        code.push(lines[index]);
      result.push(
        <CodeBlock key={index} language={language} code={code.join("\n")} />,
      );
      continue;
    }
    const heading = line.match(/^(#{1,6})\s+(.*)/);
    if (heading) {
      const Tag = heading[1].length <= 2 ? "h2" : "h3";
      result.push(
        <Tag
          key={index}
          className="mb-3 mt-6 text-base font-semibold tracking-tight text-foreground first:mt-0"
        >
          {inline(heading[2])}
        </Tag>,
      );
      continue;
    }
    if (/^\s*([-*]|\d+\.)\s/.test(line)) {
      const ordered = /^\s*\d+\./.test(line);
      const items: ReactNode[] = [];
      while (
        index < lines.length &&
        (ordered ? /^\s*\d+\.\s/ : /^\s*[-*]\s/).test(lines[index])
      ) {
        items.push(
          <li key={index} className="pl-1">
            {inline(lines[index].replace(/^\s*([-*]|\d+\.)\s/, ""))}
          </li>,
        );
        index++;
      }
      index--;
      const Tag = ordered ? "ol" : "ul";
      result.push(
        <Tag
          key={index}
          className={`my-4 space-y-2 pl-5 marker:text-muted-foreground ${ordered ? "list-decimal" : "list-disc"}`}
        >
          {items}
        </Tag>,
      );
      continue;
    }
    if (line.startsWith("> ")) {
      result.push(
        <blockquote
          key={index}
          className="my-4 border-l-2 border-primary/50 bg-primary/5 px-4 py-2 text-muted-foreground"
        >
          {inline(line.slice(2))}
        </blockquote>,
      );
      continue;
    }
    if (
      /^\|.*\|$/.test(line.trim()) &&
      /^\|?[\s:|-]+\|?$/.test(lines[index + 1] || "")
    ) {
      const cells = (row: string) =>
        row
          .trim()
          .replace(/^\||\|$/g, "")
          .split("|")
          .map((cell) => cell.trim());
      const headers = cells(line);
      const rows: string[][] = [];
      index += 2;
      while (index < lines.length && lines[index].trim().startsWith("|"))
        rows.push(cells(lines[index++]));
      index--;
      result.push(
        <div
          key={index}
          className="my-5 overflow-x-auto rounded-xl border border-border"
        >
          <table className="w-full min-w-80 text-left text-xs">
            <thead className="bg-muted">
              <tr>
                {headers.map((cell, i) => (
                  <th
                    key={i}
                    className="border-b border-border px-4 py-3 font-medium text-foreground"
                  >
                    {inline(cell)}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((row, i) => (
                <tr key={i} className="border-b border-border last:border-0">
                  {row.map((cell, j) => (
                    <td key={j} className="px-4 py-3">
                      {inline(cell)}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>,
      );
      continue;
    }
    if (/^(-{3,}|\*{3,})$/.test(line.trim())) {
      result.push(<hr key={index} className="my-6 border-border" />);
      continue;
    }
    result.push(
      <p key={index} className="mb-3 last:mb-0">
        {inline(line)}
      </p>,
    );
  }
  return (
    <div className="min-w-0 break-words text-sm leading-7 text-zinc-300">
      {result}
    </div>
  );
}
