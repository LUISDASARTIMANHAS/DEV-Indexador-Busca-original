# Relatório Técnico — Evolução do Motor de Busca do IFESDOC

## 1. Objetivo

Esta evolução final torna o motor de busca do IFESDOC mais robusto, persistente e comparável. A busca deixa de depender apenas de um índice invertido próprio e passa a oferecer também PostgreSQL Full-Text Search, ranking nativo, snippets com destaque e uma estratégia híbrida combinando PostgreSQL FTS com BM25.

## 2. Situação anterior

Antes desta evolução, o IFESDOC já possuía:

- normalização e tokenização;
- `QueryAnalyzer`;
- índice invertido próprio;
- ranking por frequência, TF-IDF e BM25;
- busca semântica/híbrida quando embeddings estão disponíveis;
- snippets/highlight gerados pelo serviço de busca;
- histórico e métricas de consultas.

As limitações principais eram:

- ausência de índice textual persistente nativo do banco;
- ausência de ranking nativo com `ts_rank`/`ts_rank_cd`;
- ausência de snippet nativo com `ts_headline`;
- comparação visual limitada entre mecanismos.

## 3. PostgreSQL Full-Text Search

O PostgreSQL Full-Text Search usa uma estrutura `tsvector` para representar texto de forma indexável. No IFESDOC, o vetor foi colocado em `historico_documento.search_vector`, porque o texto extraído fica em `historico_documento.texto_extraido` e o sistema controla versões ativas do documento nessa tabela.

Componentes usados:

- `to_tsvector`: transforma título, texto extraído e nome do arquivo em vetor textual.
- `websearch_to_tsquery`: interpreta consultas em formato próximo ao usado por buscadores.
- `ts_rank_cd`: calcula relevância nativa.
- `ts_headline`: gera snippets com `<mark>`.
- índice `GIN`: acelera consultas sobre `search_vector`.

A configuração preferencial é `portuguese`. Foi criado fallback para `simple` por meio da função:

```sql
ifesdoc_search_config()
```

Ela usa:

```sql
COALESCE(to_regconfig('pg_catalog.portuguese'), 'pg_catalog.simple'::regconfig)
```

## 4. Ajuste de schema

Script incremental:

```text
docker/postgres/init/03_full_text_search.sql
```

Principais alterações:

```sql
ALTER TABLE historico_documento
ADD COLUMN IF NOT EXISTS search_vector tsvector;

CREATE INDEX IF NOT EXISTS idx_historico_documento_search_vector
ON historico_documento
USING GIN(search_vector);
```

Também foram criados triggers para:

- atualizar `search_vector` quando o texto extraído ou arquivo da versão mudar;
- recalcular vetores quando `documento.titulo` for alterado;
- popular documentos existentes.

Além do script Docker, o backend executa uma garantia de schema no startup quando o dialeto é PostgreSQL:

```text
backend/app/core/schema.py
```

## 5. Nova arquitetura de busca

Fluxo atualizado:

```text
Consulta do usuário
→ QueryAnalyzer
→ Estratégia selecionada
  → PostgreSQL FTS
  → BM25
  → Frequência
  → TF-IDF
  → Semântica
  → Híbrida PostgreSQL
→ Ranking
→ Snippet/highlight
→ Histórico/métricas
→ API
→ Frontend
```

Novos modos:

```text
postgres_fts
hybrid_postgres
```

O modo padrão recomendado é `postgres_fts`.

## 6. Busca híbrida com PostgreSQL

A estratégia híbrida combina PostgreSQL FTS com BM25.

Fórmula:

```text
score_final =
  (postgres_weight * postgres_score_normalizado) +
  (secondary_weight * secondary_score_normalizado)
```

Pesos padrão:

```text
postgres_weight = 0.7
secondary_weight = 0.3
```

Normalização:

```text
score_normalizado = score / maior_score_da_lista
```

Vantagem: combina a persistência e velocidade do PostgreSQL FTS com sinais estatísticos do BM25.

## 7. Comparador de estratégias

