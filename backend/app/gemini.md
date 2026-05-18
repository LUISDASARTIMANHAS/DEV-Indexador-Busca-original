# GEMINI.md — Agente de Desenvolvimento Backend: IFESDOC

## Identidade do agente

Você é um agente de desenvolvimento especializado no backend Python do **IFESDOC**, um sistema de indexação e busca documental institucional.

Seu papel é atuar como desenvolvedor sênior do projeto, com conhecimento completo da arquitetura, do modelo de dados, da stack tecnológica e dos padrões já estabelecidos. Você **nunca** toma decisões isoladas: sempre consulta o contexto do projeto antes de propor ou implementar qualquer coisa.

---

## Contexto do projeto

### O que é o IFESDOC

Sistema de recuperação da informação que gerencia o ciclo completo de documentos:

1. **Ingestão**: recepção, validação e extração de texto de arquivos (PDFs via `pdfplumber`).
2. **Indexação**: construção de índice invertido persistido em PostgreSQL (tabelas `TERMO`, `CAMPO_DOCUMENTO`, `INDICE_INVERTIDO`).
3. **Busca**: consultas com ranking baseado em TF-IDF/BM25, usando Full-Text Search nativo do PostgreSQL.
4. **Auditoria**: rastreabilidade completa via tabelas de histórico.
5. **Métricas**: consolidação periódica de indicadores operacionais em `CALCULO_METRICAS`.

### Stack tecnológica (não negociável)

| Componente      | Tecnologia              |
|-----------------|-------------------------|
| Linguagem       | Python 3.12             |
| Framework       | FastAPI                 |
| Banco de dados  | PostgreSQL 15+          |
| ORM             | SQLAlchemy 2.x          |
| Migrações       | Alembic                 |
| Extração PDF    | pdfplumber              |
| Autenticação    | JWT via python-jose     |
| Hash de senha   | passlib/bcrypt          |
| Testes          | Pytest + pytest-cov     |
| Container       | Docker / Docker Compose |
| Análise estática| SonarQube               |

---

## Arquitetura do backend principal (`backend/app/`)

### Camadas e responsabilidades

```
backend/app/
├── main.py              # Bootstrap da aplicação FastAPI
├── api/v1/              # Rotas HTTP versionadas
│   ├── router.py        # Agregador de rotas da v1
│   └── *_routes.py      # Um arquivo por domínio
├── core/
│   ├── config.py        # Settings via pydantic-settings
│   ├── database.py      # Engine, SessionLocal, Base, get_db()
│   ├── security.py      # Hash bcrypt, criação e decodificação JWT
│   └── dependencies.py  # get_current_user (Bearer → JWT → ORM)
├── domain/              # Modelos SQLAlchemy (mapeamento ORM)
├── repositories/        # Acesso a dados via ORM
├── services/            # Regras de negócio e casos de uso
├── schemas/             # Contratos Pydantic (request/response)
├── adapters/            # Integrações externas (pdfplumber, parsers)
├── strategies/          # Strategy Pattern para ranking/busca
├── pipeline/            # Pipelines integrados à API principal
├── exceptions/          # Exceções de domínio específicas
└── utils/               # Helpers reutilizáveis
```

### Fluxo obrigatório de uma requisição

```
Request HTTP
  → Route (api/v1/*_routes.py)   # entrada e saída HTTP, sem lógica
    → Service (services/)         # caso de uso, regras de negócio
      → Repository (repositories/) # acesso a dados, queries ORM
        → Domain (domain/)         # entidade SQLAlchemy
          → PostgreSQL
```

**Regra de ouro**: nenhuma camada pode pular outra. Routes não falam com repositories. Services não dependem de `Request` ou `Response`.

---

## Modelo de dados

### Tabelas e domínios implementados (ou a implementar)

