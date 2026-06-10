import json
from services.ml_summarizer import generate_ml_comment_summary
from schemas import ProductAnalysisSchema
from sqlalchemy import func
from fastapi import FastAPI, Request, Form
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from passlib.context import CryptContext
from sqlalchemy.orm import joinedload
from services.ai_analyzer import analyze_product_comments
from database import Base, engine, SessionLocal
from config import SECRET_KEY
import models as models
import random

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

Base.metadata.create_all(bind=engine)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_current_user(request: Request, db):
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    return db.query(models.User).filter(models.User.id == user_id).first()


@app.get("/")
def home(request: Request):
    category = request.query_params.get("category")
    search = request.query_params.get("search")
    sort = request.query_params.get("sort")
    page = int(request.query_params.get("page", 1))
    per_page = 20

    db = SessionLocal()
    current_user = get_current_user(request, db)

    query = db.query(models.Product)

    if category:
        query = query.filter(models.Product.category == category)

    if search:
        query = query.filter(models.Product.name.ilike(f"%{search}%"))

    if sort == "asc":
        query = query.order_by(models.Product.price.asc())
    elif sort == "desc":
        query = query.order_by(models.Product.price.desc())

    total_products = query.count()
    total_pages = (total_products + per_page - 1) // per_page

    products = query.offset((page - 1) * per_page).limit(per_page).all()

    favorite_product_ids = set()
    if current_user:
        favorite_product_ids = {
            fav.product_id
            for fav in db.query(models.Favorite)
            .filter(models.Favorite.user_id == current_user.id)
            .all()
        }

    for product in products:
        avg_rating = (
            db.query(func.avg(models.Comment.rating))
            .filter(
                models.Comment.product_id == product.id,
                models.Comment.rating.isnot(None)
            )
            .scalar()
        )

        if avg_rating is not None:
            product.rating = round(float(avg_rating), 1)
        else:
            product.rating = 0

        product.is_favorite = product.id in favorite_product_ids

    db.close()

    return templates.TemplateResponse(
        request,
        "index.html",
        {
            "products": products,
            "selected_category": category,
            "search_query": search,
            "selected_sort": sort,
            "page": page,
            "total_pages": total_pages,
            "total_products": total_products,
            "current_user": current_user
        }
    )

@app.get("/product/{product_id}")
def product_detail(request: Request, product_id: int):
    db = SessionLocal()
    current_user = get_current_user(request, db)

    product = db.query(models.Product).filter(models.Product.id == product_id).first()

    if not product:
        db.close()
        return RedirectResponse(url="/", status_code=303)

    comments = db.query(models.Comment).filter(
        models.Comment.product_id == product_id
    ).all()

    # ⭐ RATING HESAPLAMA
    avg_rating = (
        db.query(func.avg(models.Comment.rating))
        .filter(
            models.Comment.product_id == product_id,
            models.Comment.rating.isnot(None)
        )
        .scalar()
    )

    rating_percent = 0

    if avg_rating is not None:
        product.rating = round(float(avg_rating), 1)
        rating_percent = (product.rating / 5) * 100
    else:
        product.rating = 0

    # yorum sayısı
    rating_count = len([c for c in comments if c.rating is not None])

    # 📊 ML TABANLI YORUM ÖZETİ
    ml_summary = generate_ml_comment_summary(
        comments=[comment.content for comment in comments]
    )

    is_favorite = False
    if current_user:
        is_favorite = db.query(models.Favorite).filter(
            models.Favorite.user_id == current_user.id,
            models.Favorite.product_id == product_id
        ).first() is not None

    db.close()

    return templates.TemplateResponse(
        request,
        "product_detail.html",
        {
            "product": product,
            "comments": comments,
            "is_favorite": is_favorite,
            "current_user": current_user,
            "rating_count": rating_count,
            "rating_percent": rating_percent,
            "ml_summary": ml_summary
        }
    )


