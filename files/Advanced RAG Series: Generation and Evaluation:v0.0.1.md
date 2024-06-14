# Advanced RAG Series: Generation and Evaluation

## 요약 정보

Advanced RAG 파이프라인의 최종 단계는 Generation과 Evaluation으로, 이는 Query Translation, Routing, Query construction, Indexing, Retrieval을 최적화한 후의 결과를 평가하고 생성하는 단계입니다. CRAG (Corrective RAG)은 'Retrieval Evaluator'를 사용하여 각 문서의 신뢰도를 평가하고, 이를 기반으로 적절한 행동을 결정하여 최종 출력을 생성합니다. Self-RAG은 고정된 수의 패시지를 검색하는 대신, 필요에 따라 검색하고 스스로 반성하는 과정을 통해 LLM의 품질과 사실성을 향상시키는 프레임워크입니다. RRR (Rewrite-Retrieve-Read) 모델은 LLM의 성능을 강화 학습 인센티브로 활용하여 쿼리를 재작성하고, 이를 통해 검색 쿼리를 최적화하여 다운스트림 작업 성능을 향상시킵니다. RAG 파이프라인의 평가 단계는 Q&A 쌍을 테스트 데이터셋으로 사용하여 출력과 실제 답변을 비교하는 방식으로 수행됩니다. RAGAs는 RAG 파이프라인을 평가하기 위한 오픈 소스 프레임워크로, 'ground truth'를 기반으로 테스트 데이터를 생성하고, 검색 및 생성 단계의 성능을 평가하는 다양한 메트릭을 제공합니다. Langsmith는 RAGAs 평가 프레임워크에 통합하여 결과를 더 깊이 분석하고, 평가를 통해 검색기나 생성기를 최적화할 수 있는 도구입니다. DeepEval은 RAG 및 파인 튜닝을 포함한 14개 이상의 메트릭을 제공하는 평가 프레임워크로, 메트릭 점수의 설명 가능성을 높여 디버깅을 용이하게 합니다.

## 핵심 논지와 이유

### 핵심 논지 1
RAG 파이프라인의 최종 단계는 Generation과 Evaluation으로, 이는 Query Translation, Routing, Query construction, Indexing, Retrieval을 최적화한 후의 결과를 평가하고 생성하는 단계임.

#### 이유
RAG 파이프라인의 각 단계는 데이터의 정확성과 관련성을 보장하기 위해 최적화되며, 최종 단계인 Generation과 Evaluation은 이러한 최적화의 결과를 실제로 평가하고 사용자에게 제공할 최종 출력을 생성하는 중요한 단계이기 때문입니다.

### 핵심 논지 2
CRAG는 'Retrieval Evaluator'를 사용하여 각 문서에 대한 신뢰 점수를 반환하고, 이 점수에 따라 적절한 행동을 결정함. 신뢰 점수가 낮으면 새로운 지식 소스를 도입하고, 높으면 지식을 정제하여 최종 출력을 생성함.

#### 이유
CRAG는 검색된 문서의 신뢰성을 평가하여 적절한 조치를 취함으로써 최종 출력의 품질을 높이기 위해 설계되었습니다. 이는 잘못된 정보가 포함되지 않도록 하고, 정확한 정보를 기반으로 최종 출력을 생성하기 위함입니다.

### 핵심 논지 3
Self-RAG는 고정된 수의 패시지를 검색하는 대신, 필요에 따라 검색하고 자체 반성을 통해 LLM의 품질과 사실성을 개선하는 프레임워크임.

#### 이유
Self-RAG는 필요에 따라 검색을 수행하고, LLM이 자체적으로 생성한 결과를 반성하여 평가함으로써, 더 정확하고 관련성 높은 출력을 생성할 수 있도록 설계되었습니다. 이는 고정된 검색 방식의 한계를 극복하고, 동적인 검색과 평가를 통해 LLM의 성능을 향상시키기 위함입니다.

### 핵심 논지 4
RRR 모델은 쿼리를 재작성하여 검색 쿼리를 최적화하고, 이를 통해 LLM의 성능을 강화하는 프레임워크임. 이 과정에서 작은 LLM을 재작성 모듈로 추가하여 성능을 향상시킴.

#### 이유
RRR 모델은 사용자의 쿼리를 더 정확하게 재작성함으로써 검색의 효율성을 높이고, 이를 통해 LLM의 전반적인 성능을 향상시키기 위해 설계되었습니다. 작은 LLM을 재작성 모듈로 추가함으로써, 이 과정에서 발생할 수 있는 오류를 줄이고, 더 나은 결과를 도출할 수 있습니다.

### 핵심 논지 5
RAG 파이프라인의 평가 단계는 Q&A 쌍을 테스트 데이터셋으로 사용하여 출력과 실제 답변을 비교하는 것부터 시작함. RAGAs는 RAG 파이프라인을 평가하기 위한 오픈 소스 프레임워크로, 다양한 평가 지표를 제공함.

#### 이유
평가 단계는 생성된 출력의 정확성과 관련성을 검증하기 위해 필수적입니다. RAGAs는 다양한 평가 지표를 제공하여 RAG 파이프라인의 성능을 다각도로 평가할 수 있게 함으로써, 최종 출력의 품질을 보장하기 위해 사용됩니다.

### 핵심 논지 6
Langsmith는 RAGAs 평가 프레임워크에 통합하여 결과를 더 깊이 분석하고 최적화할 수 있는 도구임.

#### 이유
Langsmith는 RAGAs 평가 프레임워크와 통합되어, 평가 결과를 더 깊이 분석하고, 특정 단계에서의 문제점을 파악하여 최적화할 수 있는 기능을 제공합니다. 이는 RAG 파이프라인의 전반적인 성능을 향상시키기 위해 중요합니다.

### 핵심 논지 7
DeepEval은 RAG와 미세 조정을 포함한 14개 이상의 평가 지표를 제공하는 평가 프레임워크로, Pytest 통합 및 모듈형 구성 요소를 포함한 다양한 기능을 제공함.

#### 이유
DeepEval은 다양한 평가 지표를 통해 RAG 파이프라인의 성능을 다각도로 평가할 수 있으며, Pytest 통합 및 모듈형 구성 요소를 통해 개발자 친화적인 환경을 제공합니다. 이는 RAG 파이프라인의 성능을 지속적으로 개선하고 유지하는 데 중요한 역할을 합니다.

## 결론

Advanced RAG Series의 Generation과 Evaluation은 RAG 파이프라인의 핵심적인 단계로, 최적화된 결과물을 평가하고 생성하는 과정을 담당합니다. 각각의 모델과 프레임워크는 데이터의 정확성과 품질을 보장하기 위해 설계되었으며, 다양한 평가 지표를 통해 성능을 평가하고 최적화할 수 있는 기능을 제공합니다. 이러한 과정을 통해 Advanced RAG Series는 더 나은 결과물을 생성하고 사용자에게 더욱 효과적인 정보를 제공할 수 있게 됩니다.