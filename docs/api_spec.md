# API Specification

## Overview

A API do IFESDOC é exposta pelo backend FastAPI em `http://localhost:8000` e versionada em `/api/v1`.

O ponto de entrada principal para verificação de disponibilidade é:

- `GET /` — health check da aplicação.

## Autenticação

A autenticação é feita via JWT Bearer token.

- Header: `Authorization: Bearer <token>`
- O token contém os campos `sub`, `login`, `role` e `sid`.

## Endpoints disponíveis

### `POST /api/v1/auth/login`

Solicitação:

```json
{
  "login": "usuario",
  "email": null,
  "password": "senha"
}
```

Observações:

- o campo `login` é opcional se `email` estiver informado.
- o campo `email` é opcional se `login` estiver informado.
- pelo menos um dos dois deve ser preenchido.

Resposta (`200`):

```json
{
  "id": 1,
  "name": "Nome do Usuário",
  "login": "usuario",
  "email": "usuario@exemplo.com",
  "role": "ADMIN",
  "active": true,
  "token": "<jwt-token>",
  "access_token": "<jwt-token>",
  "token_type": "bearer",
  "expiresAt": "2026-06-02T12:00:00"
}
```

Erros possíveis:

- `401 Unauthorized` — usuário ou senha inválidos.
- `403 Forbidden` — usuário inativo.
- `422 Unprocessable Entity` — payload inválido.

### `GET /api/v1/auth/me`

Requer header `Authorization: Bearer <token>`.

Resposta (`200`):

```json
{
  "id": 1,
  "name": "Nome do Usuário",
  "login": "usuario",
  "email": "usuario@exemplo.com",
  "role": "ADMIN",
  "active": true,
  "perfil": "ADMIN"
}
```

Erros possíveis:

- `401 Unauthorized` — token ausente ou inválido.
- `403 Forbidden` — usuário inativo.

### `POST /api/v1/auth/logout`

Requer header `Authorization: Bearer <token>`.

Resposta (`200`):

```json
{
  "message": "Sessão encerrada com sucesso."
}
```

Erros possíveis:

- `401 Unauthorized` — token ausente, inválido ou sessão expirada.

## Health check

### `GET /`

Resposta (`200`):

```json
{
  "message": "IFESDOC API running"
}
```

## Errors and response format

Em geral, erros retornam JSON no formato:

```json
{
  "message": "Descrição do erro"
}
```

Códigos de erro comuns:

- `401`: credenciais inválidas ou token inválido.
- `403`: acesso proibido, usuário inativo ou sessão encerrada.
- `422`: validação de dados de entrada.
- `503`: banco de dados indisponível ou schema não inicializado.
