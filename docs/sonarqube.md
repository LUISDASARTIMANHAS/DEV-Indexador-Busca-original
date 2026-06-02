# SonarQube no IFESDOC

Este projeto foi preparado para usar o SonarQube como parte do fluxo de desenvolvimento local e da futura automacao de CI.

## O que foi configurado

- `docker/docker-compose.yml`: sobe o SonarQube e um PostgreSQL dedicado para a ferramenta.
- `sonar-project.properties`: define escopo de analise para backend Python e frontend React/TypeScript.
- `scripts/sonar/run-analysis.sh`: gera cobertura e executa o scanner em sequencia.

## Servicos adicionados

Ao subir o compose em `docker/`, o ambiente passa a ter:

- `postgres`: banco principal do sistema.
- `sonarqube_db`: banco exclusivo do SonarQube.
- `sonarqube`: interface e servidor de analise na porta `9000`.

Portas publicadas no host por padrao:

- banco principal: `localhost:55433`
- banco do SonarQube: `localhost:55434`
- SonarQube: `localhost:9000`

Se alguma porta ja estiver ocupada, ajuste no arquivo `.env` da raiz:

```env
IFESDOC_POSTGRES_PORT=55433
IFESDOC_SONAR_POSTGRES_PORT=55434
```

Isso altera apenas a porta exposta na sua maquina. Entre containers, o acesso continua sendo feito pelos hosts `postgres` e `sonarqube_db` na porta interna `5432`.

## Como subir

Defina `SECRET_KEY` no `.env` da raiz com um valor aleatorio de pelo menos 32
caracteres e `INITIAL_ADMIN_PASSWORD` com uma senha inicial forte de pelo
menos 12 caracteres antes de iniciar os containers.

```bash
docker compose -f docker/docker-compose.yml up -d
```

Depois acompanhe o bootstrap:

```bash
docker compose -f docker/docker-compose.yml ps
docker compose -f docker/docker-compose.yml logs -f sonarqube
```

A interface fica em `http://localhost:9000`.

## Primeiro acesso

Credenciais padrao:

- usuario: `admin`
- senha: `admin`

No primeiro login, altere a senha e crie um token em:

`My Account` > `Security` > `Generate Tokens`

Exporte as variaveis antes de rodar o scanner:

```bash
export SONAR_HOST_URL=http://localhost:9000
export SONAR_TOKEN=seu_token
```

## Pre-requisitos locais

Para o script de analise funcionar, o ambiente precisa ter:

- `pytest`
- dependencias Python instaladas a partir de `requirements.txt`
- dependencias do frontend instaladas em `interface-web/`
- `sonar-scanner` no PATH
- provider de cobertura do Vitest instalado

Para o frontend, use:

```bash
cd interface-web
npm install
npm install -D @vitest/coverage-v8
```

## Rodando a analise

Da raiz do repositorio:

```bash
bash scripts/sonar/run-analysis.sh
```

O fluxo faz:

1. gera `reports/coverage/backend-coverage.xml`
2. gera `reports/coverage/frontend/lcov.info`
3. executa `sonar-scanner` com `sonar-project.properties`

## Recomendacao para o processo de desenvolvimento

Use o SonarQube em tres momentos:

1. antes de merge para validar bugs, code smells e hotspots
2. em pipeline de CI para bloquear regressao de qualidade
3. periodicamente no time para acompanhar divida tecnica e cobertura

## Exemplo de etapa para CI

O repositorio agora possui pipeline pronta em:

- `.github/workflows/ci.yml`

Ela executa:

1. testes Python com cobertura
2. lint, testes com cobertura e build do frontend
3. upload dos artefatos de cobertura
4. scan do SonarQube
5. validacao de Quality Gate

Para funcionar no GitHub Actions, configure os secrets do repositorio:

- `SONAR_HOST_URL`
- `SONAR_TOKEN`

Importante:

- se o SonarQube estiver apenas na sua maquina local em `http://localhost:9000`, o runner hospedado do GitHub nao vai conseguir acessar
- para CI remota funcionar, o SonarQube precisa estar exposto para a internet com seguranca adequada, ou voces precisam usar um runner self-hosted na mesma rede do servidor

Fluxo executado pela pipeline:

```bash
pip install -r requirements.txt
cd interface-web
npm ci
npm install --no-save -D @vitest/coverage-v8
npm run lint
npm run test:coverage
npm run build
cd ..
pytest backend/tests backend/pipeline_indexador/src/tests --cov=backend/app --cov=backend/pipeline_busca/src --cov=backend/pipeline_indexador/src --cov-report=xml:reports/coverage/backend-coverage.xml
sonar-scanner
```

## Observacoes operacionais

- O SonarQube usa Elasticsearch internamente; em Linux, o host precisa ter `vm.max_map_count` maior ou igual a `262144`.
- Neste ambiente, a validacao real do bootstrap mostrou `vm.max_map_count=65530`, o que impede a subida completa do SonarQube.
- Ajuste temporario:

```bash
sudo sysctl -w vm.max_map_count=262144
```

- Ajuste persistente:

```bash
echo "vm.max_map_count=262144" | sudo tee /etc/sysctl.d/99-sonarqube.conf
sudo sysctl --system
```

- Componentes de UI compartilhados em `interface-web/src/components/ui/` foram excluidos da duplicacao e da maior parte do ruido de analise, porque sao wrappers utilitarios e tendem a gerar falso positivo.
