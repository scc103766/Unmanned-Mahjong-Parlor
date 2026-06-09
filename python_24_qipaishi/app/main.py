from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.tags import OPENAPI_TAGS
from app.api.v1.routers import (
    analytics,
    auth,
    availability,
    cleaning,
    coupons,
    devices,
    group_buy,
    health,
    me,
    members,
    meta,
    operations,
    orders,
    payments,
    pricing,
    rooms,
    stores,
    tenancy,
    users,
    wallets,
    withdrawals,
)
from app.core.config import Settings, get_settings
from app.core.errors import register_exception_handlers
from app.core.logging import setup_logging
from app.core.middleware import RequestIdMiddleware


def create_app(settings: Optional[Settings] = None) -> FastAPI:
    settings = settings or get_settings()
    setup_logging(settings.log_level)

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        openapi_tags=OPENAPI_TAGS,
    )
    app.state.settings = settings

    app.add_middleware(RequestIdMiddleware)

    if settings.cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    register_exception_handlers(app)
    app.include_router(health.router, tags=["health"])
    app.include_router(me.router, prefix=settings.api_v1_prefix, tags=["auth"])
    app.include_router(auth.router, prefix=f"{settings.api_v1_prefix}/auth", tags=["auth"])
    app.include_router(meta.router, prefix=f"{settings.api_v1_prefix}/meta", tags=["meta"])
    app.include_router(
        members.router,
        prefix=f"{settings.api_v1_prefix}/members",
        tags=["members"],
    )
    app.include_router(tenancy.router, prefix=f"{settings.api_v1_prefix}/tenants", tags=["tenancy"])
    app.include_router(users.roles_router, prefix=f"{settings.api_v1_prefix}/roles", tags=["auth"])
    app.include_router(users.users_router, prefix=f"{settings.api_v1_prefix}/users", tags=["auth"])
    app.include_router(stores.router, prefix=f"{settings.api_v1_prefix}/stores", tags=["stores"])
    app.include_router(rooms.router, prefix=f"{settings.api_v1_prefix}/rooms", tags=["rooms"])
    app.include_router(
        availability.router,
        prefix=f"{settings.api_v1_prefix}/availability",
        tags=["availability"],
    )
    app.include_router(pricing.router, prefix=f"{settings.api_v1_prefix}/pricing", tags=["pricing"])
    app.include_router(orders.router, prefix=f"{settings.api_v1_prefix}/orders", tags=["orders"])
    app.include_router(
        payments.router,
        prefix=f"{settings.api_v1_prefix}/payments",
        tags=["payments"],
    )
    app.include_router(
        wallets.router,
        prefix=f"{settings.api_v1_prefix}/wallets",
        tags=["payments"],
    )
    app.include_router(
        withdrawals.router,
        prefix=f"{settings.api_v1_prefix}/withdrawals",
        tags=["payments"],
    )
    app.include_router(
        coupons.templates_router,
        prefix=f"{settings.api_v1_prefix}/coupon-templates",
        tags=["payments"],
    )
    app.include_router(
        coupons.coupons_router,
        prefix=f"{settings.api_v1_prefix}/coupons",
        tags=["payments"],
    )
    app.include_router(
        group_buy.router,
        prefix=f"{settings.api_v1_prefix}/group-buy",
        tags=["payments"],
    )
    app.include_router(devices.router, prefix=f"{settings.api_v1_prefix}/devices", tags=["devices"])
    app.include_router(
        devices.commands_router,
        prefix=f"{settings.api_v1_prefix}/device-commands",
        tags=["devices"],
    )
    app.include_router(
        cleaning.router,
        prefix=f"{settings.api_v1_prefix}/cleaning",
        tags=["cleaning"],
    )
    app.include_router(
        analytics.router,
        prefix=f"{settings.api_v1_prefix}/analytics",
        tags=["analytics"],
    )
    app.include_router(
        operations.router,
        prefix=f"{settings.api_v1_prefix}/operations",
        tags=["audit"],
    )
    return app


app = create_app()
