import uuid

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select

from app.db import async_session
from app.models import BusinessRule

router = APIRouter(prefix="/business-rules", tags=["business-rules"])


class RuleCreate(BaseModel):
    category: str
    text: str
    created_by_telegram_id: int


class RuleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    category: str
    text: str
    is_active: bool


@router.post("", response_model=RuleOut)
async def create_rule(payload: RuleCreate) -> RuleOut:
    rule = BusinessRule(
        category=payload.category,
        text=payload.text,
        created_by_telegram_id=payload.created_by_telegram_id,
    )
    async with async_session() as session:
        session.add(rule)
        await session.commit()
        await session.refresh(rule)
    return RuleOut.model_validate(rule)


@router.get("", response_model=list[RuleOut])
async def list_rules(active_only: bool = True) -> list[RuleOut]:
    async with async_session() as session:
        stmt = select(BusinessRule)
        if active_only:
            stmt = stmt.where(BusinessRule.is_active.is_(True))
        result = await session.execute(stmt.order_by(BusinessRule.created_at.desc()))
        rules = result.scalars().all()
    return [RuleOut.model_validate(rule) for rule in rules]


@router.patch("/{rule_id}", response_model=RuleOut)
async def toggle_rule(rule_id: uuid.UUID, is_active: bool) -> RuleOut:
    async with async_session() as session:
        rule = await session.get(BusinessRule, rule_id)
        if rule is None:
            raise HTTPException(status_code=404, detail="Rule not found")
        rule.is_active = is_active
        await session.commit()
        await session.refresh(rule)
    return RuleOut.model_validate(rule)
