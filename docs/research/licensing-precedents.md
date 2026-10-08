# Licensing precedents: AGPL server plus MIT SDK, CLA practice

Research for issue #8 (part of #1). Feeds the License row in `docs/handoff.md` section 1 and the dual-licensing question in section 9.

> **Not legal advice.** This is a summary of public primary sources, gathered 2026-10-08, to prepare a conversation with a lawyer. Nothing here should be acted on without that review.

## 1. Per-project findings

### Excalidraw

- **Licenses.** The editor monorepo is MIT ([LICENSE](https://github.com/excalidraw/excalidraw/blob/master/LICENSE), added 2020-01-05 in "Add MIT License (#176)"). The `@excalidraw/excalidraw` npm package declares `"license": "MIT"` ([package.json](https://github.com/excalidraw/excalidraw/blob/master/packages/excalidraw/package.json)). The collaboration relay server is a separate repo, also MIT ([excalidraw-room LICENSE](https://github.com/excalidraw/excalidraw-room/blob/master/LICENSE)). So the server, client and SDK are all MIT.
- **Dual licensing.** None. Revenue comes from a separate hosted product, Excalidraw+, which the README links to next to Open Collective sponsorship ([README](https://github.com/excalidraw/excalidraw/blob/master/README.md)).
- **CLA / DCO.** Neither. [CONTRIBUTING.md](https://github.com/excalidraw/excalidraw/blob/master/CONTRIBUTING.md) points to the [docs contributing page](https://docs.excalidraw.com/docs/introduction/contributing), which says nothing about a CLA, DCO or sign-off. PR status checks (for example [#12246](https://github.com/excalidraw/excalidraw/pull/12246)) include no CLA or DCO check.
- **License changes.** None found. The LICENSE file has one commit.

### Penpot

- **Licenses.** The monorepo (backend, frontend, exporter, render-wasm) is MPL-2.0 ([LICENSE](https://github.com/penpot/penpot/blob/develop/LICENSE)). Copyright is held by "KALEIDOS SUBSIDIARY SL" ([README](https://github.com/penpot/penpot/blob/develop/README.md#license)). The plugin system lives in `plugins/` with its own MPL-2.0 LICENSE ([plugins/LICENSE](https://github.com/penpot/penpot/blob/develop/plugins/LICENSE)). The former standalone [penpot-plugins](https://github.com/penpot/penpot-plugins) repo, now archived, was also MPL-2.0. Penpot does **not** split licenses: its plugin SDK uses the same weak-copyleft license as the server.
- **Dual licensing.** None found.
- **CLA / DCO.** DCO 1.1. "All code patches must include a `Signed-off-by` line", real names only, docs excluded ([CONTRIBUTING.md, DCO section](https://github.com/penpot/penpot/blob/develop/CONTRIBUTING.md#developers-certificate-of-origin-dco)).
- **License changes.** None. The LICENSE has been MPL-2.0 since the 2016 commits ([3f67c5b](https://github.com/penpot/penpot/commit/3f67c5b582115459123816108381b88a90cc0322), [7011293](https://github.com/penpot/penpot/commit/7011293352eaba86fbf73085bd69906d8009744f)).

### Jitsi Meet

- **Licenses.** The web app [jitsi-meet](https://github.com/jitsi/jitsi-meet/blob/master/LICENSE), the client library [lib-jitsi-meet](https://github.com/jitsi/lib-jitsi-meet/blob/master/LICENSE), the SFU [jitsi-videobridge](https://github.com/jitsi/jitsi-videobridge/blob/master/LICENSE) and the conference focus [jicofo](https://github.com/jitsi/jicofo/blob/master/LICENSE) are all Apache-2.0 (GitHub license detection on each repo).
- **Dual licensing.** Not a dual-license business. The permissive license already allows proprietary use.
- **CLA.** Required, with 8x8 as the counterparty. The handbook says "the copyright holder and principal creator is 8x8" and asks contributors to "sign our Apache-based contributor license agreement as either a corporation or an individual". Its stated reason is "to ensure that we can continue making these projects available under an Open Source license". Without a signature, "we cannot accept your contribution" ([Jitsi handbook, contributing](https://jitsi.github.io/handbook/docs/dev-guide/dev-guide-contributing/)). The ICLA and CCLA are DocuSign forms at <https://jitsi.org/icla> and <https://jitsi.org/ccla>; I could not read the clause text there. Enforcement is manual: no CLA bot appears in PR checks (for example [#17946](https://github.com/jitsi/jitsi-meet/pull/17946)).
- **License changes.**
  - jitsi-meet started as **MIT**, "Copyright (c) 2013 ESTOS GmbH / BlueJimp SARL" ([initial LICENSE](https://github.com/jitsi/jitsi-meet/blob/62530ef1235e66548946795770bdd08b285ba5af/LICENSE)).
  - jitsi-videobridge started as **LGPL-2.1** ([initial LICENSE](https://github.com/jitsi/jitsi-videobridge/blob/243cb32a45c227dfa2593973a21ba6f5e6df5178/LICENSE)).
  - Both moved to Apache-2.0 on 2015-06-18: ["Setting new distribution license"](https://github.com/jitsi/jitsi-meet/commit/2b692f5a0ae6e4b026b9f05b3e36a1ebe4218bbf) in jitsi-meet and ["Update LICENSE"](https://github.com/jitsi/jitsi-videobridge/commit/5c511f8d59eded7c5c19e98b6fe9e841fc9cf189) in jitsi-videobridge. The current jitsi-meet LICENSE still carries the note "This project was originally contributed to the community under the MIT license" ([LICENSE](https://github.com/jitsi/jitsi-meet/blob/master/LICENSE)).
  - The change followed Atlassian's acquisition of BlueJimp. Context and reaction are only available second-hand ([BlogGeek.me](https://bloggeek.me/jitsi-open-source-apache/)), which reports that the LGPL to Apache move was explained on jitsi-dev and generally welcomed as removing barriers for enterprise use. I did not find the primary mailing-list post.

### HedgeDoc (formerly HackMD CE / CodiMD)

- **Licenses.** HedgeDoc 2 is a monorepo with **mixed licenses per package**, managed with REUSE/SPDX ([REUSE.toml](https://github.com/hedgedoc/hedgedoc/blob/develop/REUSE.toml), [LICENSES/](https://github.com/hedgedoc/hedgedoc/tree/develop/LICENSES)):
  - AGPL-3.0: `backend`, `frontend`, `commons`, `html-to-react` (each `package.json` declares `"license": "AGPL-3.0"`, for example [backend](https://github.com/hedgedoc/hedgedoc/blob/develop/backend/package.json)).
  - MIT: `@hedgedoc/markdown-it-plugins` ([package.json](https://github.com/hedgedoc/hedgedoc/blob/develop/markdown-it-plugins/package.json)).
  - CC-BY-SA-4.0 and CC0: docs and config files.

  HedgeDoc 1.x is AGPLv3 ([master README](https://github.com/hedgedoc/hedgedoc/blob/master/README.md#license)). This is the closest precedent to Aequate's shape: an AGPL server and client, with a reusable MIT library carved out of the same repo.
- **Dual licensing.** None. Copyright stays with "The HedgeDoc developers (see AUTHORS file)" ([AUTHORS](https://github.com/hedgedoc/hedgedoc/blob/develop/AUTHORS)).
- **CLA / DCO.** DCO. "By contributing to this project you agree to the Developer Certificate of Origin (DCO)… add a line to every git commit message: Signed-off-by", with no pseudonyms ([CONTRIBUTING.md](https://github.com/hedgedoc/hedgedoc/blob/develop/CONTRIBUTING.md#certificate-of-origin)). The DCO text is in the repo ([developer-certificate-of-origin.txt](https://github.com/hedgedoc/hedgedoc/blob/develop/developer-certificate-of-origin.txt)).
- **License changes and reaction.** This is the most instructive history in the set:
  1. **MIT to AGPLv3, October 2017.** "Originally, this was open source under MIT license, but was relicensed in October 2017 to be AGPLv3", at the same time as hackmd.io was founded to sell a commercial version ([HedgeDoc history](https://hedgedoc.org/history/details)).
  2. **No CLA existed, so they collected consent one contributor at a time.** [hackmdio/codimd PR #578 "License Change Agreement"](https://github.com/hackmdio/codimd/pull/578) (opened 2017-10-11) asked every past contributor to comment "I agree to the change of license from MIT to AGPL on all my past code contribution… Signed-off-by: …". It collected 27 comments and was merged 2017-12-06, about eight weeks later.
  3. **Open-core proposal, March 2019.** The company proposed a "HackMD-core" licensed Apache-2.0 plus paid commercial modules, with CodiMD staying AGPL ([hackmdio/codimd #1170](https://github.com/hackmdio/codimd/issues/1170)). The community "did not reach an agreement that would have allowed us to move the repository" and "simply forked it", which became HedgeDoc ([history](https://hedgedoc.org/history/details)). The AGPL plus the lack of a CLA meant the company could not take the community's contributions into a proprietary or permissive core. The community could fork, and did.

### Hocuspocus (Tiptap GmbH)

- **Licenses.** MIT for the whole repo, "Copyright (c) 2023, Tiptap GmbH" ([LICENSE.md](https://github.com/ueberdosis/hocuspocus/blob/main/LICENSE.md)). That covers the server (`@hocuspocus/server`), the provider (client) and extensions. Tiptap's editor is also MIT ([LICENSE.md](https://github.com/ueberdosis/tiptap/blob/develop/LICENSE.md)).
- **Dual licensing.** None. Funded by sponsorship and Tiptap's paid platform ([README sponsors](https://github.com/ueberdosis/hocuspocus/blob/main/README.md#sponsors-)).
- **CLA / DCO.** Neither. There is no CONTRIBUTING file in the repo, and the README links to a missing `docs/contributing.md` ([README](https://github.com/ueberdosis/hocuspocus/blob/main/README.md#contributing)). PR checks (for example [#1166](https://github.com/ueberdosis/hocuspocus/pull/1166)) include no CLA or DCO check. Tiptap's own [CONTRIBUTING.md](https://github.com/ueberdosis/tiptap/blob/develop/CONTRIBUTING.md) also has no CLA or DCO; it asks contributors to disclose AI usage.
- **License changes.** The repo history was reset in December 2020 ([02aa3e4](https://github.com/ueberdosis/hocuspocus/commit/02aa3e4b5558e62eff69c8cf622861600f293e91)), and an MIT license was added in April 2021 ([79cc060](https://github.com/ueberdosis/hocuspocus/commit/79cc0607dd382f89956b8dca09692ae0c8560d89)). The 1.0 post "It's public!" (2023-01-18) says it was "made available for free under the MIT license" ([Tiptap blog](https://tiptap.dev/docs/blog/hocuspocus-stable-release)). I found no primary source on terms before it went public.

### LiveKit

- **Licenses.** Apache-2.0 for the server ("LiveKit server is licensed under Apache License v2.0", [README](https://github.com/livekit/livekit/blob/master/README.md#license)), the client SDK ([client-sdk-js](https://github.com/livekit/client-sdk-js/blob/main/LICENSE)), the server SDKs ([server-sdk-go](https://github.com/livekit/server-sdk-go/blob/main/LICENSE)) and Agents ([agents](https://github.com/livekit/agents/blob/main/LICENSE)). Each ships a NOTICE file.
- **Dual licensing.** No. Revenue comes from the hosted LiveKit Cloud.
- **CLA.** Required, enforced through CLA Assistant. The [agents CONTRIBUTING](https://github.com/livekit/agents/blob/main/CONTRIBUTING.md) says "On your first pull request, the CLA Assistant bot will give you a link to sign this project's Contributor License Agreement". A `license/cla` status check runs on PRs to both the server ([livekit/livekit #4958](https://github.com/livekit/livekit/pull/4958)) and agents ([#7621](https://github.com/livekit/agents/pull/7621)). The CLA text sits behind <https://cla-assistant.io/livekit/agents> and was not readable without signing in, so I could not confirm whether it is a license grant or an assignment.
- **License changes.** None. The LICENSE has been Apache-2.0 since 2021.

### tldraw

- **Licenses (now).** A source-available **"tldraw license"**, not an OSI license ([LICENSE.md](https://github.com/tldraw/tldraw/blob/main/LICENSE.md)). Without a key, use is limited to development environments ("Not to use the Software in Production Environments"). Production needs a trial, commercial or hobby license key, which the software enforces technically. Most packages declare `"SEE LICENSE IN LICENSE.md"`, but some utility packages are MIT (for example [`@tldraw/store`](https://github.com/tldraw/tldraw/blob/main/packages/store/package.json)). The 1.x line "will remain licensed under MIT forever" ([blog, 2023-12-20](https://tldraw.dev/blog/license-update-for-the-tldraw-sdk)).
- **Dual licensing.** Yes, explicitly. PR [#2167](https://github.com/tldraw/tldraw/pull/2167) (merged 2023-12-19) says "leverage dual licensing for revenue… source code… provided under a non-commercial license… while we offer to sell… an alternative… license for companies".
- **CLA.** Yes, and it is a **license grant, not an assignment** ([CLA.md](https://github.com/tldraw/tldraw/blob/main/CLA.md), v1.0, 2023-06-08). Contributors grant "a perpetual, worldwide, non-exclusive, sublicensable (through multiple tiers)… copyright license", and "Except for the license granted herein to tldraw, You reserve all right, title, and interest". The CLA predated the relicense by six months. The 2023 blog says the earlier Apache-2.0 releases came with "a contributor license agreement protecting our right to swap licenses".
- **Contribution policy (2026).** External PRs are now auto-closed, because of AI-generated PR volume rather than licensing ([CONTRIBUTING.md](https://github.com/tldraw/tldraw/blob/main/CONTRIBUTING.md), [issue #7695](https://github.com/tldraw/tldraw/issues/7695), 2026-01-15).
- **License changes and reaction.** There were three changes on the SDK:
  - **v2, December 2023:** Apache-2.0 to non-commercial ([#2167](https://github.com/tldraw/tldraw/pull/2167), [blog](https://tldraw.dev/blog/license-update-for-the-tldraw-sdk)).
  - **v3, 2024:** commercial use allowed if the "Made with tldraw" watermark is shown, or with a paid Business License ([v3.0.0 release notes](https://tldraw.dev/releases/v3.0.0)).
  - **v4, September 2025:** license keys required for production ([#6780](https://github.com/tldraw/tldraw/pull/6780), [license-key docs](https://tldraw.dev/sdk-features/license-key)).

  The public reaction on primary channels is thin: a 0-comment HN submission ([HN 39258994](https://news.ycombinator.com/item?id=39258994)) and compliance friction in issues, for example a plugin author whose hobby key broke when the host app changed ([#7185](https://github.com/tldraw/tldraw/issues/7185)) and container deployment questions ([#7208](https://github.com/tldraw/tldraw/issues/7208)). The CLA meant no contributor consent was needed for any of the three changes.

### Summary table

| Project | Server | Client / SDK | Dual license | Contributor terms | Public license change |
| --- | --- | --- | --- | --- | --- |
| Excalidraw | MIT | MIT | No | None (inbound=outbound) | None |
| Penpot | MPL-2.0 | MPL-2.0 (plugins too) | No | DCO 1.1 | None |
| Jitsi Meet | Apache-2.0 | Apache-2.0 | No | CLA (8x8, ICLA + CCLA) | MIT / LGPL to Apache-2.0 (2015) |
| HedgeDoc | AGPL-3.0 | AGPL-3.0 app, one MIT lib | No | DCO | MIT to AGPL (2017, per-contributor consent); 2019 open-core attempt led to community fork |
| Hocuspocus | MIT | MIT | No | None | None (went public as MIT, 2023 stable) |
| LiveKit | Apache-2.0 | Apache-2.0 | No | CLA (CLA Assistant) | None |
| tldraw | n/a (SDK) | tldraw license (source-available) + some MIT pkgs | Yes | CLA, sublicensable license grant | Apache-2.0 to non-commercial (2023) to watermark (2024) to license key (2025) |

None of the seven combines **AGPL with a CLA for dual licensing**. The only AGPL project (HedgeDoc) uses a DCO and does not dual-license. The only dual-licensor (tldraw) relies on a broad, sublicensable CLA grant.

## 2. What the licenses and platform docs say

- **Default contributor terms on GitHub are inbound=outbound.** GitHub ToS D.6: "Whenever you add Content to a repository containing notice of a license, you license that Content under the same terms". A separate agreement such as a CLA takes precedence ([GitHub Terms of Service, D.6](https://docs.github.com/en/site-policy/github-terms/github-terms-of-service#6-contributions-under-repository-license)). With no CLA, a contributor to the AGPL server licenses their code to everyone, including the project owner, **under AGPL only**, and keeps the copyright.
- **A DCO grants nothing extra.** DCO 1.1 only certifies that the contributor has the right to submit "under the open source license indicated in the file" ([developercertificate.org](https://developercertificate.org/)). It records provenance; it does not enable relicensing.
- **Only copyright holders can offer other licenses.** The FSF says "the copyright holder for a program can release it under several different licenses in parallel. One of them may be the GNU GPL" ([GPL FAQ #HeardOtherLicense](https://www.gnu.org/licenses/gpl-faq.html#HeardOtherLicense)). It also says "If you are the copyright holder for the code, you can release it under various different non-exclusive licenses at various times" ([#ReleaseUnderGPLAndNF](https://www.gnu.org/licenses/gpl-faq.html#ReleaseUnderGPLAndNF)). The developer is not bound by its own GPL grant ([#DeveloperViolate](https://www.gnu.org/licenses/gpl-faq.html#DeveloperViolate)). That freedom covers only code the developer owns or holds sufficient rights to.
- **The FSF itself uses assignment, for enforcement reasons.** The FSF asks contributors "to either assign the copyright on contributions to the FSF, or disclaim copyright", because "to be in the best position to enforce the GPL in court… we should keep the copyright status of the program as simple as possible" ([#AssignCopyright](https://www.gnu.org/licenses/gpl-faq.html#AssignCopyright)). This is an enforcement argument, not a dual-licensing one.
- **The AGPL's network clause (section 13).** "If you modify the Program, your modified version must prominently offer all users interacting with it remotely through a computer network… an opportunity to receive the Corresponding Source" ([AGPL-3.0 §13](https://www.gnu.org/licenses/agpl-3.0.html#section13); same text in [choosealicense](https://choosealicense.com/licenses/agpl-3.0/)). Four sources clarify the scope:
  - **FSF:** the AGPL "has one added requirement: if you run a modified program on a server and let other users communicate with it there, your server must also allow them to download the source code" ([Why the Affero GPL](https://www.gnu.org/licenses/why-affero-gpl.html)).
  - **What counts as remote interaction:** a program "expressly designed to accept user requests and send responses over a network" counts, for example "interactive web-based applications" ([#AGPLv3InteractingRemotely](https://www.gnu.org/licenses/gpl-faq.html#AGPLv3InteractingRemotely)).
  - **Client vs server labels don't matter:** "whether or not there is a reasonable expectation that a person will be interacting with the program remotely over a network" ([#AGPLv3ServerAsUser](https://www.gnu.org/licenses/gpl-faq.html#AGPLv3ServerAsUser)).
  - **OSI:** lists AGPL-3.0 as approved (2008), "specifically designed to ensure cooperation with the community in the case of network server software" ([OSI](https://opensource.org/license/agpl-v3)). GitHub's choosealicense marks it with a `network-use-disclose` condition ([source](https://github.com/github/choosealicense.com/blob/gh-pages/_licenses/agpl-3.0.txt)).

  For Aequate: a tutor running an **unmodified** release has no section 13 obligation beyond what the distributed code already provides. A tutor who **modifies** the server must offer the modified source to their students.
- **Plugins and the license boundary.** The FSF's test for whether a program and its plug-ins are "a single combined program" depends on how they communicate. Plug-ins that are dynamically linked and "make function calls to each other and share data structures" form a single combined program. Simple fork/exec with no "intimate communication" keeps them separate ([#GPLPlugins](https://www.gnu.org/licenses/gpl-faq.html#GPLPlugins)). If they are combined, the plug-in must be under the GPL or a GPL-compatible free license ([#GPLAndPlugins](https://www.gnu.org/licenses/gpl-faq.html#GPLAndPlugins)). MIT is GPL-compatible, so MIT plugins loaded into the AGPL server are fine. A **proprietary** plugin running in-process with the AGPL server is the risky case, whatever license the SDK carries.
- **MIT already allows commercial reuse.** The MIT grant includes the rights to "use, copy, modify, merge, publish, distribute, sublicense, and/or sell" (as quoted in [jitsi-meet LICENSE](https://github.com/jitsi/jitsi-meet/blob/master/LICENSE)). Contributions to the MIT SDK can therefore be reused in anything, including a commercial product, without a CLA.

## 3. What an AGPL-3.0 server plus MIT SDK / client-libs split requires, from the first contributor onward

Synthesis of the sources above. Not legal advice.

1. **Per-file or per-package license marking is needed from day one.** Contributors can only follow inbound=outbound if it is unambiguous which license a file is under. Two patterns work: separate repos (LiveKit, Jitsi), or one monorepo with SPDX headers and a `REUSE.toml`/`LICENSES/` directory (HedgeDoc).
2. **If Aequate never dual-licenses**, no CLA is needed. Contributors keep their copyright, license the server code as AGPL and the SDK code as MIT (GitHub ToS D.6), and the project can add a DCO for provenance, as HedgeDoc and Penpot do. The cost: the license can never later be changed to anything not allowed by the AGPL without asking every server contributor, as HackMD did over eight weeks in PR #578. If even one contributor refuses or cannot be found, their code must be removed or rewritten.
3. **If Aequate wants to sell non-AGPL licenses of the server (dual licensing)**, the licensor needs rights beyond AGPL in **every** server contribution. A DCO does not provide them. Possible mechanisms:
   - **CLA with a broad, sublicensable license grant.** This is tldraw's model; Jitsi and LiveKit also use CLAs, though their texts could not be read here. Contributors keep their copyright. It must be in place **before the first external server contribution is merged**, because every earlier merge without it creates code the owner holds under AGPL terms only.
   - **Copyright assignment.** This is the FSF's model, and it is heavier for contributors. It is not needed just to dual-license, because a sublicensable grant does that.
   - **Retroactive consent.** Possible (HackMD), but slow and fragile.
4. **The MIT SDK and client libs need no CLA for any business model**, because MIT already permits sublicensing and sale. One risk to watch: if code is ever moved **from** the AGPL server **into** the MIT SDK, only someone with non-AGPL rights to that code can do it. In practice that means the original author, or the project if a CLA covers it.
5. **Reputational precedent.** Moving copyleft community code toward a proprietary or permissive core, when there is no CLA and the community doesn't consent, ended in a fork (CodiMD to HedgeDoc). A dual-licensing CLA is a known source of contributor friction. Two of the seven projects require one (LiveKit and tldraw, both company-led), and Jitsi requires one with 8x8 as copyright holder.

## Answer

Of seven comparable projects, only HedgeDoc uses AGPL. It pairs an AGPL-3.0 server and client with one MIT library in the same repo, uses a DCO, and does not dual-license. Excalidraw and Hocuspocus are MIT throughout with no contributor agreement. Penpot is MPL-2.0 throughout, plugins included, with a DCO. Jitsi and LiveKit are Apache-2.0 throughout and require a CLA. tldraw used its CLA, a sublicensable license grant rather than an assignment, to move from Apache-2.0 to a paid source-available license without asking contributors. HackMD, which had no CLA, needed per-contributor consent to relicense in 2017, and its 2019 open-core attempt ended in the community fork that became HedgeDoc.

For Aequate:
- **Without dual licensing**, an AGPL-3.0 server plus MIT SDK split needs no CLA. GitHub's inbound=outbound terms plus an optional DCO are the norm, but the server license becomes effectively locked.
- **With dual licensing**, a CLA granting the project a sublicensable license is needed before the first external server contribution is merged. A DCO is not enough, and copyright assignment is not required.
- **The MIT SDK needs no CLA either way.**

This is not legal advice; confirm with a lawyer.

## Questions for the lawyer

1. Who should be the licensor and CLA counterparty (an individual maintainer, a company, a foundation), given there is no legal entity yet? What happens to CLA rights if that changes?
2. Is a sublicensable non-exclusive license grant (tldraw-style) enough to sell non-AGPL licenses in our jurisdiction (Romania/EU), or is assignment advisable given EU moral rights and assignment formalities?
3. Does a click-through CLA (CLA Assistant via GitHub login) bind contributors enforceably in the EU? Do we also need a corporate CLA for employed contributors?
4. If we start without a CLA (DCO only) and later want dual licensing, what is the cleanest path: per-contributor consent, rewriting contributed code, or a CLA that only applies going forward?
5. Where is the safe boundary between the AGPL server and MIT plugins? Can a third party ship a **proprietary** plugin that runs in-process with the server through the MIT SDK, or must plugins run out of process for that?
6. The web client is served to students' browsers from the tutor's server. Should the client app be AGPL (with the server) or MIT (with the client libs)? Do section 13 source-offer obligations then fall on tutors who modify it, and how should the UI present the source offer?
7. Do we need a trademark policy for the name "Aequate", separate from the code license (as HedgeDoc does for its logo and tldraw for its marks)?
8. Is mixed licensing in one monorepo, with SPDX headers and REUSE, legally as clear as separate repos for the server and the SDK?
