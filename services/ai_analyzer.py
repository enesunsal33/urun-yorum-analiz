from google import genai
from pydantic import ValidationError

from config import GEMINI_API_KEY
from schemas import ProductAnalysisSchema

client = genai.Client(api_key=GEMINI_API_KEY)

SYSTEM_PROMPT = """
Sen bir ürün yorum analizi uzmanısın.
Sana bir ürün adı, kategori ve kullanıcı yorumları verilecek.
Görevin yalnızca verilen yorumlara dayanarak kullanıcı için anlamlı, net ve profesyonel bir analiz üretmektir.

Kurallar:
- Sadece yorumlarda geçen bilgilere dayan.
- Yorumlarda açıkça geçmeyen özellikleri uydurma.
- Cevabı Türkçe üret.
- Dengeli, net ve profesyonel ol.
- Avantajlar ve dezavantajlar kısa maddeler halinde olsun.
- Eğer veri yetersizse bunu genel görüşte belirt.
- kime_uygun alanında bu ürünün hangi kullanıcı tipi için daha uygun olduğunu belirt.
- dikkat_edilmesi_gerekenler alanında satın almadan önce kullanıcıyı uyarabilecek noktaları yaz.
- Abartılı, pazarlama kokan veya kesin olmayan ifadeler kullanma.
"""

def build_comments_text(comments: list[str]) -> str:
    if not comments:
        return "Yorum bulunamadı."

    lines = []
    for i, comment in enumerate(comments, start=1):
        lines.append(f"{i}. {comment}")
    return "\n".join(lines)

def analyze_product_comments(product_name: str, category: str, comments: list[str]) -> ProductAnalysisSchema:
    comments_text = build_comments_text(comments)

    prompt = f"""
Ürün adı: {product_name}
Kategori: {category}

Yorumlar:
{comments_text}

Görev:
Verilen yorumlara göre aşağıdaki alanları üret:

- genel_gorus
- avantajlar
- dezavantajlar
- kime_uygun
- dikkat_edilmesi_gerekenler
- ozet

Ek kurallar:
- Avantajlar ve dezavantajlar kısa ve net maddeler olsun.
- kime_uygun alanı 1-3 cümlelik kısa ama anlamlı bir değerlendirme olsun.
- dikkat_edilmesi_gerekenler alanı 1-3 cümlelik kısa ama faydalı bir uyarı metni olsun.
- Yalnızca yorumlardan çıkarım yap.
- Ürünü gereksiz övme veya gereksiz gömme.
"""

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={
                "system_instruction": SYSTEM_PROMPT,
                "response_mime_type": "application/json",
                "response_schema": ProductAnalysisSchema,
                "temperature": 0.3,
            }
        )

        parsed = response.parsed

        if parsed:
            if isinstance(parsed, ProductAnalysisSchema):
                return parsed
            return ProductAnalysisSchema.model_validate(parsed)

        return ProductAnalysisSchema.model_validate_json(response.text)

    except ValidationError as e:
        raise ValueError(f"AI çıktısı beklenen formatta değil: {e}")

    except Exception as e:
        raise RuntimeError(f"Gemini analiz hatası: {e}")


if __name__ == "__main__":
    sample_comments = [
        "Ses kalitesi çok iyi ama fiyatı biraz yüksek.",
        "Mikrofonu başarılı, oyun oynarken işimi gördü.",
        "Uzun kullanımda rahat ama kablo kalitesi daha iyi olabilirdi."
    ]

    result = analyze_product_comments(
        product_name="Gaming Kulaklık X1",
        category="Kulaklık",
        comments=sample_comments
    )

    print(result)