Endpoint:

```http
GET /api/v1/search/compare
```

Exemplo:

```http
GET /api/v1/search/compare?q=estagio supervisionado&limit=5
```

Estratégias comparadas por padrão:

- `frequency`;
- `bm25`;
- `postgres_fts`;
- `hybrid_postgres`.

O endpoint retorna `results_by_mode`, notas explicativas e o modo com maior score no topo.

## 8. Comparativo técnico

| Estratégia | Base técnica | Persistente? | Usa índice? | Gera snippet? | Pontos fortes | Limitações |
|-----------|--------------|--------------|-------------|---------------|---------------|------------|
| Frequência | Contagem de termos | Depende da implementação | Índice invertido próprio | Parcial | Simples e rápida | Pouco precisa |
| TF-IDF | Frequência + raridade | Depende | Índice/estatísticas | Parcial | Valoriza termos específicos | Não considera tamanho tão bem quanto BM25 |
| BM25 | Frequência + raridade + tamanho | Depende | Índice/estatísticas | Parcial | Ranking textual robusto | Requer estatísticas |
| PostgreSQL FTS | `tsvector` + GIN + `ts_rank_cd` | Sim | GIN | Sim, com `ts_headline` | Persistente, rápido e integrado ao banco | Ainda é lexical |
| Híbrida PostgreSQL | FTS + BM25 | Sim/parcial | Sim | Sim | Combina sinais de relevância | Mais complexa |

## 9. Impacto no frontend

O frontend foi atualizado para:

- usar PostgreSQL FTS como modo padrão;
- permitir seleção de modo de busca;
- incluir `PostgreSQL FTS` e `Híbrida PostgreSQL`;
- exibir score PostgreSQL, score secundário e score final;
- exibir explicação do ranking por resultado;
- renderizar snippets com `<mark>` de forma controlada;
- adicionar tela `/comparar-busca` para comparação visual.

## 10. Como testar

Busca PostgreSQL FTS:

```http
GET /api/v1/search?q=estagio supervisionado&mode=postgres_fts
```

Busca híbrida:

```http
GET /api/v1/search?q=relatorios de 2025 pdf&mode=hybrid_postgres
```

Comparador:

```http
GET /api/v1/search/compare?q=estagio supervisionado
```

Script SQL para bancos novos:

```text
docker/postgres/init/03_full_text_search.sql
```

Para banco já existente, reiniciar o backend também executa a garantia de schema PostgreSQL no startup.

## 11. Limitações

- PostgreSQL FTS é lexical, não semântico.
- A qualidade depende do texto extraído dos documentos.
- PDFs escaneados ainda dependem de OCR futuro.
- Termos ambíguos podem exigir sinônimos ou expansão de consulta.
- A configuração `portuguese` pode variar por ambiente; há fallback para `simple`.
- A estratégia híbrida depende da qualidade do BM25 e dos termos extraídos.
- Testes automatizados usam fallback SQLite para validar contrato sem depender de PostgreSQL em todos os ambientes.

## 12. Próximos passos

- OCR para PDFs escaneados.
- `pgvector` para busca semântica persistente.
- Calibração de pesos híbridos com métricas reais.
- Uso de feedback de relevância.
- Expansão por sinônimos.
- Ranking personalizado por perfil de usuário.
- Dashboard de avaliação dos mecanismos.

## 13. Critérios de aceite atendidos

- suporte a PostgreSQL Full-Text Search;
- coluna `tsvector` em `historico_documento`;
- índice GIN;
- ranking com `ts_rank_cd`;
- snippet/highlight com `ts_headline`;
- integração com `QueryAnalyzer`;
- endpoint `/api/v1/search` com `mode=postgres_fts`;
- endpoint `/api/v1/search/compare`;
- busca híbrida `hybrid_postgres`;
- frontend com seletor de modo;
- tela de comparação `/comparar-busca`;
- resultados com score e snippet;
- testes backend relevantes;
- mocks frontend atualizados;
- relatório Markdown criado.
