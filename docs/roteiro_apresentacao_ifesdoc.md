# Roteiro Da Apresentacao Do IFESDOC

Este roteiro foi ajustado para ficar coeso com o slide criado em `docs/apresentacao/Slide de apresentação - IFESDOC.pptx.pdf`.

Tempo total: 10 minutos exatos.

Divisao entre apresentadores:

- Pessoa 1: contexto, problema e teoria geral do processo - 2min30s.
- Pessoa 2: tecnologias, arquitetura e diferenciais de engenharia/produto - 5min00s.
- Pessoa 3: demonstracao, dificuldades, beneficios e fechamento - 2min30s.

Orientacao de linguagem: explicar primeiro o beneficio pratico e depois o termo tecnico. A banca tem pessoas de software e pessoas leigas, entao os conceitos tecnicos devem ser citados, mas sempre acompanhados de uma traducao simples.

## Mapa Geral Do Tempo

| Tempo | Pessoa | Slides | Tema |
|---|---|---|---|
| 0:00 - 0:30 | Pessoa 1 | Slide 1 | Abertura e objetivo |
| 0:30 - 1:10 | Pessoa 1 | Slide 2 | Desafio da gestao documental |
| 1:10 - 1:50 | Pessoa 1 | Slide 3 | O que e o IFESDOC |
| 1:50 - 2:30 | Pessoa 1 | Slides 8, 9 e 10 como referencia conceitual | Teoria: ingestao, indexacao e busca |
| 2:30 - 3:10 | Pessoa 2 | Slide 4 | Pilares estrategicos |
| 3:10 - 4:00 | Pessoa 2 | Slide 5 | Tecnologias utilizadas |
| 4:00 - 4:45 | Pessoa 2 | Slide 6 | Arquitetura do sistema |
| 4:45 - 5:10 | Pessoa 2 | Slide 7 | Roadmap do projeto |
| 5:10 - 6:05 | Pessoa 2 | Slide 8 | Motor de busca |
| 6:05 - 6:45 | Pessoa 2 | Slide 9 | Fluxo de processamento |
| 6:45 - 7:10 | Pessoa 2 | Slide 10 | Pipeline de indexacao |
| 7:10 - 7:30 | Pessoa 2 | Slide 11 | Funcionalidades |
| 7:30 - 9:15 | Pessoa 3 | Slide 12 + sistema ao vivo | Demonstracao |
| 9:15 - 9:35 | Pessoa 3 | Slide 13 | Problemas de desenvolvimento |
| 9:35 - 9:50 | Pessoa 3 | Slide 14 | Beneficios |
| 9:50 - 10:00 | Pessoa 3 | Slides 15 e 16 | Fechamento e duvidas |

## Pessoa 1 - Contexto, Problema E Teoria

Tempo total: 2min30s.

### Slide 1 - IFESDOC

Tempo: 0:00 a 0:30.

Fala:

> Bom dia/boa tarde. Nos vamos apresentar o IFESDOC, um sistema de indexacao e busca de documentos institucionais. O objetivo do sistema e transformar documentos digitais em informacao facil de encontrar, com organizacao, seguranca e rastreabilidade.

> A apresentacao sera dividida em tres partes. Primeiro, vamos contextualizar o problema e a teoria por tras da busca documental. Depois, vamos mostrar a arquitetura, as tecnologias e os diferenciais do sistema. Por ultimo, faremos uma demonstracao pratica.

### Slide 2 - O Desafio Da Gestao Documental

Tempo: 0:30 a 1:10.

Fala:

> O desafio apresentado aqui e comum em ambientes institucionais: existe um grande volume de documentos, em formatos variados, como PDF, DOC e planilhas. Quando esses arquivos nao seguem um padrao ou ficam espalhados, a busca se torna lenta e pouco confiavel.

> Isso gera ineficiencia operacional. Pessoas gastam tempo procurando documentos, podem usar versoes erradas e tambem existe risco de seguranca e auditoria, porque fica mais dificil saber quem acessou, alterou ou publicou determinada informacao.

### Slide 3 - O Que E O IFESDOC?

Tempo: 1:10 a 1:50.

Fala:

> O IFESDOC foi construido para responder a esse problema. Ele nao funciona apenas como um repositorio de arquivos. A proposta e ser um motor de organizacao e recuperacao de documentos: o sistema recebe arquivos, extrai o conteudo, organiza metadados, indexa informacoes e permite buscar pelo conteudo dos documentos.

> Em outras palavras, o usuario nao precisa depender apenas do nome do arquivo. Ele pode procurar por termos, categorias, tipos, datas ou autores, e o sistema tenta retornar os documentos mais relevantes.

### Ponte Teorica - Ingestao, Indexacao E Busca

Tempo: 1:50 a 2:30.

Observacao: este trecho prepara a banca para os slides tecnicos que aparecem mais adiante, principalmente "O Motor de Busca", "Fluxo de Processamento" e "Pipeline de Indexacao".

