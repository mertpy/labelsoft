"""
GitHub'dan son sürümü indirip yerel dosyaları güncelleyen modül.
Repo: https://github.com/mertpy/labelsoft
Branch: main
Güncellenen dosyalar: yolo_annotator/, main.py, README.md
"""
import os
import io
import zipfile
import shutil
import urllib.request
import urllib.error
from PyQt5.QtCore import QThread, pyqtSignal


GITHUB_REPO = "mertpy/labelsoft"
GITHUB_BRANCH = "main"
ZIPBALL_URL = f"https://github.com/{GITHUB_REPO}/archive/refs/heads/{GITHUB_BRANCH}.zip"

# Güncellenecek dosya ve klasörler
UPDATE_TARGETS = ["yolo_annotator", "main.py", "README.md"]


class UpdateWorker(QThread):
    """Arka planda güncelleme indiren thread."""
    progress = pyqtSignal(str)       # Durum mesajları
    finished_ok = pyqtSignal()       # Başarılı tamamlanma
    finished_err = pyqtSignal(str)   # Hata mesajı

    def __init__(self, install_dir, parent=None):
        super().__init__(parent)
        self.install_dir = install_dir

    def run(self):
        try:
            self.progress.emit("GitHub'dan son sürüm indiriliyor...")
            
            req = urllib.request.Request(ZIPBALL_URL)
            with urllib.request.urlopen(req, timeout=30) as response:
                zip_data = response.read()

            self.progress.emit("Arşiv açılıyor...")

            zip_buf = io.BytesIO(zip_data)
            with zipfile.ZipFile(zip_buf, 'r') as zf:
                # Zip içindeki kök klasör adını bul (örn: "labelsoft-main/")
                root_prefix = None
                for name in zf.namelist():
                    if '/' in name:
                        root_prefix = name.split('/')[0] + '/'
                        break

                if not root_prefix:
                    self.finished_err.emit("Zip arşivinde geçerli dosya bulunamadı.")
                    return

                self.progress.emit("Dosyalar güncelleniyor...")

                for target in UPDATE_TARGETS:
                    src_prefix = root_prefix + target
                    dest_path = os.path.join(self.install_dir, target)

                    # Hedef dosyaları bul
                    matching = [n for n in zf.namelist() 
                                if n == src_prefix or n.startswith(src_prefix + '/')]

                    if not matching:
                        self.progress.emit(f"  ⚠ '{target}' repoda bulunamadı, atlanıyor.")
                        continue

                    # Eğer klasör ise, önce eskisini sil
                    if os.path.isdir(dest_path):
                        # __pycache__ klasörlerini koru (silmek sorun yaratmaz ama gereksiz)
                        shutil.rmtree(dest_path, ignore_errors=True)

                    for member in matching:
                        # Zip içindeki göreli yolu hesapla
                        rel_path = member[len(root_prefix):]
                        if not rel_path:
                            continue

                        out_path = os.path.join(self.install_dir, rel_path)

                        if member.endswith('/'):
                            # Klasör
                            os.makedirs(out_path, exist_ok=True)
                        else:
                            # Dosya
                            os.makedirs(os.path.dirname(out_path), exist_ok=True)
                            with zf.open(member) as src, open(out_path, 'wb') as dst:
                                dst.write(src.read())

                    self.progress.emit(f"  ✓ '{target}' güncellendi.")

            self.progress.emit("Güncelleme tamamlandı!")
            self.finished_ok.emit()

        except urllib.error.URLError as e:
            self.finished_err.emit(f"İndirme hatası: {e.reason}")
        except Exception as e:
            self.finished_err.emit(f"Güncelleme hatası: {e}")
