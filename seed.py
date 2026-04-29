from database import SessionLocal, Base, engine
from models import Product, Comment
from datetime import datetime, timedelta, UTC
import random

Base.metadata.create_all(bind=engine)

db = SessionLocal()

# Eski verileri temizle
db.query(Comment).delete()
db.query(Product).delete()
db.commit()

categories = {
    "Kulaklık": {
        "products": ["Kablosuz Kulaklık", "Gaming Kulaklık", "Bluetooth Kulaklık", "Kulak İçi Kulaklık"],
        "comments": [
            "Ses kalitesi günlük kullanım için gayet yeterli.",
            "Bass performansı özellikle müzik dinlerken tatmin edici.",
            "Mikrofon kalitesi konuşmalarda iş görüyor ama çok üst seviye değil.",
            "Uzun kullanımda kulağı çok fazla rahatsız etmiyor.",
            "Şarj süresi beklentimi karşıladı.",
            "Bluetooth bağlantısı genel olarak stabil ama bazen geç bağlanıyor.",
            "Fiyatına göre alınabilecek mantıklı bir ürün.",
            "Malzeme kalitesi iyi fakat daha sağlam hissedebilirdi.",
            "Dış ses yalıtımı kalabalık ortamlarda işe yarıyor.",
            "Oyunlarda gecikme çok fark edilmiyor.",
            "Kutu içeriği yeterli ve ürün düzgün paketlenmişti.",
            "Ses seviyesi yüksek ama son seviyede biraz bozulma var.",
            "Kulak pedleri yumuşak, uzun kullanımda avantaj sağlıyor.",
            "Telefonla eşleştirme işlemi kolay oldu.",
            "Mikrofonu dış ortamda biraz zayıf kalabiliyor.",
            "Tasarımı sade ve şık duruyor.",
            "Şarj kutusu küçük olduğu için taşımak kolay.",
            "Film izlerken ses gecikmesi yaşamadım.",
            "Fiyatı biraz daha düşük olsa çok daha iyi olurdu.",
            "Genel olarak beklentimi karşıladı."
        ]
    },
    "Mouse": {
        "products": ["Oyuncu Mouse", "Kablosuz Mouse", "RGB Mouse", "Ergonomik Mouse"],
        "comments": [
            "Tutuşu rahat ve ele iyi oturuyor.",
            "Tıklama hissi tok ve kaliteli.",
            "Uzun kullanımda bile eli çok yormuyor.",
            "RGB ışıklar tasarıma güzel bir hava katıyor.",
            "DPI geçişleri pratik ve hızlı çalışıyor.",
            "Boyutu küçük elliler için daha uygun olabilir.",
            "Kablosuz performansı beklediğimden daha stabil.",
            "Malzeme kalitesi fiyatına göre iyi.",
            "Oyunlarda tepki süresi başarılı.",
            "Scroll tekeri biraz sert ama alışılıyor.",
            "Günlük kullanım için de oldukça rahat.",
            "Alt kaydırma yüzeyleri masada akıcı hareket ediyor.",
            "Kablo kalitesi iyi ama biraz daha esnek olabilirdi.",
            "Yazılım desteği olsa daha iyi olurdu.",
            "Tasarımı sade ama şık duruyor.",
            "FPS oyunlarında kontrol hissi iyi.",
            "Ağırlığı bana göre ideal.",
            "Sessiz tıklama bekleyenler için uygun olmayabilir.",
            "Fiyat performans açısından başarılı.",
            "Uzun vadede dayanıklılığını görmek lazım."
        ]
    },
    "Klavye": {
        "products": ["Mekanik Klavye", "Gaming Klavye", "Kablosuz Klavye", "RGB Klavye"],
        "comments": [
            "Tuş hissiyatı yazı yazarken oldukça iyi.",
            "RGB aydınlatması canlı ve hoş görünüyor.",
            "Tuş sesleri biraz yüksek olabilir.",
            "Uzun süre yazı yazarken rahat ettiriyor.",
            "Malzeme kalitesi sağlam hissettiriyor.",
            "Tepki süresi oyunlarda yeterli.",
            "Kablosuz bağlantı genel olarak stabil.",
            "Bazı tuşlar ilk kullanımda biraz sert geldi.",
            "Fiyat performans olarak iyi bir seçenek.",
            "Bilek desteği olsa daha rahat olurdu.",
            "Masa üzerinde kayma yapmıyor.",
            "Tuş dizilimi alışması kolay bir yapıda.",
            "Işık modları yeterince çeşitli.",
            "Kablo kalitesi iyi fakat biraz kalın.",
            "Günlük kullanım ve oyun için dengeli.",
            "Yazılım desteği daha iyi olabilirdi.",
            "Tuş kapakları kaliteli duruyor.",
            "Gece kullanımında ışık seviyesi yeterli.",
            "Kompakt tasarımı masa alanı kazandırıyor.",
            "Genel olarak beklentimi karşıladı."
        ]
    },
    "Telefon": {
        "products": ["Akıllı Telefon", "Android Telefon", "Kamera Telefonu", "Performans Telefonu"],
        "comments": [
            "Kamera gündüz çekimlerinde oldukça başarılı.",
            "Batarya süresi günlük kullanım için yeterli.",
            "Performansı akıcı ve takılma çok az.",
            "Ekran kalitesi renkler açısından güzel.",
            "Şarj süresi biraz uzun gelebilir.",
            "Yoğun kullanımda biraz ısınma yapıyor.",
            "Fiyatına göre mantıklı bir telefon.",
            "Hoparlör sesi ortalama seviyede.",
            "Günlük kullanımda rahat bir deneyim sunuyor.",
            "Malzeme kalitesi premium hissettiriyor.",
            "Gece çekimleri çok iyi değil ama idare eder.",
            "Uygulamalar arası geçişler hızlı.",
            "Ekran parlaklığı dış mekanda yeterli.",
            "Kılıfla kullanınca elde tutuşu daha iyi oluyor.",
            "Depolama alanı çoğu kullanıcı için yeterli.",
            "Oyun performansı orta-üst seviyede.",
            "Ön kamera sosyal medya için yeterli.",
            "Parmak izi okuyucu hızlı çalışıyor.",
            "Fiyatı biraz yüksek ama sundukları iyi.",
            "Uzun vadeli kullanımda pil performansı önemli olacak."
        ]
    },
    "Tablet": {
        "products": ["Android Tablet", "Eğitim Tableti", "Taşınabilir Tablet", "Büyük Ekran Tablet"],
        "comments": [
            "Ekran boyutu ders ve video izlemek için ideal.",
            "Eğitim amaçlı kullanım için yeterli performans sunuyor.",
            "Batarya süresi uzun kullanımda avantaj sağlıyor.",
            "Taşıması kolay ve çok ağır değil.",
            "Dokunmatik hassasiyeti iyi.",
            "Hoparlör kalitesi biraz zayıf kalıyor.",
            "Uygulamalar genel olarak akıcı çalışıyor.",
            "Şarj süresi normal seviyede.",
            "Fiyatına göre alınabilir bir ürün.",
            "Parlaklık seviyesi dış mekanda biraz düşük kalabilir.",
            "Not almak için kullanışlı.",
            "Film izlerken ekran kalitesi tatmin edici.",
            "Çocuklar için eğitim uygulamalarında işe yarıyor.",
            "Kasa kalitesi fiyatına göre iyi.",
            "Kamera performansı çok beklentiye girilmemeli.",
            "Günlük internet kullanımı için yeterli.",
            "Depolama alanı temel kullanım için uygun.",
            "Kalem desteği olsa daha iyi olurdu.",
            "Uzun süre elde tutunca biraz yorabilir.",
            "Genel olarak beklentimi karşıladı."
        ]
    }
}

