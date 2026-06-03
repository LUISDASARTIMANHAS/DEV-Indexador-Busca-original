# 🧠 Visão Geral da Solução: Indexador e Buscador

O sistema foi concebido como uma aplicação moderna e desacoplada, focada em ser uma solução robusta de busca sem a complexidade desnecessária de microserviços prematuros.

**Pilares Estratégicos:**

* **API-first:** Foco na interface programática para múltiplos clientes.
* **Containerizada:** Isolamento completo do ambiente com Docker.
* **Modular & Extensível:** Facilidade para adicionar novos tipos de busca ou parsers.

---

## 🏗 1. Stack Tecnológica

| Componente | Tecnologia | Motivação Principal |
| --- | --- | --- |
| **Linguagem** | Python 3.10 / 3.11 | Compatível com o runtime do container e o ecossistema do backend. |
| **Backend** | FastAPI 0.111.0 | Performance, validação via Pydantic e documentação automática. |
| **Banco de Dados** | PostgreSQL | Confiabilidade e suporte a consultas relacionais e de texto. |
| **ORM** | SQLAlchemy 2.0.49 | Mapeamento moderno e integração com sessions. |
| **Migrações** | Alembic | Versionamento de banco e reprodutibilidade (presente nas dependências). |
| **Validação** | Pydantic 2.7.1 | Modelos de dados e validação de request/response. |
| **Segurança** | JWT / python-jose 3.5.0 | Autenticação stateless e geração de tokens. |
| **Testes** | Pytest 8.2.1 | Simplicidade e cobertura para o backend. |
| **Extração** | pdfplumber, python-docx | Parsers para documentos PDF e DOCX. |

---

## 🔍 2. O Motor de Busca (PostgreSQL)

Em vez de implementar um motor de busca do zero ou subir um Elasticsearch pesado, utilizamos as funcionalidades nativas do PostgreSQL. Isso resolve:

* **Índice Invertido (GIN).**
* **Ranking BM25:** Cálculo de relevância estatística.
* **Normalização:** Remoção de acentos e stop words.
* **Highlighting:** Uso de `ts_headline` para destacar termos na busca.

> **Nota Técnica:** O ranking segue a lógica de relevância de busca textual, onde o score é calculado para priorizar os documentos mais pertinentes.

$$Score(D, Q) = \sum_{q_i \in Q} \text{IDF}(q_i) \cdot \frac{f(q_i, D) \cdot (k_1 + 1)}{f(q_i, D) + k_1 \cdot (1 - b + b \cdot \frac{|D|}{\text{avgdl}})}$$

---

## 🧱 3. Arquitetura do Sistema

A solução adota uma separação de camadas rígida para garantir testabilidade e manutenção simplificada.

**Fluxo de Dados:**
`API ➔ Services ➔ Strategy ➔ Repository ➔ Database`
`                  ➔ Adapters`

### Padrões de Projeto (Design Patterns):

#### 🥇 Strategy Pattern (Comportamental)

**Motivação:** Gerenciar diferentes tipos de busca (simples, com filtros, avançada) sem poluir o código principal com condicionais complexas. Permite evoluir o ranking de forma isolada.

#### 🥈 Adapter Pattern (Estrutural)

**Motivação:** Blindar o núcleo do sistema contra mudanças em bibliotecas externas (como pdfplumber). Se precisarmos trocar o parser de PDF amanhã, mudamos apenas o Adapter.

---

## 🐳 4. Infraestrutura e Qualidade

* **Container-First:** Toda a aplicação roda via Docker Compose, garantindo que o ambiente do desenvolvedor seja idêntico ao de produção/avaliação.
* **Análise Estática:** Uso do SonarQube para monitorar code smells, complexidade ciclomática e garantir que a cobertura de testes via Pytest permaneça alta.

---

## 📋 5. Gerenciamento e Metodologia

Adotamos uma abordagem híbrida para equilibrar controle e agilidade:

### Gestão de Código

* **Gitflow Adaptado:** Branches `main` (estável), `develop` (integração) e `feature/*` (funcionalidades).
* **Code Review:** Pull Requests obrigatórios para manter a qualidade.

### Gestão de Tarefas

* **Híbrido Scrum/Kanban:**
* **Sprints:** Entregas incrementais com planejamento definido.
* **Kanban Board:** Visualização contínua do fluxo de trabalho no GitHub Projects.



---

## 🎯 6. Justificativa Estratégica

A escolha desta stack evita o famigerado Overengineering. Em vez de microserviços complexos ou dependências pesadas, focamos em uma solução monolítica modular, que é fácil de manter, rápida de implantar e perfeitamente adequada para exigências acadêmicas e profissionais.

