import os
import sqlite3
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


class SQLiteDatabase:

    def __init__(self, database_path: str, ddl_path: str, data_path: str):
        self.database_path = database_path
        self.ddl_path = ddl_path
        self.data_path = data_path

    def init(self):
        # Check if the database is an existing file
        if not os.path.exists(self.database_path):
            # Open a connection to a new database (this will create the file)
            connection = None
            try:
                connection = sqlite3.connect(self.database_path)
                cursor = connection.cursor()

                for script_path in [self.ddl_path, self.data_path]:
                    with open(script_path, 'r') as script_file:
                        cursor.executescript(script_file.read())

                # Commit changes and close the connection
                connection.commit()
            finally:
                connection.close()
            print("Database created and initialized from SQL script.")
        else:
            print("Database already exists.")

    def execute_query(self, query: str) -> QueryResult:
        connection = None

        try:
            connection = sqlite3.connect(self.database_path)
            cursor = connection.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()

            # Compute the rowcount. For select queries, the rowcount is -1, so we need to compute it manually.
            rowcount = cursor.rowcount if cursor.rowcount != -1 else len(rows)

            columns = [description[0] for description in cursor.description] if cursor.description is not None else None

            connection.commit()

            return {"success": True, "rows": rows, "rowcount": rowcount, "columns": columns}
        except sqlite3.Error as error:
            return {"success": False, "error": str(error)}
        finally:
            if connection:
                connection.close()
