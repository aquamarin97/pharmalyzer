import os

def create_tree_txt_plain(startpath, output_filename="tree_structure_plain.txt"):
    """
    Belirtilen başlangıç yolundaki klasör yapısını, 
    standart 'tree' komutuna benzer bir görünümde ve kalınlaştırma olmadan 
    .txt dosyasına yazar.

    :param startpath: Taranacak klasörün yolu.
    :param output_filename: Yapının yazılacağı çıktı dosyasının adı.
    """
    
    # Başlangıç yolunu tam yol (absolute path) olarak alalım.
    startpath = os.path.abspath(startpath)
    # Başlangıç klasörünün adını alalım.
    base_folder_name = os.path.basename(startpath)
    try:
        with open(output_filename, 'w', encoding='utf-8') as f:
            
            # İlk satırı, başlangıç klasörünün adı olarak yazıyoruz.
            f.write(f"{base_folder_name}/\n")

            # os.walk, klasörleri yinelemeli olarak gezer.
            for root, dirs, files in os.walk(startpath):
                # Başlangıç klasörünü atlayın.
                if root == startpath:
                    continue

                # Başlangıç yoluna göre göreceli yolu alın.
                relative_path = root[len(startpath) + len(os.sep):]
                
                # Derinliği hesaplayın.
                depth = relative_path.count(os.sep)

                # Geçerli klasörün adını alın.
                current_dir_name = os.path.basename(root)

                # --- Girinti ve Bağlayıcı Çizgileri Hesaplama ---
                indent = ""
                path_parts = relative_path.split(os.sep)[:-1] 
                
                # Her seviyedeki klasörün 'son' olup olmadığını kontrol ederek 
                # dikey çizgileri (│   ) veya boşlukları (    ) doğru yerleştirin.
                for i in range(depth):
                    # Bir üst seviyenin dizin listesini al.
                    parent_path = os.path.join(startpath, *path_parts[:i])
                    # os.walk'tan o seviyedeki dizin listesini alıyoruz.
                    try:
                        _, parent_dirs, _ = next(os.walk(parent_path))
                    except StopIteration:
                        # Eğer üst yol taranamıyorsa (izin hatası vb.), varsayılan çizgi kullan.
                        indent += "│   "
                        continue

                    # Eğer mevcut klasör, o seviyedeki son klasör değilse dikey çizgi kullan.
                    if path_parts[i] != parent_dirs[-1]:
                        indent += "│   "
                    else:
                        indent += "    "
                
                
                # --- Klasörün Kendisini Yazma ---
                parent_path = os.path.dirname(root)
                # Üst klasördeki dizin listesini alıyoruz.
                try:
                    _, parent_dirs, _ = next(os.walk(parent_path))
                except StopIteration:
                    parent_dirs = [] # Hata durumunda boş liste

                if current_dir_name in parent_dirs and current_dir_name == parent_dirs[-1]:
                    folder_prefix = "└──" # Son klasör
                    file_indent_prefix = "    "
                else:
                    folder_prefix = "├──" # Arada kalan klasör
                    file_indent_prefix = "│   "

                # Klasör adını kalınlaştırma olmadan yazın.
                f.write(f"{indent}{folder_prefix} {current_dir_name}/\n")

                # Dosyaları yazın.
                for i, file in enumerate(files):
                    file_prefix = "└──" if i == len(files) - 1 and not dirs else "├──"
                    f.write(f"{indent}{file_indent_prefix}{file_prefix} {file}\n")
            
            print(f"✅ Klasör yapısı başarıyla '{output_filename}' dosyasına yazıldı.")
            
    except Exception as e:
        print(f"❌ Bir hata oluştu: {e}")

# --- KULLANIM ---

# Betiğin çalıştığı klasörü tara.
folder_to_scan = "."

# Çıktı dosyasının adını belirtin.
output_file = "tree_yapisi_sonucu_sade.txt"

# Fonksiyonu çalıştırın.
create_tree_txt_plain(folder_to_scan, output_file)