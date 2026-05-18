**INSTITUTO FEDERAL DO ESPÍRITO SANTO**  
**CAMPUS COLATINA**  
**BACHARELADO EM SISTEMAS DE INFORMAÇÃO**  
**LABORATÓRIO DE ENGENHARIA DE SOFTWARE**  
**PROF.: JAIMEL DE OLIVEIRA LIMA**

**Aluno(s) / Grupo: Lucas Garcia, Luís Augusto e Pedro Emanuel**  
**Entrega/Sprint: Sprint 9 — Segurança, Gestão Documental e Experiência de Busca**  
**Data prevista de entrega: 05/05**  
**Data de envio: 05/05**

---

**1\. SITUAÇÃO DA ENTREGA** (Marque uma das opções)  

(X) Entrega Total  
(   ) Entrega Parcial (mínimo 50%) com notificação  
(   ) Entrega Parcial (mínimo 50%) sem notificação  
(   ) Entrega parcial (menos de 50% da sprint inicial)

---

**2\. JUSTIFICATIVA**  

Não houve atraso na entrega da sprint.

Todas as funcionalidades planejadas foram concluídas integralmente, validadas em backend e frontend e integradas sem comprometer o funcionamento geral do sistema.

---

**3\. O QUE FOI ENTREGUE**

• Implementação completa da autenticação com gerenciamento de sessão, incluindo geração de sessão após login, validação de sessão ativa, proteção de endpoints sensíveis, expiração por inatividade e logout  
• Implementação do versionamento de documentos, com registro de múltiplas versões, manutenção de histórico e restauração de versões anteriores sem perda das informações já armazenadas  
• Implementação da remoção lógica de documentos, preservando os registros no sistema e atualizando o índice para impedir retorno indevido em buscas  
• Consolidação da interface de resultados da busca, com integração ao backend, listagem de documentos encontrados, paginação e exibição de metadados relevantes  
• Melhoria do mecanismo de busca com indexação por campos, incluindo busca explícita em títulos, autores, categorias, tipo documental, nome de arquivo e conteúdo textual  
• Correção e fortalecimento dos filtros de busca, garantindo funcionamento consistente para categoria, autor, tipo documental, intervalo de datas e ordenação  
• Aprimoramento do ranking por relevância, com pesos diferenciados por campo, priorização de ocorrências no título, cobertura da consulta, proximidade entre termos e recência  
• Suporte a consultas curtas, prefixais e de baixa granularidade, permitindo buscas por poucos caracteres, prefixos e até mesmo uma única letra  
• Melhoria da visualização de documentos, com reorganização do texto extraído para leitura mais clara, humanização de títulos derivados do nome do arquivo e apresentação mais legível dos metadados  
• Preservação da compatibilidade com os fundamentos do sistema, mantendo armazenamento, histórico, indexação, exportação e download original funcionando de forma integrada  
• Ampliação da cobertura de testes de serviço e validações de build para garantir estabilidade após as alterações implementadas

---

**4\. O QUE NÃO FOI ENTREGUE**

Não se aplica. Todas as funcionalidades previstas para a sprint foram implementadas e entregues.

---

**5\. DIFICULDADES ENCONTRADAS**

Não houve impedimentos significativos durante a sprint.

Os principais desafios estiveram relacionados apenas à necessidade de manter compatibilidade entre os módulos já existentes, principalmente nas integrações entre autenticação, versionamento de documentos, índice invertido, mecanismo de busca e interface web.

Também foi necessário cuidado adicional para melhorar a experiência de leitura e a relevância da busca sem alterar os princípios centrais de armazenamento, indexação e recuperação documental do sistema.

---

**6\. COMO AS DIFICULDADES FORAM RESOLVIDAS**

• Evolução incremental das funcionalidades, preservando a arquitetura já existente  
• Realização de ajustes localizados nas camadas de serviço, repositório, API e interface, evitando alterações estruturais desnecessárias  
• Validação contínua com testes automatizados de serviço e compilação do frontend  
• Revisão das integrações entre busca, indexação e visualização para garantir consistência funcional em todos os fluxos principais do sistema

---

**7\. AUTOAVALIAÇÃO**

| Critério | Avaliação (1 a 5) |
| :---- | :---- |
| Organização do trabalho | 5 |
| Cumprimento do planejamento | 5 |
| Qualidade da entrega | 5 |
| Colaboração do grupo | 5 |
