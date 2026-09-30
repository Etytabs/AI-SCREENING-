"use client";

import { useEffect, useRef } from "react";
import type { DocumentContent } from "../../lib/types";

export interface Highlight {
  documentId: string;
  page: number | null;
  text: string;
}

type Range = { start: number; end: number } | null;

function findRange(pageText: string, needle: string): Range {
  const index = pageText.toLowerCase().indexOf(needle.toLowerCase());
  return index < 0 ? null : { start: index, end: index + needle.length };
}

// Page text is the page's lines joined by single spaces (see services/ingestion/document.py).
function Line({ line, offset, range }: { line: string; offset: number; range: Range }) {
  if (!range || range.end <= offset || range.start >= offset + line.length) return <p className="paper-line">{line}</p>;
  const from = Math.max(0, range.start - offset);
  const to = Math.min(line.length, range.end - offset);
  return (
    <p className="paper-line">
      {line.slice(0, from)}
      <mark data-testid="evidence-highlight">{line.slice(from, to)}</mark>
      {line.slice(to)}
    </p>
  );
}

export function DocumentViewer({ content, highlight }: { content: DocumentContent; highlight: Highlight | null }) {
  const container = useRef<HTMLDivElement>(null);
  const active = highlight && highlight.documentId === content.document_id ? highlight : null;

  useEffect(() => {
    const mark = container.current?.querySelector("mark");
    const scroller = container.current?.parentElement;
    if (!mark || !scroller || typeof scroller.scrollTo !== "function") return;
    const offset = mark.getBoundingClientRect().top - scroller.getBoundingClientRect().top + scroller.scrollTop;
    scroller.scrollTo({ top: Math.max(0, offset - scroller.clientHeight / 2), behavior: "smooth" });
  }, [active, content]);

  if (content.extraction_status !== "success" || !content.pages.length) {
    return (
      <div className="doc-empty" role="status">
        <b>No readable text</b>
        <span>Extraction status: {content.extraction_status}. The original file must be inspected directly; no findings rely on this document&apos;s text.</span>
      </div>
    );
  }
  return (
    <div className="doc-pages" ref={container}>
      {content.pages.map((page) => {
        const range = active && (active.page === null || active.page === page.page_number) ? findRange(page.text, active.text) : null;
        const lines = page.lines.length ? page.lines : [page.text];
        let offset = 0;
        return (
          <article className="paper ws-paper" key={page.page_number} aria-label={`${content.filename} page ${page.page_number}`}>
            <div className="paper-meta">{content.filename} · PAGE {page.page_number}</div>
            {lines.map((line, i) => {
              const node = <Line key={i} line={line} offset={offset} range={range} />;
              offset += line.length + 1;
              return node;
            })}
          </article>
        );
      })}
    </div>
  );
}
