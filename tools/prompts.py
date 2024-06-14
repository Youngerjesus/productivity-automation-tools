from langchain.document_loaders import WebBaseLoader
from langchain.globals import set_llm_cache
from pydantic import BaseModel, Field
from typing import List
from langchain.chat_models import ChatOpenAI
from langchain_core.prompts import PromptTemplate, FewShotPromptTemplate
from langchain.agents.output_parsers import OpenAIFunctionsAgentOutputParser
from langchain_core.output_parsers import JsonOutputParser

class Statement(BaseModel):
    statements: List[str] = Field(description="글에서 말하고자 하는 목적을 나타내는 문장들 입니다.")

def create_statement_json_parser(): 
    return JsonOutputParser(pydantic_object=Statement)

def create_statement_prompt():
    statement_prompt = PromptTemplate(
        input_variables=["title", "document"],
        partial_variables={"format_instructions": create_statement_json_parser().get_format_instructions()},
        template="""
        너는 글에서 핵심 논지를 추출하는 일을 해야해.
        다음 Input 의 Document 은 크롤링 한 문서에 대한 내용이고, Title 은 문서에 대한 제목이야. 
        문서를 읽고 핵심 논지를 추천해서 알려줘. 

        Input:
        Title: {title}
        Document: {document}

        출력은 JSON 형식으로 해 주세요. JSON 구조는 다음과 같습니다:
        {format_instructions}

        Example:
        1. Document: Rewrite-Retrieve-Read: This approach focuses on the query input by the user (ie rewriting it), rather than just adapting retriever or the reader. It prompts an LLM to generate a query and then uses a web search engine to retrieve context. There is further alignment via a trainable scheme for the pipeline using a small language model. The summary is well captured in the graphic below:
        1. Statement: 이 기법은 사용자로부터 쿼리가 주어졌을 때 해당 쿼리를 재작성하고, 검색 엔진을 통해서 검색해보고, 문맥을 가져와서 답변을 작성하는 방법임. Vector Store 에 검색을 하는 방법은 아니긴 하나, 아이디어는 차용할 수 있다.

        2. Document: RAG Fusion: Combination of RAG and reciprocal rank fusion (RRF), by generating multiple queries (to add context from different perspectives), reranking them with reciprocal scores and then fusing the documents and scores. This leads to more comprehensive and accurate answers
        2. Statement: 사용자의 질문을 다양한 관점에서 다시 작성해서 여러 쿼리를 만들고 이를 이용해서 문서를 검색한다. 그리고 총 조회된 문서들을 reciprocal rank fusion (RRF) 에 따라서 스코어링을 해서 랭킹을 매긴다. 그러니까 1등 문서는 1/1 점, 2등 문서는 1/2 점, 3등 문서는 1/3 점 이런식으로 점수를 매겨서 총 랭킹을 매기는거임.

        3. Document: Step-Back Prompting: This is a more technical prompting technique whereby the LLM does abstractions to derive high level concepts and first principles. This is an iterative process where the user question is used to generate a step back question. The step back answer is then used for reasoning to generate the final answer.
        3. Statement: 주어진 질문을 한단계 추상화해서 그 질문으로 답변을 작성하는 방법임.
        """
    )

    return statement_prompt


class Summary(BaseModel): 
    summary: List[str] = Field(description="글을 읽고나서 핵심 내용들을 요약한 글들 입니다. 중요한 내용들을 놓치지 말고 정리해 주세요.")

def create_summary_json_parser(): 
    return JsonOutputParser(pydantic_object=Summary)

