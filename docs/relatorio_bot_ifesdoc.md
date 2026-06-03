# Relatório Técnico — Bot Conversacional do IFESDOC

## 1. Objetivo

O bot conversacional do IFESDOC foi criado como uma interface adicional para consulta documental por mensagens de texto. Ele permite que usuários interajam com o sistema por Telegram, WhatsApp ou endpoint de teste, sem substituir a interface web.

O objetivo é permitir perguntas em linguagem natural, interpretar intenções, extrair termos e filtros, consultar a base documental do IFESDOC e retornar respostas curtas, rastreáveis e adequadas ao formato de mensagem.

## 2. Relação com os requisitos

O bot atende ao documento de chatbot em:

- perguntas em linguagem natural;
- identificação de intenção;
- identificação de entidades, termos, filtros, frases e termos excluídos;
- consulta à base de conhecimento documental do IFESDOC;
- resposta textual clara;
- histórico de interações;
- estrutura preparada para avaliação de qualidade em evolução futura.

O bot também se conecta ao documento de indexação e busca em:

- consulta textual;
- parser de query e análise por meio do `QueryAnalyzer`;
- recuperação documental no índice invertido;
- ranking por relevância;
- snippets e highlight vindos do serviço de busca;
- histórico de consultas registrado pelo `SearchService`.

## 3. Arquitetura

Fluxo implementado:

```text
WhatsApp/Telegram
→ Webhook FastAPI
→ Adapter do canal
→ BotService
→ IntentDetector
→ EntityExtractor/QueryAnalyzer
→ SearchService
→ MessageFormatter
→ Resposta ao usuário
```

Arquivos principais:

```text
backend/app/bot/bot_service.py
backend/app/bot/intent_detector.py
backend/app/bot/entity_extractor.py
backend/app/bot/message_formatter.py
backend/app/bot/telegram_adapter.py
backend/app/bot/whatsapp_adapter.py
backend/app/api/v1/bot_routes.py
backend/app/repositories/bot_repository.py
```

Persistência criada:

```text
bot_conversa
bot_interacao
bot_usuario_vinculado
```

## 4. Intenções suportadas

Intenções implementadas:

- `search_documents`: busca documental simples.
- `search_with_filters`: busca com filtros implícitos, como ano ou tipo de arquivo.
- `get_document_details`: detalhes de um documento por ID ou posição na última busca.
- `generate_search_report`: relatório de buscas, restrito no modo público.
- `view_search_history`: histórico de interações do bot.
- `help`: mensagem de ajuda.
- `unknown`: mensagem não compreendida.

Exemplos:

```text
buscar documentos sobre estágio
→ search_documents

mostrar PDFs de 2025 sobre TCC
→ search_with_filters

detalhes do documento 15
→ get_document_details

detalhes 1
→ get_document_details usando a última busca

ver meu histórico de consultas
→ view_search_history
```

## 5. Entidades extraídas

O bot reaproveita o `QueryAnalyzer` para extrair:

- termos de busca;
- ano;
- tipo de arquivo;
- categoria explícita;
- frases entre aspas;
- termos excluídos com `-termo`;
- operadores simples;
- filtros de data iniciais.

O `EntityExtractor` adiciona extrações específicas do bot:

- ID de documento;
- posição do resultado na última busca.

Exemplo:

```text
mostrar PDFs de 2025 sobre estágio supervisionado
```

Resultado:

```json
{
  "terms": ["estagio", "supervisionado"],
  "filters": {
    "year": 2025,
    "type": "pdf"
  },
  "document_id": null
}
```

## 6. Exemplos de uso

Usuário:

```text
buscar documentos sobre estágio
```

Bot:

```text
Encontrei 3 documento(s) para "estagio":

1. Relatório de Estágio 2025
Relevância: 91%
Trecho: "estágio supervisionado deverá seguir..."

Responda com "detalhes 1" para ver mais informações do primeiro resultado.
```

Usuário:

```text
mostrar PDFs de 2025 sobre TCC
```

Bot:

```text
Encontrei documentos filtrados por tipo PDF e ano 2025.
```

Usuário:

```text
detalhes 1
```

Bot:

```text
Detalhes do primeiro documento da última busca, incluindo ID, categoria, tipo, arquivo, autor e prévia textual.
```

## 7. Endpoints

Endpoint de teste sem integração externa:

```http
POST /api/v1/bot/test
```

Entrada:

