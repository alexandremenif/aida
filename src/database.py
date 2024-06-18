import os
import sqlite3
import threading
import time
from typing import TypedDict, Literal


class SuccessQueryResult(TypedDict):
    success: Literal[True]
    rows: list
    rowcount: int
    columns: list[str] | None


class ErrorQueryResult(TypedDict):
    success: Literal[False]
    error: str


QueryResult = SuccessQueryResult | ErrorQueryResult


class ConnectionPool:
    """
    A connection pool that manage connection according to the executing thread.
    The pool manages up to max_connections connections.
    A given thread can only have one connection at a time.
    When the pool is full, it will close all connection that has not been used since max_idle_time.
    """

    def __init__(self, database_path: str, max_connections: int, max_idle_time: int):
        self.database_path = database_path
        self.max_connections = max_connections
        self.max_idle_time = max_idle_time
        self.connections = {}

    def __del__(self):
        """
        Close all connections when the pool is deleted.
        """
        for connection in self.connections:
            connection.close()

    def _close_idle_connections(self):
        """
        Close all connections that have not been used since max_idle_time.
        """
        for thread_id, connection in self.connections.items():
            if connection.last_used + self.max_idle_time < time.time():
                connection.close()
                del self.connections[thread_id]

    def get_connection(self):
        """
        Get a connection for the current thread.
        """

        # Identify the current thread
        thread_id = threading.get_ident()

        # If the thread already has a connection, return it
        if thread_id in self.connections:
            return self.connections[thread_id]

        # If the pool is full, close all connections that have not been used since max_idle_time
        if len(self.connections) >= self.max_connections:
            self._close_idle_connections()

        # Open a new connection
        connection = sqlite3.connect(self.database_path)
        self.connections[thread_id] = connection

        return connection


class SQLiteDatabase:

    def __init__(self, connection_pool: ConnectionPool, database_path: str, ddl_path: str, data_path: str):
        self.connection_pool = connection_pool
        self.database_path = database_path
        self.ddl_path = ddl_path
        self.data_path = data_path

    def __del__(self):
        self.connection_pool.__del__()

    def init(self):
        # Check if the database is an existing file
        if not os.path.exists(self.database_path):
            # Open a connection to a new database (this will create the file)
            connection = self.connection_pool.get_connection()
            with connection.cursor() as cursor:
                # Execute the DDL and DML scripts
                for script_path in [self.ddl_path, self.data_path]:
                    with open(script_path, 'r') as script_file:
                        cursor.executescript(script_file.read())

                # Commit changes and close the connection
                connection.commit()
                print("Database created and initialized from SQL script.")
        else:
            print("Database already exists.")

    def execute_query(self, query: str, commit: bool) -> QueryResult:
        connection = self.connection_pool.get_connection()

        cursor = None

        try:
            cursor = connection.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()

            # Compute the rowcount. For select queries, the rowcount is -1, so we need to compute it manually.
            row_count = cursor.rowcount if cursor.rowcount != -1 else len(rows)

            columns = [description[0] for description in cursor.description] if cursor.description is not None else None

            if commit:
                connection.commit()

            return {"success": True, "rows": rows, "rowCount": row_count, "columns": columns}
        except sqlite3.Error as error:
            connection.rollback()
            return {"success": False, "error": str(error)}
        finally:
            if cursor is not None:
                cursor.close()

    # Return the content of the DDL script
    def ddl(self):
        with open(self.ddl_path, 'r') as ddl_file:
            return ddl_file.read()
