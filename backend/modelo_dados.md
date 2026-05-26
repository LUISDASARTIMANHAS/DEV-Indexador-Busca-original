# Modelo de Dados do IFESDOC

## Visao Geral

O modelo de dados do IFESDOC foi projetado para sustentar todo o ciclo de vida da plataforma de indexacao e busca documental: cadastro de usuarios, ingestao de arquivos, versionamento de documentos, processamento textual, indexacao em indice invertido, execucao de consultas, coleta de feedback e apuracao de metricas operacionais.

Trata-se de um modelo relacional orientado a rastreabilidade e historico. Em vez de armazenar apenas o estado atual dos documentos, a modelagem preserva eventos de ingestao, versoes documentais, indexacoes, buscas e acoes administrativas. Isso permite auditoria, reprocessamento e evolucao futura do mecanismo de busca sem perda de contexto.

## Objetivos do Modelo

- Representar documentos e seus metadados de forma normalizada.
- Registrar historico de ingestao, processamento e indexacao.
- Suportar um indice invertido persistido em banco relacional.
- Permitir consultas por usuario com armazenamento de filtros, tempos e resultados.
- Coletar feedback de relevancia para calibracao do mecanismo de busca.
- Viabilizar metricas operacionais e trilha administrativa.

## Visao Geral das Entidades

O diagrama apresenta as seguintes entidades principais:

- `USUARIO`
- `DOCUMENTO`
- `CATEGORIA_DOCUMENTO`
- `STATUS_INGESTAO`
- `HISTORICO_INGESTAO`
- `DOCUMENTOS_INVALIDOS`
- `HISTORICO_DOCUMENTO`
- `CAMPO_DOCUMENTO`
- `TIPO_CAMPO`
- `TERMO`
- `INDICE_INVERTIDO`
- `HISTORICO_INDEXACAO`
- `HISTORICO_BUSCA`
- `FEEDBACK_RELEVANCIA`
- `CALCULO_METRICAS`
- `HISTORICO_ADMINISTRATIVO`

## Descricao das Tabelas

### 1. USUARIO

Armazena os usuarios do sistema, incluindo credenciais, perfil e situacao de ativacao.

Campos principais:

- `cod_usuario`: chave primaria.
- `nome`: nome completo do usuario.
- `login`: identificador de acesso.
- `email`: endereco de email.
- `senha_hash`: senha armazenada em formato seguro.
- `perfil`: perfil de acesso, por exemplo usuario comum ou administrador.
- `ativo`: indica se a conta esta habilitada.
- `criado_em`: data de criacao da conta.
- `atualizado_em`: data da ultima alteracao cadastral.

Papel no modelo:

- Atua como entidade central de autoria e auditoria.
- Se relaciona com criacao de documentos, historico de ingestao, buscas, feedbacks, registros administrativos e documentos invalidos.

Observacao:

- O diagrama indica restricoes de unicidade em campos de identificacao como `login` e `email`.

### 2. CATEGORIA_DOCUMENTO

Tabela de dominio usada para classificar os documentos em grupos funcionais ou tematicos.

Campos principais:

- `cod_categoria`: chave primaria.
- `nome_categoria`: nome descritivo da categoria.

Papel no modelo:

- Evita repeticao textual da categoria em `DOCUMENTO`.
- Facilita filtros, agregacoes e relatórios.

### 3. DOCUMENTO

Representa o cadastro principal do documento no sistema. Essa tabela guarda os metadados mais estaveis do item documental, enquanto o conteudo e o versionamento ficam em tabelas historicas.

Campos principais:

- `cod_documento`: chave primaria.
- `cod_categoria`: chave estrangeira para `CATEGORIA_DOCUMENTO`.
- `titulo`: titulo do documento.
- `tipo`: tipo ou extensao logica do documento.
- `data_publicacao`: data de publicacao ou referencia temporal do documento.
- `ativo`: indica se o documento esta disponivel para uso e busca.
- `criado_em`: data de cadastro.
- `atualizado_em`: data da ultima atualizacao.
- `cod_usuario_criador`: chave estrangeira para `USUARIO`.

Papel no modelo:

- Funciona como raiz do agregado documental.
- Se relaciona com historico de ingestao, historico de documento e feedback de relevancia.

### 4. STATUS_INGESTAO

Tabela de apoio para padronizar os estados do processo de ingestao.

Campos principais:

- `cod_status_ingestao`: chave primaria.
- `estado_ingestao`: descricao do estado.

Exemplos de uso:

- recebido
- em processamento
- concluido
- erro

Papel no modelo:

- Garante consistencia semantica no historico de ingestao.

### 5. HISTORICO_INGESTAO

