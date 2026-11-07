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

## Startup checklist
1. `docker start db`
2. `cd ~/issue-tracker/backend`
3. `source .venv/bin/activate`
4. `uvicorn main:app --reload`