# from langchain_nvidia_ai_endpoints import ChatNVIDIA
# from langchain_core.prompts import PromptTemplate
# from langchain_core.output_parsers import StrOutputParser

# from dotenv import load_dotenv
# import os

# load_dotenv()  # Load environment variables from .env file

# class NvidiaNimModel:
#     def __init__(self, model_name: str = "moonshotai/kimi-k2-instruct-0905", temperature: float = 0.7):
#         self.llm = client = ChatNVIDIA(
#                                     model=model_name,
#                                     api_key=os.getenv("NVIDIA_NIM_API_KEY"), 
#                                     temperature=0.6,
#                                     top_p=0.9,
#                                     max_tokens=4096)

#     def prompt_model(self, query: str) -> str:
#         prompt = PromptTemplate(
#             input_variables=["query"],
#             template="{query}"
#         )

#         parser = StrOutputParser()
#         chain = prompt | self.llm | parser

#         response = chain.invoke({"query":query})
#         return response


from langchain_nvidia_ai_endpoints import ChatNVIDIA
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder # Updated import
from langchain_core.output_parsers import StrOutputParser
from langchain_core.chat_history import BaseChatMessageHistory # New import
from langchain_community.chat_message_histories import ChatMessageHistory # New import
from langchain_core.runnables.history import RunnableWithMessageHistory # New import

from dotenv import load_dotenv
import os

load_dotenv()  # Load environment variables from .env file

# 1. Create a global store to hold session histories
# This simple dictionary will map session IDs to their chat histories
store = {}

def get_session_history(session_id: str) -> BaseChatMessageHistory:
    """Factory function to get or create a chat history for a session."""
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]


class NvidiaNimModel:
    def __init__(self, model_name: str = "moonshotai/kimi-k2-instruct-0905", temperature: float = 0.7):
        self.llm = ChatNVIDIA(
            model=model_name,
            api_key=os.getenv("NVIDIA_NIM_API_KEY"),
            temperature=temperature, # Used the instance variable
            top_p=0.9,
            max_tokens=4096
        )

        # 2. Create a new prompt that includes a placeholder for history
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a helpful assistant. Answer the user's questions based on the conversation history."),
            MessagesPlaceholder(variable_name="history"),  # This is where old messages will be injected
            ("human", "{query}"),                          # This is the new user input
        ])
        
        parser = StrOutputParser()

        # 3. Define the core chain (without the history wrapper)
        core_chain = self.prompt | self.llm | parser

        # 4. Wrap the core chain with RunnableWithMessageHistory
        self.chain_with_history = RunnableWithMessageHistory(
            core_chain,
            get_session_history,  # Function to retrieve/create history
            input_messages_key="query",      # The key for the new user input
            history_messages_key="history",  # The key for the MessagesPlaceholder
        )

    async def prompt_model(self, query: str, session_id: str = "default_session") -> str:
        """
        Runs the model with conversation memory.
        
        Args:
            query: The user's new message.
            session_id: A unique identifier for the conversation.
        """
        # 5. Invoke the chain, passing the session_id in the 'config'
        # The wrapper will automatically load history for this session_id,
        # run the chain, and save the new query/response to the history.
        response = await self.chain_with_history.ainvoke(
            {"query": query},
            config={"configurable": {"session_id": session_id}}
        )
        return response
