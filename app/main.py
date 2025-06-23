from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import graph, narratives, refresh

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(narratives.router, prefix="/api")
app.include_router(graph.router, prefix="/api")
app.include_router(refresh.router, prefix="/api")


@app.get("/health")
async def health():
    """Simple health-check endpoint."""
    return {"status": "ok"}