Registra cada tentativa ou evento de ingestao de um documento, incluindo o status e eventual mensagem de erro.

Campos principais:

- `cod_historico_ingestao`: chave primaria.
- `cod_usuario`: chave estrangeira para `USUARIO`.
- `cod_documento`: chave estrangeira para `DOCUMENTO`.
- `cod_status_ingestao`: chave estrangeira para `STATUS_INGESTAO`.
- `tipo_ingestao`: identifica o tipo ou origem da ingestao.
- `mensagem_erro`: descricao do erro quando houver falha.
- `tempo_processamento_ms`: tempo de processamento em milissegundos.
- `criado_em`: data do evento.

Papel no modelo:

- Permite auditar o fluxo de carga de documentos.
- Suporta monitoramento operacional e diagnostico de falhas.

### 6. DOCUMENTOS_INVALIDOS

Armazena arquivos rejeitados durante a ingestao, antes mesmo de se consolidarem como documentos validos no cadastro principal.

Campos principais:

- `cod_documentos_invalidos`: chave primaria.
- `cod_usuario`: chave estrangeira para `USUARIO`.
- `nome_arquivo`: nome do arquivo recebido.
- `motivo_erro`: motivo da invalidacao.
- `criado_em`: data do registro.

Papel no modelo:

- Separa falhas de pre-validacao do ciclo normal de `DOCUMENTO`.
- Mantem historico dos arquivos descartados para auditoria e suporte.

### 7. HISTORICO_DOCUMENTO

Armazena as versoes do documento ao longo do tempo. Essa tabela concentra o caminho do arquivo, o texto extraido e o texto processado associado a uma versao especifica.

Campos principais:

- `cod_historico_documento`: chave primaria.
- `cod_documento`: chave estrangeira para `DOCUMENTO`.
- `cod_usuario`: chave estrangeira para `USUARIO`.
- `numero_versao`: numero da versao registrada.
- `caminho_arquivo`: localizacao logica ou fisica do arquivo.
- `texto_extraido`: texto bruto extraido da fonte.
- `texto_processado`: texto normalizado para indexacao.
- `criado_em`: data da geracao da versao.
- `versao_ativa`: indica qual versao esta vigente para busca e exibicao.

Papel no modelo:

- Separa metadado estavel do documento de seu conteudo versionado.
- Permite reindexacao de versoes anteriores.
- Mantem historico completo das transformacoes do documento.

### 8. TIPO_CAMPO

Cataloga os tipos de campo extraidos ou indexados de um documento.

Campos principais:

- `cod_tipo_campo`: chave primaria.
- `tipo_campo`: nome do campo.

Exemplos possiveis:

- titulo
- resumo
- corpo
- ementa
- palavras-chave

Papel no modelo:

- Padroniza a classificacao semantica dos trechos documentais.

### 9. CAMPO_DOCUMENTO

Representa os campos textuais extraidos de uma versao documental. Cada registro identifica um fragmento ou secao associada a um tipo de campo.

Campos principais:

- `cod_campo_documento`: chave primaria.
- `cod_historico_documento`: chave estrangeira para `HISTORICO_DOCUMENTO`.
- `cod_tipo_campo`: chave estrangeira para `TIPO_CAMPO`.
- `conteudo`: conteudo textual do campo.

Papel no modelo:

- Permite indexacao por campo.
- Viabiliza consultas mais precisas e ranking contextual.
- Cria base para pesos diferentes por tipo de campo.

### 10. TERMO

Tabela vocabular do indice invertido. Cada registro representa um termo unico conhecido pelo sistema.

Campos principais:

- `cod_termo`: chave primaria.
- `texto_termo`: forma textual do termo.
- `df`: document frequency, quantidade de documentos em que o termo aparece.
- `idf`: valor derivado de inverse document frequency.

Papel no modelo:

- Centraliza o dicionario da indexacao.
- Evita duplicidade de termos no indice invertido.

Observacao:

- O diagrama indica unicidade para `texto_termo`, o que e coerente com a natureza vocabular da tabela.

### 11. INDICE_INVERTIDO

Tabela central da estrutura de busca. Faz a associacao entre um termo e um campo documental, armazenando informacoes necessarias para ranking e localizacao.

Campos principais:

- `cod_indice_invertido`: chave primaria.
- `cod_termo`: chave estrangeira para `TERMO`.
- `cod_campo_documento`: chave estrangeira para `CAMPO_DOCUMENTO`.
- `tf`: term frequency no campo.
- `posicao_inicial`: posicao inicial da ocorrencia ou do bloco indexado.

Papel no modelo:

