"""Database connection and session management"""

import os
from pathlib import Path
from typing import Optional, Generator
from contextlib import contextmanager
import logging

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, Session, scoped_session
from sqlalchemy.pool import StaticPool, QueuePool

from .models import Base
from ..core.config import StorageConfig
from ..core.logging import get_logger

logger = get_logger(__name__)


class DatabaseManager:
    """Database connection and session manager"""
    
    def __init__(self, config: StorageConfig):
        """Initialize database manager
        
        Args:
            config: Storage configuration
        """
        self.config = config
        self.engine = None
        self.SessionLocal = None
        self._initialized = False
        
    def get_database_url(self) -> str:
        """Get database URL based on configuration
        
        Returns:
            Database connection URL
        """
        backend = self.config.backend.lower()
        
        if backend == 'sqlite':
            # Get SQLite path from config
            db_path = self.config.sqlite.get('path', '~/.docscope/docscope.db')
            db_path = os.path.expanduser(db_path)
            
            # Create directory if it doesn't exist
            Path(db_path).parent.mkdir(parents=True, exist_ok=True)
            
            # Use SQLite URL
            return f"sqlite:///{db_path}"
            
        elif backend == 'postgresql':
            # PostgreSQL connection
            pg_config = self.config.get('postgresql', {})
            host = pg_config.get('host', 'localhost')
            port = pg_config.get('port', 5432)
            database = pg_config.get('database', 'docscope')
            user = pg_config.get('user', 'docscope')
            password = pg_config.get('password', '')
            
            return f"postgresql://{user}:{password}@{host}:{port}/{database}"
            
        else:
            raise ValueError(f"Unsupported database backend: {backend}")
    
    def initialize(self, drop_existing: bool = False) -> None:
        """Initialize database connection and create tables
        
        Args:
            drop_existing: Whether to drop existing tables
        """
        if self._initialized and not drop_existing:
            return
            
        try:
            db_url = self.get_database_url()
            logger.info(f"Initializing database: {self.config.backend}")
            
            # Create engine with appropriate settings
            if self.config.backend == 'sqlite':
                # SQLite-specific settings
                self.engine = create_engine(
                    db_url,
                    connect_args={'check_same_thread': False},
                    poolclass=StaticPool,
                    echo=False
                )
                
                # Enable foreign keys and WAL mode for SQLite
                @event.listens_for(self.engine, "connect")
                def set_sqlite_pragma(dbapi_conn, connection_record):
                    cursor = dbapi_conn.cursor()
                    cursor.execute("PRAGMA foreign_keys=ON")
                    cursor.execute("PRAGMA journal_mode=WAL")
                    cursor.close()
                    
            else:
                # PostgreSQL/MySQL settings
                self.engine = create_engine(
                    db_url,
                    poolclass=QueuePool,
                    pool_size=10,
                    max_overflow=20,
                    pool_pre_ping=True,
                    echo=False
                )
            
            # Create session factory
            self.SessionLocal = scoped_session(
                sessionmaker(
                    autocommit=False,
                    autoflush=False,
                    bind=self.engine
                )
            )
            
            # Create tables
            if drop_existing:
                logger.warning("Dropping existing tables")
                Base.metadata.drop_all(bind=self.engine)
                
            Base.metadata.create_all(bind=self.engine)
            
            # Create full-text search index for SQLite
            if self.config.backend == 'sqlite':
                self._create_fts_index()
            
            self._initialized = True
            logger.info("Database initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    def _create_fts_index(self) -> None:
        """Create full-text search index for SQLite"""
        try:
            with self.engine.connect() as conn:
                # Create FTS5 virtual table for full-text search
                conn.execute(text("""
                    CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts USING fts5(
                        doc_id,
                        title,
                        content,
                        tags,
                        tokenize='porter'
                    )
                """))
                
                # Create trigger to keep FTS index in sync
                conn.execute(text("""
                    CREATE TRIGGER IF NOT EXISTS documents_fts_insert
                    AFTER INSERT ON documents
                    BEGIN
                        INSERT INTO documents_fts(doc_id, title, content)
                        VALUES (new.id, new.title, new.content);
                    END
                """))
                
                conn.execute(text("""
                    CREATE TRIGGER IF NOT EXISTS documents_fts_update
                    AFTER UPDATE ON documents
                    BEGIN
                        UPDATE documents_fts
                        SET title = new.title, content = new.content
                        WHERE doc_id = new.id;
                    END
                """))
                
                conn.execute(text("""
                    CREATE TRIGGER IF NOT EXISTS documents_fts_delete
                    AFTER DELETE ON documents
                    BEGIN
                        DELETE FROM documents_fts WHERE doc_id = old.id;
                    END
                """))
                
                conn.commit()
                logger.debug("Created FTS index for SQLite")
                
        except Exception as e:
            logger.warning(f"Could not create FTS index: {e}")
    
    def get_session(self) -> Session:
        """Get a database session
        
        Returns:
            Database session
        """
        if not self._initialized:
            self.initialize()
        return self.SessionLocal()
    
    @contextmanager
    def session_scope(self) -> Generator[Session, None, None]:
        """Provide a transactional scope for database operations
        
        Yields:
            Database session
        """
        session = self.get_session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def close(self) -> None:
        """Close database connections"""
        if self.SessionLocal:
            self.SessionLocal.remove()
        if self.engine:
            self.engine.dispose()
        self._initialized = False
        logger.debug("Database connections closed")
    
    def get_stats(self) -> dict:
        """Get database statistics
        
        Returns:
            Dictionary with database stats
        """
        stats = {
            'backend': self.config.backend,
            'initialized': self._initialized,
        }
        
        if self._initialized:
            with self.session_scope() as session:
                # Get table counts
                from .models import DocumentModel, CategoryModel, TagModel
                
                stats['documents'] = session.query(DocumentModel).count()
                stats['categories'] = session.query(CategoryModel).count()
                stats['tags'] = session.query(TagModel).count()
                
                # Get database size for SQLite
                if self.config.backend == 'sqlite':
                    db_path = os.path.expanduser(
                        self.config.sqlite.get('path', '~/.docscope/docscope.db')
                    )
                    if Path(db_path).exists():
                        stats['size_mb'] = Path(db_path).stat().st_size / (1024 * 1024)
        
        return stats
    
    def vacuum(self) -> None:
        """Optimize database (vacuum/analyze)"""
        if self.config.backend == 'sqlite':
            with self.engine.connect() as conn:
                conn.execute(text("VACUUM"))
                conn.execute(text("ANALYZE"))
                conn.commit()
            logger.info("Database vacuumed and analyzed")
        elif self.config.backend == 'postgresql':
            with self.engine.connect() as conn:
                conn.execute(text("VACUUM ANALYZE"))
                conn.commit()
            logger.info("Database vacuumed and analyzed")
    
    def backup(self, backup_path: str) -> None:
        """Backup database (SQLite only)
        
        Args:
            backup_path: Path to backup file
        """
        if self.config.backend != 'sqlite':
            raise NotImplementedError("Backup only supported for SQLite")
        
        import sqlite3
        import shutil
        
        db_path = os.path.expanduser(
            self.config.sqlite.get('path', '~/.docscope/docscope.db')
        )
        
        # Close connections before backup
        self.close()
        
        try:
            # Simple file copy for SQLite
            shutil.copy2(db_path, backup_path)
            logger.info(f"Database backed up to {backup_path}")
        finally:
            # Reinitialize
            self.initialize()