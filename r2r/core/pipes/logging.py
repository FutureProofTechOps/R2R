import uuid
import functools
import json
import logging
import os
import threading
import types
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)


class PipeLoggingProvider(ABC):
    @abstractmethod
    def close(self):
        pass

    @abstractmethod
    def log(
        self,
        timestamp,
        pipe_run_id,
        pipe_run_type,
        method,
        result,
        log_level,
    ):
        pass

    @abstractmethod
    def get_logs(
        self, max_logs: int, pipe_run_type: Optional[str] = None
    ) -> list:
        pass

class LocalPipeLoggingProvider(PipeLoggingProvider):
    def __init__(self, collection_name="logs", logging_path=None):
        self.conn = None
        self.collection_name = collection_name
        logging_path = logging_path or os.getenv("LOCAL_DB_PATH", "local.sqlite")
        if not logging_path:
            raise ValueError(
                "Please set the environment variable LOCAL_DB_PATH to run `LoggingDatabaseConnectionSingleton` with `local`."
            )
        self.logging_path = logging_path
        self.db_module = self._import_db_module()
        self._init()

    def _import_db_module(self):
        try:
            import sqlite3

            return sqlite3
        except ImportError:
            raise ValueError(
                "Error, `sqlite3` is not installed. Please install it using `pip install sqlite3`."
            )

    def _init(self):
        self.conn = self.db_module.connect(self.logging_path)
        self.conn.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {self.collection_name} (
                timestamp DATETIME,
                pipe_run_id TEXT,
                key TEXT,
                value TEXT
            )
            """
        )
        self.conn.commit()

    def close(self):
        if self.conn:
            self.conn.close()

    def log(
        self,
        pipe_run_id: uuid.UUID,
        key: str,
        value: str,
    ):
        try:
            with self.db_module.connect(self.logging_path) as conn:
                conn.execute(
                    f"INSERT INTO {self.collection_name} (timestamp, pipe_run_id, key, value) VALUES (datetime('now'), ?, ?, ?)",
                    (
                        str(pipe_run_id),
                        key,
                        value,
                    ),
                )
                conn.commit()
        except Exception as e:
            # Handle any exceptions that occur during the logging process
            logger.error(
                f"Error occurred while logging to the local database: {str(e)}"
            )

    def get_logs(self, max_logs: int, pipe_run_type=None) -> list:
        logs = []
        with self.db_module.connect(self.logging_path) as conn:
            cur = conn.cursor()
            if pipe_run_type:
                cur.execute(
                    f"SELECT * FROM {self.collection_name} WHERE pipe_run_type = ? ORDER BY timestamp DESC LIMIT ?",
                    (pipe_run_type, max_logs),
                )
            else:
                cur.execute(
                    f"SELECT * FROM {self.collection_name} ORDER BY timestamp DESC LIMIT ?",
                    (max_logs,),
                )
            colnames = [desc[0] for desc in cur.description]
            results = cur.fetchall()
            logs = [dict(zip(colnames, row)) for row in results]
        return logs


class LoggingDatabaseConnectionSingleton:
    _instance = None
    _lock = threading.Lock()
    _is_configured = False
    SUPPORTED_PROVIDERS = {
        # "postgres": PostgresPipeLoggingProvider,
        "local": LocalPipeLoggingProvider,
        # "redis": RedisPipeLoggingProvider,
    }

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                if not cls._is_configured:
                    # Raise an error if someone tries to create an instance before configuring
                    raise Exception(
                        "LoggingDatabaseConnectionSingleton is not configured. Please call configure() before accessing the instance."
                    )
                cls._instance = super(
                    LoggingDatabaseConnectionSingleton, cls
                ).__new__(cls)
                # Call init to setup the provider after instance creation
                cls._instance.init()
        return cls._instance

    @classmethod
    def configure(cls, provider="postgres", collection_name="logs"):
        if not cls._is_configured:
            cls._provider = provider
            cls._collection_name = collection_name
            cls._is_configured = True
        else:
            raise Exception(
                "LoggingDatabaseConnectionSingleton is already configured."
            )

    def init(self):
        # Initialize logging provider; this should only run once the singleton instance is being created
        self.provider = self._provider
        self.collection_name = self._collection_name
        self._setup_provider()

    def _setup_provider(self):
        # Assuming self.provider and self.collection_name are set from the configure method
        if self.provider not in self.SUPPORTED_PROVIDERS:
            raise ValueError(f"Unsupported provider: {self.provider}")
        self.logging_provider = self.SUPPORTED_PROVIDERS[self.provider](
            self.collection_name
        )

    def __enter__(self):
        return self.logging_provider

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.logging_provider.close()

    def log(
        self,
        pipe_run_id: str,
        key: str,
        value: str,
    ):
        self.logging_provider.log(pipe_run_id, key, value)

    def get_logs(self, max_logs: int, pipe_run_type: Optional[str] = None) -> list:
        return self.logging_provider.get_logs(max_logs, pipe_run_type)

# class PostgresPipeLoggingProvider(PipeLoggingProvider):
#     def __init__(self, collection_name="logs"):
#         self.conn = None
#         self.collection_name = collection_name
#         self.db_module = self._import_db_module()
#         self._init()

#     def _import_db_module(self):
#         try:
#             import psycopg2

#             return psycopg2
#         except ImportError:
#             raise ValueError(
#                 "Error, `psycopg2` is not installed. Please install it using `pip install psycopg2`."
#             )

#     def _init(self):
#         if not all(
#             [
#                 os.getenv("POSTGRES_DBNAME"),
#                 os.getenv("POSTGRES_USER"),
#                 os.getenv("POSTGRES_PASSWORD"),
#                 os.getenv("POSTGRES_HOST"),
#                 os.getenv("POSTGRES_PORT"),
#             ]
#         ):
#             raise ValueError(
#                 "Please set the environment variables POSTGRES_DBNAME, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_HOST, and POSTGRES_PORT to run `LoggingDatabaseConnectionSingleton` with `postgres`."
#             )
#         self.conn = self.db_module.connect(
#             dbname=os.getenv("POSTGRES_DBNAME"),
#             user=os.getenv("POSTGRES_USER"),
#             password=os.getenv("POSTGRES_PASSWORD"),
#             host=os.getenv("POSTGRES_HOST"),
#             port=os.getenv("POSTGRES_PORT"),
#         )
#         with self.conn.cursor() as cur:
#             cur.execute(
#                 f"""
#                 CREATE TABLE IF NOT EXISTS {self.collection_name} (
#                     timestamp TIMESTAMP,
#                     pipe_run_id UUID,
#                     pipe_run_type TEXT,
#                     method TEXT,
#                     result TEXT,
#                     log_level TEXT
#                 )
#             """
#             )
#         self.conn.commit()

