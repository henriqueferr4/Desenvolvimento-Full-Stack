ALTER TABLE aposentados  
ALTER COLUMN "Dt ocorrencia inatividade" TYPE DATE 
USING to_date(lpad("Dt ocorrencia inatividade"::text, 8, '0'), 'DDMMYYYY');

ALTER TABLE aposentados 
ALTER COLUMN "Dt ingresso servico publico" TYPE DATE 
USING to_date(lpad("Dt ingresso servico publico"::text, 8, '0'), 'DDMMYYYY');