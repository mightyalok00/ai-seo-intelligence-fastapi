from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import router
BASE_DIR = Path(__file__).resolve().parents[1]
FRONTEND_DIR = BASE_DIR / "frontend"


app = FastAPI(
    title="AI SEO Intelligence API",
    version="2.0.0",
    description=(
        "A strict, deterministic 100-point SEO audit API with 16 weighted "
        "categories, ML search-intent prediction and content-gap analysis. "
        "The audit score is not a Google ranking score."
    ),
)

app.include_router(router, prefix="/api", tags=["SEO Intelligence"])
app.mount(
    "/static",
    StaticFiles(directory=FRONTEND_DIR / "static"),
    name="static",
)


@app.get("/", include_in_schema=False)
def home():
    return FileResponse(FRONTEND_DIR / "templates" / "index.html")
