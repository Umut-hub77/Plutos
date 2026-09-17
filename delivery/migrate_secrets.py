"""
migrate_secrets.py
-------------------
Tek seferlik migrasyon: whatsapp_ayarlar.json içindeki açık Twilio SID/Token'ı
.env dosyasına taşır ve JSON dosyasından siler.

Kullanım:
    python migrate_secrets.py

Çalıştırdıktan sonra:
    1) .env dosyanızı KONTROL EDİN (proje kökünde oluşur/güncellenir).
    2) whatsapp_ayarlar.json artık sadece telefon numaraları ve saat bilgisini içerir.
    3) Bu zip'i / repoyu paylaşmadan önce .env dosyasını SİLİN ya da göndermeyin.
"""

import json
import os

AYAR_DOSYASI = "whatsapp_ayarlar.json"
ENV_DOSYASI = ".env"


def main():
    if not os.path.exists(AYAR_DOSYASI):
        print(f"'{AYAR_DOSYASI}' bulunamadı, yapılacak bir şey yok.")
        return

    with open(AYAR_DOSYASI, "r", encoding="utf-8") as f:
        ayarlar = json.load(f)

    tw_sid = ayarlar.pop("tw_sid", "")
    tw_token = ayarlar.pop("tw_token", "")
    tw_from = ayarlar.get("tw_from", "")

    if not tw_sid and not tw_token:
        print("JSON dosyasında taşınacak sır bulunamadı (zaten temiz).")
        return

    # Mevcut .env varsa satır satır oku, TWILIO_* anahtarlarını güncelle, diğerlerini koru.
    mevcut_satirlar = []
    if os.path.exists(ENV_DOSYASI):
        with open(ENV_DOSYASI, "r", encoding="utf-8") as f:
            mevcut_satirlar = [
                l for l in f.read().splitlines()
                if not l.startswith(("TWILIO_SID=", "TWILIO_TOKEN=", "TWILIO_FROM="))
            ]

    mevcut_satirlar += [
        f"TWILIO_SID={tw_sid}",
        f"TWILIO_TOKEN={tw_token}",
        f"TWILIO_FROM={tw_from}",
    ]

    with open(ENV_DOSYASI, "w", encoding="utf-8") as f:
        f.write("\n".join(mevcut_satirlar) + "\n")

    with open(AYAR_DOSYASI, "w", encoding="utf-8") as f:
        json.dump(ayarlar, f, indent=4, ensure_ascii=False)

    print(f"✅ Sırlar '{ENV_DOSYASI}' dosyasına taşındı ve '{AYAR_DOSYASI}' temizlendi.")
    print("⚠️  .env dosyasını asla paylaşmayın / commit etmeyin (.gitignore zaten hariç tutuyor).")


if __name__ == "__main__":
    main()
