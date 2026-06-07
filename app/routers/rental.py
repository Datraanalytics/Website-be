from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import Optional
from app.database import get_db
from app.schemas import RentalCityData, RentalAnalyticsResponse

router = APIRouter(prefix="/api/rental", tags=["Rental Analytics"])

# Map frontend periods to database periods
PERIOD_MAP = {
    "3M": "3M",
    "6M": "6M",
    "1Y": "12M",
    "12M": "12M",
    "CurrentMonth": "CurrentMonth"
}


@router.get("", response_model=RentalAnalyticsResponse)
async def get_rental_analytics(
    city: Optional[str] = Query(None, description="Filter by city"),
    period: str = Query("6M", description="Time period: 3M, 6M, 1Y"),
    db: AsyncSession = Depends(get_db)
):
    """Get rental analytics"""

    db_period = PERIOD_MAP.get(period, "6M")

    conditions = ["period = :period"]
    params = {"period": db_period}

    if city:
        conditions.append("city = :city")
        params["city"] = city

    where_clause = " AND ".join(conditions)

    # Get city-wise rental data
    query = text(f"""
        SELECT
            city,
            state,
            SUM(noOfTrans) as total_transactions,
            AVG(weightageAvgValue) as avg_rent
        FROM cityAveragePriceRent
        WHERE {where_clause}
        GROUP BY city, state
        ORDER BY avg_rent DESC
        LIMIT 50
    """)

    try:
        result = await db.execute(query, params)
        rows = result.fetchall()

        cities = [
            RentalCityData(
                city=row.city,
                avg_rent=float(row.avg_rent) if row.avg_rent else 0.0,
                total_transactions=int(row.total_transactions) if row.total_transactions else 0
            )
            for row in rows
        ]
    except Exception:
        cities = []

    # Get top rental gainers (localities with highest rent)
    gainers_query = text("""
        SELECT
            city,
            locality,
            AVG(weightageAvgValue) as avg_rent,
            SUM(noOfTrans) as total_transactions
        FROM topGainerRent
        WHERE period = :period
        GROUP BY city, locality
        ORDER BY avg_rent DESC
        LIMIT 10
    """)

    try:
        gainers_result = await db.execute(gainers_query, {"period": db_period})
        gainers_rows = gainers_result.fetchall()
        top_gainers = [
            {
                "city": row.city,
                "locality": row.locality,
                "avg_rent": float(row.avg_rent) if row.avg_rent else 0.0,
                "total_transactions": int(row.total_transactions) if row.total_transactions else 0
            }
            for row in gainers_rows
        ]
    except Exception:
        top_gainers = []

    return RentalAnalyticsResponse(cities=cities, top_gainers=top_gainers)


@router.get("/cities")
async def get_rental_by_cities(
    period: str = Query("6M"),
    sort_by: str = Query("avg_rent", description="Sort by: avg_rent, transactions"),
    limit: int = Query(20),
    db: AsyncSession = Depends(get_db)
):
    """Get city-wise rental data"""

    db_period = PERIOD_MAP.get(period, "6M")

    valid_sort_fields = {
        "avg_rent": "avg_rent DESC",
        "transactions": "total_transactions DESC"
    }

    order_by = valid_sort_fields.get(sort_by, "avg_rent DESC")

    query = text(f"""
        SELECT
            city,
            state,
            AVG(weightageAvgValue) as avg_rent,
            SUM(noOfTrans) as total_transactions
        FROM cityAveragePriceRent
        WHERE period = :period
        GROUP BY city, state
        ORDER BY {order_by}
        LIMIT :limit
    """)

    try:
        result = await db.execute(query, {"period": db_period, "limit": limit})
        rows = result.fetchall()

        return [
            {
                "rank": idx + 1,
                "city": row.city,
                "state": row.state,
                "avg_rent": float(row.avg_rent) if row.avg_rent else 0.0,
                "total_transactions": int(row.total_transactions) if row.total_transactions else 0
            }
            for idx, row in enumerate(rows)
        ]
    except Exception as e:
        return {"error": str(e), "message": "cityAveragePriceRent table may not exist"}


@router.get("/top-gainers")
async def get_top_rental_gainers(
    period: str = Query("6M"),
    limit: int = Query(20),
    db: AsyncSession = Depends(get_db)
):
    """Get localities with highest rental values"""

    db_period = PERIOD_MAP.get(period, "6M")

    query = text("""
        SELECT
            city,
            locality,
            AVG(weightageAvgValue) as avg_rent,
            SUM(noOfTrans) as total_transactions
        FROM topGainerRent
        WHERE period = :period
        GROUP BY city, locality
        ORDER BY avg_rent DESC
        LIMIT :limit
    """)

    try:
        result = await db.execute(query, {"period": db_period, "limit": limit})
        rows = result.fetchall()

        return [
            {
                "rank": idx + 1,
                "city": row.city,
                "locality": row.locality,
                "avg_rent": float(row.avg_rent) if row.avg_rent else 0.0,
                "total_transactions": int(row.total_transactions) if row.total_transactions else 0
            }
            for idx, row in enumerate(rows)
        ]
    except Exception as e:
        return {"error": str(e), "message": "topGainerRent table may not exist"}


@router.get("/trends")
async def get_rental_trends(
    city: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Get rental trends across different periods"""

    conditions = []
    params = {}

    if city:
        conditions.append("city = :city")
        params["city"] = city

    where_clause = " AND ".join(conditions) if conditions else "1=1"

    query = text(f"""
        SELECT
            city,
            period,
            AVG(weightageAvgValue) as avg_rent,
            SUM(noOfTrans) as total_transactions
        FROM cityAveragePriceRent
        WHERE {where_clause}
        GROUP BY city, period
        ORDER BY city, period
    """)

    try:
        result = await db.execute(query, params)
        rows = result.fetchall()

        # Group by city
        trends = {}
        for row in rows:
            if row.city not in trends:
                trends[row.city] = {}
            trends[row.city][row.period] = {
                "avg_rent": float(row.avg_rent) if row.avg_rent else 0.0,
                "transactions": int(row.total_transactions) if row.total_transactions else 0
            }

        return trends
    except Exception as e:
        return {"error": str(e)}


@router.get("/yield-analysis")
async def get_rental_yield_analysis(
    period: str = Query("6M"),
    limit: int = Query(20),
    db: AsyncSession = Depends(get_db)
):
    """Get rental yield analysis by comparing rent to property prices"""

    db_period = PERIOD_MAP.get(period, "6M")

    # Get rental data grouped by city
    query = text("""
        SELECT
            city,
            AVG(weightageAvgValue) as avg_rent,
            SUM(noOfTrans) as total_transactions
        FROM cityAveragePriceRent
        WHERE period = :period
        GROUP BY city
        ORDER BY avg_rent DESC
        LIMIT :limit
    """)

    try:
        result = await db.execute(query, {"period": db_period, "limit": limit})
        rows = result.fetchall()

        return [
            {
                "city": row.city,
                "avg_rent": float(row.avg_rent) if row.avg_rent else 0.0,
                "total_transactions": int(row.total_transactions) if row.total_transactions else 0
            }
            for row in rows
        ]
    except Exception as e:
        return {"error": str(e)}
