---
description: Dev commands for running and building the backend and frontend
---

# Commands

## Backend

```bash
cd backend
# Activate venv (Windows)
source venv/Scripts/activate
# Run dev server
python main.py
# Run tests
pytest
```

## Frontend

```bash
cd frontend
npm install        # first time
npm run dev        # dev server on :5173
npm run build      # production build → dist/
npm run test       # vitest (single run)
npm run preview    # preview production build
```

## Start both servers at once

```bash
# Windows
start.bat
# Linux/macOS
./start.sh
```