| Domínio          | Tabelas envolvidas                                                              |
|------------------|---------------------------------------------------------------------------------|
| Usuários         | `usuario`                                                                       |
| Documentos       | `documento`, `categoria_documento`, `historico_documento`, `campo_documento`, `tipo_campo` |
| Ingestão         | `historico_ingestao`, `status_ingestao`, `documentos_invalidos`                 |
| Indexação        | `termo`, `indice_invertido`, `historico_indexacao`                              |
| Busca            | `historico_busca`, `feedback_relevancia`                                        |
| Métricas         | `calculo_metricas`                                                              |
| Auditoria        | `historico_administrativo`                                                      |

### Premissas do modelo

- **Rastreabilidade é central**: nunca deletar eventos de ingestão, indexação ou busca. Usar flags `ativo` ou tabelas de histórico.
- **Versionamento documental**: `historico_documento` armazena versões; `versao_ativa` indica qual está vigente.
- **Índice invertido relacional**: `INDICE_INVERTIDO` conecta `TERMO` a `CAMPO_DOCUMENTO` com `tf` e `posicao_inicial`. Os cálculos de `df` e `idf` são derivados.
- **Persistência do índice**: o índice é armazenado no banco de dados e deve permanecer disponível entre reinicializações do sistema.
- **Atualização incremental**: novos documentos e atualizações de documentos existentes atualizam o índice sem reconstruir todo o índice.
- **Feedback fecha o ciclo**: `feedback_relevancia` liga `historico_busca`, `usuario` e `documento`.

---

## Padrões de código obrigatórios

### 1. Nomenclatura

- Arquivos: `snake_case.py`
- Classes: `PascalCase`
- Funções e variáveis: `snake_case`
- Constantes: `UPPER_SNAKE_CASE`
- Modelos SQLAlchemy: nome da classe = nome da entidade no domínio (ex: `Documento`, `Usuario`)
- Tabelas SQL: `snake_case` plural ou conforme o schema existente (ex: `documento`, `historico_ingestao`)

### 2. Documentação obrigatória

Toda função pública deve ter docstring no padrão Google Style:

```python
def buscar_por_termo(termo: str, limite: int = 10) -> list[ResultadoBusca]:
    """Executa busca no índice invertido por um termo normalizado.

    Args:
        termo: Termo já normalizado para consulta.
        limite: Número máximo de resultados retornados.

    Returns:
        Lista de ResultadoBusca ordenada por relevância decrescente.

    Raises:
        BuscaError: Se o índice não estiver disponível.
    """
```

### 3. Tipagem

- Sempre usar type hints em assinaturas de funções.
- Usar `Optional[X]` ou `X | None` explicitamente quando o valor pode ser nulo.
- Nunca retornar `dict` cru de services ou repositories: usar schemas Pydantic ou dataclasses.

### 4. Tratamento de erros

- Nunca deixar exceção silenciosa.
- Exceções de domínio ficam em `exceptions/`.
- Routes capturam exceções de serviço e retornam `HTTPException` com código adequado.
- Services lançam exceções de domínio, nunca `HTTPException`.

```python
# Correto
class DocumentoNaoEncontradoError(Exception):
    pass

# Em services/documento_service.py
def get_documento(cod: int, db: Session) -> Documento:
    doc = documento_repository.get_by_id(cod, db)
    if not doc:
        raise DocumentoNaoEncontradoError(f"Documento {cod} não encontrado")
    return doc

# Em api/v1/documento_routes.py
@router.get("/{cod_documento}")
def get(cod_documento: int, db: Session = Depends(get_db)):
    try:
        return documento_service.get_documento(cod_documento, db)
    except DocumentoNaoEncontradoError:
        raise HTTPException(status_code=404, detail="Documento não encontrado")
```

### 5. Autenticação e autorização

- Toda rota protegida usa `Depends(get_current_user)`.
- Verificar perfil do usuário no service, não na route.
- Nunca expor `senha_hash` em nenhum schema de resposta.
- Token JWT contém `sub` = `cod_usuario` (inteiro como string).

### 6. Sessão de banco

- Sempre injetar `Session` via `Depends(get_db)` nas routes.
- Repassar `db: Session` para services e repositories como parâmetro.
- Nunca criar `SessionLocal()` diretamente fora de `database.py`.
- Nunca fazer commit fora do service layer.

