from functools import partial
from http.server import HTTPServer, SimpleHTTPRequestHandler
import config
from assistant import Assistant
from database import SQLiteDatabase


class AppHTTPRequestHandler(SimpleHTTPRequestHandler):

    def __init__(self, assistant_: Assistant, *args, **kwargs):
        self.assistant = assistant_
        super().__init__(*args, directory='public', **kwargs)

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
    database_path = "database/db.sqlite"
    ddl_path = "database/ddl.sql"
    data_path = "database/data.sql"
    openai_api_key = config.OPENAI_API_KEY
    openai_model = config.OPENAI_MODEL
    database = SQLiteDatabase(database_path, ddl_path, data_path)
    assistant = Assistant(openai_api_key, openai_model, ddl_path, database)
    handler = partial(AppHTTPRequestHandler, assistant)
    httpd = HTTPServer(server_address, handler)

    print("Initializing database...")
    database.init()

    print(f"Serving HTTP on port {port}...")

    httpd.serve_forever()
