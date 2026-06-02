# Relatório Técnico — Query Analyzer do IFESDOC

## 1. Objetivo

Este relatório documenta a criação do componente `QueryAnalyzer`, responsável por tornar explícita a etapa **Parser de query + Análise** prevista no pipeline de busca do IFESDOC.

O objetivo técnico é preparar a consulta textual do usuário antes da recuperação no índice invertido, deixando claro que o sistema executa validação, normalização, tokenização, identificação de termos relevantes, filtros implícitos e interpretação básica de operadores.

## 2. Situação anterior

Antes desta alteração, o fluxo principal de busca já possuía normalização, tokenização, consulta ao índice invertido e ranking por estratégias como frequência, TF-IDF, BM25, semântica e híbrida.

O fluxo prático era semelhante a:

```text
Consulta do usuário
→ normalização/tokenização via preprocess_for_indexing
→ recuperação no índice invertido
→ ranking
→ snippets/highlight
→ UI/API
```

Apesar de funcional, a análise da consulta estava embutida no `SearchService`, sem um componente próprio que representasse claramente a etapa de parser e análise exigida no documento do professor.

## 3. Nova arquitetura da análise de consulta

O novo fluxo do backend principal passa a ser:

```text
Consulta do usuário
→ QueryAnalyzer
  → validação
  → normalização
  → tokenização
  → remoção de stopwords
  → identificação de termos relevantes
  → detecção de filtros implícitos
  → detecção de frases e operadores simples
  → classificação simples do tipo da consulta
→ recuperação no índice invertido
→ aplicação de filtros
→ ranking
→ snippets/highlight
→ UI/API
```

O componente foi implementado em:

```text
backend/app/services/query_analyzer_service.py
```

Os DTOs Pydantic foram criados em:

```text
backend/app/schemas/query_schema.py
```

Também foi adicionada uma etapa explícita no pipeline separado de busca:

```text
backend/pipeline_busca/src/stages/queryAnalyzeStage.py
```

## 4. Funções implementadas

O `QueryAnalyzer` implementa:

- validação de consulta vazia, consulta muito curta, caracteres inválidos e limite máximo de tamanho;
- normalização para minúsculas, sem acentos, sem pontuação desnecessária e com espaços padronizados;
- tokenização da consulta normalizada;
- remoção de stopwords em português;
- geração de termos relevantes para recuperação;
- detecção de tipos de arquivo como `pdf`, `txt`, `csv`, `doc`, `docx`, `xls` e `xlsx`;
- detecção de anos no formato `20xx`;
- detecção inicial de intervalos por ano, como `entre 2024 e 2025`;
- detecção de categoria quando a consulta usa expressão explícita, como `categoria estagio`;
- detecção de frases exatas entre aspas;
- detecção de termos excluídos com `-termo`;
- detecção básica de operadores `AND`, `OR`, `NOT` e `+`;
- classificação auxiliar do tipo de operação de busca.

## 5. Diferença entre Query Analyzer e detector de intenção

No IFESDOC, o `QueryAnalyzer` não substitui um chatbot. Ele atua como uma etapa técnica do pipeline de busca, preparando a consulta para recuperação documental.

A classificação de intenção operacional foi adicionada apenas como apoio para identificar se a entrada se parece com busca simples, busca com filtros, relatório, histórico, abertura de documento ou reindexação.

Valores usados:

```text
search_documents
search_with_filters
open_document
generate_report
view_history
reindex_document
unknown
```

Essa intenção é auxiliar. A busca textual continua funcionando mesmo quando a intenção é `unknown`.

## 6. Exemplos práticos

Consulta:

```text
relatórios de estágio 2025 PDF
```

Resultado esperado:

```text
terms = ["relatorios", "estagio"]
filters.year = 2025
filters.type = "pdf"
intent = "search_with_filters"
```

Consulta:

```text
"projeto pedagógico" -rascunho
```

Resultado esperado:

```text
phrases = ["projeto pedagogico"]
excluded_terms = ["rascunho"]
```

Consulta:

```text
gerar relatório das buscas sem resultado
```

Resultado esperado:

```text
intent = "generate_report"
```

## 7. Integração com a API e interface

Foi criado o endpoint de depuração:

```http
POST /api/v1/search/analyze
```

Entrada:

```json
{
  "query": "relatórios de estágio 2025 PDF"
}
```

Saída resumida:

```json
{
  "raw_query": "relatórios de estágio 2025 PDF",
  "normalized_query": "relatorios de estagio 2025 pdf",
  "tokens": ["relatorios", "de", "estagio", "2025", "pdf"],
  "terms": ["relatorios", "estagio"],
  "filters": {
    "year": 2025,
    "type": "pdf"
  },
  "intent": "search_with_filters",
  "is_valid": true,
  "warnings": []
}
```

O endpoint de busca também pode retornar um resumo da análise:

```http
GET /api/v1/search?q=relatórios%20de%20estágio%202025%20PDF&debug_analysis=true
```

Quando `debug_analysis=true`, a resposta inclui:

```json
{
  "analysis": {
    "terms": ["relatorios", "estagio"],
    "filters": {
      "year": 2025,
      "type": "pdf"
    },
    "intent": "search_with_filters"
  }
}
```

A interface web foi atualizada para solicitar a análise na tela de resultados e exibir termos, filtros, frases, termos excluídos, avisos e tipo da consulta.

## 8. Impacto no sistema

A busca fica:

- mais rastreável;
- mais explicável;
- mais próxima do pipeline exigido no documento;
- preparada para filtros implícitos;
- preparada para evolução do ranking com TF-IDF, BM25, busca híbrida e busca semântica;
- mais adequada para demonstração técnica, pois a etapa de análise pode ser consultada via API.

## 9. Limitações

As limitações atuais são:

- operadores complexos ainda são apenas detectados, não possuem parser booleano completo;
- a detecção de datas é inicial e focada em anos;
- categorias só são aplicadas como filtro quando aparecem de forma explícita, para evitar falsos positivos;
- autores são detectados de forma heurística;
- a classificação de tipo de consulta é baseada em regras simples;
- o componente não é chatbot, não usa IA generativa e não executa NLP avançado.

## 10. Próximos passos

Evoluções recomendadas:

- integrar um parser booleano completo para `AND`, `OR`, `NOT` e agrupamentos;
- melhorar extração de datas, meses e intervalos;
- usar a lista real de categorias do banco de dados;
- adicionar dicionário de sinônimos;
- usar feedback de relevância para expansão de consulta;
- melhorar integração com BM25/TF-IDF;
- avaliar busca semântica para consultas longas ou ambíguas.

## 11. Critérios de aceite atendidos

- existe um componente explícito `QueryAnalyzer`;
- ele valida, normaliza e tokeniza consultas;
- ele remove stopwords;
- ele extrai termos relevantes;
- ele detecta ano e tipo de arquivo como filtros implícitos;
- ele detecta frases entre aspas;
- ele detecta termos excluídos com `-termo`;
- ele classifica o tipo da consulta de forma simples;
- há testes unitários;
- existe endpoint `/api/v1/search/analyze`;
- a busca usa o resultado do `QueryAnalyzer`;
- existe documentação Markdown do componente;
- login e autenticação JWT não foram alterados.
