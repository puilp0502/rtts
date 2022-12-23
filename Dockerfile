FROM python:3.11-alpine
RUN apk --no-cache add git curl tini && \
	curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="/root/.local/bin:$PATH"
WORKDIR /app
COPY poetry.lock pyproject.toml /app/
RUN poetry config virtualenvs.create false && \
	poetry install 
COPY . /app

ENTRYPOINT ["tini", "-v", "-g", "--", "./start.sh"]