```json
{
  "channel": "test",
  "external_user_id": "lucas",
  "message": "mostrar PDFs de 2025 sobre estágio"
}
```

Saída:

```json
{
  "intent": "search_with_filters",
  "entities": {
    "terms": ["estagio"],
    "filters": {
      "year": 2025,
      "type": "pdf"
    }
  },
  "response_text": "Encontrei documentos..."
}
```

Telegram:

```http
POST /api/v1/bot/telegram/webhook
```

WhatsApp:

```http
GET /api/v1/bot/whatsapp/webhook
POST /api/v1/bot/whatsapp/webhook
```

## 8. Configuração

Variáveis adicionadas ao `.env.example`:

```text
TELEGRAM_BOT_TOKEN=
TELEGRAM_WEBHOOK_SECRET=
WHATSAPP_ACCESS_TOKEN=
WHATSAPP_PHONE_NUMBER_ID=
WHATSAPP_VERIFY_TOKEN=
BOT_ENABLE_TELEGRAM=false
BOT_ENABLE_WHATSAPP=false
BOT_PUBLIC_MODE=true
BOT_RATE_LIMIT_PER_MINUTE=20
```

Telegram:

1. Criar bot no BotFather.
2. Definir `TELEGRAM_BOT_TOKEN`.
3. Opcionalmente definir `TELEGRAM_WEBHOOK_SECRET`.
4. Ativar `BOT_ENABLE_TELEGRAM=true`.
5. Registrar o webhook apontando para `/api/v1/bot/telegram/webhook`.

WhatsApp:

1. Configurar app na Meta Cloud API.
2. Definir `WHATSAPP_ACCESS_TOKEN`.
3. Definir `WHATSAPP_PHONE_NUMBER_ID`.
4. Definir `WHATSAPP_VERIFY_TOKEN`.
5. Ativar `BOT_ENABLE_WHATSAPP=true`.
6. Registrar webhook em `/api/v1/bot/whatsapp/webhook`.

## 9. Segurança

Cuidados implementados:

- tokens de webhook podem ser validados quando configurados;
- tokens de Telegram e WhatsApp ficam em variáveis de ambiente;
- modo público inicial permite busca documental, mas bloqueia relatórios administrativos para usuários externos não vinculados;
- comandos administrativos não são executados sem vínculo com usuário IFESDOC administrador;
- interações são registradas;
- há rate limit simples por canal e usuário externo.

Estratégia atual:

- modo público: permite busca em documentos ativos do índice;
- modo autenticado futuro: usar `bot_usuario_vinculado` para vincular Telegram/WhatsApp a `usuario.cod_usuario`.

## 10. Limitações atuais

- o envio real para Telegram depende de `TELEGRAM_BOT_TOKEN` e `BOT_ENABLE_TELEGRAM=true`;
- o envio real para WhatsApp depende de credenciais da Meta Cloud API e `BOT_ENABLE_WHATSAPP=true`;
- quando os canais estão desativados, os webhooks funcionam em modo simulado e retornam a resposta gerada;
- contas externas ainda não possuem fluxo de vinculação por código temporário;
- relatórios administrativos são bloqueados no modo público;
- o bot usa regras heurísticas, não LLM;
- avaliação de qualidade do bot ainda não possui endpoint próprio.

## 11. Próximos passos

Evoluções recomendadas:

- criar fluxo de vinculação com código temporário entre IFESDOC e Telegram/WhatsApp;
- permitir autenticação por comando seguro;
- permitir envio de documentos ou links assinados pelo bot;
- gerar relatórios em PDF e enviar link;
- integrar busca semântica em consultas longas;
- adicionar avaliação da resposta do bot;
- usar feedback dos usuários para melhorar ranking;
- configurar webhooks reais em ambiente público com HTTPS.

## 12. Critérios de aceite atendidos

- existe módulo `backend/app/bot`;
- existe `BotService`;
- existe `IntentDetector`;
- existe `EntityExtractor` reaproveitando o `QueryAnalyzer`;
- existe `MessageFormatter`;
- existe endpoint `/api/v1/bot/test`;
- existe webhook de Telegram;
- existe webhook de WhatsApp;
- o bot responde busca documental;
- o bot responde ajuda;
- o bot registra histórico de interação;
- há testes unitários e de API;
- existe relatório técnico em `docs/relatorio_bot_ifesdoc.md`;
- autenticação JWT e busca existente não foram alteradas como dependência do bot.
