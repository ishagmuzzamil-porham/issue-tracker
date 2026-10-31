import os
from typing import Literal, Optional

import psycopg
from psycopg.rows import dict_row
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://tracker:devpass@localhost:5432/issues",
)

app = FastAPI(title="Issue Tracker API")


class IssueCreate(BaseModel):
    title: str = Field(min_length=3, max_length=200)
    description: str = Field(min_length=3)
    type: Literal["issue", "incident", "improvement_request"] = "issue"
    project_id: int
    location: Optional[str] = None
    reported_by: str = Field(min_length=1)


def get_connection():
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/issues")
def list_issues():
    query = """
        SELECT i.id, i.title, i.type, i.status, i.location,
               i.reported_by, i.reported_at,
               p.name AS project, c.name AS customer
        FROM issues i
        JOIN projects p ON p.id = i.project_id
        JOIN customers c ON c.id = p.customer_id
        ORDER BY i.reported_at DESC
    """
    with get_connection() as conn:
        rows = conn.execute(query).fetchall()
    return rows


@app.post("/issues", status_code=201)
def create_issue(issue: IssueCreate):
    query = """
        INSERT INTO issues (title, description, type, project_id, location, reported_by)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id, title, type, status, project_id, reported_at
    """
    values = (
        issue.title,
        issue.description,
        issue.type,
        issue.project_id,
        issue.location,
        issue.reported_by,
    )
    with get_connection() as conn:
        try:
            row = conn.execute(query, values).fetchone()
        except psycopg.errors.ForeignKeyViolation:
            raise HTTPException(status_code=404, detail="Project not found")
    return row
