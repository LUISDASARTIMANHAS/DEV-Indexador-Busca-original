**INSTITUTO FEDERAL DO ESPÍRITO SANTO**  
**CAMPUS COLATINA**  
**BACHARELADO EM SISTEMAS DE INFORMAÇÃO**  
**LABORATÓRIO DE ENGENHARIA DE SOFTWARE**  
**PROF.: JAIMEL DE OLIVEIRA LIMA**

**Aluno(s) / Grupo: Lucas Garcia, Luís Augusto e Pedro Emanuel**  
**Entrega/Sprint: Sprint 11 — Qualidade da Busca, Relatórios e Exportações**  
**Data prevista de entrega: 18/05**  
**Data de envio: 18/05**

---

**1\. SITUAÇÃO DA ENTREGA** (Marque uma das opções)  

(X) Entrega Total  
(   ) Entrega Parcial (mínimo 50%) com notificação  
(   ) Entrega Parcial (mínimo 50%) sem notificação  
(   ) Entrega parcial (menos de 50% da sprint inicial)

---

**2\. JUSTIFICATIVA**  

Não houve atraso na entrega da sprint.

As funcionalidades previstas foram implementadas, integradas ao sistema existente e validadas em backend e frontend, com foco em ampliar a capacidade analítica do mecanismo de busca e disponibilizar relatórios administrativos exportáveis.

---

**3\. O QUE FOI ENTREGUE**

• Implementação da análise de qualidade da busca com base no histórico de consultas já registrado pelo sistema  
• Consolidação das métricas de consultas realizadas, incluindo total de buscas, tempo médio de resposta, média de resultados, consultas sem retorno e taxa de buscas sem resultados  
• Implementação da análise de frequência de consultas e termos buscados, permitindo identificar padrões de uso e oportunidades de melhoria no mecanismo de recuperação  
• Persistência de cálculos consolidados de métricas em armazenamento relacional para análise posterior e comparação entre períodos  
• Implementação de rastreamento de acesso a documentos visualizados, baixados e exportados, permitindo identificar os documentos mais acessados no ambiente administrativo  
• Criação de módulo de relatórios analíticos de busca com resumo do período, consultas mais frequentes, consultas sem resultados, termos mais recorrentes e documentos mais acessados  
• Implementação de exportação de relatórios em formatos estruturados CSV e JSON diretamente pela API  
• Exposição de endpoints administrativos para consulta de métricas, geração de relatórios, listagem de consolidações armazenadas e persistência manual de novos cálculos  
• Integração completa da interface administrativa com o módulo de relatórios e exportações, permitindo filtrar período, consolidar métricas e exportar relatórios pela tela de métricas  
• Ampliação da cobertura de testes automatizados para validar persistência dos cálculos, rastreamento de acessos, geração de relatórios e exportação dos dados analíticos  
• Preservação da compatibilidade com os fundamentos do sistema, mantendo fluxo de busca, indexação, histórico, visualização documental e autenticação funcionando de forma integrada

---

**4\. O QUE NÃO FOI ENTREGUE**

Não se aplica. Todas as funcionalidades previstas para a sprint foram implementadas e entregues.

---

**5\. DIFICULDADES ENCONTRADAS**

Não houve impedimentos significativos durante a sprint.

Os principais cuidados estiveram concentrados em ampliar a camada analítica do sistema sem duplicar responsabilidades já existentes entre histórico de consultas, métricas operacionais e interface administrativa.

Também foi necessário estruturar relatórios exportáveis e persistência de consolidações sem comprometer o comportamento atual das rotas de busca e de visualização documental.

---

**6\. COMO AS DIFICULDADES FORAM RESOLVIDAS**

• Reaproveitamento do histórico de consultas já implementado como base para a análise de qualidade da busca  
• Evolução incremental do serviço de métricas, incorporando consolidação persistida, relatórios administrativos e exportações sem reescrever os fluxos anteriores  
• Inclusão de rastreamento específico de acesso a documentos para suportar relatórios mais completos sobre uso do sistema  
• Integração controlada entre backend analítico e frontend administrativo, centralizando relatórios dentro da tela de métricas já existente  
• Validação contínua com testes automatizados de serviço, compilação do backend, lint, testes e build do frontend

---

**7\. AUTOAVALIAÇÃO**

| Critério | Avaliação (1 a 5) |
| :---- | :---- |
| Organização do trabalho | 5 |
| Cumprimento do planejamento | 5 |
| Qualidade da entrega | 5 |
| Colaboração do grupo | 5 |
