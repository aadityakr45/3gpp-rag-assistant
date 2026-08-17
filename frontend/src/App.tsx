import { FormEvent, useState } from "react";

type Citation = {
  source_id: string;
  specification: string;
  release: string;
  version: string;
  clause: string | null;
  page_start: number;
  page_end: number;
  source_document: string;
  text?: string;
};

type ChatResponse = {
  status: "ANSWERED" | "ABSTAINED";
  answer: string;
  citations: Citation[];
  grounding: { score: number; verified: boolean; unsupported_claims: string[] };
  retrieval: { candidate_count: number; evidence_count: number };
};

export default function App() {
  const [question, setQuestion] = useState("");
  const [response, setResponse] = useState<ChatResponse | null>(null);
  const [selected, setSelected] = useState<Citation | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!question.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const result = await fetch("http://localhost:8000/api/v1/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question }),
      });
      if (!result.ok) throw new Error(`Request failed (${result.status})`);
      setResponse((await result.json()) as ChatResponse);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Request failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="shell">
      <header>
        <p className="eyebrow">3GPP EVIDENCE ASSISTANT</p>
        <h1>TeleRAG</h1>
        <p className="subtitle">Ask questions grounded in indexed telecommunications standards.</p>
      </header>
      <form className="question-form" onSubmit={submit}>
        <textarea value={question} onChange={(event) => setQuestion(event.target.value)} placeholder="Ask about AMF, NAS, RRC, procedures, or a specific clause…" maxLength={2000} />
        <button disabled={loading}>{loading ? "Searching…" : "Ask TeleRAG"}</button>
      </form>
      {error && <p className="error">{error}</p>}
      {response && (
        <section className={response.status === "ABSTAINED" ? "answer abstained" : "answer"}>
          <div className="answer-heading"><span>{response.status === "ANSWERED" ? "Answer" : "Controlled abstention"}</span><span>{response.grounding.verified ? "VERIFIED" : "NOT VERIFIED"}</span></div>
          <p>{response.answer}</p>
          <div className="meta">Evidence: {response.retrieval.evidence_count} · Grounding score: {response.grounding.score.toFixed(2)}</div>
          {response.citations.length > 0 && <div className="sources"><h2>Sources</h2>{response.citations.map((citation) => <button className="source" key={citation.source_id} onClick={() => setSelected(citation)}><strong>{citation.source_id} · {citation.specification}</strong><span>Release {citation.release} · v{citation.version} · Clause {citation.clause ?? "front matter"} · pp. {citation.page_start}–{citation.page_end}</span></button>)}</div>}
        </section>
      )}
      {selected && <aside className="inspector"><button className="close" onClick={() => setSelected(null)}>Close</button><h2>{selected.source_id}</h2><p>{selected.text}</p></aside>}
    </main>
  );
}
