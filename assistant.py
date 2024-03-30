import openai
import json

from database import SQLiteDatabase


class Assistant:

    def __init__(self, openai_api_key: str, openai_model: str, ddl_path: str, database: SQLiteDatabase):
        self.client = openai.OpenAI(api_key=openai_api_key)
        self.model = openai_model
        self.database = database

        prompt_path = "prompt.md"

        with (open(ddl_path, 'r') as ddl_file):
            ddl_script = ddl_file.read()

        with (open(prompt_path, 'r') as prompt_file):
            self.system_prompt = prompt_file.read()
            self.system_prompt = self.system_prompt.replace('REPLACE_SQLITE_SCHEMA_HERE', ddl_script)

    def generate(self, content: str) -> str:

        print('Generating response for:', content)

        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": content}
        ]

        while True:
            response = self.client.chat.completions.create(
                model=self.model,
                response_format={"type": "json_object"},
                tools=[
                    {
                        "type": "function",
                        "function": {
                            "name": "executeQuery",
                            "description": "Execute an SQLite query in the events SQLite database and return the results",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "query": {
                                        "type": "string",
                                        "description": "An SQLite query to execute in the database."
                                    }
                                },
                                "required": ["query"]
                            }
                        }
                    }
                ],
                messages=messages
            )

            choice = response.choices[0]

            # Is the response a function call?
            if choice.finish_reason == "tool_calls":
                for tool_call in choice.message.tool_calls:
                    if tool_call.function.name == "executeQuery":
                        query = json.loads(tool_call.function.arguments)["query"]
                        print('Executing query:', query)
                        query_results = self.database.execute_query(query)
                        messages.append({"role": "system", "content": json.dumps(query_results)})
            else:
                # Assume the response is an HTML message
                lines = choice.message.content.splitlines()

                if len(lines) > 1:
                    print('GPT is doing it again! It returned multiple lines.')

                message = json.loads(lines[0])

                if "html" in message:
                    print('Response:', message["html"])
                    return message["html"]
                else:
                    raise Exception(f"Unknown response: {response}")
