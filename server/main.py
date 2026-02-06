"""
GreenScreen Bet Generator - FastAPI Backend
"""

import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from video_engine import generate_video

app = FastAPI(title="GreenScreen Bet Generator", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve React static build if available
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
if os.path.isdir(STATIC_DIR):
    app.mount("/assets", StaticFiles(directory=os.path.join(STATIC_DIR, "assets")), name="assets")


class VideoRequest(BaseModel):
    home_team: str = Field(..., min_length=1, max_length=100, examples=["Flamengo"])
    away_team: str = Field(..., min_length=1, max_length=100, examples=["Palmeiras"])
    odd: float = Field(..., gt=1.0, examples=[2.10])
    profit: float = Field(..., ge=0, examples=[1500.00])
    stats_label: str = Field(default="Performance", max_length=100)
    stats_value: str = Field(default="", max_length=100)
    extra_tip: str = Field(default="", max_length=300)


class VideoResponse(BaseModel):
    video_url: str
    filename: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/generate-video", response_model=VideoResponse)
def create_video(req: VideoRequest):
    try:
        path = generate_video(
            home_team=req.home_team,
            away_team=req.away_team,
            odd=req.odd,
            profit=req.profit,
            stats_label=req.stats_label,
            stats_value=req.stats_value,
            extra_tip=req.extra_tip,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Video generation failed: {e}")

    filename = os.path.basename(path)
    return VideoResponse(
        video_url=f"/videos/{filename}",
        filename=filename,
    )


@app.get("/videos/{filename}")
def get_video(filename: str):
    # Prevent path traversal
    if "/" in filename or "\\" in filename or ".." in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")

    path = os.path.join(os.path.dirname(__file__), "output", filename)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Video not found")

    return FileResponse(path, media_type="video/mp4", filename=filename)


# Catch-all: serve React index.html for any non-API route (SPA routing)
@app.get("/{full_path:path}")
def serve_spa(full_path: str):
    index = os.path.join(STATIC_DIR, "index.html")
    if os.path.isdir(STATIC_DIR) and os.path.exists(index):
        return HTMLResponse(open(index).read())
    return HTMLResponse("<h1>GreenScreen API</h1><p>Frontend not built. Run the Dockerfile.</p>")
