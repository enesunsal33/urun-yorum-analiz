from database import SessionLocal, Base, engine
from models import Product, Comment
from datetime import datetime, timedelta, UTC
import random

Base.metadata.create_all(bind=engine)

db = SessionLocal()

db.query(Comment).delete()
db.query(Product).delete()
db.commit()

categories = {
    "Kulaklık": {
        "products": ["Kablosuz Kulaklık", "Gaming Kulaklık", "Bluetooth Kulaklık", "Kulak İçi Kulaklık"],
        "comments": [
            "Ses kalitesi oldukça başarılı.",
            "Bass performansı beklediğimden iyi çıktı.",
            "Mikrofon kalitesi biraz zayıf.",
            "Uzun kullanımda kulağı rahatsız etmiyor.",
            "Şarj süresi yeterli.",
            "Bluetooth bağlantısı bazen geç kuruluyor.",
            "Fiyatına göre gayet iyi.",
            "Malzeme kalitesi daha iyi olabilirdi.",
            "Dış ses yalıtımı başarılı.",
            "Oyunlarda gecikme yok."
        ]
    },
    "Mouse": {
        "products": ["Oyuncu Mouse", "Kablosuz Mouse", "RGB Mouse", "Ergonomik Mouse"],
        "comments": [
            "Tutuşu çok rahat.",
            "Tıklama hissi güzel.",
            "Uzun kullanımda yormuyor.",
            "RGB ışıklar hoş.",
            "DPI geçişleri iyi.",
            "Boyutu biraz küçük.",
            "Kablosuz performansı stabil.",
            "Malzeme kalitesi iyi.",
            "Oyun performansı başarılı.",
            "Scroll biraz sert."
        ]
    },
    "Klavye": {
        "products": ["Mekanik Klavye", "Gaming Klavye", "Kablosuz Klavye", "RGB Klavye"],
        "comments": [
            "Tuş hissiyatı çok iyi.",
            "RGB aydınlatma güzel.",
            "Tuş sesleri biraz yüksek.",
            "Yazı yazarken rahat.",
            "Malzeme kaliteli.",
            "Uzun kullanımda sorun yok.",
            "Tepki süresi iyi.",
            "Kablosuz bağlantı stabil.",
            "Bazı tuşlar sert.",
            "Fiyat performans iyi."
        ]
    },
    "Telefon": {
        "products": ["Akıllı Telefon", "Android Telefon", "Kamera Telefonu", "Performans Telefonu"],
        "comments": [
            "Kamera çok iyi.",
            "Batarya süresi başarılı.",
            "Performans akıcı.",
            "Ekran kalitesi güzel.",
            "Şarj süresi uzun.",
            "Biraz ısınıyor.",
            "Fiyatına göre iyi.",
            "Hoparlör ortalama.",
            "Günlük kullanım rahat.",
            "Malzeme premium."
        ]
    },
    "Tablet": {
        "products": ["Android Tablet", "Eğitim Tableti", "Taşınabilir Tablet", "Büyük Ekran Tablet"],
        "comments": [
            "Ekran boyutu ideal.",
            "Ders için çok iyi.",
            "Batarya uzun gidiyor.",
            "Taşıması kolay.",
            "Dokunmatik hassas.",
            "Hoparlör zayıf.",
            "Uygulamalar akıcı.",
            "Şarj normal.",
            "Fiyatına göre iyi.",
            "Parlaklık biraz düşük."
        ]
    }
}

image_urls = {
    "Kulaklık": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e",
    "Mouse": "https://images.unsplash.com/photo-1527814050087-3793815479db",
    "Klavye": "https://images.unsplash.com/photo-1511467687858-23d96c32e4ae",
    "Telefon": "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9",
    "Tablet": "https://images.unsplash.com/photo-1544244015-0df4b3ffc6b0"
}

usernames = ["Ahmet", "Mehmet", "Ayşe", "Zeynep", "Ali", "Can", "Elif", "Mert"]

products = []

for category, data in categories.items():
    product_names = data["products"]

    for i in range(1, 51):
        base_name = product_names[i % len(product_names)]

        product = Product(
            name=f"{base_name} {i}",
            price=random.randint(500, 20000),
            description=f"{category} kategorisinde yer alan örnek ürün {i}.",
            image_url=image_urls[category],
            category=category
        )
        products.append(product)

db.add_all(products)
db.commit()

all_products = db.query(Product).all()

comments = []

for product in all_products:
    comment_pool = categories[product.category]["comments"]
    selected = random.sample(comment_pool, 3)

    if random.random() > 0.5:
        selected.append(random.choice(comment_pool))

    for text in selected:
        random_days = random.randint(1, 30)
        comment_date = datetime.now(UTC) - timedelta(days=random_days)

        comments.append(
            Comment(
                product_id=product.id,
                content=text,
                username=random.choice(usernames),
                created_at=comment_date
            )
        )

db.add_all(comments)
db.commit()
db.close()

print("Ürünler ve yorumlar başarıyla eklendi.")