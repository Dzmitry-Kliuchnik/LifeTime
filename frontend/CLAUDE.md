# CLAUDE.md — Frontend

## Running the Frontend

```bash
cd frontend
npm install
npm run dev       # dev server at http://localhost:5173
npm run build     # production build → dist/
npm run preview   # serve dist/ locally
```

Node.js requirement: `^20.19.0 || >=22.12.0` (enforced in `package.json`).

## Source Structure

```
frontend/src/
├── main.js                        # App entry — mounts App.vue, imports main.css
├── App.vue                        # Shell: theme system + view routing
├── components/
│   ├── LifetimeCalendar.vue       # Main calendar grid + week modal
│   └── UserSettings.vue           # Settings modal (birthdate / life expectancy)
└── assets/
    ├── design-system.css          # CSS custom properties (design tokens)
    ├── base.css                   # CSS reset + base element styles
    └── main.css                   # App-level layout; imports base.css
```

`design-system.css` → `base.css` → `main.css` → `main.js` — all CSS variables globally available.
`@` alias resolves to `frontend/src/` (configured in `vite.config.js`).

## Dependencies

| Package | Role |
|---|---|
| `vue@^3.5` | UI framework (Composition API, `<script setup>`) |
| `axios@^1.12` | HTTP client for all API calls |
| `vite@^7` | Build tool and dev server |
| `@vitejs/plugin-vue@^6` | Vue SFC transform |
| `vite-plugin-vue-devtools@^8` | Browser devtools panel (dev only) |

No Pinia, no Vue Router, no component library. All state is local `ref`/`reactive` within components.

## Project Skills

Detailed reference has been extracted into skills in `.claude/skills/`:

- **`lifetime-frontend-components`** — App.vue theme/routing, LifetimeCalendar.vue grid + voice state machine, UserSettings.vue validation
- **`lifetime-design-system`** — CSS token reference, theme switching rules, responsive breakpoints, accessibility conventions
- **`lifetime-frontend-best-practices`** — Vue 3 composables, reactivity, Axios instance + cancellation, Vite env vars, CSS rules
