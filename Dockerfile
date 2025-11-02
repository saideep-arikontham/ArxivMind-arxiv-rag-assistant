# ---- Base with uv ----
FROM ghcr.io/astral-sh/uv:python3.12-bookworm AS base

ENV UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_PROJECT_ENVIRONMENT=/app/.venv

WORKDIR /app

# 1) Lock-aware deps layer
COPY pyproject.toml uv.lock* ./
RUN uv sync --frozen --no-install-project

# 2) App code
COPY . .
RUN uv sync --frozen

# ---- Streamlit ----
FROM base AS streamlit
EXPOSE 8501
CMD ["uv", "run", "streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]

# ---- FastAPI (generic; provider picked via env) ----
FROM base AS api
EXPOSE 8000
CMD ["uv", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
