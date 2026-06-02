BEGIN;

CREATE TABLE IF NOT EXISTS usuario (
    cod_usuario BIGSERIAL PRIMARY KEY,
    nome VARCHAR(255) NOT NULL,
    login VARCHAR(255) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    senha_hash VARCHAR(255) NOT NULL,
    perfil VARCHAR(20) NOT NULL,
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP
);

CREATE TABLE IF NOT EXISTS categoria_documento (
    cod_categoria BIGSERIAL PRIMARY KEY,
    nome_categoria VARCHAR(255) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS status_ingestao (
    cod_status_ingestao BIGSERIAL PRIMARY KEY,
    estado_ingestao VARCHAR(255) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS tipo_campo (
    cod_tipo_campo BIGSERIAL PRIMARY KEY,
    tipo_campo VARCHAR(255) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS calculo_metricas (
    cod_calculo_metricas BIGSERIAL PRIMARY KEY,
    periodo_inicio TIMESTAMP NOT NULL,
    periodo_fim TIMESTAMP NOT NULL,
    total_consultas BIGINT NOT NULL DEFAULT 0,
    tempo_medio_respostas NUMERIC(19, 0) NOT NULL DEFAULT 0,
    media_resultados NUMERIC(19, 0) NOT NULL DEFAULT 0,
    consultas_sem_resultado BIGINT NOT NULL DEFAULT 0,
    calculado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_calculo_metricas_periodo
        CHECK (periodo_fim >= periodo_inicio),
    CONSTRAINT chk_calculo_metricas_total_consultas
        CHECK (total_consultas >= 0),
    CONSTRAINT chk_calculo_metricas_tempo
        CHECK (tempo_medio_respostas >= 0),
    CONSTRAINT chk_calculo_metricas_media_resultados
        CHECK (media_resultados >= 0),
    CONSTRAINT chk_calculo_metricas_sem_resultado
        CHECK (consultas_sem_resultado >= 0)
);

CREATE TABLE IF NOT EXISTS documento (
    cod_documento BIGSERIAL PRIMARY KEY,
    cod_categoria BIGINT NOT NULL,
    titulo VARCHAR(255) NOT NULL,
    tipo VARCHAR(255) NOT NULL,
    data_publicacao TIMESTAMP,
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP,
    cod_usuario_criador BIGINT NOT NULL,
    CONSTRAINT fk_documento_categoria
        FOREIGN KEY (cod_categoria)
        REFERENCES categoria_documento (cod_categoria),
    CONSTRAINT fk_documento_usuario_criador
        FOREIGN KEY (cod_usuario_criador)
        REFERENCES usuario (cod_usuario)
);

CREATE TABLE IF NOT EXISTS documentos_invalidos (
    cod_documentos_invalidos BIGSERIAL PRIMARY KEY,
    cod_usuario BIGINT NOT NULL,
    nome_arquivo VARCHAR(255) NOT NULL,
    motivo_erro VARCHAR(255) NOT NULL,
    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_documentos_invalidos_usuario
        FOREIGN KEY (cod_usuario)
        REFERENCES usuario (cod_usuario)
);

CREATE TABLE IF NOT EXISTS historico_busca (
    cod_historico_busca BIGSERIAL PRIMARY KEY,
    cod_usuario BIGINT NOT NULL,
    consulta_texto TEXT NOT NULL,
    filtros VARCHAR(255),
    quantidade_resultados BIGINT NOT NULL DEFAULT 0,
    tempo_resposta_ms NUMERIC(19, 0) NOT NULL DEFAULT 0,
    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_historico_busca_usuario
        FOREIGN KEY (cod_usuario)
        REFERENCES usuario (cod_usuario),
    CONSTRAINT chk_historico_busca_quantidade_resultados
        CHECK (quantidade_resultados >= 0),
    CONSTRAINT chk_historico_busca_tempo_resposta
        CHECK (tempo_resposta_ms >= 0)
);

CREATE TABLE IF NOT EXISTS acesso_documento (
    cod_acesso_documento BIGSERIAL PRIMARY KEY,
    cod_documento BIGINT NOT NULL,
    cod_usuario BIGINT NOT NULL,
    tipo_acesso VARCHAR(20) NOT NULL,
    origem VARCHAR(80),
    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_acesso_documento_documento
        FOREIGN KEY (cod_documento)
        REFERENCES documento (cod_documento),
    CONSTRAINT fk_acesso_documento_usuario
        FOREIGN KEY (cod_usuario)
        REFERENCES usuario (cod_usuario),
    CONSTRAINT chk_acesso_documento_tipo
        CHECK (tipo_acesso IN ('view', 'download', 'export'))
);

CREATE TABLE IF NOT EXISTS historico_administrativo (
    cod_historico_administrativo BIGSERIAL PRIMARY KEY,
    cod_usuario BIGINT NOT NULL,
    descricao VARCHAR(255) NOT NULL,
    tipo_acao VARCHAR(255) NOT NULL,
    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    entidade_tipo VARCHAR(255) NOT NULL,
    cod_entidade BIGINT NOT NULL,
    CONSTRAINT fk_historico_administrativo_usuario
        FOREIGN KEY (cod_usuario)
        REFERENCES usuario (cod_usuario)
);

CREATE TABLE IF NOT EXISTS notificacao (
    cod_notificacao BIGSERIAL PRIMARY KEY,
    cod_usuario BIGINT NOT NULL,
    titulo VARCHAR(120) NOT NULL,
    mensagem TEXT NOT NULL,
    tipo VARCHAR(30) NOT NULL DEFAULT 'info',
    origem VARCHAR(80) NOT NULL DEFAULT 'ifesdoc',
    lida BOOLEAN NOT NULL DEFAULT FALSE,
    criada_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    lida_em TIMESTAMP,
    chave_dedupe VARCHAR(160),
    CONSTRAINT fk_notificacao_usuario
        FOREIGN KEY (cod_usuario)
        REFERENCES usuario (cod_usuario),
    CONSTRAINT chk_notificacao_tipo
        CHECK (tipo IN ('info', 'success', 'warning', 'error')),
    CONSTRAINT uq_notificacao_usuario_chave_dedupe
        UNIQUE (cod_usuario, chave_dedupe)
);

CREATE TABLE IF NOT EXISTS historico_documento (
    cod_historico_documento BIGSERIAL PRIMARY KEY,
    cod_documento BIGINT NOT NULL,
    cod_usuario BIGINT NOT NULL,
    numero_versao NUMERIC(19, 0) NOT NULL,
    caminho_arquivo VARCHAR(255) NOT NULL,
    nome_arquivo_original VARCHAR(255),
    mime_type VARCHAR(255),
    tamanho_bytes BIGINT,
    hash_arquivo VARCHAR(64),
    texto_extraido TEXT,
    texto_processado TEXT,
    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    versao_ativa BOOLEAN NOT NULL DEFAULT FALSE,
    CONSTRAINT fk_historico_documento_documento
        FOREIGN KEY (cod_documento)
        REFERENCES documento (cod_documento),
    CONSTRAINT fk_historico_documento_usuario
        FOREIGN KEY (cod_usuario)
        REFERENCES usuario (cod_usuario),
    CONSTRAINT uq_historico_documento_versao
        UNIQUE (cod_documento, numero_versao),
    CONSTRAINT chk_historico_documento_numero_versao
        CHECK (numero_versao >= 1)
);

CREATE TABLE IF NOT EXISTS documento_embedding (
    cod_embedding BIGSERIAL PRIMARY KEY,
    cod_documento BIGINT NOT NULL,
    versao_documento BIGINT,
    modelo_embedding VARCHAR(255) NOT NULL,
    embedding JSONB NOT NULL,
    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_documento_embedding_documento
        FOREIGN KEY (cod_documento)
        REFERENCES documento (cod_documento),
    CONSTRAINT uq_documento_embedding_documento_versao_modelo
        UNIQUE (cod_documento, versao_documento, modelo_embedding)
);

CREATE TABLE IF NOT EXISTS documento_metadado (
    cod_documento_metadado BIGSERIAL PRIMARY KEY,
    cod_documento BIGINT NOT NULL,
    autor VARCHAR(255),
    tipo_documento VARCHAR(100),
    nome_arquivo_original VARCHAR(255) NOT NULL,
    mime_type VARCHAR(255) NOT NULL,
    tamanho_bytes BIGINT NOT NULL DEFAULT 0,
    hash_arquivo VARCHAR(64) NOT NULL,
    metadados_extras TEXT,
    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TIMESTAMP,
    CONSTRAINT fk_documento_metadado_documento
        FOREIGN KEY (cod_documento)
        REFERENCES documento (cod_documento),
    CONSTRAINT uq_documento_metadado_documento
        UNIQUE (cod_documento),
    CONSTRAINT chk_documento_metadado_tamanho
        CHECK (tamanho_bytes >= 0)
);

CREATE TABLE IF NOT EXISTS historico_ingestao (
    cod_historico_ingestao BIGSERIAL PRIMARY KEY,
    cod_usuario BIGINT NOT NULL,
    cod_documento BIGINT NOT NULL,
    cod_status_ingestao BIGINT NOT NULL,
    tipo_ingestao VARCHAR(20) NOT NULL,
    mensagem_erro VARCHAR(255),
    tempo_processamento_ms NUMERIC(19, 0),
    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_historico_ingestao_usuario
        FOREIGN KEY (cod_usuario)
        REFERENCES usuario (cod_usuario),
    CONSTRAINT fk_historico_ingestao_documento
        FOREIGN KEY (cod_documento)
        REFERENCES documento (cod_documento),
    CONSTRAINT fk_historico_ingestao_status
        FOREIGN KEY (cod_status_ingestao)
        REFERENCES status_ingestao (cod_status_ingestao),
    CONSTRAINT chk_historico_ingestao_tempo
        CHECK (tempo_processamento_ms IS NULL OR tempo_processamento_ms >= 0)
);

CREATE TABLE IF NOT EXISTS termo (
    cod_termo BIGSERIAL PRIMARY KEY,
    texto_termo VARCHAR(255) NOT NULL UNIQUE,
    df NUMERIC(19, 0) NOT NULL DEFAULT 0,
    idf BIGINT,
    CONSTRAINT chk_termo_df
        CHECK (df >= 0),
    CONSTRAINT chk_termo_idf
        CHECK (idf IS NULL OR idf >= 0)
);

CREATE TABLE IF NOT EXISTS campo_documento (
    cod_campo_documento BIGSERIAL PRIMARY KEY,
    cod_historico_documento BIGINT NOT NULL,
    cod_tipo_campo BIGINT NOT NULL,
    conteudo TEXT NOT NULL,
    CONSTRAINT fk_campo_documento_historico_documento
        FOREIGN KEY (cod_historico_documento)
        REFERENCES historico_documento (cod_historico_documento),
    CONSTRAINT fk_campo_documento_tipo_campo
        FOREIGN KEY (cod_tipo_campo)
        REFERENCES tipo_campo (cod_tipo_campo)
);

CREATE TABLE IF NOT EXISTS historico_indexacao (
    cod_historico_indexacao BIGSERIAL PRIMARY KEY,
    cod_historico_documento BIGINT NOT NULL,
    tempo_indexacao_ms NUMERIC(19, 0) NOT NULL DEFAULT 0,
    mensagem_erro VARCHAR(255),
    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_historico_indexacao_historico_documento
        FOREIGN KEY (cod_historico_documento)
        REFERENCES historico_documento (cod_historico_documento),
    CONSTRAINT chk_historico_indexacao_tempo
        CHECK (tempo_indexacao_ms >= 0)
);

CREATE TABLE IF NOT EXISTS indice_invertido (
    cod_indice_invertido BIGSERIAL PRIMARY KEY,
    cod_termo BIGINT NOT NULL,
    cod_campo_documento BIGINT NOT NULL,
    tf INTEGER NOT NULL,
    posicao_inicial INTEGER NOT NULL,
    CONSTRAINT fk_indice_invertido_termo
        FOREIGN KEY (cod_termo)
        REFERENCES termo (cod_termo),
    CONSTRAINT fk_indice_invertido_campo_documento
        FOREIGN KEY (cod_campo_documento)
        REFERENCES campo_documento (cod_campo_documento),
    CONSTRAINT chk_indice_invertido_tf
        CHECK (tf >= 0),
    CONSTRAINT chk_indice_invertido_posicao
        CHECK (posicao_inicial >= 0)
);

CREATE TABLE IF NOT EXISTS feedback_relevancia (
    cod_feedback_relevancia BIGSERIAL PRIMARY KEY,
    cod_usuario BIGINT NOT NULL,
    cod_historico_busca BIGINT NOT NULL,
    cod_documento BIGINT NOT NULL,
    nota INTEGER,
    comentario VARCHAR(255),
    criado_em TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_feedback_relevancia_usuario
        FOREIGN KEY (cod_usuario)
        REFERENCES usuario (cod_usuario),
    CONSTRAINT fk_feedback_relevancia_historico_busca
        FOREIGN KEY (cod_historico_busca)
        REFERENCES historico_busca (cod_historico_busca),
    CONSTRAINT fk_feedback_relevancia_documento
        FOREIGN KEY (cod_documento)
        REFERENCES documento (cod_documento),
    CONSTRAINT chk_feedback_relevancia_nota
        CHECK (nota IS NULL OR nota BETWEEN 0 AND 10)
);

CREATE INDEX IF NOT EXISTS idx_documento_categoria
    ON documento (cod_categoria);

CREATE INDEX IF NOT EXISTS idx_documento_usuario_criador
    ON documento (cod_usuario_criador);

CREATE INDEX IF NOT EXISTS idx_documentos_invalidos_usuario
    ON documentos_invalidos (cod_usuario);

CREATE INDEX IF NOT EXISTS idx_historico_busca_usuario
    ON historico_busca (cod_usuario);

CREATE INDEX IF NOT EXISTS idx_historico_busca_criado_em
    ON historico_busca (criado_em);

CREATE INDEX IF NOT EXISTS idx_acesso_documento_documento
    ON acesso_documento (cod_documento);

CREATE INDEX IF NOT EXISTS idx_acesso_documento_usuario
    ON acesso_documento (cod_usuario);

CREATE INDEX IF NOT EXISTS idx_acesso_documento_criado_em
    ON acesso_documento (criado_em);

CREATE INDEX IF NOT EXISTS idx_historico_administrativo_usuario
    ON historico_administrativo (cod_usuario);

CREATE INDEX IF NOT EXISTS idx_historico_administrativo_entidade
    ON historico_administrativo (entidade_tipo, cod_entidade);

CREATE INDEX IF NOT EXISTS idx_notificacao_usuario_lida
    ON notificacao (cod_usuario, lida, criada_em);

CREATE INDEX IF NOT EXISTS idx_notificacao_criada_em
    ON notificacao (criada_em);

CREATE INDEX IF NOT EXISTS idx_historico_documento_documento
    ON historico_documento (cod_documento);

CREATE INDEX IF NOT EXISTS idx_historico_documento_usuario
    ON historico_documento (cod_usuario);

CREATE INDEX IF NOT EXISTS idx_documento_embedding_documento
    ON documento_embedding (cod_documento);

CREATE INDEX IF NOT EXISTS idx_documento_embedding_modelo
    ON documento_embedding (modelo_embedding);

CREATE UNIQUE INDEX IF NOT EXISTS uq_historico_documento_versao_ativa
    ON historico_documento (cod_documento)
    WHERE versao_ativa = TRUE;

CREATE INDEX IF NOT EXISTS idx_documento_metadado_autor
    ON documento_metadado (autor);

CREATE INDEX IF NOT EXISTS idx_documento_metadado_tipo
    ON documento_metadado (tipo_documento);

CREATE INDEX IF NOT EXISTS idx_historico_ingestao_usuario
    ON historico_ingestao (cod_usuario);

CREATE INDEX IF NOT EXISTS idx_historico_ingestao_documento
    ON historico_ingestao (cod_documento);

CREATE INDEX IF NOT EXISTS idx_historico_ingestao_status
    ON historico_ingestao (cod_status_ingestao);

CREATE INDEX IF NOT EXISTS idx_campo_documento_historico
    ON campo_documento (cod_historico_documento);

CREATE INDEX IF NOT EXISTS idx_campo_documento_tipo
    ON campo_documento (cod_tipo_campo);

CREATE INDEX IF NOT EXISTS idx_historico_indexacao_historico_documento
    ON historico_indexacao (cod_historico_documento);

CREATE INDEX IF NOT EXISTS idx_indice_invertido_termo
    ON indice_invertido (cod_termo);

CREATE INDEX IF NOT EXISTS idx_indice_invertido_campo
    ON indice_invertido (cod_campo_documento);

CREATE UNIQUE INDEX IF NOT EXISTS uq_indice_invertido_termo_campo_posicao
    ON indice_invertido (cod_termo, cod_campo_documento, posicao_inicial);

CREATE INDEX IF NOT EXISTS idx_feedback_relevancia_usuario
    ON feedback_relevancia (cod_usuario);

CREATE INDEX IF NOT EXISTS idx_feedback_relevancia_historico_busca
    ON feedback_relevancia (cod_historico_busca);

CREATE INDEX IF NOT EXISTS idx_feedback_relevancia_documento
    ON feedback_relevancia (cod_documento);

CREATE INDEX IF NOT EXISTS idx_calculo_metricas_periodo
    ON calculo_metricas (periodo_inicio, periodo_fim);

CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS unaccent;

COMMIT;
