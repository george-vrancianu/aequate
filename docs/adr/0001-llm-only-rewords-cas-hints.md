# The LLM only rewords hints the CAS produced

When the optional LLM plugin is on, it rewords the CAS's facts for rungs 1–3 of a hint ladder and nothing else. It never produces a rung the CAS could not, it never sees the next step below rung 4, and rung 4 is always the CAS's step shown as math. This keeps the CAS the only source of mathematics in a hint, so a hint cannot be wrong or give away the answer through the LLM, and the leak check only has to compare the LLM's text against facts the CAS already knows.

## Considered Options

- **The LLM fills gaps in the rule engine.** Where the ported Mathsteps rules or `integral_steps` have no coverage, the LLM proposes an operation and the CAS checks that the result is equivalent and makes progress. This would cover far more steps, but it means the LLM produces mathematics, the reason step-by-step Solve was ruled out. Rejected for now. Revisit once the LLM hint bake-off measures how often the rule engine has no coverage.

## Consequences

- Without coverage from the rule engine, a student sees fewer rungs, or "No automatic hint for this step" followed by an ask to the tutor, even when an LLM is configured.
- The LLM is optional. A self-hosted instance without one gives the same rungs with template wording.
