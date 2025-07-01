FROM python:3.12-slim

# install Poetry
RUN pip install --no-cache-dir poetry

WORKDIR /app
COPY . /app

# install dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi

EXPOSE 5000
CMD ["curator", "web"]
