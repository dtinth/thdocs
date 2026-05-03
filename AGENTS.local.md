# AGENTS.local.md

- After CSS/theme changes, run `just build-theme` to regenerate compiled CSS; do NOT edit `src/thdocs/static/thdocs.css` directly.
- After any changes (CSS, JS, templates, config, etc.), always run `just build-theme && just build` so the user can verify at `localhost:8080`.
- We have an http-server running at `localhost:8080`; you can use `agent-browser` to inspect
- For visual reference, the apiref project lives at `~/ghq/github.com/dtinth/apiref/`
