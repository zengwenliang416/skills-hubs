import { useState } from "react";

// Import once from your app or feature style entrypoint.
// This example carries its own Amicro scope; remove it only when a parent already provides one:
// import "../../styles/amicro/amicro-tokens.css";
// import "../../styles/amicro/amicro-primitives.css";
// import "../../styles/amicro/amicro-motion.css";

type Props = {
  title: string;
  description: string;
  onApply?: () => Promise<void> | void;
};

export function AmicroFeatureCard({ title, description, onApply }: Props) {
  const [status, setStatus] = useState<"idle" | "working" | "done">("idle");

  async function apply() {
    if (status === "working") return;
    setStatus("working");
    try {
      await onApply?.();
      setStatus("done");
      window.setTimeout(() => setStatus("idle"), 1400);
    } catch {
      setStatus("idle");
    }
  }

  const label = status === "working" ? "Applying…" : status === "done" ? "Applied" : "Apply style";

  return (
    <article className="amicro amicro-card amicro-hover-lift" data-amicro-root data-amicro-theme="auto" data-interactive="true">
      <div className="amicro-card__stage" style={{ padding: "1.25rem" }}>
        <div className="amicro-stack">
          <span className="amicro-chip">React · CSS first</span>
          <h3 className="amicro-heading">{title}</h3>
          <p className="amicro-copy">{description}</p>
        </div>
      </div>
      <footer className="amicro-card__footer">
        <span className="amicro-card__meta" aria-live="polite">{status === "done" ? "Change saved" : "No motion dependency"}</span>
        <button className="amicro-button amicro-pressable" data-variant="primary" type="button" onClick={apply} disabled={status === "working"} aria-busy={status === "working"}>
          {label}
        </button>
      </footer>
    </article>
  );
}
