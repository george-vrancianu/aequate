# The hint LLM sits behind an OpenAI-compatible endpoint and is checked before display

Aequate talks to the optional hint LLM only through the OpenAI-compatible `/v1/chat/completions` API. An admin configures it with a base URL, a model name and an optional key. An optional `llm` Compose profile runs a pinned `llama-server` (CPU or CUDA image) serving one GGUF file chosen by the admin. Ollama, vLLM, a Modal deployment in development, or a hosted API work by changing the URL, and Aequate has no code specific to any of them. We chose this because llama.cpp, Ollama, vLLM and hosted APIs all speak this protocol with JSON-schema output, and the model is chosen by the bake-off, not by the interface.

The API server makes the call and the CAS worker runs the leak check on the complete output. The student never sees LLM text that has not passed. When a rung is revealed, the template wording appears at once, and the LLM wording replaces it only after it passes the check. Nothing streams token by token. We chose this because the leak check needs the whole hint, and streaming would show a leaked answer before the check could reject it. The check also needs the next step and the answer, which must never reach the browser below rung 4.

## Considered Options

- **Streaming tokens over the template, as first decided in the hint ladder.** Rejected: it shows text before the leak check runs.
- **Calling the LLM from the browser.** Rejected: the leak check would need the next step and the answer on the client.
- **Bundling and managing a runtime (Ollama or llama.cpp) inside Aequate.** Rejected: it ties Aequate to one runtime's model management. The Compose profile gives the same convenience without coupling.
- **Using the same LLM to judge leaks.** Rejected: small models judge poorly, so the check is deterministic (numbers and SymPy-parsed formulas against the next step and the answer).

## Consequences

- Aequate builds the prompt: an English system message, one versioned template for every model, output in the locale's language as JSON `{hint, math[]}`, temperature 0 and thinking off. Its input is the rung's cached CAS facts and never the next step or the answer (ADR 0001).
- Each reveal has a 20 s budget covering its queue time and both attempts. A rejected hint is retried once, with the reason, only if at least 5 s remain. When the budget runs out, the template stays. At most N requests (default 2) reach the LLM at once.
- On a slow CPU-only model, students see template wording for longer before it changes. An unconfigured, unhealthy or failing LLM shows the template wording with no error. The server checks `/v1/models` at startup and every minute, and the admin page shows the status.
- Only wording that passed is cached in Postgres. The key hashes the rung's facts, rung, locale, model and digest, prompt version and leak-check version. Each hint record stores the text shown, whether it came from the LLM or the template, the model and the prompt version.
- A hosted endpoint sends students' steps to a third party, so the admin gets a warning for an address outside the instance's network, and the privacy notice names the provider.