def create_summary_prompt():
    summary_prompt = PromptTemplate(
        input_variables=["document", "title", "statements"],
        partial_variables={"format_instructions": create_summary_json_parser().get_format_instructions()},
        template="""
        
        당신은 고급 언어 모델(LLM)로서 주어진 텍스트를 읽고, 그 텍스트의 핵심 내용을 추출하고, 추론하여 요약하는 역할을 맡고 있습니다. 
        주어진 문서의 내용, 제목, 그리고 핵심 논지들을 바탕으로 명확하고 간결한 요약을 작성해 주세요.:

        Input:
        문서 제목: {title}
        문서 내용: {document}
        핵심 논지: {statements}

        작업 지침:

        1.	문서의 주요 내용을 정확히 반영하여 요약합니다.
        2.	문서의 전체적인 맥락과 논지를 유지합니다.
        3.	불필요한 세부사항은 생략하고, 중요한 정보만 포함합니다.
        4.	요약은 최대 5-10 문장으로 작성합니다.

        출력은 JSON 형식으로 해 주세요. JSON 구조는 다음과 같습니다:
        {format_instructions}    
        """
    )

    return summary_prompt

class OneStatement(BaseModel):
    statement: str = Field(description="문서에서 주장한 내용을 나타내는 문장입니다.")

class Reason(BaseModel):
    reason: str = Field(description="글에서 주장한 내용에 대한 이유를 나타내는 문장입니다.")

class ReasonStatementPair(BaseModel):
    statement: OneStatement = Field(description="문서에서 주장한 내용을 나타내는 문장입니다.")
    reason: Reason = Field(description="글에서 주장한 내용에 대한 이유를 나타내는 문장입니다.")

class ReasonStatementPairList(BaseModel):
    reaseon_statement_pair_list: List[ReasonStatementPair] = Field(description="문서에서 주장한 내용과 그에 대한 이유를 나타내는 문장들입니다.")

def create_reason_json_parser(): 
    return JsonOutputParser(pydantic_object=ReasonStatementPairList)

def create_reason_prompt():
    reason_prompt = PromptTemplate(
        input_variables=["document", "title", "statements"],
        partial_variables={"format_instructions": create_reason_json_parser().get_format_instructions()},
        template="""
        
        당신은 고급 언어 모델(LLM)로서 문서의 핵심 논지들로 부터 왜 이렇게 주장하는지 이유를 추론하는 일을 해야합니다. 
        핵심 논지들은 여러개가 있으니 각 논지들마다 이유를 추론해야합니다. 
        
        Input:
        문서 제목: {title}
        문서 내용: {document}
        핵심 논지: {statements}

        작업 지침:

        출력은 JSON 형식으로 해 주세요. JSON 구조는 다음과 같습니다:
        {format_instructions}    
        """
    )

    return reason_prompt

