from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from database import engine, get_db
from models import Article, Base, Series
from schemas import (
    ArticleCreate,
    ArticleResponse,
    ArticleUpdate,
    ArticleWithSeries,
    SeriesCreate,
    SeriesResponse,
    SeriesUpdate,
    SeriesWithArticles,
)

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Recompile Archive API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"name": "Recompile Archive API", "version": "1.0.0"}


@app.get("/health")
def health():
    return {"status": "ok"}


# ---------- Series ----------

@app.get("/series", response_model=list[SeriesResponse])
def list_series(db: Session = Depends(get_db)):
    return db.query(Series).order_by(Series.name).all()


@app.get("/series/{series_id}", response_model=SeriesWithArticles)
def get_series(series_id: int, db: Session = Depends(get_db)):
    series = db.query(Series).filter(Series.id == series_id).first()
    if series is None:
        raise HTTPException(status_code=404, detail="Series not found")
    return series


@app.post("/series", response_model=SeriesResponse, status_code=201)
def create_series(data: SeriesCreate, db: Session = Depends(get_db)):
    if db.query(Series).filter(Series.slug == data.slug).first():
        raise HTTPException(status_code=409, detail="Slug already exists")
    series = Series(**data.model_dump())
    db.add(series)
    db.commit()
    db.refresh(series)
    return series


@app.put("/series/{series_id}", response_model=SeriesResponse)
def update_series(series_id: int, data: SeriesUpdate, db: Session = Depends(get_db)):
    series = db.query(Series).filter(Series.id == series_id).first()
    if series is None:
        raise HTTPException(status_code=404, detail="Series not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(series, field, value)
    db.commit()
    db.refresh(series)
    return series


@app.delete("/series/{series_id}")
def delete_series(series_id: int, db: Session = Depends(get_db)):
    series = db.query(Series).filter(Series.id == series_id).first()
    if series is None:
        raise HTTPException(status_code=404, detail="Series not found")
    db.delete(series)
    db.commit()
    return {"message": "Series deleted", "id": series_id}


# ---------- Articles ----------

@app.get("/articles", response_model=list[ArticleResponse])
def list_articles(
    series_id: int | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(Article)
    if series_id is not None:
        query = query.filter(Article.series_id == series_id)
    return query.order_by(Article.published_at.desc().nullslast()).all()


@app.get("/articles/{article_id}", response_model=ArticleWithSeries)
def get_article(article_id: int, db: Session = Depends(get_db)):
    article = db.query(Article).filter(Article.id == article_id).first()
    if article is None:
        raise HTTPException(status_code=404, detail="Article not found")
    return article


@app.post("/articles", response_model=ArticleResponse, status_code=201)
def create_article(data: ArticleCreate, db: Session = Depends(get_db)):
    if data.series_id is not None:
        if db.query(Series).filter(Series.id == data.series_id).first() is None:
            raise HTTPException(status_code=400, detail="Referenced series does not exist")
    article = Article(**data.model_dump())
    db.add(article)
    db.commit()
    db.refresh(article)
    return article


@app.put("/articles/{article_id}", response_model=ArticleResponse)
def update_article(article_id: int, data: ArticleUpdate, db: Session = Depends(get_db)):
    article = db.query(Article).filter(Article.id == article_id).first()
    if article is None:
        raise HTTPException(status_code=404, detail="Article not found")

    payload = data.model_dump(exclude_unset=True)
    if "series_id" in payload and payload["series_id"] is not None:
        if db.query(Series).filter(Series.id == payload["series_id"]).first() is None:
            raise HTTPException(status_code=400, detail="Referenced series does not exist")

    for field, value in payload.items():
        setattr(article, field, value)
    db.commit()
    db.refresh(article)
    return article


@app.delete("/articles/{article_id}")
def delete_article(article_id: int, db: Session = Depends(get_db)):
    article = db.query(Article).filter(Article.id == article_id).first()
    if article is None:
        raise HTTPException(status_code=404, detail="Article not found")
    db.delete(article)
    db.commit()
    return {"message": "Article deleted", "id": article_id}
