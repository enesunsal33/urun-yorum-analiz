from database import Base, engine
import models

print("1- Tablolar oluşturuluyor...")
Base.metadata.create_all(bind=engine)
print("2- Tablolar oluşturuldu.")