@app.post("/product/{product_id}/favorite")
def toggle_favorite(request: Request, product_id: int, next: str = Form(None)):
    db = SessionLocal()
    current_user = get_current_user(request, db)

    if not current_user:
        db.close()
        return RedirectResponse(url="/login", status_code=303)

    product = db.query(models.Product).filter(models.Product.id == product_id).first()

    existing_favorite = db.query(models.Favorite).filter(
        models.Favorite.user_id == current_user.id,
        models.Favorite.product_id == product_id
    ).first()

    if existing_favorite:
        db.delete(existing_favorite)
    else:
        db.add(models.Favorite(user_id=current_user.id, product_id=product_id))

    db.commit()
    db.close()

    # 👇 önemli kısım
    redirect_url = next if next else f"/product/{product_id}"

    return RedirectResponse(url=redirect_url, status_code=303)

@app.post("/api/product/{product_id}/favorite")
def toggle_favorite_api(request: Request, product_id: int):
    db = SessionLocal()
    current_user = get_current_user(request, db)

    if not current_user:
        db.close()
        return JSONResponse(
            {"success": False, "message": "Giriş yapmalısınız."},
            status_code=401
        )

    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        db.close()
        return JSONResponse(
            {"success": False, "message": "Ürün bulunamadı."},
            status_code=404
        )

    existing_favorite = (
        db.query(models.Favorite)
        .filter(
            models.Favorite.user_id == current_user.id,
            models.Favorite.product_id == product_id
        )
        .first()
    )

    if existing_favorite:
        db.delete(existing_favorite)
        is_favorite = False
    else:
        favorite = models.Favorite(
            user_id=current_user.id,
            product_id=product_id
        )
        db.add(favorite)
        is_favorite = True

    db.commit()
    db.close()

    return {"success": True, "is_favorite": is_favorite}


@app.post("/product/{product_id}/comment")
def add_comment(request: Request, product_id: int, content: str = Form(...), rating: int = Form(...)):
    db = SessionLocal()
    current_user = get_current_user(request, db)

    if not current_user:
        db.close()
        return RedirectResponse(url="/login", status_code=303)

    product = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product:
        db.close()
        return RedirectResponse(url="/", status_code=303)

    content = content.strip()

    if not content:
        db.close()
        return RedirectResponse(url=f"/product/{product_id}", status_code=303)

    new_comment = models.Comment(
        product_id=product_id,
        user_id=current_user.id,
        username=current_user.username,
        content=content,
        rating=rating
    )

    db.add(new_comment)
    db.commit()
    db.close()

    return RedirectResponse(url=f"/product/{product_id}", status_code=303)


