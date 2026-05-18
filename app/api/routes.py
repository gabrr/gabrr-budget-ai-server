import logging

from fastapi import APIRouter

from app.api.agents_routes import agents_router
from app.api.categories_routes import categories_router
from app.api.import_jobs_routes import import_jobs_router
from app.api.transactions_routes import transactions_router

router = APIRouter()
logger = logging.getLogger(__name__)

router.include_router(categories_router)
router.include_router(transactions_router)
router.include_router(agents_router)
router.include_router(import_jobs_router)
