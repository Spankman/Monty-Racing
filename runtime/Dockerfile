FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y --no-install-recommends git ca-certificates && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements-runner.txt /app/
COPY monty_v6/requirements.txt /app/monty_v6/requirements.txt
RUN pip install --no-cache-dir -r requirements-runner.txt
# Public pinned code only; no provider tokens or private archive are build args.
RUN git init /opt/monty-v7 && cd /opt/monty-v7 && git remote add origin https://github.com/Spankman/Monty-Racing.git && git config core.sparseCheckout true && printf 'v7/\n' > .git/info/sparse-checkout && git fetch --depth=1 origin efc51abb1595ef1eb8417e2d4e0d591f6d3c9378 && git checkout --detach FETCH_HEAD
COPY . /app
ARG MONTY_SOURCE_COMMIT
# The existing executor records git HEAD. Retain its exact provenance contract
# rather than substituting an environment string or weakening that check.
RUN python -c 'import os,re; assert re.fullmatch("[0-9a-f]{40}",os.environ["MONTY_SOURCE_COMMIT"])' && git init /app && git remote add origin https://github.com/Spankman/Monty-Racing.git && git fetch --depth=1 origin "$MONTY_SOURCE_COMMIT" && git reset --mixed FETCH_HEAD && git diff --exit-code && test -z "$(git ls-files --others --exclude-standard)"
RUN useradd --uid 10001 --create-home monty && mkdir -m 0700 /state && chown monty:monty /state && git config --system --add safe.directory /app && git config --system --add safe.directory /opt/monty-v7
USER monty
EXPOSE 8080
# Supply original manifest-matching private artifacts by secure mount/init.
CMD ["python","-m","runtime.http_api","--bind","0.0.0.0","--port","8080","--data","/state","--v7-root","/opt/monty-v7"]
