from langchain_core.language_models import BaseLanguageModel
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import BaseTool

from tools import ExecuteQueryTool, PythonREPLTool

import operator
from typing import TypedDict, Annotated, Sequence, Literal


class AgentState(TypedDict):
    messages: Annotated[list, operator.add]
    html: str | Literal[False]
    database_query_completed: bool


class Agent:
    def __init__(self, system_prompt: str, model: BaseLanguageModel, tools: Sequence[BaseTool]):
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="messages"),
        ])
        self.runnable = prompt | model.bind_tools(tools)

    def __call__(self, state: AgentState):
        raise NotImplementedError


class DatabaseQueryAgent(Agent):
    TOKEN = "DATABASE QUERY COMPLETED"

    def __init__(self, model: BaseLanguageModel, tool: ExecuteQueryTool):
        system_prompt = """
        You manage an SQLite database. You can execute queries in the database to retrieve information or perform
        operations as requested by the user. You can use the `{tool_name}` tool to execute an SQLite query in the
        database and retrieve the results.
        Eventually, all data that you have will be used to generate a response in HTML for the user, but this will be
        handled by another assistant.
        
        Complex request can be executed by combining multiple queries. You can also use the results of previous queries
        to generate new queries. Also complex queries that involve DML operations must be executed in a single 
        transaction, ending with a commit. To retrieve the id of the last inserted row, you should use the 
        `last_insert_rowid()` function.
        
        When you consider that you have retrieved all information needed to generate the response, or executed
        all the necessary operations, you notify that you are done with a last simple message that must only contains 
        "{token}". Another AI agent will take over to generate the HTML view. 
        
        You should keep in mind the following constraints:
        
        * It is critical that you only use data from the database to generate the HTML view. Do not hardcode or fake
          any data.
        * If the user is asking for data that does not exist in the database, you should return a message indicating
          that the data is not available.
        * Do not expect that the data from the user input will match exactly the data in the database: if a query with
          an exact match does not return any results, you should try a more flexible approach, for example using the
          LIKE operator.
        * If the user request is not related to the database data, you do not need to interact with the database. You
          can emit the "{token}" message directly.
        
        Here is the SQLite schema that you should use to initialize the database:
        
        ```sql
        {ddl_script}
        ```
        """.format(
            tool_name=tool.name,
            ddl_script=tool.database.ddl(),
            token=self.TOKEN
        )

        super().__init__(system_prompt, model, [tool])

    def __call__(self, state: AgentState):
        database_query_completed = False
        response = self.runnable.invoke(state['messages'])

        if self.TOKEN in response.content:
            database_query_completed = True

        return {"messages": [response], "database_query_completed": database_query_completed}


class HTMLGeneratorAgent(Agent):

    TOKEN = "HTML GENERATION COMPLETED"

    def __init__(self, model: BaseLanguageModel, tool: PythonREPLTool):
        system_prompt = """
        You are a member of a multi agent system that generates dynamic HTML views to answer user requests.
        
        Your role in this architecture is to use the `{tool_name}` tool to generate the HTML content for the response
        to the user's request. Another agent has already retrieved the necessary data from the database.
        
        You can see the data retrieved from the database in the message history, however you must not rewrite this data
        in the Python code. The tool will provide you with global variables that already contains this data. The global
        variables will be named according to the names provided when executing the queries.
        
        The HTML code will be inserted into an existing web page, so you should not include the <html>, <body> or
        <head> tags.
        
        You must use semantic-ui in your HTML content. The CSS classes and JS code are already included in the web page 
        where the HTML content will be inserted. You must always use a semantic ui container appropriate for the
        content. E.g. for text content, you should use a "ui text container" container.
        
        When you consider that you have generated the HTML content to format the response for the user, you must
        generate a last simple message that only contains "{token}". This message must directly follow the output of
        Python interpreter that contains the HTML content.
        
        You should keep in mind the following constraints:
        - on top of the Python standard library, you can also use matplotlib for charts and jinja2 for templating
        - you must make sure that the Python script is valid, if the script fails to execute, the tool will return an
          error message and you will have to fix the issue before resubmitting your code
        - pay attention to the structure of the data that you use, the data is the result of a SQL query, so it is a
          list of tuples, you can iterate over this list to generate the HTML content
        - pay attention to the date format as they are returned in the SQL query results, you can use the `datetime`
          module to parse the date and format it as needed
        """.format(
            tool_name=tool.name,
            token=self.TOKEN
        )
        super().__init__(system_prompt, model, [tool])

    def __call__(self, state: AgentState):
        html = False
        messages = state['messages']
        response = self.runnable.invoke(messages)

        if self.TOKEN in response.content:
            last_message = messages[-1]
            html = last_message.content

        return {"messages": [response], "html": html}