def create_formatting_prompt():
    formatting_prompt = PromptTemplate(
        input_variables=["title", "summaries", "reason_statement_pair_list"],
        template="""
        
        당신은 고급 언어 모델(LLM)로서 주어진 정보를 바탕으로 글을 포맷팅하여 작성하는 역할을 맡고 있습니다. 주어진 제목, 요약, 핵심 논지들, 그리고 각각의 논지에 대한 이유를 바탕으로 체계적이고 명확하게 Markdown 형식으로 글을 작성해 주세요. 다음과 같은 정보를 제공합니다:

        Input:
        1.	글의 제목:  {title}
        2.	추론한 요약: {summaries}
        3.	핵심 논지들 및 이유들: {reason_statement_pair_list}

        작업 지침:
        1.	제공된 제목, 요약, 논지, 이유를 기반으로 체계적으로 글을 작성합니다.
        2.	글의 서론에서는 요약을 포함하여 전체적인 내용을 소개합니다.
        3.	본론에서는 각 핵심 논지를 제시하고, 각각의 논지를 뒷받침하는 이유를 설명합니다.
        4.	결론에서는 요약과 논지들을 다시 강조하며 글을 마무리합니다.
        5.	글은 논리적이고 일관되게 작성하며, 각 문단은 명확한 주제를 포함합니다.
        6.	최종 출력 형식은 Markdown입니다.

        예시: 
        {{
            "글의 제목": “AI의 발전과 윤리적 문제”,
            "추론한 요약": "인공지능은 빠르게 발전하며 의료, 금융, 교육 등 다양한 분야에서 혁신을 주도하고 있다. 그러나 이러한 발전에는 여러 윤리적 문제들이 따르며, 이를 해결하기 위한 연구와 노력이 필요하다", 
            "핵심 논지들 및 이유들:": [
                {{
                    "핵심 논지": "AI의 발전은 편향성을 초래할 수 있다", 
                    "이유": “AI 시스템이 학습하는 데이터가 편향되어 있을 경우, 그 결과도 편향될 수 있다. 이는 특정 그룹에 불이익을 줄 수 있다.”, 
                }},
                {{
                    "핵심 논지": "AI는 개인 프라이버시 침해의 위험이 있다", 
                    "이유": "AI가 수집하고 처리하는 방대한 데이터에는 개인의 민감한 정보가 포함될 수 있으며, 이에 대한 적절한 보호가 필요하다.”, 
                }},
                {{
                    "핵심 논지": "AI의 결정 과정은 투명성을 요구한다", 
                    "이유": "AI의 자동화된 결정은 이해하기 어려울 수 있으며, 이는 책임 소재를 명확히 하기 위해 투명한 프로세스가 필요하다”, 
                }}
            ]
        }}

        작성된 글 (Markdown 형식):
        # AI의 발전과 윤리적 문제

        ## 핵심 논지와 이유

        ### 핵심 논지 1
        AI의 발전은 편향성을 초래할 수 있다.

        #### 이유
        AI 시스템이 학습하는 데이터가 편향되어 있을 경우, 그 결과도 편향될 수 있다. 이는 특정 그룹에 불이익을 줄 수 있다.

        ### 핵심 논지 2
        AI는 개인 프라이버시 침해의 위험이 있다.

        #### 이유
        AI가 수집하고 처리하는 방대한 데이터에는 개인의 민감한 정보가 포함될 수 있으며, 이에 대한 적절한 보호가 필요하다.

        ### 핵심 논지 3
        AI의 결정 과정은 투명성을 요구한다.

        #### 이유
        AI의 자동화된 결정은 이해하기 어려울 수 있으며, 이는 책임 소재를 명확히 하기 위해 투명한 프로세스가 필요하다.

        ## 요약 정보

        인공지능(AI)은 빠르게 발전하며 의료, 금융, 교육 등 다양한 분야에서 혁신을 주도하고 있습니다. 이러한 기술 발전은 우리의 생활 방식을 급격히 변화시키고 있으며, 많은 긍정적인 영향을 미치고 있습니다. 그러나, 이러한 발전의 이면에는 중요한 윤리적 문제가 존재합니다.

        첫째로, AI의 발전은 편향성을 초래할 수 있습니다. AI 시스템이 학습하는 데이터가 편향되어 있을 경우, 그 결과도 편향될 수 있습니다. 이는 특정 그룹에 불이익을 줄 수 있습니다. 둘째로, AI는 개인 프라이버시 침해의 위험이 있습니다. AI가 수집하고 처리하는 방대한 데이터에는 개인의 민감한 정보가 포함될 수 있으며, 이에 대한 적절한 보호가 필요합니다. 셋째로, AI의 결정 과정은 투명성을 요구합니다. AI의 자동화된 결정은 이해하기 어려울 수 있으며, 이는 책임 소재를 명확히 하기 위해 투명한 프로세스가 필요합니다.

        이러한 문제를 해결하기 위해서는 기술적 진보뿐만 아니라 윤리적 기준 마련이 필수적입니다. 연구자들과 정책 입안자들은 AI 기술이 윤리적 원칙을 준수하며 발전할 수 있도록 긴밀히 협력해야 합니다. 구체적인 가이드라인과 규제는 AI 시스템이 신뢰성을 유지하며, 공정하게 사용될 수 있도록 돕습니다.

        결론적으로, AI의 발전은 우리의 삶에 많은 혜택을 가져오지만, 그에 따른 윤리적 문제도 간과해서는 안 됩니다. 이를 해결하기 위해서는 지속적인 연구와 노력이 필요하며, 사회 전반에 걸쳐 윤리적 기준을 마련하는 것이 중요합니다. 
        """
    )

    return formatting_prompt