# Relatório de Melhorias no Mecanismo de Busca do IFESDOC

## 1. Situação anterior

O IFESDOC já possuía uma busca textual baseada em normalização, tokenização,
índice invertido relacional e ranking por relevância textual. O backend principal
usa FastAPI, SQLAlchemy e PostgreSQL, com tabelas como `documento`, `termo`,
`indice_invertido`, `historico_busca`, `historico_indexacao` e
`feedback_relevancia`.

Os pipelines independentes em `backend/pipeline_indexador` e
`backend/pipeline_busca` funcionavam como protótipos em memória/arquivo. O
pipeline de indexação processava texto, tokenizava e montava índice invertido. O
pipeline de busca normalizava consulta, tokenizava, consultava o índice e
ordenava por frequência simples.

Não havia tabela para embeddings antes desta evolução. A busca textual no banco
já era suportada por `termo`, `campo_documento` e `indice_invertido`. O frontend
já possuía serviços e páginas para busca, resultados, indexação, métricas e
histórico, com suporte a mocks.

## 2. Mecanismos implementados

### 2.1 Frequência simples

A estratégia `FrequencyRankingStrategy` conta quantas vezes os termos da
consulta aparecem em cada documento. Documentos com mais ocorrências recebem
maior `score`.

Vantagens:

- simples de entender e depurar;
- rápida para bases pequenas;
- útil como baseline de comparação.

Limitações:

- não diferencia termos comuns de termos raros;
- favorece documentos longos;
- não entende significado, apenas correspondência lexical.

Exemplo: para a consulta `plano institucional`, um documento que contém `plano`
várias vezes tende a subir, mesmo que outro documento menor seja mais preciso.

### 2.2 TF-IDF

A estratégia `TFIDFRankingStrategy` combina frequência do termo no documento
com raridade do termo na coleção. A pontuação usa IDF suavizado:

```text
tfidf(t, d) = tf(t, d) * (log((N + 1) / (df(t) + 1)) + 1)
```

Diferença para frequência simples:

- frequência simples só conta ocorrências;
- TF-IDF aumenta o peso de termos mais específicos e reduz o peso de termos
  comuns.

Quando melhora os resultados:

- consultas com termos institucionais específicos;
- bases com muitos documentos semelhantes;
- cenários em que palavras muito frequentes aparecem em quase todos os textos.

Limitações:

- continua dependendo de termos iguais ou prefixos indexados;
- não considera semântica;
- pode ser menos estável em coleções muito pequenas.

### 2.3 BM25

A estratégia `BM25RankingStrategy` usa frequência, raridade e tamanho do
documento. Ela evita que documentos longos sejam beneficiados apenas por terem
mais palavras.

Parâmetros usados:

- `k1 = 1.5`;
- `b = 0.75`.

Papel dos componentes:

- frequência: mede presença do termo no documento;
- raridade: aumenta peso de termos pouco comuns;
- tamanho do documento: normaliza pontuação por extensão do texto;
- tamanho médio: compara cada documento com a coleção.

Por que costuma ser melhor para busca textual:

- controla saturação de frequência;
- reduz viés para documentos longos;
- é um padrão forte para motores de busca lexical.

Limitações:

- ainda depende de termos;
- não encontra sinônimos se eles não estiverem indexados;
- precisa de estatísticas de coleção atualizadas.

### 2.4 Busca semântica

A busca semântica representa consulta e documentos como vetores de embedding. A
similaridade de cosseno mede a proximidade entre o vetor da consulta e o vetor de
cada documento.

Diferença para busca textual:

- busca textual procura palavras iguais ou prefixos;
- busca semântica procura proximidade de significado.

Exemplo prático:

Consulta: `documentos sobre permanência estudantil`

A busca textual pode encontrar documentos com exatamente `permanência
estudantil`. A busca semântica pode recuperar também documentos sobre:

- assistência ao estudante;
- auxílio estudantil;
- política de apoio discente;
- evasão e permanência.

Implementação atual:

- foi criada a abstração `EmbeddingAdapter`;
- foi implementado `MockEmbeddingAdapter`, baseado em hashing determinístico;
- existe `SentenceTransformerEmbeddingAdapter` preparado para uso futuro com
  `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`;