- Materializa o indice invertido em banco relacional.
- Permite recuperar rapidamente quais documentos e campos contem determinado termo.
- Sustenta calculos de relevancia com base em `tf`, `df` e `idf`.

### 12. HISTORICO_INDEXACAO

Registra as execucoes de indexacao de uma determinada versao documental.

Campos principais:

- `cod_historico_indexacao`: chave primaria.
- `cod_historico_documento`: chave estrangeira para `HISTORICO_DOCUMENTO`.
- `tempo_indexacao_ms`: duracao da indexacao em milissegundos.
- `mensagem_erro`: detalhe de falha, quando houver.
- `criado_em`: data do processamento.

Papel no modelo:

- Permite medir desempenho do indexador.
- Suporta reprocessamento, auditoria e diagnostico tecnico.

### 13. HISTORICO_BUSCA

Armazena cada consulta realizada por um usuario, com texto pesquisado, filtros aplicados, quantidade de resultados e tempo de resposta.

Campos principais:

- `cod_historico_busca`: chave primaria.
- `cod_usuario`: chave estrangeira para `USUARIO`.
- `consulta_texto`: texto da consulta submetida.
- `filtros`: representacao serializada dos filtros.
- `quantidade_resultados`: total de resultados retornados.
- `tempo_resposta_ms`: tempo de resposta da busca.
- `criado_em`: data da consulta.

Papel no modelo:

- Fornece base para metricas de uso.
- Permite estudar comportamento de pesquisa e qualidade do motor de busca.

### 14. FEEDBACK_RELEVANCIA

Registra a avaliacao do usuario sobre a relevancia de um documento retornado em uma busca especifica.

Campos principais:

- `cod_feedback_relevancia`: chave primaria.
- `cod_usuario`: chave estrangeira para `USUARIO`.
- `cod_historico_busca`: chave estrangeira para `HISTORICO_BUSCA`.
- `cod_documento`: chave estrangeira para `DOCUMENTO`.
- `nota`: avaliacao numerica do resultado.
- `comentario`: observacao textual opcional.
- `criado_em`: data do feedback.

Papel no modelo:

- Gera sinal supervisionado para melhoria de ranking.
- Relaciona usuario, busca e documento em um unico evento de avaliacao.

### 15. CALCULO_METRICAS

Armazena resultados consolidados de metricas calculadas em janelas de tempo.

Campos principais:

- `cod_calculo_metricas`: chave primaria.
- `periodo_inicio`: inicio do periodo analisado.
- `periodo_fim`: fim do periodo analisado.
- `total_consultas`: numero total de consultas no periodo.
- `tempo_medio_respostas`: media do tempo de resposta das buscas.
- `media_resultados`: media de resultados retornados por consulta.
- `consultas_sem_resultado`: quantidade de buscas sem retorno.
- `calculado_em`: instante em que a consolidacao foi executada.

Papel no modelo:

- Evita recalculo frequente de indicadores operacionais.
- Apoia acompanhamento de desempenho e qualidade de busca.

### 16. HISTORICO_ADMINISTRATIVO

Tabela de trilha de auditoria para acoes administrativas executadas por usuarios com privilegios de gestao.

Campos principais:

- `cod_historico_administrativo`: chave primaria.
- `cod_usuario`: chave estrangeira para `USUARIO`.
- `descricao`: descricao da acao realizada.
- `tipo_acao`: classificacao da acao administrativa.
- `criado_em`: data do evento.
- `entidade_tipo`: tipo da entidade impactada.
- `cod_entidade`: identificador da entidade relacionada.

Papel no modelo:

- Registra alteracoes criticas para governanca e conformidade.
- Permite rastrear quem executou determinada operacao administrativa e sobre qual entidade.

## Relacionamentos Principais

Os relacionamentos do diagrama podem ser entendidos nos seguintes blocos:

### Usuarios e autoria

- Um `USUARIO` pode criar varios `DOCUMENTO`.
- Um `USUARIO` pode gerar varios registros em `HISTORICO_INGESTAO`.
- Um `USUARIO` pode possuir varios registros em `DOCUMENTOS_INVALIDOS`.
- Um `USUARIO` pode executar varias `HISTORICO_BUSCA`.
- Um `USUARIO` pode registrar varios `FEEDBACK_RELEVANCIA`.
- Um `USUARIO` pode gerar varios `HISTORICO_ADMINISTRATIVO`.
- Um `USUARIO` tambem se relaciona a `HISTORICO_DOCUMENTO`, indicando autoria ou responsabilidade sobre a versao.

### Documentos e ciclo de vida

