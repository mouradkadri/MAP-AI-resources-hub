# AI Resource Intelligence Hub (v6.0)

![Console Preview](assets/console.png)

AI Resource Intelligence Hub is a desktop app (CustomTkinter + Python) that extracts, categorizes and stores AI resources found in documents using a generative model (Gemini). It can export results to CSV or upload them to a Supabase database.

---

## 🚀 Quick Start

1. Create a virtual environment and install dependencies (example):

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

2. Configure API keys in `config.ini` (or use the Settings dialog in the app):

- `GEMINI_API_KEY` (Gemini / Google generative)
- `SUPABASE_KEY` and `SUPABASE_URL` (if using DB upload)

3. Run the GUI:

```bash
python main.py
```

4. To run workers headlessly for quick checks:

```bash
# CSV mode (append to CSV)
python -c "from app.workers.script_csv import main; main()"

# DB mode (upload to Supabase)
python -c "from app.workers.script_db import main; main()"
```

---

## ✅ Features

- Stream `.pdf`, `.docx`, `.txt` files and extract resource metadata (title, provider, description, link, tags)
- Tagging engine driven by `tagging_reference.csv` (robust parser handles messy formats)
- Save to CSV (`data/ai_resources_tagged.csv`) or upload to Supabase
- Live operation logs, progress bar, and analytics (donut chart, bar chart, timeline)
- Thread-safe logging and file-based debug log (`data/logger_debug.log`) for troubleshooting

---

## 📁 Key files & folders

- `Resources/` — put your `.pdf`, `.docx`, `.txt` inputs here
- `data/ai_resources_tagged.csv` — main CSV output
- `processed_history.log` — which files have been processed (used to avoid duplicate work)
- `tagging_reference.csv` — tagging dictionary used by the AI prompt
- `data/logger_debug.log` — persistent logger debug output when needed

---

## 🛠️ Developer Notes

- Main entry: `main.py` (starts the CustomTkinter GUI)
- Workers:
  - `app/workers/script_csv.py` (CSV export mode)
  - `app/workers/script_db.py` (Supabase upload mode)
- Core modules:
  - `app/core/ai_service.py` — wraps Gemini calls and returns strict JSON
  - `app/core/content_streamer.py` — file chunking/streaming (memory-efficient)
  - `app/core/data_handler.py` — CSV handling, tagging guide parsing, history tracking

---

## 📸 Screenshots

> Add the screenshots to the `assets/` directory using the following file names and they will appear here:

- `assets/console.png` — Console / live logs preview
- `assets/analytics.png` — Analytics dashboard (donut + bar + timeline)
- `assets/data.png` — Data table view (Treeview)

Example markdown (already included at top of this file):

```md
![Console Preview](assets/console.png)
```

---

## ⚙️ Troubleshooting

- If the app reports "No new resources" but files changed, try removing the filename from `processed_history.log` to force a re-scan. A future update adds mtime-aware history.
- If the AI responses aren't parsed, check `data/logger_debug.log` for raw model outputs and parsing failures.
- If CSV append fails due to file locks, close Excel or other programs using the file and re-run.

---

## Contributing

Contributions welcome! Suggested improvements:
- Add unit tests for `DataHandler` parsing and worker flows
- Add CI (tests, linting, packaging)
- Add a settings toggle for verbose logger UI output

Please open an issue or a PR describing the change.

---

## License

Add a `LICENSE` file to the repo (MIT recommended) and reference it here.

---

Made with ❤️ — keep your `tagging_reference.csv` updated for best results.
