# Onboarding — working on this repo (for Bo)

## Setup (once)

```bash
git clone https://github.com/Anis12392/chargebotic.git
cd chargebotic
```

If you use Claude Code: run it inside this folder. It reads `CLAUDE.md` and `directives/project_brief.md` automatically and will follow the same rules Anis's does.

## Every session

```bash
git pull            # ALWAYS first. Deploys come from local files.
# ... work ...
git add -A && git commit -m "what you did"
git push
```

## Preview the website locally

```bash
python3 -m http.server 4321 --directory website
# open http://localhost:4321
```

## Deploying to production

Today only Anis deploys (Vercel CLI on his machine). After you push, ping him to deploy, or:
- Better setup (pending): connect the Vercel project to this GitHub repo so every push to main auto-deploys. Ask Anis.

## The three rules you cannot break

1. Never sell with the word "drone" (see CLAUDE.md rule 1).
2. Never claim more than what is demonstrated. TRL, watts, autonomy: honest, always.
3. No emoji, no em dashes, austere tone everywhere.

Questions: anis@chargebotic.com
