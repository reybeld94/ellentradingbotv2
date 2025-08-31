from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.core.auth import get_current_verified_user
from app.services.exit_rules_service import ExitRulesService
from app.models.strategy_exit_rules import StrategyExitRules
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


# Schemas de request/response
class ExitRulesCreate(BaseModel):
    strategy_id: str = Field(..., min_length=1, max_length=50)
    stop_loss_pct: float = Field(0.02, ge=0.001, le=0.5, description="Stop loss percentage (0.02 = 2%)")
    take_profit_pct: float = Field(0.04, ge=0.001, le=1.0, description="Take profit percentage (0.04 = 4%)")
    trailing_stop_pct: float = Field(0.015, ge=0.001, le=0.5, description="Trailing stop percentage (0.015 = 1.5%)")
    use_trailing: bool = Field(True, description="Enable trailing stop")
    risk_reward_ratio: float = Field(2.0, ge=0.5, le=10.0, description="Risk/reward ratio")


class ExitRulesUpdate(BaseModel):
    stop_loss_pct: Optional[float] = Field(None, ge=0.001, le=0.5)
    take_profit_pct: Optional[float] = Field(None, ge=0.001, le=1.0)
    trailing_stop_pct: Optional[float] = Field(None, ge=0.001, le=0.5)
    use_trailing: Optional[bool] = None
    risk_reward_ratio: Optional[float] = Field(None, ge=0.5, le=10.0)


class ExitRulesResponse(BaseModel):
    strategy_id: str
    stop_loss_pct: float
    take_profit_pct: float
    trailing_stop_pct: float
    use_trailing: bool
    risk_reward_ratio: float
    created_at: str
    updated_at: str


class PriceCalculationRequest(BaseModel):
    entry_price: float = Field(..., gt=0, description="Entry price for calculation")
    side: str = Field("buy", pattern="^(buy|sell)$", description="Order side")


class PriceCalculationResponse(BaseModel):
    strategy_id: str
    entry_price: float
    stop_loss_price: float
    take_profit_price: float
    rules: Dict[str, Any]


