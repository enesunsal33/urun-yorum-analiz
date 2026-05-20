import csv
from pathlib import Path

from database import SessionLocal
from models import Comment


BASE_DIR = Path(__file__).resolve().parent
OUTPUT_PATH = BASE_DIR / "data" / "project_sentiment_data.csv"


def rating_to_label(rating):
    if rating is None:
        return None

    if rating >= 4:
        return "positive"

    if rating <= 2:
        return "negative"

    return None


def main():
    db = SessionLocal()

    comments = db.query(Comment).filter(Comment.rating.isnot(None)).all()

    positive_count = 0
    negative_count = 0

    with open(OUTPUT_PATH, "w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["text", "label"])

        for comment in comments:
            label = rating_to_label(comment.rating)

            if not label:
                continue

            writer.writerow([comment.content, label])

            if label == "positive":
                positive_count += 1
            elif label == "negative":
                negative_count += 1

    db.close()

    print(f"CSV oluşturuldu: {OUTPUT_PATH}")
    print(f"Positive: {positive_count}")
    print(f"Negative: {negative_count}")


if __name__ == "__main__":
    main()