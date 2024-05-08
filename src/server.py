from functools import partial
from http.server import HTTPServer, SimpleHTTPRequestHandler

from langchain_openai import ChatOpenAI

import config
from assistant import Assistant
from database import SQLiteDatabase
from data_store import DataStore
from agents import DatabaseQueryAgent, HTMLGeneratorAgent
from tools import PythonREPLTool, ExecuteQueryTool


class AppHTTPRequestHandler(SimpleHTTPRequestHandler):

    def __init__(self, assistant_: Assistant, *args, **kwargs):
        self.assistant = assistant_
        super().__init__(*args, directory='../public', **kwargs)

    def do_POST(self):
        if self.path == '/query':
            self.handle_query()
        else:
            self.send_error(404, "Not found.")

    def handle_query(self):
        # Your custom handler for POST /query
        # Example: Reading post data (you might want to handle parsing differently)
        content_length = int(self.headers['Content-Length'])
        query = self.rfile.read(content_length).decode('utf-8')  # Decode the bytes to a string

        content = self.assistant.generate(str(query))

        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(content.encode('utf-8'))


if __name__ == '__main__':
    port = 8000
    server_address = ('', port)
    database_path = "../database/db.sqlite"
    ddl_path = "../database/ddl.sql"
    data_path = "../database/data.sql"
    openai_api_key = config.OPENAI_API_KEY
    openai_model = config.OPENAI_MODEL
    database = SQLiteDatabase(database_path, ddl_path, data_path)
    data_store = DataStore()
    python_repl_tool = PythonREPLTool(data_store)
    execute_query_tool = ExecuteQueryTool(database, data_store)
    model = ChatOpenAI(model=openai_model, api_key=openai_api_key)
    database_query_agent = DatabaseQueryAgent(model, execute_query_tool)
    html_generator_agent = HTMLGeneratorAgent(model, python_repl_tool)
    assistant = Assistant(python_repl_tool, execute_query_tool, database_query_agent, html_generator_agent)
    handler = partial(AppHTTPRequestHandler, assistant)
    httpd = HTTPServer(server_address, handler)

    print("Initializing database...")
    database.init()

    print(f"Serving HTTP on port {port}...")

    httpd.serve_forever()
