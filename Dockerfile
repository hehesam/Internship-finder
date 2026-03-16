FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get upgrade -y \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY internship_bot ./internship_bot
COPY sample_data ./sample_data
COPY tools ./tools
COPY README.md .
COPY .env.example .

CMD ["python", "-m", "internship_bot.main"]
