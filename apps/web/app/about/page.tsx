export default function AboutPage() {
  return (
    <div className="prose-invert mx-auto max-w-2xl space-y-6">
      <h1 className="text-2xl font-bold">About, privacy & limitations</h1>

      <section className="card space-y-2 p-5 text-sm leading-relaxed text-ink-300">
        <h2 className="font-bold text-white">What ScamShield AI is</h2>
        <p>
          A hackathon prototype that detects the psychological coercion sequence of
          digital-arrest and payment scams: authority impersonation, fabricated accusations,
          isolation, secrecy, continuous-call control, threats and “safe account” payment
          demands. It produces an explainable risk score, extracts and masks fraud entities,
          links complaints in a fraud graph, and generates auditable PDF evidence reports.
        </p>
      </section>

      <section className="card space-y-2 p-5 text-sm leading-relaxed text-ink-300">
        <h2 className="font-bold text-white">What it is not</h2>
        <ul className="list-disc space-y-1 pl-5">
          <li>It does not listen to live calls or access telecom metadata.</li>
          <li>It does not block bank accounts or freeze transactions.</li>
          <li>It does not contact police, banks or family automatically — alerts are simulated.</li>
          <li>It does not detect AI-generated voices, and rule-based analysis can be wrong.</li>
          <li>Its output is decision support, not a legal determination of fraud or guilt.</li>
        </ul>
      </section>

      <section className="card space-y-2 p-5 text-sm leading-relaxed text-ink-300">
        <h2 className="font-bold text-white">Privacy & consent</h2>
        <ul className="list-disc space-y-1 pl-5">
          <li>Analysis requires an explicit consent checkbox before a case is created.</li>
          <li>Sensitive identifiers (phones, accounts, UPI IDs) are masked in the interface and reports.</li>
          <li>Uploaded files are hashed with SHA-256 and never modified; raw evidence is kept only as long as needed.</li>
          <li>All complaint data in this demo is synthetic — no real victims, numbers or accounts.</li>
          <li>The audit trail is append-only; no silent deletion path exists in the prototype.</li>
        </ul>
      </section>

      <section className="card space-y-2 p-5 text-sm leading-relaxed text-ink-300">
        <h2 className="font-bold text-white">False positives</h2>
        <p>
          Legitimate urgent communication (real bank fraud alerts, genuine authority contact)
          can resemble scam language. The engine uses awareness-message guards, sequence
          requirements and confidence scores to reduce this, and every assessment carries a
          human-review disclaimer. Investigator review is part of the product, not an
          afterthought.
        </p>
      </section>
    </div>
  );
}
