"""
migrate_json_to_db.py
----------------------
Tek seferlik migrasyon: users_master_db.json içindeki mevcut kullanıcıları
db.py üzerinden gerçek veritabanına (varsayılan: SQLite, isterseniz .env'de
DATABASE_URL ile Postgres/Supabase) aktarır.

Kullanım:
    python migrate_json_to_db.py

Bu script:
    1) users_master_db.json'ı okur (varsa).
    2) Her kullanıcıyı db.py üzerinden veritabanına upsert eder.
    3) Orijinal JSON dosyasına DOKUNMAZ (silmez) — kontrol edip siz silin.
       (İstersen kontrolden sonra .gitignore zaten bu dosyayı hariç tutuyor.)
"""

import json
import os

from db import upsert_users_from_dict, get_all_users_as_dict

JSON_DOSYASI = "users_master_db.json"


def main():
    if not os.path.exists(JSON_DOSYASI):
        print(f"'{JSON_DOSYASI}' bulunamadı — taşınacak veri yok.")
        return

    with open(JSON_DOSYASI, "r", encoding="utf-8") as f:
        eski_db = json.load(f)

    if not eski_db:
        print("JSON dosyası boş, taşınacak kullanıcı yok.")
        return

    print(f"{len(eski_db)} kullanıcı bulundu, veritabanına aktarılıyor...")
    upsert_users_from_dict(eski_db)

    # Doğrulama: DB'den geri okuyup sayıyı kontrol et
    yeni_db = get_all_users_as_dict()
    print(f"✅ Veritabanında şu an {len(yeni_db)} kullanıcı kayıtlı.")
    print("JSON dosyası silinmedi; her şey yolundaysa manuel olarak silebilir "
          "veya arşivleyebilirsiniz (artık uygulama tarafından okunmuyor).")


if __name__ == "__main__":
    main()
