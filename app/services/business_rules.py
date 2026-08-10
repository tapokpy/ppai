from sqlalchemy import or_, select

from app.db import async_session
from app.models import BusinessRule


async def get_active_rules_text(category: str) -> str:
    async with async_session() as session:
        result = await session.execute(
            select(BusinessRule).where(
                BusinessRule.is_active.is_(True),
                or_(BusinessRule.category == category, BusinessRule.category == "general"),
            )
        )
        rules = result.scalars().all()

    if not rules:
        return ""
    return "\n".join(f"- {rule.text}" for rule in rules)
