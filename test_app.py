import sys, os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer
from yolo_annotator.ui.main_window import MainWindow

dataset_dir = "/tmp/test_dataset2"
os.makedirs(dataset_dir, exist_ok=True)
open(os.path.join(dataset_dir, "test1.jpg"), "w").close()
open(os.path.join(dataset_dir, "test1.json"), "w").write('{"shapes":[]}')
open(os.path.join(dataset_dir, "test2.jpg"), "w").close()
open(os.path.join(dataset_dir, "test2.json"), "w").write('{"shapes":[]}')

app = QApplication(sys.argv)
window = MainWindow()
window.dataset_dir = dataset_dir
window.image_files = [os.path.join(dataset_dir, "test1.jpg"), os.path.join(dataset_dir, "test2.jpg")]
window.current_image_idx = 0
window.current_image_path = window.image_files[0]
# fake pixmap to avoid error
from PyQt5.QtGui import QPixmap
window.viewer.set_image(QPixmap())

print("Before delete:", os.listdir(dataset_dir))

# patch messagebox to auto-yes
from PyQt5.QtWidgets import QMessageBox
QMessageBox.question = lambda *args, **kwargs: QMessageBox.Yes
window.delete_current_image()

print("After delete:", os.listdir(dataset_dir))
sys.exit(0)
