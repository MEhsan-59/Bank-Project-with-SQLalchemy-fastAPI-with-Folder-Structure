from fastapi import FastAPI

from routers.admin import router as admin_router
from routers.accounts import router as accounts_router
from routers.statements import router as statements_router
from routers.transactions import router as transactions_router

app = FastAPI(title="Bank Manager API", version="1.0")
app.include_router(admin_router)
app.include_router(accounts_router)
app.include_router(statements_router)
app.include_router(transactions_router)