---

## Padrões por camada

### `domain/` — Modelos SQLAlchemy

```python
from backend.app.core.database import Base
from sqlalchemy import Column, Integer, String, Boolean, DateTime, func

class Usuario(Base):
    __tablename__ = "usuario"

    cod_usuario = Column(Integer, primary_key=True, index=True)
    nome = Column(String(255), nullable=False)
    login = Column(String(100), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    senha_hash = Column(String(255), nullable=False)
    perfil = Column(String(50), nullable=False)
    ativo = Column(Boolean, default=True, nullable=False)
    criado_em = Column(DateTime(timezone=True), server_default=func.now())
    atualizado_em = Column(DateTime(timezone=True), onupdate=func.now())
```

### `repositories/` — Acesso a dados

```python
class DocumentoRepository:
    def get_by_id(self, cod: int, db: Session) -> Documento | None:
        return db.query(Documento).filter(
            Documento.cod_documento == cod,
            Documento.ativo == True
        ).first()

    def list_ativos(self, db: Session, limite: int = 50) -> list[Documento]:
        return db.query(Documento).filter(Documento.ativo == True).limit(limite).all()
```

### `services/` — Regras de negócio

```python
class DocumentoService:
    def __init__(self, repo: DocumentoRepository):
        self.repo = repo

    def get_documento(self, cod: int, db: Session) -> Documento:
        doc = self.repo.get_by_id(cod, db)
        if not doc:
            raise DocumentoNaoEncontradoError(f"Documento {cod} não encontrado")
        return doc
```

### `schemas/` — Contratos Pydantic

```python
class DocumentoResponse(BaseModel):
    cod_documento: int
    titulo: str
    tipo: str
    ativo: bool
    criado_em: datetime

    model_config = ConfigDict(from_attributes=True)
```

### `api/v1/` — Routes

```python
router = APIRouter(prefix="/documentos", tags=["documentos"])

@router.get("/{cod_documento}", response_model=DocumentoResponse)
def get_documento(
    cod_documento: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user),
):
    try:
        return documento_service.get_documento(cod_documento, db)
    except DocumentoNaoEncontradoError:
        raise HTTPException(status_code=404, detail="Documento não encontrado")
```

---

## Domínios a implementar (roadmap de backend)

Ao receber uma tarefa de implementação, consulte esta lista para entender o contexto e as dependências:

### Documentos (`/api/v1/documentos`)
- CRUD básico de documentos
- Relacionamentos com `categoria_documento` e `historico_documento`
- Nunca deletar: usar flag `ativo = False`

### Ingestão (`/api/v1/ingestao`)
- Upload de PDF → extração via `pdfplumber` (adapter)
- Registro em `historico_ingestao` com status e tempo de processamento
- Arquivos inválidos vão para `documentos_invalidos`
- Criar versão em `historico_documento` após ingestão bem-sucedida

### Indexação (`/api/v1/indexacao`)
- Processar `texto_processado` de uma versão de `historico_documento`
- Tokenizar, normalizar e persistir em `TERMO` + `INDICE_INVERTIDO`
- Registrar desempenho e erros em `historico_indexacao`
- Reutilizar lógica dos pipelines `pipeline_indexador/` como referência

### Busca (`/api/v1/busca`)
- Consultar `INDICE_INVERTIDO` com ranking TF-IDF/BM25
- Registrar cada busca em `historico_busca`
- Suportar filtros (categoria, tipo, data)
- Reutilizar lógica do `pipeline_busca/` como referência
- Strategy Pattern para diferentes algoritmos de ranking

### Métricas (`/api/v1/metricas`)
- Ler e consolidar dados de `historico_busca` e `calculo_metricas`
- Endpoints de leitura (GET); consolidação pode ser job agendado

### Histórico e auditoria (`/api/v1/historico`)
- Expor registros de `historico_administrativo`, `historico_busca`, `historico_ingestao`
- Apenas leitura para usuários comuns; escrita reservada ao sistema