@app.post("/product/{product_id}/analyze")
def analyze_product(request: Request, product_id: int):
    db = SessionLocal()
    current_user = get_current_user(request, db)

    product = db.query(models.Product).filter(models.Product.id == product_id).first()

    if not product:
        db.close()
        return templates.TemplateResponse(
            request,
            "product_detail.html",
            {
                "product": None,
                "comments": [],
                "analysis": None,
                "error": "Ürün bulunamadı.",
                "current_user": current_user,
                "is_favorite": False,
                "rating_count": 0,
                "rating_percent": 0,
                "ml_summary": ml_summary
            }
        )

    comments = (
        db.query(models.Comment)
        .options(joinedload(models.Comment.user))
        .filter(models.Comment.product_id == product_id)
        .order_by(models.Comment.created_at.desc())
        .all()
    )

    avg_rating = (
        db.query(func.avg(models.Comment.rating))
        .filter(
            models.Comment.product_id == product_id,
            models.Comment.rating.isnot(None)
        )
        .scalar()
    )

    rating_percent = 0

    if avg_rating is not None:
        product.rating = round(float(avg_rating), 1)
        rating_percent = (product.rating / 5) * 100
    else:
        product.rating = 0

    rating_count = len([c for c in comments if c.rating is not None])
    ml_summary = generate_ml_comment_summary(
    comments=[comment.content for comment in comments]
)

    is_favorite = False
    if current_user:
        is_favorite = (
            db.query(models.Favorite)
            .filter(
                models.Favorite.user_id == current_user.id,
                models.Favorite.product_id == product_id
            )
            .first()
            is not None
        )

    if not comments:
        db.close()
        return templates.TemplateResponse(
            request,
            "product_detail.html",
            {
                "product": product,
                "comments": [],
                "analysis": None,
                "error": "Bu ürün için analiz edilecek yorum bulunamadı.",
                "current_user": current_user,
                "is_favorite": is_favorite,
                "rating_count": rating_count,
                "rating_percent": rating_percent,
                "ml_summary": ml_summary
            }
        )

    comment_texts = [comment.content for comment in comments]
    current_comment_count = len(comments)

    try:
        cache = (
            db.query(models.ProductAnalysisCache)
            .filter(models.ProductAnalysisCache.product_id == product.id)
            .first()
        )

        if cache and cache.comments_count == current_comment_count:
            analysis = ProductAnalysisSchema.model_validate_json(cache.result_json)
        else:
            analysis = analyze_product_comments(
                product_name=product.name,
                category=product.category,
                comments=comment_texts
            )

            analysis_json = analysis.model_dump_json()

            if cache:
                cache.result_json = analysis_json
                cache.comments_count = current_comment_count
            else:
                cache = models.ProductAnalysisCache(
                    product_id=product.id,
                    result_json=analysis_json,
                    comments_count=current_comment_count
                )
                db.add(cache)

            db.commit()
            db.refresh(cache)

        if current_user:
            history = models.AnalysisHistory(
                user_id=current_user.id,
                product_id=product.id,
                cache_id=cache.id
            )
            db.add(history)
            db.commit()

        db.close()

        return templates.TemplateResponse(
            request,
            "product_detail.html",
            {
                "product": product,
                "comments": comments,
                "analysis": analysis,
                "error": None,
                "current_user": current_user,
                "is_favorite": is_favorite,
                "rating_count": rating_count,
                "rating_percent": rating_percent,
                "ml_summary": ml_summary
            }
        )

    except Exception as e:
        db.close()

        return templates.TemplateResponse(
            request,
            "product_detail.html",
            {
                "product": product,
                "comments": comments,
                "analysis": None,
                "error": f"Analiz sırasında hata oluştu: {str(e)}",
                "current_user": current_user,
                "is_favorite": is_favorite,
                "rating_count": rating_count,
                "rating_percent": rating_percent,
                "ml_summary": ml_summary
            }
        )


@app.get("/register")
def register_page(request: Request):
    db = SessionLocal()
    current_user = get_current_user(request, db)
    db.close()

    return templates.TemplateResponse(
        request,
        "register.html",
        {
            "error": None,
            "current_user": current_user
        }
    )


@app.post("/register")
def register(request: Request, username: str = Form(...), password: str = Form(...)):
    db = SessionLocal()

    username = username.strip()
    password = password.strip()

    current_user = get_current_user(request, db)

    if len(username) < 3:
        db.close()
        return templates.TemplateResponse(
            request,
            "register.html",
            {
                "error": "Kullanıcı adı en az 3 karakter olmalı.",
                "current_user": current_user
            }
        )

    if len(password) < 4:
        db.close()
        return templates.TemplateResponse(
            request,
            "register.html",
            {
                "error": "Şifre en az 4 karakter olmalı.",
                "current_user": current_user
            }
        )

    existing_user = db.query(models.User).filter(models.User.username == username).first()
    if existing_user:
        db.close()
        return templates.TemplateResponse(
            request,
            "register.html",
            {
                "error": "Bu kullanıcı adı zaten alınmış.",
                "current_user": current_user
            }
        )

    user = models.User(
        username=username,
        hashed_password=hash_password(password)
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    request.session["user_id"] = user.id

    db.close()
    return RedirectResponse(url="/", status_code=303)


@app.get("/login")
def login_page(request: Request):
    db = SessionLocal()
    current_user = get_current_user(request, db)
    db.close()

    return templates.TemplateResponse(
        request,
        "login.html",
        {
            "error": None,
            "current_user": current_user
        }
    )


@app.post("/login")
def login(request: Request, username: str = Form(...), password: str = Form(...)):
    db = SessionLocal()

    user = db.query(models.User).filter(models.User.username == username.strip()).first()

    if not user or not verify_password(password, user.hashed_password):
        db.close()
        return templates.TemplateResponse(
            request,
            "login.html",
            {
                "error": "Kullanıcı adı veya şifre hatalı.",
                "current_user": None
            }
        )

    request.session["user_id"] = user.id

    db.close()
    return RedirectResponse(url="/", status_code=303)


@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=303)


