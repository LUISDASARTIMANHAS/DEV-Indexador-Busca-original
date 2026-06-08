ALTER TABLE historico_documento
ADD COLUMN IF NOT EXISTS ocr_executado BOOLEAN DEFAULT FALSE NOT NULL;

ALTER TABLE historico_documento
ADD COLUMN IF NOT EXISTS ocr_status VARCHAR(50);

ALTER TABLE historico_documento
ADD COLUMN IF NOT EXISTS ocr_idioma VARCHAR(20);

ALTER TABLE historico_documento
ADD COLUMN IF NOT EXISTS ocr_paginas_processadas INTEGER;

ALTER TABLE historico_documento
ADD COLUMN IF NOT EXISTS ocr_tempo_ms INTEGER;

ALTER TABLE historico_documento
ADD COLUMN IF NOT EXISTS ocr_erro TEXT;

ALTER TABLE historico_documento
ADD COLUMN IF NOT EXISTS ocr_executado_em TIMESTAMP;

CREATE TABLE IF NOT EXISTS historico_ocr (
    cod_ocr BIGSERIAL PRIMARY KEY,
    cod_documento BIGINT NOT NULL,
    cod_historico_documento BIGINT,
    status VARCHAR(50) NOT NULL,
    idioma VARCHAR(20),
    paginas_processadas INTEGER,
    tamanho_texto INTEGER,
    tempo_ms INTEGER,
    erro TEXT,
    executado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_historico_ocr_documento
        FOREIGN KEY (cod_documento)
        REFERENCES documento (cod_documento),
    CONSTRAINT fk_historico_ocr_historico_documento
        FOREIGN KEY (cod_historico_documento)
        REFERENCES historico_documento (cod_historico_documento)
);

CREATE INDEX IF NOT EXISTS idx_historico_ocr_documento
    ON historico_ocr (cod_documento);

CREATE INDEX IF NOT EXISTS idx_historico_ocr_historico_documento
    ON historico_ocr (cod_historico_documento);
