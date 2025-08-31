-- Crear tabla strategy_exit_rules
CREATE TABLE strategy_exit_rules (
    id VARCHAR(50) PRIMARY KEY,
    stop_loss_pct FLOAT NOT NULL DEFAULT 0.02,
    take_profit_pct FLOAT NOT NULL DEFAULT 0.04,
    trailing_stop_pct FLOAT NOT NULL DEFAULT 0.015,
    use_trailing BOOLEAN NOT NULL DEFAULT TRUE,
    risk_reward_ratio FLOAT NOT NULL DEFAULT 2.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Índices para performance
CREATE INDEX idx_strategy_exit_rules_id ON strategy_exit_rules(id);

-- Insertar reglas por defecto para estrategias existentes
INSERT INTO strategy_exit_rules (id) 
SELECT DISTINCT strategy_id FROM signals 
WHERE strategy_id NOT IN (SELECT id FROM strategy_exit_rules);
