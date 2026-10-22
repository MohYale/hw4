# Campus Customs — HW4

Yale EMBA 409 Assignment 4. This is the Campus Customs shop: a product catalogue, accounts, and a chat assistant that reads prices and stock from the database.

## What is here

- `backend/` — FastAPI shop and the PydanticAI assistant
- `frontend/` — the website
- `data/` — `campus_customs.db` and the product photos
- `output/` — harness, usability, design, the app check, and the audit trail
- `AI_prompts.md` — the prompts for each problem

The API key is not in this repository. Create `backend/.env` and set `OPENAI_API_KEY` or `PORTKEY_API_KEY` before you use the chat.

## Run the API

From `backend/`:

```
pip install -r requirements.txt
python -m uvicorn main:app --reload --port 8000
```

## Run the website

From `frontend/`:

```
npm install
npm run dev
```

Open http://127.0.0.1:5173/. The site sends `/api` to the API on port 8000.

How the assistant, tools, safety rules, and limits work is in `output/harness.md`.
