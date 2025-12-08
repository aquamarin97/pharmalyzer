import hashlib
import os
import sys

from cryptography.fernet import Fernet

LICENSE_FILE = "license.key"

# Lisans anahtarı oluşturucu (Geliştirici için)
def generate_license_key(app_name: str, user_name: str, key_file: str = LICENSE_FILE):
    secret_key = Fernet.generate_key()
    cipher = Fernet(secret_key)

    # Lisans için kullanıcı ve uygulama bilgilerinden hash oluştur
    license_data = f"{app_name}:{user_name}"
    hashed_data = hashlib.sha256(license_data.encode()).hexdigest()

    # Şifreli veri oluştur
    encrypted_data = cipher.encrypt(hashed_data.encode())

    # Anahtar ve şifreli veriyi dosyaya yaz
    with open(key_file, "wb") as file:
        file.write(secret_key + b"\n" + encrypted_data)

    print(f"Lisans anahtarı oluşturuldu ve '{key_file}' dosyasına kaydedildi.")

# Lisansı kontrol eden fonksiyon
def check_and_setup_license():
    if not os.path.exists(LICENSE_FILE):
        print("Lisans dosyası bulunamadı. Lütfen lisans anahtarınızı sağlayın.")
        sys.exit(1)

    with open(LICENSE_FILE, "rb") as file:
        secret_key, encrypted_data = file.read().split(b"\n", 1)

    cipher = Fernet(secret_key)

    try:
        # Şifreyi çöz
        decrypted_data = cipher.decrypt(encrypted_data).decode()
    except Exception as e:
        print("Lisans doğrulama hatası:", e)
        sys.exit(1)

    # Uygulama ve kullanıcı bilgileri ile karşılaştır
    app_name = "PharmaLyser SMA"
    user_name = "PharmaLine"

    expected_hash = hashlib.sha256(f"{app_name}:{user_name}".encode()).hexdigest()
    if decrypted_data != expected_hash:
        print("Lisans geçersiz!")
        sys.exit(1)

    print("Lisans doğrulandı.")
