# pharmalizer_v2/app/licensing/manager.py
import os


def get_app_data_dir(app_folder_name: str = ".pharmalyzer") -> str:
    base_dir = os.path.expanduser("~")
    app_dir = os.path.join(base_dir, app_folder_name)
    os.makedirs(app_dir, exist_ok=True)
    return app_dir


def get_license_storage_path() -> str:
    """
    Lisans dosya yolunun kaydedileceği dosya:
    Örn: C:/Users/User/.pharmalyzer/license_path.txt
    """
    return os.path.join(get_app_data_dir(), "license_path.txt")


def read_saved_license_path() -> str | None:
    path_file = get_license_storage_path()
    if not os.path.exists(path_file):
        return None
    try:
        with open(path_file, "r", encoding="utf-8") as f:
            p = f.read().strip()
        return p or None
    except Exception:
        return None


def save_license_path(license_file_path: str) -> None:
    path_file = get_license_storage_path()
    with open(path_file, "w", encoding="utf-8") as f:
        f.write(license_file_path)
