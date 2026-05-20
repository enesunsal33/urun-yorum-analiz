import csv
import re
from functools import lru_cache
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline


BASE_DIR = Path(__file__).resolve().parent.parent
TRAINING_DATA_PATH = BASE_DIR / "data" / "project_sentiment_data.csv"


def clean_text(text: str) -> str:
    text = text.lower()
    text = text.replace("İ", "i").replace("I", "ı")
    text = re.sub(r"http\S+|www\S+", " ", text)
    text = re.sub(r"[^a-zçğıöşü\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def load_training_data():
    texts = []
    labels = []

    with open(TRAINING_DATA_PATH, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            text = row.get("text", "").strip()
            label = row.get("label", "").strip()

            if text and label in ["positive", "negative"]:
                texts.append(clean_text(text))
                labels.append(label)

    return texts, labels


@lru_cache(maxsize=1)
def build_sentiment_model():
    train_texts, train_labels = load_training_data()

    model = Pipeline([
        ("tfidf", TfidfVectorizer(
            ngram_range=(1, 2),
            min_df=2,
            max_df=0.95,
            sublinear_tf=True
        )),
        ("classifier", LogisticRegression(
            max_iter=1000,
            class_weight="balanced"
        ))
    ])

    model.fit(train_texts, train_labels)
    return model

def extract_positive_topics(comments: list[str], predictions) -> list[str]:
    topic_patterns = {
        "ses kalitesi": ["ses", "ses kalitesi", "bass"],
        "mikrofon performansı": ["mikrofon"],
        "şarj süresi": ["şarj", "batarya", "pil"],
        "bağlantı kolaylığı": ["bağlantı", "bluetooth", "eşleştirme"],
        "kullanım rahatlığı": ["rahat", "konforlu", "ergonomik"],
        "fiyat-performans": ["fiyat", "performans", "fiyatına göre"],
        "malzeme kalitesi": ["malzeme", "sağlam", "kaliteli"],
        "ekran kalitesi": ["ekran", "parlaklık", "renk"],
        "kamera performansı": ["kamera", "fotoğraf", "çekim"],
        "günlük kullanım": ["günlük", "temel kullanım"]
    }

    positive_signals = [
        "iyi", "güzel", "başarılı", "memnun", "kaliteli", "rahat",
        "yeterli", "stabil", "akıcı", "şık", "tatmin", "kolay",
        "hızlı", "sağlam", "sorunsuz", "karşıladı", "avantaj",
        "olumlu", "mantıklı", "pratik"
    ]

    return extract_topics_by_sentiment(
        comments=comments,
        predictions=predictions,
        target_sentiment="positive",
        topic_patterns=topic_patterns,
        signal_words=positive_signals
    )


def extract_negative_topics(comments: list[str], predictions) -> list[str]:
    topic_patterns = {
        "ses kalitesi": ["ses", "ses kalitesi", "bass"],
        "mikrofon performansı": ["mikrofon"],
        "şarj süresi": ["şarj", "batarya", "pil"],
        "bağlantı": ["bağlantı", "bluetooth", "eşleştirme"],
        "kullanım rahatlığı": ["rahat", "konforlu", "ergonomik"],
        "fiyat": ["fiyat", "pahalı", "fiyatına göre"],
        "malzeme kalitesi": ["malzeme", "sağlam", "kaliteli"],
        "ekran kalitesi": ["ekran", "parlaklık", "renk"],
        "kamera performansı": ["kamera", "fotoğraf", "çekim"],
        "performans": ["performans", "yavaş", "takılma", "ısınma"]
    }

    negative_signals = [
        "kötü", "zayıf", "pahalı", "sorun", "gecikme", "sert",
        "yetersiz", "rahatsız", "düşük", "eksik", "bozulma",
        "ısınma", "uzun", "kalitesiz", "başarısız", "kopma",
        "tutarsız", "karşılamadı", "memnun kalmadım"
    ]

    return extract_topics_by_sentiment(
        comments=comments,
        predictions=predictions,
        target_sentiment="negative",
        topic_patterns=topic_patterns,
        signal_words=negative_signals
    )


def extract_topics_by_sentiment(
    comments: list[str],
    predictions,
    target_sentiment: str,
    topic_patterns: dict,
    signal_words: list[str]
) -> list[str]:
    topic_scores = {}

    for comment, prediction in zip(comments, predictions):
        if prediction != target_sentiment:
            continue

        comment_text = comment.lower()

        has_signal = any(signal in comment_text for signal in signal_words)

        if not has_signal:
            continue

        for topic, patterns in topic_patterns.items():
            if any(pattern in comment_text for pattern in patterns):
                topic_scores[topic] = topic_scores.get(topic, 0) + 1

    sorted_topics = sorted(
        topic_scores.items(),
        key=lambda item: item[1],
        reverse=True
    )

    return [topic for topic, score in sorted_topics[:2]]


def get_sentiment_summary(predictions, probabilities, model):
    positive_index = list(model.classes_).index("positive")

    positive_scores = [
        prob[positive_index]
        for prob in probabilities
    ]

    avg_positive_score = sum(positive_scores) / len(positive_scores)

    if avg_positive_score >= 0.52:
        return "Yorumlara bakıldığında kullanıcıların üründen genel olarak memnun kaldığı görülüyor."

    if avg_positive_score <= 0.45:
        return "Yorumlara bakıldığında kullanıcıların ürünle ilgili bazı olumsuz deneyimler yaşadığı görülüyor."

    return "Yorumlarda ürünle ilgili hem olumlu hem de olumsuz deneyimlerin bulunduğu görülüyor."


def generate_ml_comment_summary(comments: list[str]) -> str:
    cleaned_comments = [
        clean_text(comment)
        for comment in comments
        if comment and comment.strip()
    ]

    cleaned_comments = [
        comment for comment in cleaned_comments
        if len(comment.split()) >= 3
    ]

    if len(cleaned_comments) < 2:
        return "Bu ürün için makine öğrenmesi tabanlı yorum özeti oluşturmak adına yeterli yorum bulunmamaktadır."

    try:
        model = build_sentiment_model()

        predictions = model.predict(cleaned_comments)
        probabilities = model.predict_proba(cleaned_comments)

        sentiment_sentence = get_sentiment_summary(predictions, probabilities, model)

        positive_topics = extract_positive_topics(cleaned_comments, predictions)
        negative_topics = extract_negative_topics(cleaned_comments, predictions)

        summary_parts = [sentiment_sentence]

        if positive_topics:
            summary_parts.append(
                f"Olumlu yorumlarda özellikle {', '.join(positive_topics)} öne çıkıyor."
            )

        if negative_topics:
            summary_parts.append(
                f"Bazı olumsuz yorumlarda ise {', '.join(negative_topics)} eleştiriliyor."
            )

        return " ".join(summary_parts)

    except Exception as e:
        return f"ML özet hatası: {e}"

    

  