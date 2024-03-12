import functools
import os
import types
from abc import ABC, abstractmethod
from typing import Optional
import json


class LoggingProvider(ABC):
    @abstractmethod
    def connect(self):
        pass

    @abstractmethod
    def close(self):
        pass

    @abstractmethod
    def log(self, timestamp, pipeline_run_id, pipeline_run_type, method, result, log_level):
        pass

    @abstractmethod
    def get_logs(self) -> list:
        pass


class PostgresLoggingProvider(LoggingProvider):
    def __init__(self, log_table_name="logs"):
        self.conn = None
        self.log_table_name = log_table_name
        self.db_module = self._import_db_module()

    def _import_db_module(self):
        try:
            import psycopg2
            return psycopg2
        except ImportError:
            raise ValueError(
                "Error, `psycopg2` is not installed. Please install it using `pip install psycopg2`."
            )

    def connect(self):
        if not all(
            [
                os.getenv("POSTGRES_DBNAME"),
                os.getenv("POSTGRES_USER"),
                os.getenv("POSTGRES_PASSWORD"),
                os.getenv("POSTGRES_HOST"),
                os.getenv("POSTGRES_PORT"),
            ]
        ):
            raise ValueError(
                "Please set the environment variables POSTGRES_DBNAME, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_HOST, and POSTGRES_PORT to run `LoggingDatabaseConnection` with `postgres`."
            )
        self.conn = self.db_module.connect(
            dbname=os.getenv("POSTGRES_DBNAME"),
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD"),
            host=os.getenv("POSTGRES_HOST"),
            port=os.getenv("POSTGRES_PORT"),
        )
        with self.conn.cursor() as cur:
            cur.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {self.log_table_name} (
                    timestamp TIMESTAMP,
                    pipeline_run_id UUID,
                    pipeline_run_type TEXT,
                    method TEXT,
                    result TEXT,
                    log_level TEXT
                )
            """
            )
        self.conn.commit()

    def close(self):
        if self.conn:
            self.conn.close()

    def log(self, timestamp, pipeline_run_id, pipeline_run_type, method, result, log_level):
        with self.conn.cursor() as cur:
            cur.execute(
                f"INSERT INTO {self.log_table_name} (timestamp, pipeline_run_id, pipeline_run_type, method, result, log_level) VALUES (NOW(), %s, %s, %s, %s, %s)",
                (
                    str(pipeline_run_id),
                    pipeline_run_type,
                    method,
                    str(result),
                    log_level,
                ),
            )
        self.conn.commit()

    def get_logs(self) -> list:
        logs = []
        with self.db_module.connect(
            dbname=os.getenv("POSTGRES_DBNAME"),
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD"),
            host=os.getenv("POSTGRES_HOST"),
            port=os.getenv("POSTGRES_PORT"),
        ) as conn:
            with conn.cursor() as cur:
                cur.execute(f"SELECT * FROM {self.log_table_name}")
                colnames = [desc[0] for desc in cur.description]
                logs = [dict(zip(colnames, row)) for row in cur.fetchall()]
        return logs


class LocalLoggingProvider(LoggingProvider):
    def __init__(self, log_table_name="logs", local_db_path: Optional[str] = None):
        self.conn = None
        self.log_table_name = log_table_name
        self.local_db_path = local_db_path
        self.db_module = self._import_db_module()

    def _import_db_module(self):
        import sqlite3
        return sqlite3

    def connect(self):
        self.conn = self.db_module.connect(self.local_db_path or os.getenv("LOCAL_DB_PATH"))
        self.conn.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {self.log_table_name} (
                timestamp DATETIME,
                pipeline_run_id TEXT,
                pipeline_run_type TEXT,
                method TEXT,
                result TEXT,
                log_level TEXT
            )
            """
        )
        self.conn.commit()

    def close(self):
        if self.conn:
            self.conn.close()

    def log(self, timestamp, pipeline_run_id, pipeline_run_type, method, result, log_level):
        self.conn.execute(
            f"INSERT INTO {self.log_table_name} (timestamp, pipeline_run_id, pipeline_run_type, method, result, log_level) VALUES (datetime('now'), ?, ?, ?, ?, ?)",
            (
                str(pipeline_run_id),
                pipeline_run_type,
                method,
                str(result),
                log_level,
            ),
        )
        self.conn.commit()

    def get_logs(self) -> list:
        logs = []
        with self.db_module.connect(self.local_db_path or os.getenv("LOCAL_DB_PATH")) as conn:
            cur = conn.execute(f"SELECT * FROM {self.log_table_name}")
            colnames = [desc[0] for desc in cur.description]
            logs = [dict(zip(colnames, row)) for row in cur.fetchall()]
        return logs


