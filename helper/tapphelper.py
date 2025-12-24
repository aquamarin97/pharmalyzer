import os
from pathlib import Path

class TAppHelper:
    """
    Proje dosyaları üzerinde toplu işlemler yapmayı sağlayan yardımcı sınıf.
    """

    @staticmethod
    def add_path_comment():
        """
        Belirtilen kök dizinde ve alt dizinlerinde tüm .py dosyalarına
        dosya yolunu yorum satırı olarak en tepeye ekler. 
        Eğer yol zaten ekliyse tekrar eklemez.
        """
        root_dir = Path.cwd()
        print(f"--- İşlem Başlatıldı ---")
        print(f"Dizin: {root_dir}\n")

        processed_count = 0
        skipped_count = 0

        # Tüm .py dosyalarını bul (rekürsif)
        for py_file in root_dir.rglob("*.py"):
            # Kendi dosyasını (tapphelper.py) değiştirmesini istemeyebilirsin
            if py_file.name == "tapphelper.py" or not py_file.is_file():
                continue
            
            try:
                # Proje köküne göre bağıl yol
                relative_path = py_file.relative_to(root_dir)
                comment_line = f"# {relative_path}\n"
                
                # Dosya içeriğini oku
                with open(py_file, "r", encoding="utf-8") as f:
                    content = f.readlines()

                # Kontrol: Yol zaten dosyanın en başında var mı?
                if content and content[0] == comment_line:
                    print(f"Zaten mevcut: {relative_path}")
                    skipped_count += 1
                    continue

                # Yeni içeriği oluştur (Yorum satırı + eski içerik)
                new_content = [comment_line] + content

                # Dosyayı güncelle
                with open(py_file, "w", encoding="utf-8") as f:
                    f.writelines(new_content)
                
                print(f"Eklendi: {relative_path}")
                processed_count += 1

            except (UnicodeDecodeError, PermissionError) as e:
                print(f"Hata! Atlanıyor: {py_file.name} ({e})")
                continue
            except Exception as e:
                print(f"Beklenmedik hata ({py_file.name}): {e}")
                continue

        print(f"\n--- İşlem Tamamlandı ---")
        print(f"Güncellenen: {processed_count} | Atlanan: {skipped_count}") 

    @staticmethod
    def export_folder_tree():
        startpath = Path.cwd()
        output_filename = "folder_structure.txt"

        IGNORE_DIRS = {'.git', '.vscode', '__pycache__', 'venv', '.idea'}
        IGNORE_EXTENSIONS = {'.pyc', '.pyo', '.ds_store', '.gitignore'}

        try:
            with open(output_filename, 'w', encoding='utf-8') as f:
                f.write(f"{startpath.name}/\n")

                for root, dirs, files in os.walk(startpath):
                    # 1. KRİTİK DÜZELTME: Listeyi yerinde (in-place) temizle
                    # Bu sayede os.walk bu klasörlerin içine hiç girmez.
                    dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
                    
                    # Göreceli yolu al
                    relative_path = Path(root).relative_to(startpath)
                    
                    # Başlangıç dizinini tekrar yazma
                    if relative_path == Path('.'):
                        # Ama başlangıç dizinindeki dosyaları listelememiz lazım
                        current_depth = 0
                    else:
                        current_depth = len(relative_path.parts)
                        indent = "    " * (current_depth - 1)
                        f.write(f"{indent}└── {relative_path.name}/\n")

                    # 2. Dosyaları Filtrele ve Yaz
                    filtered_files = [
                        fname for fname in files 
                        if Path(fname).suffix not in IGNORE_EXTENSIONS 
                        and fname != output_filename # Çıktı dosyasını listeye ekleme
                    ]

                    file_indent = "    " * current_depth
                    for i, fname in enumerate(filtered_files):
                        is_last = (i == len(filtered_files) - 1)
                        prefix = "└──" if is_last else "├──"
                        f.write(f"{file_indent}{prefix} {fname}\n")

            print(f"✅ Klasör yapısı '{output_filename}' dosyasına yazıldı.")

        except Exception as e:
            print(f"❌ Hata: {e}") 
            
    @staticmethod
    def fix_path_comments():
        """
        Dosya başındaki yolu kontrol eder:
        - Yanlışsa siler ve doğrusunu ekler.
        - Yoksa ekler.
        - Doğruysa dokunmaz.
        """
        root_dir = Path.cwd()
        print(f"--- Güncelleme İşlemi Başlatıldı ---")

        updated_count = 0
        correct_count = 0

        for py_file in root_dir.rglob("*.py"):
            if py_file.name == "tapphelper.py" or not py_file.is_file():
                continue
            
            try:
                relative_path = py_file.relative_to(root_dir)
                correct_comment = f"# {relative_path}\n"
                
                with open(py_file, "r", encoding="utf-8") as f:
                    content = f.readlines()

                needs_update = False
                
                if content and content[0].startswith("# "):
                    if content[0] == correct_comment:
                        # Zaten doğru yol ekli
                        correct_count += 1
                        continue
                    else:
                        # Başında yorum var ama YANLIŞ yol. 
                        # İlk satırı atıp yenisini ekleyeceğiz.
                        content = content[1:]
                        needs_update = True
                else:
                    # Başında hiç yorum satırı yok
                    needs_update = True

                if needs_update:
                    new_content = [correct_comment] + content
                    with open(py_file, "w", encoding="utf-8") as f:
                        f.writelines(new_content)
                    
                    print(f"Güncellendi: {relative_path}")
                    updated_count += 1

            except Exception as e:
                print(f"Hata ({py_file.name}): {e}")

        print(f"\n--- İşlem Tamamlandı ---")
        print(f"Güncellenen/Eklenen: {updated_count} | Zaten Doğru: {correct_count}")