from langchain_core.messages import AIMessage, HumanMessage
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode

from agents import AgentState
from agents import DatabaseQueryAgent, HTMLGeneratorAgent
from tools import PythonREPLTool, ExecuteQueryTool


class Assistant:

    def __init__(
            self,
            python_repl_tool: PythonREPLTool,
            execute_query_tool: ExecuteQueryTool,
            database_query_agent: DatabaseQueryAgent,
            html_generator_agent: HTMLGeneratorAgent
    ):
        tools = [python_repl_tool, execute_query_tool]

        # Define the state machine
        database_query = "database_query"
        html_generation = "html_generation"
        call_tool = "call_tool"

        def router(state: AgentState):

            # Print the last message
            last_message = state['messages'][-1]
            print(last_message)

            # Check if the last message is a tool call message, if so we must call the tool
            if isinstance(last_message, AIMessage) and last_message.tool_calls:
                return call_tool

            # Check if the HTML generation is completed
            if state['html'] is not False:
                return END

            # Check if the database query is completed
            if state['database_query_completed']:
                return html_generation

            # Otherwise, we are in the database query phase
            return database_query

        graph = StateGraph(AgentState)
        graph.add_node(call_tool, ToolNode(tools))
        graph.add_node(database_query, database_query_agent)
        graph.add_node(html_generation, html_generator_agent)
        graph.add_conditional_edges(database_query, router)
        graph.add_conditional_edges(html_generation, router)
        graph.add_conditional_edges(call_tool, router)
        graph.set_entry_point(database_query)
        self.runnable = graph.compile()

    def generate(self, request: str) -> str:
        state = self.runnable.invoke({
            "messages": [HumanMessage(content=request)],
            "html": False,
            "database_query_completed": False
        })
        return state['html']
