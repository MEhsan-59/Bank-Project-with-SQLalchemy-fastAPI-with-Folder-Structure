from fastapi import FastAPI

from routers.accounts import router as accounts_router

app = FastAPI(title="Bank Manager API", version="1.0")
app.include_router(accounts_router)
