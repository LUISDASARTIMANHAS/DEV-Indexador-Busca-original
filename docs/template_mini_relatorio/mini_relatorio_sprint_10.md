**INSTITUTO FEDERAL DO ESPÍRITO SANTO**  
**CAMPUS COLATINA**  
**BACHARELADO EM SISTEMAS DE INFORMAÇÃO**  
**LABORATÓRIO DE ENGENHARIA DE SOFTWARE**  
**PROF.: JAIMEL DE OLIVEIRA LIMA**

**Aluno(s) / Grupo: Lucas Garcia, Luís Augusto e Pedro Emanuel**  
**Entrega/Sprint: Sprint 10 — Remoção Física, Persistência do Índice e Métricas de Desempenho**  
**Data prevista de entrega: 12/05**  
**Data de envio: 12/05**

---

**1\. SITUAÇÃO DA ENTREGA** (Marque uma das opções)  

(X) Entrega Total  
(   ) Entrega Parcial (mínimo 50%) com notificação  
(   ) Entrega Parcial (mínimo 50%) sem notificação  
(   ) Entrega parcial (menos de 50% da sprint inicial)

---

**2\. JUSTIFICATIVA**  

Não houve atraso na entrega da sprint.

Todas as funcionalidades planejadas foram implementadas e integradas ao sistema. Porem, durante a validacao em backend e frontend, ainda foram identificados alguns bugs de menor impacto e pontos de desempenho que impediram considerar o resultado final como plenamente satisfatorio em termos de estabilidade e performance.

---

**3\. O QUE FOI ENTREGUE**

• Implementação da remoção física definitiva de documentos, com exclusão dos arquivos armazenados, limpeza dos registros associados e retirada completa do documento da base documental  
• Garantia de consistência entre base documental e índice invertido após remoção física, impedindo retorno indevido de documentos excluídos em consultas futuras  
• Exposição da remoção física por endpoint dedicado com controle administrativo, preservando a separação entre remoção lógica e remoção definitiva  
• Consolidação da persistência do índice invertido em armazenamento relacional, garantindo disponibilidade das estruturas indexadas mesmo após reinicialização da aplicação  
• Validação do suporte à atualização incremental do índice, permitindo indexação de novos documentos e reprocessamento de documentos atualizados sem reconstrução total da base  
• Garantia de consistência do índice durante uploads, atualizações, restaurações de versão, remoções lógicas e remoções físicas  
• Implementação dos cálculos de desempenho da busca, incluindo tempo médio de resposta, média de resultados por consulta, quantidade de consultas sem retorno e taxa de consultas sem resultados  
• Geração de indicadores consolidados de desempenho a partir do histórico de buscas, com distribuição de consultas e termos mais pesquisados  
• Integração das novas métricas à interface web de monitoramento, ampliando a visualização analítica do comportamento do mecanismo de busca  
• Ampliação da cobertura de testes automatizados para remoção física, persistência do índice entre sessões, atualização incremental e cálculos de desempenho da busca  
• Preservação dos princípios centrais da aplicação, mantendo compatibilidade com versionamento, indexação por campos, mecanismos de relevância, autenticação e visualização documental

---

**4\. O QUE NÃO FOI ENTREGUE**

Do ponto de vista funcional, não houve itens deixados de fora da sprint, pois todas as features previstas foram implementadas.

Entretanto, a etapa de refinamento fino de desempenho e a eliminacao completa de pequenos bugs remanescentes ainda nao pode ser considerada totalmente concluida.

---

**5\. DIFICULDADES ENCONTRADAS**

Nao houve impedimentos significativos que bloqueassem a entrega das funcionalidades da sprint.

Os cuidados principais estiveram concentrados em garantir consistência entre armazenamento físico, histórico documental, metadados e índice invertido, especialmente nos fluxos de exclusão definitiva e persistência entre reinicializações.

Tambem foi necessario manter os indicadores de desempenho alinhados ao historico real de buscas sem alterar os contratos centrais ja utilizados pelo sistema.

Mesmo com as features implementadas, foram observados alguns comportamentos que ainda demandam melhoria, principalmente pequenos bugs em fluxos especificos e limitacoes de desempenho em determinados cenarios de uso, o que impactou a percepcao de maturidade final da sprint.

---

**6\. COMO AS DIFICULDADES FORAM RESOLVIDAS**

• Evolução incremental dos serviços existentes, evitando refatorações estruturais desnecessárias  
• Implementação de testes específicos para validar persistência do índice entre sessões e limpeza completa após remoção física  
• Reaproveitamento da arquitetura relacional já adotada para o índice invertido, reforçando consistência sem quebrar o modelo da aplicação  
• Integração controlada das métricas ao frontend, mantendo compatibilidade com a API já existente e com os fluxos administrativos do sistema  
• Validação contínua com testes automatizados de serviço, lint, testes do frontend e build de produção  
• Identificacao dos principais pontos de lentidao e dos bugs menores remanescentes, deixando o sistema funcional, mas com necessidade de aprimoramento posterior para atingir um nivel de desempenho mais satisfatorio

---

**7\. AUTOAVALIAÇÃO**

| Critério | Avaliação (1 a 5) |
| :---- | :---- |
| Organização do trabalho | 5 |
| Cumprimento do planejamento | 5 |
| Qualidade da entrega | 4 |
| Colaboração do grupo | 5 |
