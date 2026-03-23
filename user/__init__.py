"""
User Package Initialization
Aggregates all routers from sub-modules.
"""
from aiogram import Router

from .start import router as start_router
from .submit import router as submit_router
from .reports import router as reports_router
from .payment import router as payment_router
from .manual import router as manual_router

user_router = Router(name="user_router")

user_router.include_router(start_router)
user_router.include_router(submit_router)
user_router.include_router(reports_router)
user_router.include_router(payment_router)
user_router.include_router(manual_router)