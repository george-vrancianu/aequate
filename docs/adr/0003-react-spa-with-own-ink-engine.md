---
status: accepted (provisional)
---

# A React single-page app with our own ink engine on Perfect Freehand

The client is a TypeScript React single-page app built with Vite, installable as a web app with offline support, and served as static files by the self-hosted stack. Board ink is drawn by an engine we write ourselves: Perfect Freehand turns each stroke's points and pressure into an outline, and our code owns pointer input, the stroke model and rendering. Rendering is two Canvas 2D layers: committed strokes cached per stroke, and a low-latency live layer. We chose React for its ecosystem (mature ICU i18n through FormatJS, math-input wrappers, testing tools) and because agents, who will do most of the build, write it most reliably. Strokes never enter React state, which removes most of the performance argument against it. We chose our own engine because no ready-made one fits an AGPL, self-hosted, Yjs-native board with math-specific selection.

The decision is provisional because the ink spike was deferred until the app produces usage data. The ink layer sits behind a module interface (pointer events in, stroke records out, plus a renderer) so it can be swapped. Revisit if, in the real app, median pen-to-pixel latency on the iPad exceeds about 50 ms, strokes visibly lag or drop points at the stroke counts boards actually reach, or a stylus's pressure or tilt can't be read through pointer events.

## Considered Options

- **Svelte 5.** Smaller, faster bundles and simpler reactive code, but a thinner ecosystem, less mature ICU i18n and less reliable agent output.
- **tldraw.** Its SDK needs a license key for production use (unlicensed builds show a watermark), which sits badly with an AGPL self-hosted project. Its data model isn't Yjs.
- **Excalidraw.** A whole whiteboard app with its own data model. Yjs support exists only as community add-ons, and math-specific selection would mean fighting it.
- **WebGL rendering.** Not needed: the sync spike found CPU is not the limit up to 10k strokes. SVG was ruled out because it slows down with thousands of paths.
- **Server rendering (Next.js, SvelteKit).** It adds a server runtime and buys nothing for an authenticated, canvas-heavy app.

## Consequences

- The eraser, pages and later board tools are ours to build.
- The rest of the client stack follows from this:
  - Yjs (persisted in IndexedDB) for board data;
  - TanStack Query for server data;
  - Zustand for shared UI state;
  - `react-intl` with flat per-locale JSON catalogs for Weblate;
  - KaTeX for math display and MathLive for math input;
  - CSS Modules with design tokens as CSS variables, plus Radix UI primitives;
  - Vitest and Playwright, including WebKit.
