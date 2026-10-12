# NaoVisuals

Minecraft client website (static, hosted on GitHub Pages).

## Pages
- `index.html` — landing page (includes standalone login / registration / profile, works offline)
- `purchase.html`, `documents.html`, `auth.html`, `account.html`, `themes.html`,
  `ecosystem.html`, `referral.html`, `my-purchases.html`

## Local run
Just open `index.html` in a browser — the built-in auth uses `localStorage`.

Or run the Flask backend (saves profiles/passwords in `data/users.json`):

```
pip install -r requirements.txt
python server.py
```

Then open http://localhost:8080

## Deploy
GitHub Pages serves the repo root (`index.html`). No build step needed.
