import csv
from datasets import load_dataset


OUTPUT_PATH = "data/sentiment_training_data.csv"
MAX_POSITIVE = 300
MAX_NEGATIVE = 300


dataset = load_dataset("boun-tabilab/Turkish-Product-Reviews", split="train")

positive_count = 0
negative_count = 0

with open(OUTPUT_PATH, "w", encoding="utf-8", newline="") as file:
    writer = csv.writer(file)
    writer.writerow(["text", "label"])

    for row in dataset:
        text = str(row.get("text", "")).strip()
        label = row.get("label")

        if not text:
            continue

        if label == 1 and positive_count < MAX_POSITIVE:
            writer.writerow([text, "positive"])
            positive_count += 1

        elif label == 0 and negative_count < MAX_NEGATIVE:
            writer.writerow([text, "negative"])
            negative_count += 1

        if positive_count >= MAX_POSITIVE and negative_count >= MAX_NEGATIVE:
            break

print(f"CSV oluşturuldu: {OUTPUT_PATH}")
print(f"Positive: {positive_count}")
print(f"Negative: {negative_count}")