class RedisLoggingProvider(LoggingProvider):
    def __init__(self, decode_responses: bool = True):
        if not all(
            [
                os.getenv("REDIS_CLUSTER_IP"),
                os.getenv("REDIS_CLUSTER_PORT"),
                os.getenv("REDIS_LOG_KEY"),
            ]
        ):
            raise ValueError(
                "Please set the environment variables REDIS_CLUSTER_IP and REDIS_CLUSTER_PORT to run `LoggingDatabaseConnection` with `redis`."
            )
        try:
            from redis import Redis
        except ImportError:
            raise ValueError(
                "Error, `redis` is not installed. Please install it using `pip install redis`."
            )

        cluster_ip = os.getenv("REDIS_CLUSTER_IP")
        port = os.getenv("REDIS_CLUSTER_PORT")
        log_key = os.getenv("REDIS_LOG_KEY")
        self.redis = Redis(cluster_ip, port, decode_responses=decode_responses)
        self.log_key = log_key

    def connect(self):
        pass

    def close(self):
        pass

    def log(self, timestamp, pipeline_run_id, pipeline_run_type, method, result, log_level):
        log_entry = {
            "timestamp": timestamp,
            "pipeline_run_id": str(pipeline_run_id),
            "pipeline_run_type": pipeline_run_type,
            "method": method,
            "result": str(result),
            "log_level": log_level,
        }
        self.redis.lpush(self.log_key, json.dumps(log_entry))

    def get_logs(self) -> list:
        logs = self.redis.lrange(self.log_key, 0, -1)
        return [json.loads(log) for log in logs]


class LoggingDatabaseConnection:
    """
    A class to connect to a database and log the execution of methods to it.
    """

    supported_providers = {
        "postgres": PostgresLoggingProvider,
        "local": LocalLoggingProvider,
        "redis": RedisLoggingProvider,
    }

    def __init__(
        self,
        provider="postgres",
        log_table_name="logs",
        local_db_path: Optional[str] = None,
        cluster_ip: Optional[str] = None,
        port: Optional[int] = None,
    ):
        if provider not in self.supported_providers:
            raise ValueError(
                f"Error, `{provider}` is not in LoggingDatabaseConnection's list of supported providers."
            )

        self.provider = provider
        if provider == "redis":
            self.logging_provider = self.supported_providers[provider](cluster_ip, port, log_table_name)
        else:
            self.logging_provider = self.supported_providers[provider](log_table_name, local_db_path)

    def __enter__(self):
        self.logging_provider.connect()
        return self.logging_provider

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.logging_provider.close()

    def get_logs(self) -> list:
        return self.logging_provider.get_logs()


def log_execution_to_db(func):
    """A decorator to log the execution of a method to the database."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        instance = args[0]
        inst_provider = instance.logging_provider
        if not inst_provider:
            return func(*args, **kwargs)

        arg_pipeline_run_id = instance.pipeline_run_info["run_id"]
        arg_pipeline_run_type = instance.pipeline_run_info["type"]

        try:
            result = func(*args, **kwargs)
            if isinstance(result, types.GeneratorType):
                def generator_wrapper():
                    log_level = "INFO"
                    results = []
                    try:
                        for res in result:
                            results.append(res)
                            yield res
                    except Exception as e:
                        results.append(str(e))
                        log_level = "ERROR"
                    finally:
                        inst_provider.log(
                            None,
                            arg_pipeline_run_id,
                            arg_pipeline_run_type,
                            func.__name__,
                            "".join(results),
                            log_level,
                        )

                return generator_wrapper()
            else:
                inst_provider.log(
                    None,
                    arg_pipeline_run_id,
                    arg_pipeline_run_type,
                    func.__name__,
                    str(result),
                    "INFO",
                )
                return result

        except Exception as e:
            result = str(e)
            log_level = "ERROR"
            inst_provider.log(
                None,
                arg_pipeline_run_id,
                arg_pipeline_run_type,
                func.__name__,
                result,
                log_level,
            )
            raise Exception(result)

    return wrapper