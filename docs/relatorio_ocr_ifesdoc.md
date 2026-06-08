# Relatório Técnico — OCR no IFESDOC

## 1. Objetivo

Implementar OCR no IFESDOC para permitir a indexação de PDFs escaneados ou PDFs sem camada textual. O OCR atua como fallback automático quando a extração textual comum retorna texto vazio ou insuficiente.

## 2. Problema resolvido

A busca textual do IFESDOC depende do conteúdo salvo em `historico_documento.texto_extraido`. PDFs escaneados são compostos por imagens; nesses casos, bibliotecas como `pdfplumber` podem retornar pouco texto ou nenhum texto. Com OCR, o PDF é convertido em imagens por página e o Tesseract transforma a imagem em texto pesquisável.

## 3. Arquitetura implementada

Fluxo aplicado na ingestão:

```text
Upload do PDF
→ validação do arquivo
→ extração textual comum com pdfplumber
→ verificação de texto suficiente
→ fallback OCR, se necessário
→ texto OCR salvo em historico_documento.texto_extraido
→ metadados de OCR salvos na versão do documento
→ search_vector atualizado pelo trigger do PostgreSQL FTS
→ índice relacional/invertido reprocessado
→ documento fica disponível na busca
```

Componentes criados:

- `backend/app/adapters/ocr_adapter.py`: converte PDF em imagens e executa Tesseract.
- `backend/app/services/ocr_service.py`: decide quando OCR deve rodar, persiste status e integra com reindexação.
- `backend/app/api/v1/ocr_routes.py`: expõe execução manual, status e reprocessamento de pendentes.
- `backend/app/domain/ocr_history.py`: registra histórico detalhado de execuções OCR.

## 4. Tecnologias utilizadas

- Tesseract OCR.
- `pytesseract`.
- `pdf2image`.
- `Pillow`.
- Poppler (`poppler-utils`) para renderizar páginas PDF.
- Idioma português via pacote `tesseract-ocr-por`.

Configurações:

```env
OCR_ENABLED=true
OCR_LANGUAGE=por
OCR_DPI=200
OCR_MAX_PAGES=20
OCR_MIN_TEXT_LENGTH=50
OCR_TIMEOUT_SECONDS=120
```

## 5. Integração com versionamento

O OCR é associado à versão do documento em `historico_documento`. Cada versão possui seus próprios campos:

- `ocr_executado`
- `ocr_status`
- `ocr_idioma`
- `ocr_paginas_processadas`
- `ocr_tempo_ms`
- `ocr_erro`
- `ocr_executado_em`

Isso mantém coerência com o versionamento: uma versão antiga pode ter OCR diferente da versão ativa.

## 6. Integração com PostgreSQL FTS

O texto OCR é salvo em `historico_documento.texto_extraido`, que já alimenta o `search_vector` persistente. Como o trigger de FTS observa updates em `texto_extraido`, após OCR bem-sucedido o documento passa a ser localizado por:

```text
GET /api/v1/search?q=termo_extraido_do_pdf&mode=postgres_fts
```

A resposta de busca inclui metadados como `ocrExecuted` e `textSource`, permitindo que a interface indique quando o texto veio de OCR.

## 7. Endpoints criados

```text
POST /api/v1/ocr/document/{document_id}
GET  /api/v1/ocr/document/{document_id}/status
POST /api/v1/ocr/reprocess-pending
```

Parâmetros do endpoint manual:

- `version_id`: versão específica, opcional.
- `force`: força novo OCR mesmo quando já há texto suficiente.

Execução e reprocessamento exigem perfil administrador. Consulta de status exige usuário autenticado.

## 8. Interface frontend

A tela de documento passou a exibir:

- status de OCR;
- origem do texto (`native` ou `ocr`);
- idioma;
- páginas processadas;
- tempo de processamento;
- erro, quando existir;
- botão para executar OCR;
- botão para forçar OCR novamente para administradores.

A tela de status de indexação passou a exibir:

- documentos com OCR;
- OCRs com sucesso;
- OCRs com falha;
- tempo médio de OCR.

## 9. Testes realizados

Foram adicionados testes unitários com mocks:

- `should_run_ocr` com texto vazio;
- `should_run_ocr` com texto suficiente;
- `OCRAdapter` extraindo texto de páginas mockadas;
- falha estruturada do adapter;
- `OCRService` atualizando versão, texto e histórico;
- endpoint manual de OCR com `TestClient` e reindexação mockada.

Testes manuais recomendados:

1. PDF textual normal:
   - `pdfplumber` extrai texto;
   - OCR fica como `skipped`;
   - documento é indexado normalmente.
2. PDF escaneado:
   - extração comum retorna texto insuficiente;
   - OCR roda;
   - texto é salvo;
   - documento aparece na busca PostgreSQL FTS.
3. PDF ruim ou inválido:
   - OCR falha de forma controlada;
   - erro fica registrado;
   - endpoint retorna erro estruturado.

## 10. Limitações

- OCR pode errar em imagens de baixa qualidade.
- OCR é mais lento que extração textual comum.
- O processamento inicial é síncrono e limitado por páginas/timeout.
- PDFs muito grandes devem ser processados por worker/fila em produção.
- Depende de Tesseract e Poppler instalados no ambiente.
- Suporte inicial focado em português.
- Não há correção automática avançada de rotação, contraste ou resolução.

## 11. Próximos passos

- Mover OCR pesado para fila/worker.
- Adicionar pré-processamento de imagem.
- Detectar e corrigir rotação automaticamente.
- Salvar OCR por página para auditoria granular.
- Exibir painel de métricas históricas de OCR.
- Suportar OCR multilíngue.
- Comparar qualidade de busca antes/depois do OCR.
