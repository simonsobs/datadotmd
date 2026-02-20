FROM python:3.13

WORKDIR /app

COPY pyproject.toml .
RUN pip install --no-cache-dir -e .

COPY datadotmd/ ./datadotmd/

ENV APP_BASE_URL=http://localhost:8000
ENV DATABASE_URL=sqlite:///./datadotmd.db
ENV DATA_ROOT=/data

EXPOSE 8000

CMD ["uvicorn", "datadotmd.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
