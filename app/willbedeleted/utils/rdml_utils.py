import os
import tempfile
import zipfile


def extract_xml_from_rdml(file_path: str):
    try:
        temp_dir = tempfile.mkdtemp()
        with zipfile.ZipFile(file_path, "r") as zip_ref:
            xml_file = next(
                (name for name in zip_ref.namelist() if name.endswith(".xml")), None
            )
            if xml_file:
                zip_ref.extract(xml_file, temp_dir)
                return True, os.path.join(temp_dir, xml_file)
        return False, ""
    except zipfile.BadZipFile:
        return False, "Geçersiz RDML dosyası."
    except Exception as e:
        return False, str(e)
