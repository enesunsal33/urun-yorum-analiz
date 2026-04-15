from fastapi import FastAPI, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from passlib.context import CryptContext
from sqlalchemy.orm import joinedload

from services.ai_analyzer import analyze_product_comments
from database import Base, engine, SessionLocal
from config import SECRET_KEY
import models
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

    for product in products:
        product.rating = round(random.uniform(3.0, 5.0), 1)

    db.close()

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
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
    comments = (
        db.query(models.Comment)
        .options(joinedload(models.Comment.user))
        .filter(models.Comment.product_id == product_id)
        .order_by(models.Comment.created_at.desc())
        .all()
    )

    db.close()

    return templates.TemplateResponse(
        "product_detail.html",
        {
            "request": request,
            "product": product,
            "comments": comments,
            "current_user": current_user,
            "analysis": None,
            "error": None
        }
    )


@app.post("/product/{product_id}/comment")
def add_comment(request: Request, product_id: int, content: str = Form(...)):
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
        content=content
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
    comments = (
        db.query(models.Comment)
        .options(joinedload(models.Comment.user))
        .filter(models.Comment.product_id == product_id)
        .order_by(models.Comment.created_at.desc())
        .all()
    )

    if not product:
        db.close()
        return templates.TemplateResponse(
            "product_detail.html",
            {
                "request": request,
                "product": None,
                "comments": [],
                "analysis": None,
                "error": "Ürün bulunamadı.",
                "current_user": current_user
            }
        )

    if not comments:
        db.close()
        return templates.TemplateResponse(
            "product_detail.html",
            {
                "request": request,
                "product": product,
                "comments": [],
                "analysis": None,
                "error": "Bu ürün için analiz edilecek yorum bulunamadı.",
                "current_user": current_user
            }
        )

    comment_texts = [comment.content for comment in comments]

    try:
        analysis = analyze_product_comments(
            product_name=product.name,
            category=product.category,
            comments=comment_texts
        )

        db.close()

        return templates.TemplateResponse(
            "product_detail.html",
            {
                "request": request,
                "product": product,
                "comments": comments,
                "analysis": analysis,
                "error": None,
                "current_user": current_user
            }
        )

    except Exception as e:
        db.close()

        return templates.TemplateResponse(
            "product_detail.html",
            {
                "request": request,
                "product": product,
                "comments": comments,
                "analysis": None,
                "error": f"Analiz sırasında hata oluştu: {str(e)}",
                "current_user": current_user
            }
        )


@app.get("/register")
def register_page(request: Request):
    db = SessionLocal()
    current_user = get_current_user(request, db)
    db.close()

    return templates.TemplateResponse(
        "register.html",
        {
            "request": request,
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
            "register.html",
            {
                "request": request,
                "error": "Kullanıcı adı en az 3 karakter olmalı.",
                "current_user": current_user
            }
        )

    if len(password) < 4:
        db.close()
        return templates.TemplateResponse(
            "register.html",
            {
                "request": request,
                "error": "Şifre en az 4 karakter olmalı.",
                "current_user": current_user
            }
        )

    existing_user = db.query(models.User).filter(models.User.username == username).first()
    if existing_user:
        db.close()
        return templates.TemplateResponse(
            "register.html",
            {
                "request": request,
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
        "login.html",
        {
            "request": request,
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
            "login.html",
            {
                "request": request,
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


@app.get("/about")
def about(request: Request):
    db = SessionLocal()
    current_user = get_current_user(request, db)
    db.close()

    return templates.TemplateResponse(
        "about.html",
        {
            "request": request,
            "current_user": current_user
        }
    )