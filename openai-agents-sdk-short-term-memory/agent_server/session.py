"""
TODO: Refactor into db-ai-bridge/openai sdk
"""

import logging
import os
import time
import uuid
from threading import Lock
from typing import Optional

from agents.extensions.memory import SQLAlchemySession
from databricks.sdk import WorkspaceClient
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

logger = logging.getLogger(__name__)

# Lakebase defaults from https://docs.databricks.com/aws/en/oltp/projects/connect-overview
DEFAULT_TOKEN_CACHE_DURATION_SECONDS = 50 * 60  # Cache token for 50 minutes
DEFAULT_SSLMODE = "require"
DEFAULT_PORT = 5432
DEFAULT_DATABASE = "databricks_postgres"

# Global state for engine and token caching
_engine: Optional[AsyncEngine] = None
_cached_token: Optional[str] = None
_cache_ts: Optional[float] = None
_cache_lock = Lock()
_workspace_client: Optional[WorkspaceClient] = None
_instance_name: Optional[str] = None


def _get_workspace_client() -> WorkspaceClient:
    """Get or create the WorkspaceClient."""
    global _workspace_client
    if _workspace_client is None:
        _workspace_client = WorkspaceClient()
    return _workspace_client


def _infer_username(w: WorkspaceClient) -> str:
    """Get username for database connection, prioritizing service principal first."""
    try:
        sp = w.current_service_principal.me()
        if sp and getattr(sp, "application_id", None):
            return sp.application_id
    except Exception:
        logger.debug(
            "Could not get service principal, using current user for Lakebase credentials."
        )
    user = w.current_user.me()
    return user.user_name


def _resolve_lakebase_instance(instance_name: str) -> tuple[str, str]:
    """
    Resolve Lakebase instance to get host and username.
    Args:
        instance_name: Name of the Lakebase instance
    Returns:
        Tuple of (host, username)
    """
    w = _get_workspace_client()
    
    try:
        instance = w.database.get_database_instance(instance_name)
    except Exception as exc:
        raise ValueError(
            f"Unable to resolve Lakebase instance '{instance_name}'. "
            "Ensure the instance name is correct and you have access."
        ) from exc
    
    resolved_host = getattr(instance, "read_write_dns", None) or getattr(
        instance, "read_only_dns", None
    )
    if not resolved_host:
        raise ValueError(
            f"Lakebase host not found for instance '{instance_name}'. "
            "Ensure the instance is running and in AVAILABLE state."
        )
    
    username = _infer_username(w)
    return resolved_host, username


def _mint_token(instance_name: str) -> str:
    """Mint a new database credential token."""
    w = _get_workspace_client()
    try:
        cred = w.database.generate_database_credential(
            request_id=str(uuid.uuid4()),
            instance_names=[instance_name],
        )
    except Exception as exc:
        raise ConnectionError(
            f"Failed to obtain credential for Lakebase instance "
            f"'{instance_name}'. Ensure the caller has access."
        ) from exc
    return cred.token


def _get_token(instance_name: str) -> str:
    """Get cached token or mint a new one if expired."""
    global _cached_token, _cache_ts
    
    with _cache_lock:
        now = time.time()
        if (
            _cached_token
            and _cache_ts
            and (now - _cache_ts) < DEFAULT_TOKEN_CACHE_DURATION_SECONDS
        ):
            return _cached_token
        
        token = _mint_token(instance_name)
        _cached_token = token
        _cache_ts = now
        logger.info("Minted new Lakebase credential token")
        return token


def get_database_url() -> str:
    """
    Get the PostgreSQL database URL from Databricks Lakebase.
    
    Uses the LAKEBASE_INSTANCE_NAME environment variable to resolve the
    database instance and generates rotating credentials automatically.
    
    Falls back to DATABASE_URL or individual PG* environment variables
    for non-Databricks environments (e.g., local development).
    """
    global _instance_name
    
    # Check for Lakebase instance name (preferred for Databricks)
    instance_name = os.getenv("LAKEBASE_INSTANCE_NAME")
    if instance_name:
        _instance_name = instance_name
        host, username = _resolve_lakebase_instance(instance_name)
        token = _get_token(instance_name)
        database = os.getenv("LAKEBASE_DATABASE", DEFAULT_DATABASE)
        
        # Use psycopg (async) driver for rotating credentials support
        return (
            f"postgresql+psycopg://{username}:{token}@{host}:{DEFAULT_PORT}/{database}"
            f"?sslmode={DEFAULT_SSLMODE}"
        )
    
    # Fallback: Check for direct URL (for local development)
    database_url = os.getenv("DATABASE_URL")
    if database_url:
        # Ensure it's an async URL
        if database_url.startswith("postgresql://"):
            return database_url.replace("postgresql://", "postgresql+psycopg://")
        return database_url
    
    # Fallback: Build from individual components (for local development)
    host = os.getenv("PGHOST", "localhost")
    port = os.getenv("PGPORT", "5432")
    database = os.getenv("PGDATABASE", "agent_sessions")
    user = os.getenv("PGUSER", "postgres")
    password = os.getenv("PGPASSWORD", "")
    
    return f"postgresql+psycopg://{user}:{password}@{host}:{port}/{database}"


def get_engine() -> AsyncEngine:
    """
    Get or create the async database engine.
    
    For Lakebase, this will check if the token is still valid and
    recreate the engine if the token has expired.
    """
    global _engine, _cache_ts
    
    # Check if we need to recreate the engine due to token expiration
    if _engine is not None and _instance_name is not None:
        with _cache_lock:
            now = time.time()
            if _cache_ts and (now - _cache_ts) >= DEFAULT_TOKEN_CACHE_DURATION_SECONDS:
                # Token expired, dispose old engine
                logger.info("Lakebase token expired, recreating engine")
                _engine.sync_engine.dispose()
                _engine = None
    
    if _engine is None:
        _engine = create_async_engine(
            get_database_url(),
            echo=False,  # Set to True for SQL debugging
            pool_pre_ping=True,
        )
    return _engine


async def get_session(
    thread_id: Optional[str] = None, 
    create_tables: bool = True
) -> tuple[SQLAlchemySession, str]:
    """
    Get or create a session for the given thread_id.
    
    Args:
        thread_id: Optional thread ID. If not provided, a new UUID is generated.
        create_tables: Whether to create database tables if they don't exist.
        
    Returns:
        A tuple of (session, thread_id) where thread_id is the resolved ID.
    """
    # Generate new thread_id if not provided
    resolved_thread_id = thread_id or str(uuid.uuid4())
    
    # Create session using the engine
    engine = get_engine()
    session = SQLAlchemySession(
        session_id=resolved_thread_id,
        engine=engine,
        create_tables=create_tables,
    )
    
    return session, resolved_thread_id


def generate_thread_id() -> str:
    """Generate a new unique thread ID."""
    return str(uuid.uuid4())
