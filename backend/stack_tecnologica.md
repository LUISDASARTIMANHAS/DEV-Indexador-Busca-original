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
| **Linguagem** | Python 3.12 | Ecossistema vasto e alta produtividade. |
| **Backend** | FastAPI | Performance, validação via Pydantic e Swagger nativo. |
| **Banco de Dados** | PostgreSQL 15+ | Confiabilidade e suporte a Full-Text Search. |
| **ORM** | SQLAlchemy 2.x | Mapeamento moderno e integração com Alembic. |
| **Migrações** | Alembic | Versionamento de banco e reprodutibilidade. |
| **Extração** | pdfplumber | Precisão na extração de texto de documentos PDF. |
| **Segurança** | JWT (JOSE) | Autenticação stateless e segura. |
| **Testes** | Pytest | Simplicidade e cobertura (pytest-cov). |

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

