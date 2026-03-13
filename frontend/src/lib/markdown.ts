// =============================================================================
// src/lib/markdown.ts — Simple markdown to HTML converter (shared utility)
// =============================================================================

export function simpleMarkdown(text: string): string {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/^### (.+)$/gm, '<h3 class="font-bold mt-3 mb-1">$1</h3>')
    .replace(/^## (.+)$/gm, '<h2 class="font-bold mt-3 mb-2">$1</h2>')
    .replace(/^# (.+)$/gm, '<h1 class="font-bold text-lg mt-3 mb-2">$1</h1>')
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/\*(.+?)\*/g, "<em>$1</em>")
    .replace(/`([^`]+)`/g, '<code class="bg-muted px-1 rounded text-xs">$1</code>')
    .replace(/^---$/gm, '<hr class="border-border/50 my-3" />')
    .replace(/^- (.+)$/gm, '<li class="ml-4">$1</li>')
    .replace(/^\d+\. (.+)$/gm, '<li class="ml-4 list-decimal">$1</li>')
    .replace(
      /\|(.+)\|/g,
      (match) => {
        const cells = match.split("|").filter(Boolean).map((c) => c.trim());
        if (cells.every((c) => /^[-:]+$/.test(c))) return "";
        return `<tr>${cells.map((c) => `<td class="border border-border/30 px-2 py-1">${c}</td>`).join("")}</tr>`;
      }
    )
    .replace(/(<tr>.*<\/tr>\n?)+/g, (match) => `<table class="w-full border-collapse my-2">${match}</table>`)
    .replace(/\n/g, "<br />");
}