#     def close(self):
#         if self.conn:
#             self.conn.close()

#     def log(
#         self,
#         pipe_run_id,
#         pipe_run_type,
#         method,
#         result,
#         log_level,
#     ):
#         try:
#             with self.conn.cursor() as cur:
#                 cur.execute(
#                     f"INSERT INTO {self.collection_name} (timestamp, pipe_run_id, pipe_run_type, method, result, log_level) VALUES (NOW(), %s, %s, %s, %s, %s)",
#                     (
#                         str(pipe_run_id),
#                         pipe_run_type,
#                         method,
#                         str(result),
#                         log_level,
#                     ),
#                 )
#             self.conn.commit()
#         except Exception as e:
#             # Handle any exceptions that occur during the logging process
#             logger.error(
#                 f"Error occurred while logging to the PostgreSQL database: {str(e)}"
#             )

#     def get_logs(self, max_logs: int, pipe_run_type=None) -> list:
#         logs = []
#         with self.conn.cursor() as cur:
#             if pipe_run_type:
#                 cur.execute(
#                     f"SELECT * FROM {self.collection_name} WHERE pipe_run_type = %s ORDER BY timestamp DESC LIMIT %s",
#                     (pipe_run_type, max_logs),
#                 )
#             else:
#                 cur.execute(
#                     f"SELECT * FROM {self.collection_name} ORDER BY timestamp DESC LIMIT %s",
#                     (max_logs,),
#                 )
#             colnames = [desc[0] for desc in cur.description]
#             logs = [dict(zip(colnames, row)) for row in cur.fetchall()]
#         self.conn.commit()
#         return logs

# class RedisPipeLoggingProvider(PipeLoggingProvider):
#     def __init__(self, collection_name="logs"):
#         if not all(
#             [
#                 os.getenv("REDIS_CLUSTER_IP"),
#                 os.getenv("REDIS_CLUSTER_PORT"),
#             ]
#         ):
#             raise ValueError(
#                 "Please set the environment variables REDIS_CLUSTER_IP and REDIS_CLUSTER_PORT to run `LoggingDatabaseConnectionSingleton` with `redis`."
#             )
#         try:
#             from redis import Redis
#         except ImportError:
#             raise ValueError(
#                 "Error, `redis` is not installed. Please install it using `pip install redis`."
#             )

#         cluster_ip = os.getenv("REDIS_CLUSTER_IP")
#         port = os.getenv("REDIS_CLUSTER_PORT")
#         self.redis = Redis(cluster_ip, port, decode_responses=True)
#         self.log_key = collection_name

#     def connect(self):
#         pass

#     def close(self):
#         pass

#     def log(
#         self,
#         pipe_run_id,
#         pipe_run_type,
#         method,
#         result,
#         log_level,
#     ):
#         timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#         log_entry = {
#             "timestamp": timestamp,
#             "pipe_run_id": str(pipe_run_id),
#             "pipe_run_type": pipe_run_type,
#             "method": method,
#             "result": str(result),
#             "log_level": log_level,
#         }
#         try:
#             # Save log entry under a key that includes the pipe_run_type
#             type_specific_key = f"{self.log_key}:{pipe_run_type}"
#             self.redis.lpush(type_specific_key, json.dumps(log_entry))
#         except Exception as e:
#             logger.error(f"Error occurred while logging to Redis: {str(e)}")

#     def get_logs(self, max_logs: int, pipe_run_type=None) -> list:
#         if pipe_run_type:
#             if pipe_run_type not in RUN_TYPES:
#                 raise ValueError(
#                     f"Error, `{pipe_run_type}` is not in LoggingDatabaseConnectionSingleton's list of supported run types."
#                 )
#             # Fetch logs for a specific type
#             key_to_fetch = f"{self.log_key}:{pipe_run_type}"
#             logs = self.redis.lrange(key_to_fetch, 0, max_logs - 1)
#             return [json.loads(log) for log in logs]
#         else:
#             # Fetch logs for all types
#             all_logs = []
#             for run_type in RUN_TYPES:
#                 key_to_fetch = f"{self.log_key}:{run_type}"
#                 logs = self.redis.lrange(key_to_fetch, 0, max_logs - 1)
#                 all_logs.extend([json.loads(log) for log in logs])
#             # Sort logs by timestamp if needed and slice to max_logs
#             all_logs.sort(key=lambda x: x["timestamp"], reverse=True)
#             return all_logs[:max_logs]
