# Prompt Para Criar Apresentacao De Slides Do IFESDOC

Use este prompt em uma ferramenta de criacao de apresentacoes, como Gamma, Canva, PowerPoint Copilot, Google Slides com IA ou ferramenta equivalente.

```text
Crie uma apresentacao de slides para uma banca avaliadora sobre o IFESDOC, um sistema web de indexacao, busca e gestao de documentos institucionais.

Contexto da apresentacao:
- Tempo total: 10 minutos exatos.
- Apresentadores: 3 pessoas.
- Publico: banca mista, com pessoas da area de software e tambem pessoas leigas.
- Linguagem: clara, institucional, objetiva e didatica.
- O slide deve ter pouco texto. Os detalhes devem ficar nas notas do apresentador.

Divisao obrigatoria:
1. Primeiro tempo - 2min30s:
   Contextualizar a teoria por tras de ingestao, indexacao e busca documental.
   Explicar de forma sucinta:
   - problema de documentos institucionais dispersos;
   - ingestao de documentos;
   - extracao de texto e metadados;
   - normalizacao, tokenizacao e indice;
   - consulta do usuario, ranking, snippets e visualizacao.

2. Segundo tempo - 5min00s:
   Ocupar a maior parte da apresentacao.
   Explicar o arcabouco tecnologico, tecnicas e caracteristicas unicas do IFESDOC.
   Incluir:
   - Backend FastAPI;
   - Frontend React + TypeScript + Vite;
   - PostgreSQL;
   - SQLAlchemy;
   - Docker Compose;
   - autenticacao JWT;
   - arquitetura em camadas: API, Services, Repositories, Domain, Strategies, Pipeline e Schemas;
   - QueryAnalyzer;
   - indice invertido;
   - TF-IDF;
   - BM25;
   - PostgreSQL Full-Text Search com tsvector, indice GIN, ts_rank_cd e ts_headline;
   - busca hibrida;
   - snippets e highlight;
   - versionamento de documentos com historico_documento;
   - OCR com Tesseract para PDFs escaneados;
   - metricas, historico, auditoria e feedback de relevancia;
   - bot conversacional como interface adicional.

3. Terceiro tempo - 2min30s:
   Demonstrar o sistema funcionando.
   Incluir uma sequencia visual:
   - login;
   - tela principal/menu;
   - ingestao de documento;
   - status de indexacao;
   - busca;
   - resultados com relevancia, snippet e highlight;
   - abertura de documento;
   - selecao de versao;
   - painel de OCR;
   - metricas ou comparador de estrategias.

Quantidade de slides:
Crie 8 slides, organizados assim:

Slide 1 - IFESDOC: objetivo do sistema
Conteudo:
- Sistema de indexacao e busca documental
- Centraliza, processa e recupera documentos
- Foco em rastreabilidade e eficiencia
Visual:
- Capa limpa com icones de documento, lupa e banco de dados
Notas:
- Explicar em 30 segundos o que e o IFESDOC.

Slide 2 - Problema e fundamento teorico
Conteudo:
- Muitos documentos, formatos e versoes
- Busca por nome de arquivo e limitada
- Recuperacao de informacao usa analise, indice e ranking
Visual:
- Comparacao simples: arquivos dispersos vs busca organizada
Notas:
- Explicar para leigos que o sistema busca pelo conteudo, nao apenas pelo nome.

Slide 3 - Pipeline: ingestao, indexacao e busca
Conteudo:
- Upload e validacao
- Extracao de texto/metadados
- Normalizacao, tokenizacao e indice
- Ranking, snippets e interface
Visual:
- Diagrama horizontal:
  Upload -> Extracao -> Processamento -> Indice -> Busca -> Resultados
Notas:
- Mostrar a teoria do processo de busca documental.

Slide 4 - Arquitetura do IFESDOC
Conteudo:
- Frontend React + TypeScript
- Backend FastAPI + SQLAlchemy
- PostgreSQL + Docker Compose
- Camadas separadas
Visual:
- Diagrama em camadas: UI/API/Services/Repositories/Domain/Banco
Notas:
- Destacar manutencao, testes e separacao de responsabilidades.

Slide 5 - Motor de busca e diferenciais tecnicos
Conteudo:
- QueryAnalyzer
- Indice invertido, TF-IDF e BM25
- PostgreSQL FTS com GIN
- Busca hibrida
- OCR para PDFs escaneados
Visual:
- Diagrama de sinais de relevancia combinados
Notas:
- Explicar termos tecnicos em linguagem simples.
- FTS: busca textual nativa do banco.
- OCR: transforma imagem em texto pesquisavel.

Slide 6 - Funcionalidades do produto
Conteudo:
- Ingestao individual e em lote
- Busca com filtros, snippets e highlight
- Versionamento de documentos
- Metricas, auditoria e feedback
- Bot conversacional
Visual:
- Grade com 5 blocos funcionais e icones
Notas:
- Mostrar valor para usuario comum e administrador.

Slide 7 - Demonstracao do sistema
Conteudo:
- Login
- Upload/indexacao
- Busca e resultados
- Documento, versoes e OCR
- Metricas/comparador
Visual:
- Sequencia numerada com miniaturas ou icones
Notas:
- Este slide deve servir como roteiro da demo.
- Se possivel, usar capturas reais do sistema.

Slide 8 - Fechamento
Conteudo:
- Busca documental mais eficiente
- Documentos rastreaveis e versionados
- Motor de busca robusto
- Sistema preparado para evolucao
Visual:
- Resumo em 4 cards
Notas:
- Fechar em 15 segundos e abrir para perguntas.

Requisitos visuais:
- Visual limpo, institucional e moderno.
- Usar cores associadas a tecnologia, educacao, confiabilidade e documentos.
- Evitar slides carregados de texto.
- Usar icones de documento, lupa, banco de dados, engrenagem, seguranca, grafico e servidor.
- Usar diagramas simples para os fluxos.
- Se houver capturas de tela do IFESDOC, priorizar capturas reais na parte da demonstracao.

Notas do apresentador:
Para cada slide, gere notas com fala sugerida. As notas devem seguir exatamente a divisao:
- Pessoa 1: slides 1 a 3, 2min30s.
- Pessoa 2: slides 4 a 6, 5min00s.
- Pessoa 3: slides 7 e 8, 2min30s.

Tom das notas:
- Linguagem natural, como fala oral.
- Explicar beneficios antes de termos tecnicos.
- Quando citar tecnologia, explicar rapidamente o papel dela.
- Nao usar frases longas demais.

Resultado esperado:
Uma apresentacao objetiva, com 8 slides, adequada para 10 minutos, com equilibrio entre teoria, engenharia do sistema e demonstracao pratica.
```

## Observacoes De Uso

- Depois que a ferramenta gerar os slides, revise o excesso de texto.
- A demo deve ser ensaiada com cronometro.
- Se a apresentacao tiver capturas reais, use-as principalmente no slide 7.
- Nao inclua detalhes de codigo nos slides; deixe isso para perguntas da banca.
- Use o roteiro em [roteiro_apresentacao_ifesdoc.md](roteiro_apresentacao_ifesdoc.md) como base para as falas.
