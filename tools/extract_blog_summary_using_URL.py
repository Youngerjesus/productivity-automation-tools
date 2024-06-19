from langchain.document_loaders import WebBaseLoader
from langchain.globals import set_llm_cache
from pydantic import BaseModel, Field
from typing import List
from langchain.chat_models import ChatOpenAI
from langchain_core.prompts import PromptTemplate, FewShotPromptTemplate
from langchain.agents.output_parsers import OpenAIFunctionsAgentOutputParser
from langchain_core.output_parsers import JsonOutputParser
from operator import itemgetter
from langchain_core.output_parsers import StrOutputParser
import json 
from prompts import * 
from utils import * 


set_llm_cache(None)  # This will disable the caching globally

def extract_page_content(URL):
    loader = WebBaseLoader(URL)
    documents = loader.load()
    doc = documents[0]
    return doc.page_content

# This will load the blog post from the URL
URL = "https://div.beehiiv.com/p/advanced-rag-series-retrieval"

# This is title of the blog post
title = "Advanced RAG Series: Retrieval"

document = extract_page_content(URL)

statement_llm = ChatOpenAI(
    temperature=0.1, 
    max_tokens=2048, 
    model="gpt-4o-2024-05-13"
)

summarry_llm = ChatOpenAI(
    temperature=0.1, 
    max_tokens=2048,
    model="gpt-4o-2024-05-13"
)

reason_llm = ChatOpenAI(
    temperature=0.1, 
    max_tokens=2048,
    model="gpt-4o-2024-05-13"
)

formatting_llm = ChatOpenAI(
    temperature=0.1, 
    max_tokens=4096,
)

metadata = { 
    "model": {
        "statement": statement_llm.model_name, 
        "summary": summarry_llm.model_name,
        "reason": reason_llm.model_name,
        "formatting": formatting_llm.model_name
    }
}


statement_prompt = create_statement_prompt()

summary_prompt = create_summary_prompt()

reason_prompt = create_reason_prompt()

formatting_prompt = create_formatting_prompt()

statement_chain = {
    "title": itemgetter("title"), 
    "document": itemgetter("document")
} | statement_prompt | statement_llm | create_statement_json_parser()   

summary_chain = {
    "title": itemgetter("title"), 
    "document": itemgetter("document"), 
    "statements": statement_chain
} | summary_prompt | summarry_llm | create_summary_json_parser()

reason_chain = {
    "title": itemgetter("title"),
    "document": itemgetter("document"), 
    "statements": statement_chain
} | reason_prompt | reason_llm | create_reason_json_parser()

final_chain = {
    "title": itemgetter("title"), 
    "summaries": summary_chain,
    "reason_statement_pair_list": reason_chain
} | formatting_prompt | formatting_llm | StrOutputParser()


final_result = final_chain.invoke({
    "title": title, 
    "document": document
})


markdown_content = final_result

file_version = get_file_version(title)

if file_version:
    file_version = increment_version(file_version)
else: 
    file_version = default_version

file_path = f"{directory_path}{title}:{file_version}.md"
metadata_file_path = f"{directory_path}{title}:metadata:{file_version}.json"

with open(file_path, "w") as file:
    file.write(markdown_content)

with open(metadata_file_path, "w") as file:
    file.write(json.dumps(metadata))

print("Markdown file saved successfully.")