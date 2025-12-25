# Copilot Instructions — AI Resource Intelligence Hub

## Quick summary
- Desktop Python app (CustomTkinter UI) that extracts resources from files in `Resources/` using Google Gemini and stores them in either a CSV (`data/ai_resources_tagged.csv`) or Supabase DB.
- Major components: UI (`app/ui/*`), Core logic (`app/core/*`), Worker scripts (`app/workers/*`), repo-level config (`config.ini`) and tagging reference CSV (`tagging_reference.csv`).

## Big picture (what to know first)
- Main entry: `python main.py` launches the GUI (tested on Windows). The UI starts background workers using `app.workers.script_csv.main()` and `app.workers.script_db.main()`.
- AI interaction: `app/core/ai_service.py` configures `google.generativeai` and calls a Gemini model (`gemini-2.5-flash-lite`). It expects the model to return a JSON list of objects describing resources (keys: `title`, `provider`, `description`, `link`, `tags`, `tech_tags`, `category`, `subcategory`).
- Content ingestion: `app/core/content_streamer.py` streams text from `.pdf`, `.docx`, and `.txt` in memory-efficient chunks (default 4k with 500 overlap).
- Data handling: `app/core/data_handler.py` centralizes CSV read/write, tagging-guide parsing (`tagging_reference.csv` supports semicolons/tabs/commas), history tracking (`processed_history.log`), and safe append behavior.

## Developer workflows & useful commands ✅
- Run GUI locally: `python main.py` (opens CustomTkinter window). Use Settings dialog to set `GEMINI_API_KEY` and `SUPABASE_KEY` (these are also stored in `config.ini`).
- Run CSV worker headlessly for quick debug: `python -c "from app.workers.script_csv import main; main()"` (or import and call `main(stop_event)` for cancellable runs).
- Run DB worker similarly: `python -c "from app.workers.script_db import main; main()"`
- Check/seed `Resources/` directory with a few `.pdf`/`.docx`/`.txt` to exercise streaming + AI extraction.

## Project-specific patterns & conventions 🔧
- AppConfig centralizes paths and settings. Use `AppConfig` instead of hardcoding file paths.
- Logging is UI-forward: `print()`/stdout is captured by `ConsoleLogger` and surfaced in the UI console frame — prefer simple `print()` for user-facing events and keep messages short and emoji-tagged (e.g., `✅`, `❌`, `⚠️`).
- Worker cancellation uses `stop_event` (threading.Event). Long-running loops check `stop_event.is_set()` and exit gracefully.
- Tagging dictionary parsing: `DataHandler.load_tagging_guide()` first tries CSV parsing (supports multiple encodings/delimiters) then falls back to brute-force text parsing.
- Deduplication: script_csv checks existing CSV `link` values; script_db fetches `link` values from Supabase to avoid duplicates. Also `processed_history.log` records finished files.

## Important files to reference 📁
- app/core/ai_service.py — AI calls, safety handling, JSON recovery logic
- app/core/content_streamer.py — file streaming and chunking
- app/core/data_handler.py — CSV/guide/history helpers
- app/workers/script_csv.py — CSV worker; uses `AIService` + `DataHandler.append_csv_safe`
- app/workers/script_db.py — DB worker; uploads to Supabase
- tagging_reference.csv — authoritative tag dictionary (semicolon delimited in this repo)
- config.ini — example keys and settings (DO NOT commit live/sensitive keys)

## Notable gotchas & suggestions ⚠️
- Bug found: In `app/workers/script_csv.py` the call

```py
DataHandler.append_csv_safe(AppConfig.CSV_FILE, cols=[...], row_data=row)
```

doesn't match `DataHandler.append_csv_safe(file_path, fieldnames, row_data)` (no `cols` kwarg). Suggested fixes:
  - Change call to positional: `DataHandler.append_csv_safe(AppConfig.CSV_FILE, ['id', ...], row)`
  - OR update `append_csv_safe` signature to accept `cols=` and forward to `fieldnames`.

- Secrets: `config.ini` holds API keys (there is a sample file). Keys can be set via Settings dialog in the UI; avoid committing secrets to VCS.
- There is no `requirements.txt` or tests folder. For setup, install at minimum:
  - customtkinter, google-generativeai, PyPDF2, python-docx, psutil, supabase
  - Example: `pip install customtkinter google-generativeai PyPDF2 python-docx psutil supabase`.

## How to extend or change the AI prompt safely 💡
- Keep strict JSON expectation: the code expects the model to return strict JSON (list of objects). If you change prompts, keep a documented alternate parser or robust error handling (see current safety checks in `ai_service.extract_resource` — it guards `response.text` and retries on JSON decode errors).
- Test prompt changes on small excerpts (use `ContentStreamer.generator()` to get deterministic chunks).

## Testing & contributing notes
- Tests not present; recommended places for unit tests:
  - `tests/core/test_data_handler.py` (encoding/delimiter behavior)
  - `tests/core/test_content_streamer.py` (pdf/docx/txt streaming)
  - `tests/workers/test_script_csv.py` (deduplication, append behavior — mock `AIService`)
- When proposing fixes, include a small integration test that simulates a `Resources/` file and a fake GEMINI response.

---
If any of the above sections are unclear or you'd like extra detail (examples, PRs to fix the `cols` bug, or adding a `requirements.txt` + CI tests), tell me which you'd like me to tackle next.