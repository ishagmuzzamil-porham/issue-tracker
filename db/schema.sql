CREATE TABLE IF NOT EXISTS customers (
    id      SERIAL PRIMARY KEY,
    name    TEXT NOT NULL,
    contact TEXT
);

CREATE TABLE IF NOT EXISTS projects (
    id          SERIAL PRIMARY KEY,
    name        TEXT NOT NULL,
    customer_id INTEGER NOT NULL REFERENCES customers(id)
);
CREATE TABLE IF NOT EXISTS issues (
    id          SERIAL PRIMARY KEY,
    title       TEXT NOT NULL,
    description TEXT NOT NULL,

    type        TEXT NOT NULL DEFAULT 'issue'
                CHECK (type IN ('issue', 'incident', 'improvement_request')),
    status      TEXT NOT NULL DEFAULT 'open'
                CHECK (status IN ('open', 'in_progress', 'resolved', 'not_feasible')),

    project_id  INTEGER NOT NULL REFERENCES projects(id),
    location    TEXT,
    reported_by TEXT NOT NULL,
    reported_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    resolution  TEXT,
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);