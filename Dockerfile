FROM python:3.12-slim

WORKDIR /app

# Install system dependencies (required for some PDF libraries)
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your bot code
COPY bot.py .

# Run the bot
CMD ["python", "bot.py"]
