# Lessons learned

## 1. POST /issues returned 500
- What happened: I sent a new issue from /docs and the server answered "Internal Server Error".
- Cause: The table `issues` did not exist in the database, because the file `db/schema.sql` was never created and loaded.
- How I found it: I read the last line of the traceback in the uvicorn terminal: `relation "issues" does not exist`.
- Fix: I created `db/schema.sql`, loaded it with `docker exec -i db psql -U tracker -d issues < db/schema.sql`, then added a customer and a project.
- Lesson: the browser only shows "Internal Server Error". The real reason is in the server logs, on the last line.

## 2. Other problems on the way
- The db container was stopped: after the laptop was off, containers stay stopped until I run `docker start db`.
- uvicorn was "command not found": the virtual environment was not active, and uvicorn is installed only inside it. Fix: `source .venv/bin/activate`.
- The SQL syntax error: the first command had no `;` at the end, so SQL read the second `CREATE TABLE` as part of the first.
- The project id was 2, not 1: a refused insert still uses up a number from the id counter. Always read the id, never assume it.

## 3. Earlier lessons
- A password inside the code ends up on GitHub. The database password is currently a default value in `main.py`, and I will move it to a `.env` file that Git ignores when I add Docker Compose.
- `git push` needs a Personal Access Token, not the account password.
- Copy only the commands, one at a time, and understand what each one does before running it.

## 4. Docker Compose
- Inside a container, `localhost` means the container itself. Containers on the same Compose network reach each other by service name (`db`), because Compose runs a name directory (service discovery).
- Compose describes the desired state in a file. `docker compose up` compares it with what is running and changes only the difference.
- `name: pgdata` makes Compose reuse my existing volume. Without it, Compose creates `issue-tracker_pgdata`, a new empty volume, and the data seems lost.
- `docker compose down` removes containers and the network. `docker compose down -v` also deletes the volumes and my data. Never use `-v` by accident.
- `depends_on` controls start order only, not readiness. A health check is needed for that (to do).
- Secrets: I removed the password default from `main.py`, but Git history still contains `devpass`. With a real password I would have to change it. `.env` is ignored, `.env.example` documents the variables.
- Fail fast: a missing required setting should stop the app at start-up with a clear error (`KeyError: 'DATABASE_URL'`).
- A system is trustworthy when I can destroy it and rebuild it from the files, with the data intact.

## 5. Health checks
- A container being "started" does not mean the service is "ready". `depends_on` alone only controls start order.
- A health check is a command Docker runs repeatedly. Exit code 0 means healthy. Status goes starting, healthy, unhealthy.
- `depends_on` with `condition: service_healthy` makes `api` wait until `db` accepts connections.
- Our `/health` endpoint says "alive", it does not check the database. A deeper readiness check can come later.

## 6. GitHub Actions and tokens
- CI runs on a fresh temporary machine, so hidden dependencies on my laptop become failures.
- The pipeline is code in `.github/workflows/`.
- My first push of a workflow was rejected: a Personal Access Token needs the `workflow` scope to change workflow files. Principle of least privilege: give a token only the permissions it needs. Workflow files run code with access to secrets, so they need an extra permission.
- Never paste a token in a chat, code or commit. Give tokens an expiry date.

## 7. Tests
- A green build is not a correct system. Tests check behavior: arrange, act, assert.
- Tests are executable promises. If someone breaks one, the robot tells them within minutes.
- Put fast cheap checks first (`needs:` in the workflow) and heavy ones later.
- Keep test tools out of the production image: `requirements.txt` (runtime) and `requirements-dev.txt` (runtime plus tests).
- `main.py` fails fast without DATABASE_URL, so the tests set a fake value before importing it.
- `>>` appends to a file, `>` overwrites it. Don't overwrite `.gitignore` by mistake.
- Quote versions in YAML: `"3.14"`, because unquoted `3.10` would be read as the number 3.1.

## 8. Full system in CI
- The stranger test: a fresh machine must reach a working system from the repo alone. CI is the perfect stranger.
- Postgres runs the .sql files in /docker-entrypoint-initdb.d/ once, on an empty data folder, so the schema can load itself (bootstrapping). It does not update an existing database; that needs migrations.
- Bind mount = a path of mine shared into the container. Named volume = Docker-managed storage for data. `:ro` means read-only.
- `docker compose up --wait` uses the health checks, so CI waits for "healthy" instead of guessing with sleep.
- `curl --fail-with-body` makes curl fail on HTTP errors. `exec -T` is needed where there is no terminal. `if: failure()` prints logs only when something broke.
- A CI runner is ephemeral: it is destroyed afterwards, so cleanup doesn't matter there. On my laptop I never use `down -v` carelessly.
- A relative path in `docker run -v` is read as a volume name; a bind mount needs the full path ($PWD).

## 9. Image hygiene
- Each `FROM` starts a new build stage and only the last one becomes the image. My Dockerfile had `FROM` three times by accident: it still worked, but it was wasted work and confusing.
- The build context is everything `docker build` sends to Docker. Without a `.dockerignore`, my 95 MB `.venv` was sent every time, even though only `main.py` was copied. Now the context is a few bytes.
- `.dockerignore` also keeps secrets and junk (`.env`, caches) from ever getting into an image by accident.
- Containers run as root unless I say otherwise. `USER app` follows least privilege: if the app is broken into, the attacker is not root. Check with `docker run --rm --entrypoint whoami <image>`.
- Order layers from rarely changed to often changed (dependencies first, code last), so a code change reuses the cached `pip install` layer.

## 10. Publishing images (CD)
- A registry stores images (Docker Hub, GHCR). `docker push` uploads, `docker pull` downloads.
- Image name = registry/owner/name:tag. The commit-ID tag never moves; `latest` always moves to the newest.
- The publish job has `needs: integration`, so only tested images are published, and only on push to main.
- `GITHUB_TOKEN` is a temporary token per run. `permissions: packages: write` gives it only what it needs.
- `--password-stdin` and the password prompt keep tokens out of logs and shell history.
- "denied" means a permission problem, not a code problem. My fix: ...


## Startup checklist
1. `cd ~/issue-tracker`
2. `docker compose up -d --build --wait`
3. Open http://localhost:8000/docs
4. When done: `docker compose stop` (never `down -v`)

Local development without Docker (hot reload): start only the database with `docker compose up -d db`, then in `backend/` run `source .venv/bin/activate` and `DATABASE_URL=postgresql://tracker:<password>@localhost:5432/issues uvicorn main:app --reload`.
