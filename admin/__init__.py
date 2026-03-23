from aiogram import Router
from . import (
    login,
    reports,
    export,
    config_time,
    config_price,
    payment_methods,
    user_stats
)

admin_router = Router()

admin_router.include_router(login.router)
admin_router.include_router(reports.router)
admin_router.include_router(export.router)
admin_router.include_router(config_time.router)
admin_router.include_router(config_price.router)
admin_router.include_router(payment_methods.router)
admin_router.include_router(user_stats.router)