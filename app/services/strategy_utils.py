from typing import Dict, Any, List
from datetime import datetime
import json


def serialize_strategy_rules(rules: Dict[str, Any]) -> str:
    """Serializar reglas a JSON string"""
    return json.dumps(rules, default=str)


def deserialize_strategy_rules(rules_json: str) -> Dict[str, Any]:
    """Deserializar reglas desde JSON string"""
    try:
        return json.loads(rules_json)
    except (json.JSONDecodeError, TypeError):
        return {}


def validate_entry_conditions(entry_rules: Dict[str, Any], market_data: Dict[str, Any]) -> bool:
    """Validar si se cumplen las condiciones de entrada"""
    # Esta función se expandirá más adelante con lógica de indicadores
    if not entry_rules.get("conditions"):
        return False
    
    # Placeholder para validación básica
    return True


def validate_exit_conditions(exit_rules: Dict[str, Any], position_data: Dict[str, Any]) -> bool:
    """Validar si se cumplen las condiciones de salida"""
    # Esta función se expandirá más adelante
    return False


def calculate_position_size(sizing_config: Dict[str, Any], account_balance: float, price: float) -> float:
    """Calcular tamaño de posición según configuración"""
    if sizing_config.get("type") == "fixed":
        amount = sizing_config.get("amount", 0)
        return amount / price if price > 0 else 0
    
    elif sizing_config.get("type") == "percentage":
        percentage = sizing_config.get("percentage", 0)
        amount = account_balance * (percentage / 100)
        return amount / price if price > 0 else 0
    
    return 0
