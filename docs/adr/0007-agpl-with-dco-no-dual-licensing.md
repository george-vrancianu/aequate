---
status: accepted (provisional)
---

# AGPL-3.0-or-later with a DCO and no dual licensing

The whole repository, the web client included, is licensed `AGPL-3.0-or-later`, and docs, the glossary and ADRs are `CC-BY-4.0`. Aequate is not dual-licensed. Contributors keep their copyright, contribute under the license of the files they touch (GitHub's inbound=outbound terms), and sign off every commit under the Developer Certificate of Origin. There is no CLA. We chose the AGPL because Aequate is self-hosted software that students use over a network, and anyone who modifies it should have to offer those students the source. We chose no dual licensing because there is no company to be a CLA counterparty, the project is meant for a community of self-hosters, and HedgeDoc's history shows that a copyleft community resists a later turn to a proprietary or permissive core.

The decision is provisional until the lawyer review ([Lawyer review of licensing](https://github.com/george-vrancianu/aequate/issues/55)). No external pull request is merged before then, because the first external contribution under a DCO is what makes switching to a CLA expensive.

## Considered Options

- **AGPL server with MIT client libraries and plugin SDK, as the handoff leaned.** The web client is what students interact with, and the AGPL's network clause cares about interaction, not client or server labels. v1 has no plugin SDK. MIT carve-outs are allowed later, per package, for code built for reuse by others.
- **Dual licensing with a CLA (a sublicensable license grant, as tldraw does).** It keeps the option of selling non-AGPL licenses, but it needs a counterparty that doesn't exist, it must be in place before the first external contribution, and it puts off contributors.
- **`AGPL-3.0-only`.** It would block fixes in future AGPL versions without a relicense, which needs every contributor's consent.
- **A permissive license (MIT or Apache-2.0) for everything.** It lets anyone run a modified, closed hosted version for students.

## Consequences

- The license is effectively locked. Changing it later to anything the AGPL doesn't allow needs every contributor's consent, as HackMD needed in 2017.
- Integrations go through network protocols (the OpenAI-compatible LLM endpoint, Mathpix HTTP, later adapter services), so they can be under any license. Code loaded into Aequate's process must be AGPL-compatible.
- Under the AGPL's network clause, the login page and the account menu link to the source of the exact release. The admin must point that link at their own source when they modify the server.
- Only model weights whose licenses permit commercial use ship or are downloaded, each listed in `THIRD_PARTY_NOTICES`. Weights trained on CC BY-NC-SA data wait for the lawyer review and a recognizer revisit (ADR 0004).
- An MIT carve-out is decided per package when the package is created and marked with SPDX headers. AGPL code moves into it only with its author's consent.
- Copyright is "the Aequate contributors", recorded in git history. Commits made with an agent carry a `Co-Authored-By` trailer, and the human who signs off takes responsibility.
- The name and logo are not covered by these licenses. A trademark policy belongs to the name check.
