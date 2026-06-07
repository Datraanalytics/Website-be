from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import Optional, List
from app.database import get_db
from app.schemas import CityData, CityAnalyticsResponse

router = APIRouter(prefix="/api/city-analytics", tags=["City Analytics"])

# Map frontend periods to database periods
PERIOD_MAP = {
    "3M": "3M",
    "6M": "6M",
    "1Y": "12M",
    "12M": "12M",
    "CurrentMonth": "CurrentMonth"
}


@router.get("", response_model=CityAnalyticsResponse)
async def get_city_analytics(
    period: str = Query("6M", description="Time period: 3M, 6M, 1Y"),
    transaction_type: Optional[str] = Query(None, description="Residential or Commercial"),
    state: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Get city-wise analytics"""

    db_period = PERIOD_MAP.get(period, "6M")

    conditions = ["period = :period"]
    params = {"period": db_period}

    if transaction_type:
        conditions.append("transactionType = :transaction_type")
        params["transaction_type"] = transaction_type

    if state:
        conditions.append("state = :state")
        params["state"] = state

    where_clause = " AND ".join(conditions)

    # Get city data from topGainer
    query = text(f"""
        SELECT
            city,
            state,
            SUM(noOfTrans) as total_transactions,
            SUM(compensationInCr) as total_value,
            AVG(weightageAvgValue) as avg_price,
            SUM(chargeableSQFTInMillion) as area_sold
        FROM topGainer
        WHERE {where_clause}
        GROUP BY city, state
        ORDER BY total_value DESC
        LIMIT 50
    """)

    result = await db.execute(query, params)
    rows = result.fetchall()

    cities = [
        CityData(
            city=row.city,
            state=row.state,
            total_transactions=int(row.total_transactions) if row.total_transactions else 0,
            total_value=float(row.total_value) if row.total_value else 0.0,
            avg_price=float(row.avg_price) if row.avg_price else 0.0,
            area_sold=float(row.area_sold) * 1000000 if row.area_sold else 0.0
        )
        for row in rows
    ]

    # Get top gainers - cities with highest average price
    gainers_query = text("""
        SELECT
            city,
            AVG(weightageAvgValue) as avg_price,
            SUM(noOfTrans) as total_transactions
        FROM topGainer
        WHERE period = :period
        GROUP BY city
        ORDER BY avg_price DESC
        LIMIT 10
    """)

    try:
        gainers_result = await db.execute(gainers_query, {"period": db_period})
        gainers_rows = gainers_result.fetchall()
        top_gainers = [
            {
                "city": row.city,
                "price_change": float(row.avg_price) if row.avg_price else 0.0,
                "percent_change": 0.0  # No percent change data available
            }
            for row in gainers_rows
        ]
    except Exception:
        top_gainers = []

    return CityAnalyticsResponse(cities=cities, top_gainers=top_gainers)


@router.get("/ranking")
async def get_city_ranking(
    period: str = Query("6M"),
    sort_by: str = Query("total_value", description="Sort by: total_value, transactions, avg_price"),
    limit: int = Query(20),
    db: AsyncSession = Depends(get_db)
):
    """Get city ranking based on different metrics"""

    db_period = PERIOD_MAP.get(period, "6M")

    valid_sort_fields = {
        "total_value": "total_value DESC",
        "transactions": "total_transactions DESC",
        "avg_price": "avg_price DESC"
    }

    order_by = valid_sort_fields.get(sort_by, "total_value DESC")

    query = text(f"""
        SELECT
            city,
            state,
            SUM(noOfTrans) as total_transactions,
            SUM(compensationInCr) as total_value,
            AVG(weightageAvgValue) as avg_price
        FROM topGainer
        WHERE period = :period
        GROUP BY city, state
        ORDER BY {order_by}
        LIMIT :limit
    """)

    result = await db.execute(query, {"period": db_period, "limit": limit})
    rows = result.fetchall()

    return [
        {
            "rank": idx + 1,
            "city": row.city,
            "state": row.state,
            "total_transactions": int(row.total_transactions) if row.total_transactions else 0,
            "total_value": float(row.total_value) if row.total_value else 0.0,
            "avg_price": float(row.avg_price) if row.avg_price else 0.0
        }
        for idx, row in enumerate(rows)
    ]


@router.get("/comparison")
async def compare_cities(
    cities: str = Query(..., description="Comma-separated city names"),
    period: str = Query("6M"),
    db: AsyncSession = Depends(get_db)
):
    """Compare multiple cities"""

    db_period = PERIOD_MAP.get(period, "6M")

    city_list = [c.strip() for c in cities.split(",")]
    placeholders = ", ".join([f":city_{i}" for i in range(len(city_list))])
    params = {"period": db_period}
    params.update({f"city_{i}": city for i, city in enumerate(city_list)})

    query = text(f"""
        SELECT
            city,
            transactionType,
            SUM(noOfTrans) as transactions,
            SUM(compensationInCr) as value,
            AVG(weightageAvgValue) as avg_price
        FROM topGainer
        WHERE period = :period AND city IN ({placeholders})
        GROUP BY city, transactionType
        ORDER BY city, transactionType
    """)

    result = await db.execute(query, params)
    rows = result.fetchall()

    comparison = {}
    for row in rows:
        if row.city not in comparison:
            comparison[row.city] = {}
        comparison[row.city][row.transactionType] = {
            "transactions": int(row.transactions) if row.transactions else 0,
            "value": float(row.value) if row.value else 0.0,
            "avg_price": float(row.avg_price) if row.avg_price else 0.0
        }

    return comparison


@router.get("/average-price")
async def get_city_average_prices(
    period: str = Query("6M"),
    limit: int = Query(20),
    db: AsyncSession = Depends(get_db)
):
    """Get city average prices from cityAveragePrice"""

    db_period = PERIOD_MAP.get(period, "6M")

    query = text("""
        SELECT
            city,
            state,
            period,
            transactionType,
            avgPrice,
            totalTransactions,
            totalValue
        FROM cityAveragePrice
        WHERE period = :period
        ORDER BY avgPrice DESC
        LIMIT :limit
    """)

    try:
        result = await db.execute(query, {"period": db_period, "limit": limit})
        rows = result.fetchall()

        return [
            {
                "city": row.city,
                "state": row.state,
                "transaction_type": row.transactionType,
                "avg_price": float(row.avgPrice) if row.avgPrice else 0.0,
                "total_transactions": int(row.totalTransactions) if row.totalTransactions else 0,
                "total_value": float(row.totalValue) if row.totalValue else 0.0
            }
            for row in rows
        ]
    except Exception as e:
        return {"error": str(e), "message": "cityAveragePrice table may not exist"}
