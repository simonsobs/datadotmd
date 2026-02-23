# DataDotMD

A small web app for browsing and tracking DATA.md files across a directory tree.

## Features

- **Browse + history**: Directory tree, DATA.md rendering, and version history
- **Pagination**: Ordered by most recently updated underlying data
- **Scan on demand**: POST /scan triggers a background scan (Slack-signed or grant)
- **Auto scan**: Optional scheduler runs scans on an interval
- **Notifications**: New/changed DATA.md and underlying data updates

## Technology Stack

- FastAPI, Jinja2, HTMX, SQLModel, Pydantic Settings

## Installation

1. Install dependencies:
   ```bash
   pip install -e .
   ```

2. Create a `.env` file (optional):
   ```bash
   cp .env.example .env
   ```

3. Configure the data directory in `.env`:
   ```
   DATA_ROOT=./data
   ```

## Running the Application

Start the development server:

```bash
uvicorn datadotmd.app.main:app --reload
```

Or:

```bash
./run.sh
```

The application will be available at http://localhost:8000

## Configuration

Configuration is managed through environment variables or a `.env` file:

- `APP_NAME`, `APP_BASE_URL`, `DEBUG`
- `DATA_ROOT`, `DATABASE_URL`, `ITEMS_PER_PAGE`
- `ENABLE_AUTO_SCAN`, `AUTO_SCAN_INTERVAL_MINUTES`
- `NOTIFIER_NAME` (see notifiers library credentials)
- `ROOT_DIRECTORY_NAME`
- `AUTH_TYPE` (mock|soauth), `REQUIRED_GRANT`
- `AUTHENTICATION_BASE_URL`, `APP_ID`, `CLIENT_SECRET`, `PUBLIC_KEY`, `KEY_PAIR_TYPE`
- `SLACK_SIGNING_SECRET`