@router.get("/{strategy_id}", response_model=ExitRulesResponse)
async def get_exit_rules(
    strategy_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    """Obtener reglas de salida para una estrategia específica"""
    try:
        service = ExitRulesService(db)
        rules = service.get_rules(strategy_id)
        
        return ExitRulesResponse(
            strategy_id=rules.id,
            stop_loss_pct=rules.stop_loss_pct,
            take_profit_pct=rules.take_profit_pct,
            trailing_stop_pct=rules.trailing_stop_pct,
            use_trailing=rules.use_trailing,
            risk_reward_ratio=rules.risk_reward_ratio,
            created_at=rules.created_at.isoformat(),
            updated_at=rules.updated_at.isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error getting exit rules for {strategy_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get exit rules: {str(e)}")


@router.put("/{strategy_id}", response_model=ExitRulesResponse)
async def update_exit_rules(
    strategy_id: str,
    rules_update: ExitRulesUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    """Actualizar reglas de salida para una estrategia"""
    try:
        service = ExitRulesService(db)
        
        # Filtrar solo campos no None
        update_data = {k: v for k, v in rules_update.dict().items() if v is not None}
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No fields provided for update")
        
        updated_rules = service.update_rules(strategy_id, **update_data)
        
        logger.info(f"Updated exit rules for {strategy_id}: {update_data}")
        
        return ExitRulesResponse(
            strategy_id=updated_rules.id,
            stop_loss_pct=updated_rules.stop_loss_pct,
            take_profit_pct=updated_rules.take_profit_pct,
            trailing_stop_pct=updated_rules.trailing_stop_pct,
            use_trailing=updated_rules.use_trailing,
            risk_reward_ratio=updated_rules.risk_reward_ratio,
            created_at=updated_rules.created_at.isoformat(),
            updated_at=updated_rules.updated_at.isoformat()
        )
        
    except Exception as e:
        logger.error(f"Error updating exit rules for {strategy_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update exit rules: {str(e)}")


@router.post("/{strategy_id}", response_model=ExitRulesResponse)
async def create_exit_rules(
    strategy_id: str,
    rules_create: ExitRulesCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    """Crear reglas de salida para una estrategia (forzar creación con valores específicos)"""
    try:
        service = ExitRulesService(db)
        
        # Verificar si ya existen reglas
        existing = db.query(StrategyExitRules).filter(StrategyExitRules.id == strategy_id).first()
        if existing:
            raise HTTPException(status_code=409, detail=f"Exit rules already exist for strategy {strategy_id}")
        
        # Crear nuevas reglas
        new_rules = StrategyExitRules(
            id=strategy_id,
            stop_loss_pct=rules_create.stop_loss_pct,
            take_profit_pct=rules_create.take_profit_pct,
            trailing_stop_pct=rules_create.trailing_stop_pct,
            use_trailing=rules_create.use_trailing,
            risk_reward_ratio=rules_create.risk_reward_ratio
        )
        
        db.add(new_rules)
        db.commit()
        db.refresh(new_rules)
        
        logger.info(f"Created exit rules for {strategy_id}")
        
        return ExitRulesResponse(
            strategy_id=new_rules.id,
            stop_loss_pct=new_rules.stop_loss_pct,
            take_profit_pct=new_rules.take_profit_pct,
            trailing_stop_pct=new_rules.trailing_stop_pct,
            use_trailing=new_rules.use_trailing,
            risk_reward_ratio=new_rules.risk_reward_ratio,
            created_at=new_rules.created_at.isoformat(),
            updated_at=new_rules.updated_at.isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating exit rules for {strategy_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create exit rules: {str(e)}")


@router.get("", response_model=List[ExitRulesResponse])
async def list_all_exit_rules(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    """Listar todas las reglas de salida configuradas"""
    try:
        service = ExitRulesService(db)
        all_rules = service.get_all_rules()
        
        return [
            ExitRulesResponse(
                strategy_id=rules.id,
                stop_loss_pct=rules.stop_loss_pct,
                take_profit_pct=rules.take_profit_pct,
                trailing_stop_pct=rules.trailing_stop_pct,
                use_trailing=rules.use_trailing,
                risk_reward_ratio=rules.risk_reward_ratio,
                created_at=rules.created_at.isoformat(),
                updated_at=rules.updated_at.isoformat()
            )
            for rules in all_rules
        ]
        
    except Exception as e:
        logger.error(f"Error listing exit rules: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list exit rules: {str(e)}")


@router.post("/{strategy_id}/calculate", response_model=PriceCalculationResponse)
async def calculate_exit_prices(
    strategy_id: str,
    calculation_request: PriceCalculationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    """Calcular precios de salida para una entrada específica (para testing/preview)"""
    try:
        service = ExitRulesService(db)
        result = service.calculate_exit_prices(
            strategy_id,
            Decimal(str(calculation_request.entry_price)),
            calculation_request.side
        )
        
        return PriceCalculationResponse(**result)
        
    except Exception as e:
        logger.error(f"Error calculating exit prices for {strategy_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to calculate exit prices: {str(e)}")


@router.delete("/{strategy_id}")
async def delete_exit_rules(
    strategy_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    """Eliminar reglas de salida para una estrategia"""
    try:
        service = ExitRulesService(db)
        deleted = service.delete_rules(strategy_id)
        
        if not deleted:
            raise HTTPException(status_code=404, detail=f"Exit rules not found for strategy {strategy_id}")
        
        logger.info(f"Deleted exit rules for {strategy_id}")
        
        return {"message": f"Exit rules deleted for strategy {strategy_id}"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting exit rules for {strategy_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete exit rules: {str(e)}")


@router.get("/{strategy_id}/test")
async def test_exit_rules(
    strategy_id: str,
    entry_price: float = Query(..., gt=0, description="Test entry price"),
    side: str = Query("buy", pattern="^(buy|sell)$", description="Test side"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_verified_user)
):
    """Endpoint de testing para probar cálculos de salida"""
    try:
        service = ExitRulesService(db)
        result = service.calculate_exit_prices(strategy_id, Decimal(str(entry_price)), side)
        
        return {
            "test_scenario": {
                "strategy_id": strategy_id,
                "entry_price": entry_price,
                "side": side
            },
            "calculated_exits": result,
            "profit_loss_scenarios": {
                "max_loss": (result["entry_price"] - result["stop_loss_price"]) if side == "buy" else (result["stop_loss_price"] - result["entry_price"]),
                "max_profit": (result["take_profit_price"] - result["entry_price"]) if side == "buy" else (result["entry_price"] - result["take_profit_price"]),
            }
        }
        
    except Exception as e:
        logger.error(f"Error testing exit rules for {strategy_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to test exit rules: {str(e)}")