Fala:

> Teoricamente, um sistema de busca documental segue tres grandes etapas. A primeira e a ingestao: o documento entra no sistema, passa por validacao e tem seu texto extraido. A segunda e a indexacao: o texto e normalizado, tokenizado e armazenado em estruturas que facilitam a busca. A terceira e a recuperacao: quando o usuario faz uma consulta, o sistema interpreta os termos, procura no indice, ranqueia os resultados e exibe trechos relevantes.

> Essa e a base que vamos ver implementada no IFESDOC: ingestao, processamento, indexacao, ranking e apresentacao dos resultados.

Transicao:

> Agora vamos entrar na parte central da apresentacao: como essa ideia foi implementada tecnicamente e quais diferenciais foram construidos no sistema.

## Pessoa 2 - Tecnologias, Arquitetura E Diferenciais

Tempo total: 5min00s.

### Slide 4 - Pilares Estrategicos

Tempo: 2:30 a 3:10.

Fala:

> O IFESDOC foi pensado com tres pilares principais. O primeiro e ser API-first, ou seja, o backend foi estruturado para expor funcionalidades de forma clara para diferentes clientes, como a interface web e futuramente outras integracoes.

> O segundo pilar e a containerizacao. Usamos Docker Compose para deixar o ambiente mais reprodutivel, com backend, banco, frontend e worker. O terceiro pilar e a modularidade. O sistema foi feito para receber novos parsers, novos tipos de busca e novas estrategias sem quebrar o restante da aplicacao.

### Slide 5 - Tecnologias Utilizadas

Tempo: 3:10 a 4:00.

Fala:

> No backend, usamos Python com FastAPI. Isso nos deu uma API performatica, documentacao automatica via Swagger e validacao com Pydantic. O acesso ao banco foi feito com SQLAlchemy, mantendo a comunicacao com o banco organizada e testavel.

> No frontend, usamos React com TypeScript e Vite para criar uma interface responsiva e mais segura em relacao a tipos. No banco, usamos PostgreSQL, que alem de armazenar metadados tambem oferece recursos nativos de busca textual.

> Em seguranca, o sistema usa autenticacao via JWT e controle por perfil. Em qualidade, usamos Pytest para testes automatizados e SonarQube como apoio para observar code smells, complexidade e qualidade do codigo.

### Slide 6 - Arquitetura Do Sistema

Tempo: 4:00 a 4:45.

Fala:

> A arquitetura foi separada em camadas para evitar que regra de negocio fique misturada diretamente nas rotas. As rotas HTTP ficam na camada de API. A orquestracao dos casos de uso fica em services. A comunicacao com o banco fica em repositories. As entidades principais ficam em domain.

> Tambem usamos patterns importantes. O Strategy Pattern permite alternar estrategias de busca e ranking, como frequencia, BM25, busca PostgreSQL FTS e busca hibrida. O Adapter Pattern isola bibliotecas externas, como o parser de PDF. Se trocarmos a biblioteca de extracao de texto, mudamos o adapter sem afetar o nucleo do sistema.

### Slide 7 - Roadmap Do Projeto

Tempo: 4:45 a 5:10.

Fala:

> O desenvolvimento seguiu uma evolucao incremental. Primeiro levantamos requisitos e definimos a interface. Depois criamos a base do sistema e a gestao documental. Em seguida, evoluimos o motor de busca, indexacao, metricas, qualidade, integracao e melhorias finais.

> Esse roadmap mostra que o sistema nao nasceu apenas como uma tela de upload, mas como uma solucao progressiva de recuperacao e gestao documental.

### Slide 8 - O Motor De Busca

Tempo: 5:10 a 6:05.

Fala:

> O motor de busca e um dos pontos mais importantes do IFESDOC. Em vez de depender apenas de uma busca simples por texto, implementamos diferentes estrategias. O PostgreSQL Full-Text Search usa um indice invertido do proprio banco, baseado em `tsvector` e indice GIN. Isso permite buscar rapidamente dentro do conteudo indexado.

> Para ranking, usamos criterios de relevancia textual. O sistema tambem possui estrategias como frequencia, TF-IDF e BM25. O BM25 e uma tecnica estatistica muito usada em mecanismos de busca porque considera frequencia dos termos, raridade e tamanho do documento.

> Alem disso, usamos `ts_headline` para destacar termos encontrados nos trechos exibidos. Para o usuario final, isso aparece como highlight nos resultados. Para a parte tecnica, isso mostra que a busca nao retorna apenas documentos, mas tambem evidencias do motivo pelo qual eles foram encontrados.

### Slide 9 - Fluxo De Processamento

Tempo: 6:05 a 6:45.

Fala:

> Este slide mostra o fluxo pratico. Primeiro vem a ingestao: o documento e recebido pela interface e validado por formato, tamanho, categoria e integridade. Depois vem a extracao e o processamento: o sistema extrai texto, organiza metadados e prepara o conteudo para indexacao.

