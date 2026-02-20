# DataDotMD

A web application for browsing and tracking DATA.md files across directory structures.

## Features

- **Homepage**: Lists all DATA.md files with pagination, sorted by most recently updated data
- **Directory Browser**: Navigate through directories and view DATA.md content
- **History Tracking**: Maintains version history of DATA.md files
- **Missing File Warnings**: Highlights directories without DATA.md files
- **Filesystem Scanner**: Automatically scans and updates the database

## Technology Stack

- **FastAPI**: Web framework
- **HTMX**: Dynamic content updates
- **SQLModel**: Database ORM
- **Tailwind CSS**: Styling
- **Pydantic Settings**: Configuration management

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

The application will be available at http://localhost:8000

## Configuration

Configuration is managed through environment variables or a `.env` file:

- `APP_NAME`: Application name (default: "DataDotMD")
- `APP_BASE_URL`: Base URL for the application (default: "http://localhost:8000")
- `DEBUG`: Enable debug mode (default: False)
- `DATA_ROOT`: Root directory to scan for DATA.md files (default: "data")
- `DATABASE_URL`: SQLite database URL (default: "sqlite:///./datadotmd.db")
- `ITEMS_PER_PAGE`: Number of items per page (default: 10)

## Usage

1. **Initial Scan**: Click the "Scan Filesystem" button to scan your data directory and populate the database
2. **Browse Files**: Navigate to the homepage to see all DATA.md files
3. **View Directory**: Click on any DATA.md file to view its content and the directory structure
4. **View History**: On the directory page, expand the history section to see previous versions

## Project Structure

```
datadotmd/
  app/
    main.py              # FastAPI application
    config.py            # Configuration settings
    routes.py            # API routes
    templating.py        # Template utilities
    templates/           # Jinja2 templates
      base.html          # Base template
      index.html         # Homepage
      browse.html        # Directory browser
      htmx/              # HTMX partials
        file_list.html
        history.html
  system/
    scanner.py           # Filesystem scanner
    sync.py              # Database synchronization
  database/
    models.py            # SQLModel models
    service.py           # Database service layer
```

## Development

Install development dependencies:

```bash
pip install -e ".[dev]"
```

Run tests:

```bash
pytest
```

## License

MIT
