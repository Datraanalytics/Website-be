from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from pydantic import BaseModel, EmailStr
from typing import List, Optional
from app.database import get_db

router = APIRouter(prefix="/api/demo", tags=["Demo Requests"])


class DemoRequest(BaseModel):
    full_name: str
    company: str
    email: EmailStr
    phone: str
    designation: Optional[str] = None
    company_size: Optional[str] = None
    services: List[str]
    message: Optional[str] = None


@router.post("/request")
async def submit_demo_request(
    request: DemoRequest,
    db: AsyncSession = Depends(get_db)
):
    """Submit a demo request"""

    try:
        # Convert services list to JSON string
        import json
        services_json = json.dumps(request.services)

        query = text("""
            INSERT INTO demo_requests
            (full_name, company, email, phone, designation, company_size, services, message)
            VALUES (:full_name, :company, :email, :phone, :designation, :company_size, :services, :message)
        """)

        await db.execute(query, {
            "full_name": request.full_name,
            "company": request.company,
            "email": request.email,
            "phone": request.phone,
            "designation": request.designation,
            "company_size": request.company_size,
            "services": services_json,
            "message": request.message
        })
        await db.commit()

        return {"success": True, "message": "Demo request submitted successfully"}

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to submit request: {str(e)}")


@router.get("/requests")
async def get_demo_requests(db: AsyncSession = Depends(get_db)):
    """Get all demo requests (admin endpoint)"""

    try:
        query = text("""
            SELECT id, full_name, company, email, phone, designation,
                   company_size, services, message, created_at
            FROM demo_requests
            ORDER BY created_at DESC
        """)

        result = await db.execute(query)
        rows = result.fetchall()

        import json
        return [
            {
                "id": row.id,
                "full_name": row.full_name,
                "company": row.company,
                "email": row.email,
                "phone": row.phone,
                "designation": row.designation,
                "company_size": row.company_size,
                "services": json.loads(row.services) if row.services else [],
                "message": row.message,
                "created_at": row.created_at.isoformat() if row.created_at else None
            }
            for row in rows
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch requests: {str(e)}")
