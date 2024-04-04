import openai
import json
import os

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

        execution_context = {'html': ''}

        # When generating HTML from python script, we can ask the model to retry up to 3 times in case of an error by
        # providing the exception message as a response.
        remaining_attempts = 10

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
                                    },
                                    "commit": {
                                        "type": "boolean",
                                        "description": "Whether to commit the transaction after executing the query.",
                                        "default": True
                                    },
                                    "name": {
                                        "type": "string",
                                        "description": "A valid python variable name to store the query results."
                                    }
                                },
                                "required": ["query", "name"]
                            }
                        }
                    }
                ],
                messages=messages
            )

            choice = response.choices[0]

            print(response.usage)

            # Is the response a function call?
            if choice.finish_reason == "tool_calls":
                for tool_call in choice.message.tool_calls:
                    if tool_call.function.name == "executeQuery":
                        params = json.loads(tool_call.function.arguments)
                        query = params["query"]
                        commit = params.get("commit", True)
                        print('Executing query:', query, 'commit:', commit)
                        query_results = self.database.execute_query(query, commit)

                        if query_results['success']:
                            name = params["name"]
                            query_results['name'] = name
                            execution_context[name] = query_results['rows']

                        print('Query results:', query_results)

                        messages.append({"role": "system", "content": json.dumps(query_results)})
            else:
                # Assume the response is an HTML message
                lines = choice.message.content.splitlines()

                if len(lines) > 1:
                    print('GPT is doing it again! It returned multiple lines.')

                print('Response:', lines[0])

                message = json.loads(lines[0])

                if "html" in message:
                    print('Response:', message["html"])
                    return message["html"]
                if "python" in message:

                    # Try to execute the python code and get the HTML content.
                    # If an exception occurs, send it as a response and retry.
                    try:
                        print('Executing python code:')
                        exec(message["python"], execution_context)
                        return execution_context['html']
                    except Exception as e:
                        print('Error executing python code:', e)
                        remaining_attempts -= 1
                        if remaining_attempts == 0:
                            raise e
                        else:
                            content = "An error occurred while executing the python code, please fix it and try again: " + str(e)
                            messages.append({"role": "system", "content": content})
                else:
                    raise Exception(f"Unknown response: {response}")
