import json
from typing import Type, Any

from langchain_experimental.utilities import PythonREPL
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from database import SQLiteDatabase
from data_store import DataStore


# Define tool to execute SQL queries
class ExecuteQueryInput(BaseModel):
    query: str = Field(description="An SQLite query to execute in the database.")
    commit: bool = Field(description="Whether to commit the transaction after executing the query.", default=True)
    name: str = Field(
        description="A valid python variable name to use as the key to store the results in the data store."
    )


class ExecuteQueryTool(BaseTool):
    name = "executeQuery"
    description = """
    Execute an SQLite query in the SQLite database and return the results. If the query is successful, the results will
    be stored in the data store with the provided name.
    """
    args_schema: Type[BaseModel] = ExecuteQueryInput
    database: SQLiteDatabase = None
    data_store: DataStore = None

    def __init__(self, database: SQLiteDatabase, data_store: DataStore):
        super().__init__()
        self.database = database
        self.data_store = data_store

    def _run(self, query: str, name: str, commit: bool = True) -> Any:

        if not name.isidentifier():
            return json.dumps({"success": False, "error": "The name provided is not a valid python variable name."})

        query_results = self.database.execute_query(query, commit)
        if query_results['success']:
            query_results['name'] = name
            self.data_store.set(name, query_results['rows'])

        return json.dumps(query_results)


class PythonREPLInput(BaseModel):
    code: str = Field(description="Python code to execute.")


class PythonREPLTool(BaseTool):
    name = "pythonREPL"
    description = """
    A Python shell. Use this to execute python commands. Input should be a valid python command. If you want to see the
    output of a value, you should print it out with `print(...)`.
    
    All data from the data store can be accessed in the code execution as global variables named according to the keys
    in the data store.
    
    Do not pass the code directly as a string, use the `code` field in the input.
    """
    args_schema: Type[BaseModel] = PythonREPLInput
    data_store: DataStore = None

    def __init__(self, data_store: DataStore):
        super().__init__()
        self.data_store = data_store

    def _run(self, code: str) -> str:
        repl = PythonREPL()
        repl.globals = self.data_store.data
        content = repl.run(code)

        if not content:
            return 'No output, check the code.'

        return content
