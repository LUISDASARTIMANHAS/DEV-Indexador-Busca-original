# Roteiro Da Apresentacao Do IFESDOC

Este roteiro foi pensado para uma apresentacao objetiva, clara e completa sobre o IFESDOC. Ele pode ser usado junto com os slides gerados a partir do prompt em [prompt_apresentacao_ifesdoc.md](prompt_apresentacao_ifesdoc.md).

## Slide 1 - Capa

Apresentar o IFESDOC como um sistema de indexacao e busca de documentos.

Fala sugerida:

> Esta apresentacao mostra o IFESDOC, um sistema desenvolvido para indexacao e busca de documentos institucionais. A proposta e facilitar o armazenamento, a organizacao, a recuperacao e o acompanhamento de documentos dentro de uma instituicao.

Pontos principais:

- Nome do sistema: IFESDOC.
- Finalidade: indexacao e busca documental.
- Contexto: organizacao e recuperacao de documentos institucionais.

## Slide 2 - Problema

Explicar o problema que motivou o desenvolvimento do sistema.

Fala sugerida:

> Em ambientes institucionais, e comum existir um grande volume de documentos em diferentes formatos, categorias e versoes. Sem uma ferramenta adequada, encontrar o documento correto pode ser demorado, principalmente quando o usuario nao sabe o nome exato do arquivo ou quando existem documentos semelhantes.

Pontos principais:

- Grande volume de documentos.
- Dificuldade de localizacao.
- Falta de padronizacao.
- Existencia de diferentes versoes.
- Necessidade de rastreabilidade.

## Slide 3 - Solucao Proposta

Apresentar o IFESDOC como resposta ao problema.

Fala sugerida:

> O IFESDOC resolve esse problema criando uma plataforma centralizada. O sistema permite cadastrar documentos, extrair o conteudo textual, indexar as informacoes e disponibilizar uma busca mais inteligente, organizada e rastreavel.

Pontos principais:

- Centralizacao dos documentos.
- Indexacao do conteudo textual.
- Busca com filtros e ranking.
- Visualizacao rapida dos resultados.
- Monitoramento do uso do sistema.

## Slide 4 - Visao Geral Do Fluxo

Mostrar o caminho completo de um documento dentro do sistema.

Fala sugerida:

> O funcionamento comeca com a ingestao do documento. Depois, o sistema valida o arquivo, extrai texto e metadados, processa o conteudo, atualiza o indice de busca e torna o documento disponivel para consulta pelos usuarios.

Fluxo:

1. Upload do documento.
2. Validacao de formato, tamanho e categoria.
3. Extracao de texto e metadados.
4. Processamento textual.
5. Indexacao.
6. Busca e exibicao dos resultados.

## Slide 5 - Perfis De Usuario

Explicar a separacao entre usuario comum e administrador.

Fala sugerida:

> O sistema trabalha com controle de acesso. O usuario comum pode buscar, visualizar documentos, acessar previas e avaliar a relevancia dos resultados. O administrador possui permissoes adicionais, como enviar documentos, gerenciar usuarios, acompanhar metricas, consultar auditoria e controlar configuracoes.

Pontos principais:

- Usuario comum: busca e visualizacao.
- Administrador: gestao e operacao do sistema.
- Separacao de permissoes.
- Protecao das rotas administrativas.

## Slide 6 - Ingestao De Documentos

Explicar como documentos entram na base.

Fala sugerida:

> Na ingestao, o administrador pode enviar um documento individual ou varios arquivos em lote. O sistema valida o arquivo, registra falhas quando houver problema e armazena os dados necessarios para que o documento seja processado e encontrado posteriormente.

Pontos principais:

- Upload individual.
- Upload em lote.
- Validacao de arquivos.
- Registro de documentos invalidos.
- Armazenamento de metadados.

## Slide 7 - Pipeline De Indexacao

Explicar o processamento interno depois do upload.

Fala sugerida:

> Depois da validacao, o texto passa por pre-processamento. O sistema normaliza os termos, remove ruidos, identifica palavras relevantes e grava essas informacoes no indice invertido. Esse indice permite localizar documentos rapidamente durante a busca.

Pontos principais:

- Extracao de texto.
- Normalizacao.
- Tokenizacao.
- Remocao de termos irrelevantes.
- Atualizacao incremental do indice.

## Slide 8 - Busca De Documentos

Explicar como o usuario encontra documentos.

Fala sugerida:

> Na busca, o usuario informa termos e pode aplicar filtros por categoria, tipo de documento, autor e periodo. O sistema calcula a relevancia dos documentos encontrados e permite ordenacao dinamica por relevancia, data ou titulo.

Pontos principais:

- Busca por termos.
- Filtros por metadados.
- Ordenacao dinamica.
- Ranking de relevancia.
- Historico de consultas.

## Slide 9 - Apresentacao Avancada Dos Resultados

