from fastapi import FastAPI

from routers.accounts import router as accounts_router
from routers.transactions import router as transactions_router

app = FastAPI(title="Bank Manager API", version="1.0")
app.include_router(accounts_router)
app.include_router(transactions_router)
