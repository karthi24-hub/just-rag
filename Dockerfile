# Use astral-sh/uv for fast builds
FROM ghcr.io/astral-sh/uv:python3.10-bookworm-slim

# Set working directory
WORKDIR /app

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy from the host to the container
COPY . .

# Install the project's dependencies using uv
RUN uv sync --frozen --no-install-project

# Expose Streamlit port
EXPOSE 8501

# Command to run the application using uv
CMD ["uv", "run", "streamlit", "run", "app/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