Explicar os recursos visuais da tela de resultados.

Fala sugerida:

> A tela de resultados nao mostra apenas uma lista simples. Ela destaca os termos buscados, exibe trechos relevantes, mostra percentual de relevancia, permite previa rapida, abertura do documento e exportacao dos resultados em CSV ou PDF.

Pontos principais:

- Destaque dos termos buscados.
- Trechos relevantes.
- Barra ou percentual de relevancia.
- Previa rapida do documento.
- Exportacao CSV/PDF.

## Slide 10 - Versionamento De Documentos

Explicar o controle de versoes.

Fala sugerida:

> O IFESDOC tambem controla versoes de documentos. Isso e importante porque um mesmo documento pode ser atualizado ao longo do tempo. O usuario pode selecionar a versao que deseja visualizar, e o administrador pode registrar novas versoes ou restaurar versoes anteriores.

Pontos principais:

- Multiplas versoes para um mesmo documento.
- Selecao de versao na visualizacao.
- Registro de nova versao.
- Restauracao de versoes.
- Preservacao do historico documental.

## Slide 11 - Metricas E Relatorios

Explicar os recursos de monitoramento.

Fala sugerida:

> O sistema registra metricas de uso da busca, como quantidade de consultas, tempo medio de resposta, buscas sem resultado, termos mais pesquisados e documentos mais acessados. Esses dados ajudam a avaliar a qualidade da busca e o uso do sistema.

Pontos principais:

- Total de consultas.
- Tempo medio de resposta.
- Consultas sem resultado.
- Termos frequentes.
- Documentos mais acessados.
- Exportacao de relatorios.

## Slide 12 - Auditoria E Seguranca

Explicar os controles de seguranca.

Fala sugerida:

> A seguranca e baseada em autenticacao por token, controle de perfil e restricao de rotas administrativas. Tentativas de acesso negado sao registradas na auditoria, o que melhora a rastreabilidade das acoes e ajuda na administracao do sistema.

Pontos principais:

- Autenticacao por token JWT.
- Perfis de usuario.
- Rotas administrativas protegidas.
- Registro de acoes.
- Auditoria de tentativas negadas.
- Segredos configurados por variaveis de ambiente.

## Slide 13 - Arquitetura Tecnica

Apresentar a estrutura tecnica do sistema.

Fala sugerida:

> Tecnicamente, o IFESDOC usa frontend em React, backend em FastAPI, banco PostgreSQL e Docker Compose para execucao dos servicos. O backend e dividido em camadas, como API, servicos, repositorios, dominio, estrategias e pipeline.

Pontos principais:

- Frontend: React.
- Backend: FastAPI.
- Banco de dados: PostgreSQL.
- Containerizacao: Docker Compose.
- Worker de notificacoes.
- Arquitetura em camadas.

## Slide 14 - Beneficios

Resumir o valor entregue pelo sistema.

Fala sugerida:

> Os principais beneficios sao: recuperacao mais rapida de documentos, melhor organizacao institucional, controle de versoes, historico de acoes, metricas para gestao e uma experiencia de busca mais clara para o usuario.

Pontos principais:

- Busca mais eficiente.
- Organizacao documental.
- Rastreabilidade.
- Controle de versoes.
- Apoio a decisao com metricas.
- Melhor experiencia de uso.

## Slide 15 - Demonstracao Sugerida

Guiar uma demonstracao pratica do sistema.

Fala sugerida:

> Uma demonstracao ideal comeca pelo login, depois mostra o envio de um documento, a execucao de uma busca, a visualizacao dos resultados, a previa, a selecao de versoes, a avaliacao de relevancia e a consulta de metricas.

Sequencia sugerida:

1. Fazer login como administrador.
2. Enviar um documento pela tela de ingestao.
3. Executar uma busca.
4. Mostrar resultados com destaque e relevancia.
5. Abrir previa do documento.
6. Selecionar uma versao.
7. Registrar uma avaliacao de relevancia.
8. Abrir metricas e relatorios.
9. Mostrar auditoria administrativa.

## Slide 16 - Conclusao

Fechar a apresentacao retomando o objetivo do sistema.

Fala sugerida:

> Concluindo, o IFESDOC oferece uma base solida para gestao e busca documental. Ele melhora a eficiencia no acesso a informacao, aumenta a rastreabilidade, organiza o ciclo de vida dos documentos e pode evoluir futuramente com recursos como busca semantica, inteligencia artificial e integracoes externas.

Pontos principais:

- Sistema centralizado.
- Busca documental eficiente.
- Controle e rastreabilidade.
- Base preparada para evolucao.
- Potencial para busca semantica e IA.

## Encerramento

Fala final sugerida:

> O IFESDOC nao e apenas um repositorio de arquivos. Ele e uma ferramenta para transformar documentos em informacao acessivel, pesquisavel e monitoravel, apoiando tanto usuarios finais quanto administradores na gestao documental.
