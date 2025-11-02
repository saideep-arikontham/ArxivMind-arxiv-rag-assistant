from langchain_ollama import ChatOllama
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser


class OllamaModel:
    def __init__(self, model_name: str = "llama3.2", temperature: float = 0.7):
        self.llm = ChatOllama(model=model_name, temperature=temperature)

    def prompt_model(self, query: str) -> str:
        prompt = PromptTemplate(
            input_variables=["query"],
            template="{query}"
        )

        parser = StrOutputParser()
        chain = prompt | self.llm | parser

        response = chain.invoke({"query":query})
        return response