> Por fim, ocorre a indexacao e a busca. O indice e atualizado e o documento fica disponivel para consultas. Quando o usuario busca, o sistema aplica ranking de relevancia para priorizar os documentos mais pertinentes.

### Slide 10 - Pipeline De Indexacao

Tempo: 6:45 a 7:10.

Fala:

> No pipeline de indexacao, o texto bruto e transformado em dados pesquisaveis. O sistema normaliza o texto, remove acentos, reduz ruido, tokeniza as palavras e gera termos relevantes. Documentos validos sao indexados; documentos invalidos sao registrados separadamente para controle e auditoria.

> Alem disso, adicionamos OCR com Tesseract para PDFs escaneados. Quando a extracao comum nao encontra texto suficiente, o OCR transforma a imagem do PDF em texto pesquisavel, que passa a ser salvo e indexado.

### Slide 11 - Funcionalidades

Tempo: 7:10 a 7:30.

Fala:

> Como produto, o sistema oferece metricas e relatorios, versionamento de documentos, auditoria e seguranca. Isso significa que alem de buscar documentos, o IFESDOC tambem acompanha uso, preserva historico, controla acesso por perfil e permite restaurar versoes anteriores.

Transicao:

> Agora vamos sair da explicacao e mostrar o sistema funcionando na pratica.

## Pessoa 3 - Demonstracao, Problemas E Fechamento

Tempo total: 2min30s.

### Slide 12 - Performance De Busca E Demonstracao

Tempo: 7:30 a 9:15.

Objetivo: usar o slide de performance como ponte para a demonstracao ao vivo.

Sequencia da demo:

1. Fazer login no sistema.
2. Mostrar rapidamente o menu principal.
3. Abrir a busca.
4. Pesquisar um termo relevante.
5. Mostrar resultados com snippet, highlight e relevancia.
6. Abrir um documento.
7. Mostrar metadados, versoes e texto extraido.
8. Se possivel, mostrar painel de OCR ou status de indexacao.
9. Mostrar rapidamente metricas ou comparador de estrategias.

Fala durante a demo:

> Agora vamos demonstrar o IFESDOC em uso. Primeiro, entramos no sistema com um usuario autenticado. Isso mostra que o acesso nao e aberto sem controle: existem perfis e permissoes.

> Na busca, digitamos um termo relacionado aos documentos indexados. O sistema retorna resultados com titulo, tipo, categoria, trecho relevante e relevancia. O destaque nos termos ajuda o usuario a entender rapidamente por que aquele documento apareceu.

> Ao abrir o documento, vemos os metadados, o conteudo extraido e as versoes. Esse ponto e importante porque documentos institucionais podem mudar ao longo do tempo, e o sistema preserva o historico.

> Tambem podemos acompanhar indexacao, metricas e, quando aplicavel, OCR. Isso mostra que o IFESDOC nao e apenas uma busca visual: ele registra processamento, qualidade e rastreabilidade.

Plano de contingencia se a demo falhar:

> Caso o ambiente apresente instabilidade, vamos seguir com as capturas e explicar o fluxo: login, busca, resultados, abertura do documento, versoes, OCR e metricas.

### Slide 13 - Principais Problemas De Desenvolvimento

Tempo: 9:15 a 9:35.

Fala:

> Durante o desenvolvimento, os principais desafios foram integrar modulos interdependentes, manter o indice sincronizado com documentos e versoes, estabilizar o pipeline de ingestao e garantir desempenho no mecanismo de busca.

> Esses problemas foram importantes porque representam dificuldades reais de engenharia: consistencia, desempenho, evolucao incremental e manutencao.

### Slide 14 - Beneficios Do IFESDOC

Tempo: 9:35 a 9:50.

Fala:

> Como resultado, o IFESDOC entrega tres beneficios principais: organizacao e recuperacao da informacao, controle com seguranca e rastreabilidade, e apoio a gestao por meio de metricas e relatorios.

> Em termos simples, o sistema reduz tempo de procura, melhora o controle documental e oferece dados para tomada de decisao.

### Slides 15 E 16 - Fechamento E Duvidas

Tempo: 9:50 a 10:00.

Fala:

> Para concluir, o IFESDOC transforma documentos isolados em conhecimento acessivel. Ele combina fundamentos de recuperacao da informacao, boas praticas de engenharia de software e uma interface voltada para uso real.

> Obrigado. Estamos a disposicao para perguntas.

## Observacoes De Ensaio

- Ensaiar com cronometro. O segundo apresentador tem a maior carga de conteudo.
- Pessoa 1 deve evitar aprofundar nas tecnologias, porque isso fica para Pessoa 2.
- Pessoa 2 deve ser objetiva: explicar o diferencial sem entrar em codigo.
- Pessoa 3 deve deixar o sistema aberto antes da apresentacao.
- Se a demo atrasar, cortar metricas/comparador e manter apenas busca, resultado e documento.
- Se a demo falhar, usar o plano de contingencia e manter o tempo.