comment_suffixes = [
    "Genel olarak memnun kaldım.",
    "Beklentimi büyük ölçüde karşıladı.",
    "Fiyatı biraz daha uygun olsa daha iyi olurdu.",
    "Uzun vadede performansını görmek lazım.",
    "Günlük kullanım için rahatlıkla tercih edilebilir.",
    "Küçük eksikleri var ama genel deneyim iyi.",
    "Tekrar almayı düşünebilirim.",
    "Benzer ürünlere göre başarılı buldum.",
    "İlk izlenimim olumlu oldu.",
    "Çok üst seviye beklemeyenler için yeterli."
]

image_urls = {
    "Kulaklık": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e",
    "Mouse": "https://images.unsplash.com/photo-1527814050087-3793815479db",
    "Klavye": "https://images.unsplash.com/photo-1511467687858-23d96c32e4ae",
    "Telefon": "https://images.unsplash.com/photo-1511707171634-5f897ff02aa9",
    "Tablet": "https://images.unsplash.com/photo-1544244015-0df4b3ffc6b0"
}

usernames = [
    "Ahmet", "Mehmet", "Ayşe", "Zeynep", "Ali", "Can", "Elif", "Mert",
    "Burak", "Ece", "Deniz", "Selin", "Kaan", "Cem", "İrem", "Berk",
    "Yağmur", "Emre", "Sude", "Kerem"
]

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

    # Her ürün için 8-20 yorum
    comment_count = random.randint(8, 20)

    for _ in range(comment_count):
        base_comment = random.choice(comment_pool)
        suffix = random.choice(comment_suffixes)

        text = f"{base_comment} {suffix}"

        random_days = random.randint(1, 60)
        comment_date = datetime.now(UTC) - timedelta(days=random_days)

        rating = random.choices(
            [1, 2, 3, 4, 5],
            weights=[5, 10, 20, 35, 30]
        )[0]

        comments.append(
            Comment(
                product_id=product.id,
                content=text,
                username=random.choice(usernames),
                created_at=comment_date,
                rating=rating
            )
        )

db.add_all(comments)
db.commit()
db.close()

print("Ürünler ve geliştirilmiş yorumlar başarıyla eklendi.")