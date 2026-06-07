from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import Optional
from app.database import get_db
from app.schemas import ProjectData, ProjectAnalyticsResponse

router = APIRouter(prefix="/api/projects", tags=["Project Analytics"])


@router.get("", response_model=ProjectAnalyticsResponse)
async def get_project_analytics(
    city: Optional[str] = Query(None, description="Filter by city"),
    developer: Optional[str] = Query(None, description="Filter by developer"),
    period: str = Query("6M", description="Time period: 3M, 6M, 1Y"),
    db: AsyncSession = Depends(get_db)
):
    """Get project analytics"""

    conditions = ["period = :period"]
    params = {"period": period}

    if city:
        conditions.append("city = :city")
        params["city"] = city

    if developer:
        conditions.append("developer = :developer")
        params["developer"] = developer

    where_clause = " AND ".join(conditions)

    query = text(f"""
        SELECT
            project,
            developer,
            city,
            locality,
            SUM(totalTransactions) as total_transactions,
            AVG(priceChange) as price_change,
            AVG(percentChange) as percent_change
        FROM topGainerByProject
        WHERE {where_clause}
        GROUP BY project, developer, city, locality
        ORDER BY percent_change DESC
        LIMIT 50
    """)

    try:
        result = await db.execute(query, params)
        rows = result.fetchall()

        projects = [
            ProjectData(
                project=row.project,
                developer=row.developer,
                city=row.city,
                locality=row.locality,
                total_transactions=int(row.total_transactions) if row.total_transactions else 0,
                price_change=float(row.price_change) if row.price_change else 0.0,
                percent_change=float(row.percent_change) if row.percent_change else 0.0
            )
            for row in rows
        ]

        return ProjectAnalyticsResponse(projects=projects)
    except Exception as e:
        return ProjectAnalyticsResponse(projects=[])


@router.get("/top-gainers")
async def get_top_gaining_projects(
    city: Optional[str] = Query(None),
    period: str = Query("6M"),
    limit: int = Query(20),
    db: AsyncSession = Depends(get_db)
):
    """Get top gaining projects by price appreciation"""

    conditions = ["period = :period"]
    params = {"period": period, "limit": limit}

    if city:
        conditions.append("city = :city")
        params["city"] = city

    where_clause = " AND ".join(conditions)

    query = text(f"""
        SELECT
            project,
            developer,
            city,
            locality,
            totalTransactions as transactions,
            priceChange as price_change,
            percentChange as percent_change
        FROM topGainerByProject
        WHERE {where_clause}
        ORDER BY percentChange DESC
        LIMIT :limit
    """)

    try:
        result = await db.execute(query, params)
        rows = result.fetchall()

        return [
            {
                "rank": idx + 1,
                "project": row.project,
                "developer": row.developer,
                "city": row.city,
                "locality": row.locality,
                "transactions": int(row.transactions) if row.transactions else 0,
                "price_change": float(row.price_change) if row.price_change else 0.0,
                "percent_change": float(row.percent_change) if row.percent_change else 0.0
            }
            for idx, row in enumerate(rows)
        ]
    except Exception as e:
        return {"error": str(e), "message": "topGainerByProject table may not exist"}


@router.get("/by-developer")
async def get_projects_by_developer(
    developer: str = Query(...),
    period: str = Query("6M"),
    db: AsyncSession = Depends(get_db)
):
    """Get all projects by a specific developer"""

    query = text("""
        SELECT
            project,
            city,
            locality,
            totalTransactions as transactions,
            priceChange as price_change,
            percentChange as percent_change
        FROM topGainerByProject
        WHERE developer = :developer AND period = :period
        ORDER BY percentChange DESC
    """)

    try:
        result = await db.execute(query, {"developer": developer, "period": period})
        rows = result.fetchall()

        return [
            {
                "project": row.project,
                "city": row.city,
                "locality": row.locality,
                "transactions": int(row.transactions) if row.transactions else 0,
                "price_change": float(row.price_change) if row.price_change else 0.0,
                "percent_change": float(row.percent_change) if row.percent_change else 0.0
            }
            for row in rows
        ]
    except Exception as e:
        return {"error": str(e)}


@router.get("/by-locality")
async def get_projects_by_locality(
    city: str = Query(...),
    locality: str = Query(...),
    period: str = Query("6M"),
    db: AsyncSession = Depends(get_db)
):
    """Get all projects in a specific locality"""

    query = text("""
        SELECT
            project,
            developer,
            totalTransactions as transactions,
            priceChange as price_change,
            percentChange as percent_change
        FROM topGainerByProject
        WHERE city = :city AND locality = :locality AND period = :period
        ORDER BY percentChange DESC
    """)

    try:
        result = await db.execute(query, {"city": city, "locality": locality, "period": period})
        rows = result.fetchall()

        return [
            {
                "project": row.project,
                "developer": row.developer,
                "transactions": int(row.transactions) if row.transactions else 0,
                "price_change": float(row.price_change) if row.price_change else 0.0,
                "percent_change": float(row.percent_change) if row.percent_change else 0.0
            }
            for row in rows
        ]
    except Exception as e:
        return {"error": str(e)}


@router.get("/transaction-volume")
async def get_projects_by_transaction_volume(
    city: Optional[str] = Query(None),
    period: str = Query("6M"),
    limit: int = Query(20),
    db: AsyncSession = Depends(get_db)
):
    """Get projects sorted by transaction volume"""

    conditions = ["period = :period"]
    params = {"period": period, "limit": limit}

    if city:
        conditions.append("city = :city")
        params["city"] = city

    where_clause = " AND ".join(conditions)

    query = text(f"""
        SELECT
            project,
            developer,
            city,
            locality,
            totalTransactions as transactions,
            priceChange as price_change,
            percentChange as percent_change
        FROM topGainerByProject
        WHERE {where_clause}
        ORDER BY totalTransactions DESC
        LIMIT :limit
    """)

    try:
        result = await db.execute(query, params)
        rows = result.fetchall()

        return [
            {
                "rank": idx + 1,
                "project": row.project,
                "developer": row.developer,
                "city": row.city,
                "locality": row.locality,
                "transactions": int(row.transactions) if row.transactions else 0,
                "price_change": float(row.price_change) if row.price_change else 0.0,
                "percent_change": float(row.percent_change) if row.percent_change else 0.0
            }
            for idx, row in enumerate(rows)
        ]
    except Exception as e:
        return {"error": str(e)}
