from utils import get_session_id, logger
from dotenv import load_dotenv
import os
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langchain_core.messages import SystemMessage, trim_messages
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import START, MessagesState, StateGraph
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from typing import Sequence
from langgraph.graph.message import add_messages
from typing_extensions import Annotated, TypedDict


# Load environment variables from the .env file
load_dotenv()

def initialize_model():
    """Initialize the Groq model with proper error handling."""
    groq_api_key = os.getenv("GROQ_API_KEY")
    if groq_api_key is None:
        logger.error("GROQ_API_KEY not found in environment variables")
        raise ValueError("GROQ_API_KEY not found in environment variables")
    
    os.environ["GROQ_API_KEY"] = groq_api_key
    return ChatGroq(
        model="llama3-8b-8192",
        temperature=0.7,  # Add some variability to responses
        max_tokens=2048   # Increase max tokens for longer responses
    )

# Initialize the model
model = initialize_model()

# Define the chat prompt template with more context
prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a helpful assistant that provides clear and concise answers. "
            "Respond to all questions to the best of your ability in {language}. "
            "If you're unsure about something, be honest about it."
        ),
        MessagesPlaceholder(variable_name="messages"),
    ]
)

# Define the trimmer for messages with adjusted parameters
trimmer = trim_messages(
    max_tokens=768,  # Increased from 512 for more context
    strategy="last",
    token_counter=model,
    include_system=True,
    allow_partial=False,
    start_on="human",
)

# Define the state schema
class State(TypedDict):
    messages: Annotated[Sequence[BaseMessage], add_messages]
    language: str

# Create the workflow
workflow = StateGraph(state_schema=State)

# Define the model invocation function with error handling
def call_model(state: State):
    try:
        chain = prompt | model
        trimmed_messages = trimmer.invoke(state["messages"])
        response = chain.invoke(
            {"messages": trimmed_messages, "language": state["language"]}
        )
        return {"messages": [response]}
    except Exception as e:
        logger.error(f"Error in model call: {str(e)}")
        error_message = AIMessage(content="I apologize, but I encountered an error. Please try again.")
        return {"messages": [error_message]}

# Add nodes and edges to the workflow
workflow.add_edge(START, "model")
workflow.add_node("model", call_model)
memory = MemorySaver()
app = workflow.compile(checkpointer=memory)

def generate_response(query: str, language: str = "English", thread_id: str = None) -> str:
    """
    Handles a user query and returns the model's response, with enhanced error handling.
    
    Args:
        query (str): The user's input query.
        language (str, optional): Language in which the assistant should respond. Default is "English".
        thread_id (str, optional): Unique identifier for the conversation thread.

    Returns:
        str: The assistant's response or an error message if an exception occurs.
    """
    try:
        # Validate inputs
        if not query or not query.strip():
            return "I cannot process an empty query. Please provide some input."
        if not thread_id:
            thread_id = get_session_id()

        # Log the incoming request
        logger.info(f"Processing query in {language}. Thread ID: {thread_id}")
        
        # Configuring the thread_id for session continuity
        config = {"configurable": {"thread_id": thread_id}}
        input_messages = [HumanMessage(content=query.strip())]
        # Invoke the workflow with the provided input
        output = app.invoke(
            {"messages": input_messages, "language": language},
            config,
        )
        response = output["messages"][-1].content
        logger.info("Successfully generated response")
        return response
    
    except ValueError as ve:
        logger.error(f"Value error: {str(ve)}")
        return f"I couldn't process your request: {str(ve)}"
    
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return "I apologize, but I encountered an unexpected error. Please try again or contact support if the issue persists."
