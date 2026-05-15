from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status

from exception.auth_exceptions import raise_auth_http_exception

from .dependencies import get_admin_db, get_current_admin_id

router = APIRouter()


@router.get(
    "/dashboard",
    status_code=status.HTTP_200_OK,
    summary="Admin dashboard metrics",
)
async def admin_dashboard(
    _admin_id=Depends(get_current_admin_id),
    connection=Depends(get_admin_db),
):
    try:
        total_users = await connection.fetchval("SELECT COUNT(*) FROM users")
        total_drivers = await connection.fetchval("SELECT COUNT(*) FROM drivers")
        active_rides = await connection.fetchval(
            "SELECT COUNT(*) FROM rides WHERE status IN ('requested', 'offered', 'accepted', 'in_progress')"
        )
        completed_rides = await connection.fetchval(
            "SELECT COUNT(*) FROM rides WHERE status = 'completed'"
        )
        total_revenue = await connection.fetchval(
            "SELECT COALESCE(SUM(amount), 0) FROM payments WHERE status = 'completed'"
        )
        failed_payments = await connection.fetchval(
            "SELECT COUNT(*) FROM payments WHERE status = 'failed'"
        )
        return {
            "total_users": int(total_users or 0),
            "total_drivers": int(total_drivers or 0),
            "active_rides": int(active_rides or 0),
            "completed_rides": int(completed_rides or 0),
            "total_revenue": str(total_revenue or 0),
            "failed_payments": int(failed_payments or 0),
        }
    except Exception as exc:
        raise_auth_http_exception(exc)


@router.get(
    "/rides",
    status_code=status.HTTP_200_OK,
    summary="Admin rides list",
)
async def admin_rides(
    _admin_id=Depends(get_current_admin_id),
    connection=Depends(get_admin_db),
    limit: int = Query(default=50, ge=1, le=200),
):
    try:
        rows = await connection.fetch(
            """
            SELECT id, rider_id, driver_id, status, origin, destination, fare, created_at, updated_at
            FROM rides
            ORDER BY created_at DESC
            LIMIT $1
            """,
            limit,
        )
        return {"rides": [dict(row) for row in rows], "count": len(rows)}
    except Exception as exc:
        raise_auth_http_exception(exc)


@router.get(
    "/users",
    status_code=status.HTTP_200_OK,
    summary="Admin users list",
)
async def admin_users(
    _admin_id=Depends(get_current_admin_id),
    connection=Depends(get_admin_db),
    limit: int = Query(default=50, ge=1, le=200),
):
    try:
        rows = await connection.fetch(
            """
            SELECT id, full_name, email, role, created_at, updated_at
            FROM users
            ORDER BY created_at DESC
            LIMIT $1
            """,
            limit,
        )
        return {"users": [dict(row) for row in rows], "count": len(rows)}
    except Exception as exc:
        raise_auth_http_exception(exc)