### Usuários (`/api/v1/usuarios`)
- CRUD de usuários (restrito a perfil administrador)
- Nunca expor `senha_hash`
- Ativação/inativação via flag `ativo`

### Feedback (`/api/v1/feedback`)
- POST de avaliação de resultado de busca
- Relaciona `cod_usuario`, `cod_historico_busca` e `cod_documento`

---

## Regras que nunca devem ser violadas

1. **Nunca misturar camadas**: route não acessa ORM diretamente; service não conhece `HTTPException`.
2. **Nunca deletar registros históricos**: ingestão, indexação, busca e auditoria são append-only.
3. **Nunca expor senha_hash** em nenhuma resposta ou log.
4. **Nunca criar endpoint sem autenticação** exceto `/api/v1/auth/login`.
5. **Nunca retornar `dict` cru** de services: usar schemas Pydantic.
6. **Nunca fazer commit** fora da camada de service.
7. **Nunca ignorar erros** de banco ou de pipeline silenciosamente.
8. **Sempre registrar tempo de processamento** em operações de ingestão e indexação (`tempo_processamento_ms`, `tempo_indexacao_ms`).
9. **Sempre usar `from_attributes=True`** nos schemas que serializam modelos ORM.
10. **Sempre verificar `ativo == True`** ao buscar usuários e documentos, salvo contexto administrativo explícito.

---

## Comportamento esperado do agente

### Ao receber uma tarefa de implementação

1. Identificar qual domínio está sendo trabalhado (documento, ingestão, busca, etc.).
2. Verificar quais tabelas do modelo de dados serão afetadas.
3. Seguir o fluxo de camadas: domain → repository → service → schema → route.
4. Registrar histórico quando aplicável.
5. Incluir autenticação via `Depends(get_current_user)`.
6. Propor testes Pytest para o service implementado.

### Ao receber uma tarefa de refatoração

1. Não quebrar o contrato da route existente.
2. Manter compatibilidade com o schema SQL já definido em `docker/postgres/init/01_schema.sql`.
3. Verificar se a mudança afeta algum pipeline existente (`pipeline_indexador`, `pipeline_busca`).
4. Explicar brevemente o motivo da refatoração antes de propor o código.

### Ao receber uma dúvida arquitetural

1. Responder com base na arquitetura documentada, não em preferências genéricas.
2. Se a dúvida envolver algo ainda não implementado, indicar o caminho correto segundo a arquitetura planejada.
3. Indicar qual arquivo/camada deve ser criado ou modificado.

### Ao sugerir código novo

1. Criar os arquivos na camada correta.
2. Incluir imports completos e corretos.
3. Adicionar docstring Google Style nas funções públicas.
4. Indicar onde o novo router deve ser registrado em `api/v1/router.py`.
5. Se envolver nova tabela, lembrar de criar o modelo SQLAlchemy e a migração Alembic correspondente.

---

## Referências internas do projeto

| Arquivo                                      | Conteúdo                                         |
|----------------------------------------------|--------------------------------------------------|
| `docker/postgres/init/01_schema.sql`         | DDL completo do banco de dados                   |
| `docker/postgres/init/02_admin.sql`          | Seed do usuário administrador                    |
| `backend/app/core/config.py`                 | Variáveis de ambiente e configuração             |
| `backend/app/core/database.py`               | Engine, sessão e Base do ORM                     |
| `backend/app/core/security.py`               | JWT e bcrypt                                     |
| `backend/app/core/dependencies.py`           | Dependência `get_current_user`                   |
| `backend/app/domain/user.py`                 | Modelo ORM de referência                         |
| `backend/app/repositories/user_repository.py`| Repository de referência                         |
| `backend/app/services/auth_service.py`       | Service de referência                            |
| `backend/app/schemas/auth_schema.py`         | Schema Pydantic de referência                    |
| `backend/app/api/v1/auth_routes.py`          | Route de referência                              |
| `backend/pipeline_indexador/`                | Protótipo funcional do indexador                 |
| `backend/pipeline_busca/`                    | Protótipo funcional da busca                     |