@app.get("/favorites")
def favorites_page(request: Request):
    db = SessionLocal()
    current_user = get_current_user(request, db)

    if not current_user:
        db.close()
        return RedirectResponse(url="/login", status_code=303)

    favorites = (
        db.query(models.Favorite)
        .options(joinedload(models.Favorite.product))
        .filter(models.Favorite.user_id == current_user.id)
        .order_by(models.Favorite.created_at.desc())
        .all()
    )

    db.close()

    return templates.TemplateResponse(
        request,
        "favorites.html",
        {
            "favorites": favorites,
            "current_user": current_user
        }
    )

@app.get("/my-comments")
def my_comments_page(request: Request):
    db = SessionLocal()
    current_user = get_current_user(request, db)

    if not current_user:
        db.close()
        return RedirectResponse(url="/login", status_code=303)

    comments = (
        db.query(models.Comment)
        .options(joinedload(models.Comment.product))
        .filter(models.Comment.user_id == current_user.id)
        .order_by(models.Comment.created_at.desc())
        .all()
    )

    db.close()

    return templates.TemplateResponse(
        request,
        "my_comments.html",
        {
            "comments": comments,
            "current_user": current_user
        }
    )

@app.get("/profile")
def profile_page(request: Request):
    db = SessionLocal()
    current_user = get_current_user(request, db)

    if not current_user:
        db.close()
        return RedirectResponse(url="/login", status_code=303)

    comment_count = (
        db.query(models.Comment)
        .filter(models.Comment.user_id == current_user.id)
        .count()
    )

    favorite_count = (
        db.query(models.Favorite)
        .filter(models.Favorite.user_id == current_user.id)
        .count()
    )

    analysis_count = (
        db.query(models.AnalysisHistory)
        .filter(models.AnalysisHistory.user_id == current_user.id)
        .count()
    )

    recent_comments = (
        db.query(models.Comment)
        .options(joinedload(models.Comment.product))
        .filter(models.Comment.user_id == current_user.id)
        .order_by(models.Comment.created_at.desc())
        .limit(3)
        .all()
    )

    recent_analyses = (
        db.query(models.AnalysisHistory)
        .options(joinedload(models.AnalysisHistory.product))
        .filter(models.AnalysisHistory.user_id == current_user.id)
        .order_by(models.AnalysisHistory.created_at.desc())
        .limit(3)
        .all()
    )

    db.close()

    return templates.TemplateResponse(
        request,
        "profile.html",
        {
            "current_user": current_user,
            "comment_count": comment_count,
            "favorite_count": favorite_count,
            "analysis_count": analysis_count,
            "recent_comments": recent_comments,
            "recent_analyses": recent_analyses
        }
    )

@app.get("/analysis-history")
def analysis_history_page(request: Request):
    db = SessionLocal()
    current_user = get_current_user(request, db)

    if not current_user:
        db.close()
        return RedirectResponse(url="/login", status_code=303)

    history_items = (
        db.query(models.AnalysisHistory)
        .options(
            joinedload(models.AnalysisHistory.product),
            joinedload(models.AnalysisHistory.cache)
        )
        .filter(models.AnalysisHistory.user_id == current_user.id)
        .order_by(models.AnalysisHistory.created_at.desc())
        .all()
    )

    db.close()

    return templates.TemplateResponse(
        request,
        "analysis_history.html",
        {
            "history_items": history_items,
            "current_user": current_user
        }
    )

@app.get("/about")
def about(request: Request):
    db = SessionLocal()
    current_user = get_current_user(request, db)
    db.close()

    return templates.TemplateResponse(
        request,
        "about.html",
        {
            "current_user": current_user
        }
    )