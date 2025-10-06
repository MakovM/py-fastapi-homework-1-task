from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db, MovieModel
from schemas import MovieListResponseSchema, MovieDetailResponseSchema

router = APIRouter()


@router.get("/movies/", response_model=MovieListResponseSchema)
async def movies_list(
        request: Request,
        page: int = Query(1, ge=1, description="Page number"),
        per_page: int = Query(10, ge=1, le=20, description="Items per page"),
        db: AsyncSession = Depends(get_db)
):
    total_items = int(await db.scalar(select(func.count()).select_from(MovieModel)))

    if total_items == 0:
        raise HTTPException(status_code=404, detail="No movies found.")

    total_pages = (total_items + per_page - 1) // per_page
    offset = (page - 1) * per_page
    stmt = select(MovieModel).offset(offset).limit(per_page)
    movies = (await db.scalars(stmt)).all()

    if not movies:
        raise HTTPException(status_code=404, detail="No movies found.")

    root_path = request.scope.get("root_path", "")
    base_path = root_path + request.url.path
    prev_page = f"{base_path}?page={page - 1}&per_page={per_page}" if page > 1 else None
    next_page = f"{base_path}?page={page + 1}&per_page={per_page}" if page < total_pages else None

    return {
        "movies": [MovieDetailResponseSchema.model_validate(m) for m in movies],
        "prev_page": prev_page,
        "next_page": next_page,
        "total_pages": total_pages,
        "total_items": total_items,
    }


@router.get("/movies/{movie_id}/", response_model=MovieDetailResponseSchema)
async def movies_detail(movie_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MovieModel).where(MovieModel.id == movie_id))
    movie = result.scalar_one_or_none()
    if movie is None:
        raise HTTPException(status_code=404, detail="Movie with the given ID was not found.")
    return MovieDetailResponseSchema.model_validate(movie)
