from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from uvicorn import logging
import core.logger_setup
from routers.admin import router as admin_router
from routers.accounts import router as accounts_router
from routers.statements import router as statements_router
from routers.transactions import router as transactions_router
from utils.exceptions import BankError
logger = core.logger_setup.logger



limiter = Limiter(
    key_func=get_remote_address,  
    default_limits=["200/minute"],
    headers_enabled=True,         
)
app = FastAPI(title="Bank Manager API", version="1.0")

@app.exception_handler(BankError)
async def bank_error_handler(request: Request, exc: BankError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "message": exc.message},
    )

@app.exception_handler(RequestValidationError)
async def validation_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"success": False, "message": "Invalid request data.", "errors": exc.errors()},
    )

@app.exception_handler(Exception)
async def unhandled_handler(request: Request, exc: Exception):
    logger.exception("Unexpected error on %s %s", request.method, request.url)
    return JSONResponse(
        status_code=500,
        content={"success": False, "message": "Internal server error."},
    )
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.include_router(admin_router)
app.include_router(accounts_router)
app.include_router(statements_router)
app.include_router(transactions_router)