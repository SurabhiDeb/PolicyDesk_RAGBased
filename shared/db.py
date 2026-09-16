"""The only file that knows where the database lives."""

import os

import psycopg
from dotenv import load_dotenv
from pgvector.psycopg import register_vector

load_dotenv()

DSN = os.environ.get("POLICYDESK_DSN", "postgresql:///policydesk")


def connect():
    """An open connection that understands the vector type."""
    conn = psycopg.connect(DSN)
    register_vector(conn)
    return conn