- Uma `CATEGORIA_DOCUMENTO` classifica varios `DOCUMENTO`.
- Um `DOCUMENTO` pode possuir varios registros em `HISTORICO_INGESTAO`.
- Um `DOCUMENTO` pode possuir varias versoes em `HISTORICO_DOCUMENTO`.
- Um `DOCUMENTO` pode receber varios `FEEDBACK_RELEVANCIA`.

### Versionamento e indexacao

- Um `HISTORICO_DOCUMENTO` pode originar varios `CAMPO_DOCUMENTO`.
- Um `HISTORICO_DOCUMENTO` pode possuir varios `HISTORICO_INDEXACAO`.
- Um `TIPO_CAMPO` classifica varios `CAMPO_DOCUMENTO`.
- Um `CAMPO_DOCUMENTO` pode participar de varias ocorrencias em `INDICE_INVERTIDO`.
- Um `TERMO` pode aparecer em varios registros de `INDICE_INVERTIDO`.

### Busca e aprendizado

- Um `HISTORICO_BUSCA` pode gerar varios `FEEDBACK_RELEVANCIA`.
- Cada `FEEDBACK_RELEVANCIA` referencia simultaneamente o usuario, a busca e o documento avaliado.

## Fluxo Logico do Modelo

### 1. Cadastro e governanca

O usuario e cadastrado em `USUARIO`, com perfil e status de ativacao. Toda acao administrativa relevante pode ser refletida em `HISTORICO_ADMINISTRATIVO`.

### 2. Entrada documental

Quando um arquivo chega ao sistema, ele pode seguir dois caminhos:

- Se falhar em validacoes iniciais, e registrado em `DOCUMENTOS_INVALIDOS`.
- Se for aceito, gera um registro em `DOCUMENTO` e eventos em `HISTORICO_INGESTAO`.

### 3. Versionamento e processamento

Cada versao processada do documento e armazenada em `HISTORICO_DOCUMENTO`, com texto extraido e texto processado. Os fragmentos estruturados da versao sao registrados em `CAMPO_DOCUMENTO`, classificados por `TIPO_CAMPO`.

### 4. Construcao do indice invertido

Os termos normalizados sao persistidos em `TERMO`. As ocorrencias desses termos nos campos documentais sao gravadas em `INDICE_INVERTIDO`, incluindo frequencia e informacao posicional. O desempenho e erros da etapa sao registrados em `HISTORICO_INDEXACAO`.

### 5. Execucao de buscas

Cada consulta do usuario e registrada em `HISTORICO_BUSCA`, com filtros, quantidade de resultados e tempo de resposta. Esses dados alimentam estatisticas operacionais e analises de comportamento.

### 6. Feedback e metricas

O usuario pode avaliar os resultados por meio de `FEEDBACK_RELEVANCIA`. Em paralelo, consolidacoes periodicas sao armazenadas em `CALCULO_METRICAS`.

## Como o Modelo Sustenta o Indice Invertido

O nucleo da busca textual esta apoiado no conjunto `TERMO`, `CAMPO_DOCUMENTO` e `INDICE_INVERTIDO`.

Funcionamento conceitual:

1. O texto processado de uma versao documental e dividido em campos.
2. Cada campo gera tokens normalizados.
3. Cada token unico passa a existir em `TERMO`.
4. Cada ocorrencia relevante gera um registro em `INDICE_INVERTIDO`.
5. O sistema pode combinar `tf`, `df` e `idf` para calcular relevancia.

Essa modelagem oferece:

- indexacao por campo
- possibilidade de ranking estatistico
- reaproveitamento da mesma estrutura para novos algoritmos
- suporte futuro a pesos por campo e estrategias hibridas

## Beneficios Arquiteturais do Modelo

- Separacao clara entre entidade principal e historico de versoes.
- Rastreabilidade completa do ciclo de ingestao, indexacao e busca.
- Base consistente para auditoria, seguranca e administracao.
- Estrutura favoravel a testes e reprocessamentos.
- Facilidade de extensao para busca semantica e modulos analiticos.

## Observacoes de Implementacao

- O diagrama mostra chaves primarias inteiras e diversas chaves estrangeiras para garantir integridade referencial.
- Algumas colunas aparecem com indicativos de unicidade ou nulabilidade no desenho. Essas regras devem ser refletidas no DDL final e nas migracoes do projeto.
- O modelo foi desenhado para PostgreSQL, mas a separacao por camadas no backend permite evolucoes na persistencia sem alterar o dominio central.

## Conclusao

O modelo de dados do IFESDOC nao se limita a armazenar documentos. Ele organiza o dominio da recuperacao da informacao de ponta a ponta: quem interage com o sistema, quais documentos entram, como eles sao transformados, como sao indexados, como sao consultados e como a qualidade da busca pode ser medida e aprimorada ao longo do tempo.
