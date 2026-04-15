from pydantic import BaseModel
from typing import List

class ProductAnalysisSchema(BaseModel):
    genel_gorus: str
    avantajlar: List[str]
    dezavantajlar: List[str]
    kime_uygun: str
    dikkat_edilmesi_gerekenler: str
    ozet: str