- a tabela `documento_embedding` armazena embeddings em `JSONB`.

Vantagens:

- prepara o sistema para busca por significado;
- desacopla o backend do modelo de embedding;
- permite troca futura para sentence-transformers ou outro provedor.

Limitações:

- o embedding ativo é mockado, não um modelo semântico real;
- a qualidade semântica depende de substituir o adapter por um modelo treinado;
- `JSONB` é compatível, mas menos eficiente que `pgvector` para grandes bases.

### 2.5 Busca híbrida

A estratégia `HybridRankingStrategy` combina score textual e score semântico:

```text
score_final = peso_textual * score_textual_normalizado
            + peso_semantico * score_semantico_normalizado
```

Pesos padrão:

- textual: `0.6`;
- semântico: `0.4`.

Quando usar mais peso textual:

- consultas por número de portaria, edital, resolução ou nome exato;
- cenários em que correspondência literal é essencial.

Quando usar mais peso semântico:

- consultas conceituais;
- busca exploratória;
- termos com sinônimos ou variações de vocabulário.

## 3. Comparativo entre mecanismos

| Mecanismo | Base de funcionamento | Pontos fortes | Limitações | Melhor cenário de uso |
|----------|----------------------|---------------|------------|------------------------|
| Frequência simples | Contagem de termos | Simples e rápida | Pouco precisa | Bases pequenas |
| TF-IDF | Frequência + raridade | Valoriza termos específicos | Não considera semântica | Busca textual tradicional |
| BM25 | Frequência, raridade e tamanho do documento | Ranking textual mais robusto | Ainda depende de termos | Motores de busca textual |
| Semântica | Similaridade entre embeddings | Entende sentido aproximado | Custo maior e depende do modelo | Consultas conceituais |
| Híbrida | Combinação textual + semântica | Equilibra precisão e significado | Mais complexa | Busca institucional avançada |

## 4. Busca normal x busca semântica

A busca normal/textual depende de correspondência entre os termos da consulta e
os termos indexados. Ela funciona bem para nomes oficiais, códigos, siglas,
títulos, tipos de documento e expressões literais.

A busca semântica depende da proximidade entre vetores. Ela pode encontrar
documentos relevantes mesmo quando as palavras não são exatamente iguais, desde
que o modelo de embedding represente bem o domínio.

## 5. Impacto arquitetural

Foram adicionados:

- Strategy Pattern em `backend/app/strategies`;
- estratégias `frequency`, `tfidf`, `bm25`, `semantic` e `hybrid`;
- adapter de embeddings em `backend/app/adapters/embedding_adapter.py`;
- serviço semântico em `backend/app/services/semantic_search_service.py`;
- repositório e domínio para `documento_embedding`;
- endpoint `GET /api/v1/search` com seleção de `mode`;
- endpoint `POST /api/v1/search/reindex` para reconstruir embeddings;
- suporte no frontend para modos e novos campos de score;
- estatísticas no pipeline em memória para TF-IDF/BM25.

## 6. Limitações atuais

- A busca semântica usa `MockEmbeddingAdapter`; não há dependência obrigatória de
  modelo externo.
- O banco usa `JSONB` para embeddings. `pgvector` é recomendado para escala e
  consultas vetoriais nativas.
- A busca semântica calcula similaridade em aplicação, adequada para evolução
  inicial, mas não ideal para coleções grandes.
- A integração textual com PostgreSQL está ativa; os pipelines independentes
  continuam como protótipos e foram mantidos compatíveis.
- A qualidade semântica real depende de habilitar um modelo multilíngue leve ou
  outro provedor de embeddings.

## 7. Próximos passos

- Integrar completamente os pipelines independentes à API principal.
- Migrar a busca vetorial para `pgvector`, se disponível.
- Substituir `MockEmbeddingAdapter` por sentence-transformers ou serviço externo.
- Calibrar pesos da busca híbrida com dados reais.
- Usar `feedback_relevancia` para ajustar ranking.
- Monitorar métricas de tempo de resposta por modo de busca.
- Criar avaliação offline com consultas reais e julgamentos de relevância.
