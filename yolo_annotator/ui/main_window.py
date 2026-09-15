import os
from PyQt5.QtWidgets import QMainWindow, QToolBar, QAction, QFileDialog, QMessageBox, QDialog
from PyQt5.QtCore import Qt, QPointF, QRectF
from PyQt5.QtGui import QPixmap, QPolygonF

from .viewer import Viewer
from .dialogs import ClassSelectionDialog, ClassChangeDialog
from ..models.polygon_item import PolygonAnnotation
from ..models.box_item import BoxAnnotation
from ..utils.file_io import load_classes_txt, save_classes_txt

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YOLOv8 Instance Segmentation Etiketleme Aracı")
        self.resize(1024, 768)
        
        self.dataset_dir = ""
        self.image_files = []
        self.current_image_idx = -1
        self.classes = {}
        
        self.viewer = Viewer(self)
        self.viewer.on_polygon_completed = self.on_polygon_completed
        self.viewer.on_box_completed = self.on_box_completed
        self.viewer.on_scene_changed = self.save_labels
        self.viewer.on_right_click_item = self.on_right_click_item
        self.setCentralWidget(self.viewer)
        
        self.init_toolbar()
        
    def init_toolbar(self):
        toolbar = QToolBar("Ana Araç Çubuğu")
        self.addToolBar(toolbar)
        
        btn_open = QAction("📂 Klasör Seç", self)
        btn_open.triggered.connect(self.open_folder)
        toolbar.addAction(btn_open)
        
        toolbar.addSeparator()
        
        self.btn_draw = QAction("✏️ Çokgen Çiz (W)", self)
        self.btn_draw.setShortcut("W")
        self.btn_draw.setCheckable(True)
        self.btn_draw.setChecked(True)
        self.btn_draw.triggered.connect(lambda: self.set_mode('draw'))
        toolbar.addAction(self.btn_draw)
        
        self.btn_draw_box = QAction("🔲 Kutu Çiz (B)", self)
        self.btn_draw_box.setShortcut("B")
        self.btn_draw_box.setCheckable(True)
        self.btn_draw_box.triggered.connect(lambda: self.set_mode('draw_box'))
        toolbar.addAction(self.btn_draw_box)
        
        self.btn_edit = QAction("🖱️ Düzenle (E)", self)
        self.btn_edit.setShortcut("E")
        self.btn_edit.setCheckable(True)
        self.btn_edit.triggered.connect(lambda: self.set_mode('edit'))
        toolbar.addAction(self.btn_edit)
        
        toolbar.addSeparator()
        
        btn_prev = QAction("⬅️ Önceki (A)", self)
        btn_prev.setShortcut("A")
        btn_prev.triggered.connect(self.prev_image)
        toolbar.addAction(btn_prev)
        
        btn_next = QAction("➡️ Sonraki (D)", self)
        btn_next.setShortcut("D")
        btn_next.triggered.connect(self.next_image)
        toolbar.addAction(btn_next)
        
        toolbar.addSeparator()
        
        btn_fit = QAction("🔍 Ekrana Sığdır", self)
        btn_fit.triggered.connect(self.fit_window)
        toolbar.addAction(btn_fit)
        
        toolbar.addSeparator()
        
        btn_del_img = QAction("🗑️ Fotoğrafı Sil", self)
        btn_del_img.triggered.connect(self.delete_current_image)
        toolbar.addAction(btn_del_img)
        
    def set_mode(self, mode):
        self.viewer.mode = mode
        
        self.btn_draw.setChecked(mode == 'draw')
        self.btn_draw_box.setChecked(mode == 'draw_box')
        self.btn_edit.setChecked(mode == 'edit')
        
        if mode == 'draw' or mode == 'draw_box':
            self.viewer.scene.clearSelection()
        else:
            self.viewer.cancel_drawing()

    def open_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Dataset Ana Dizinini Seçin")
        if not folder: return
        
        self.dataset_dir = folder
        images_dir = os.path.join(self.dataset_dir, 'images')
        labels_dir = os.path.join(self.dataset_dir, 'labels')
        
        if not os.path.exists(images_dir):
            QMessageBox.warning(self, "Hata", f"Seçilen dizinde 'images' klasörü bulunamadı!\nLütfen dataset ana dizinini seçin.")
            return
            
        os.makedirs(labels_dir, exist_ok=True)
        self.classes = load_classes_txt(self.dataset_dir)
        
        supported_exts = ('.jpg', '.jpeg', '.png', '.bmp')
        self.image_files = []
        for file in os.listdir(images_dir):
            if file.lower().endswith(supported_exts):
                self.image_files.append(os.path.join(images_dir, file))
                
        self.image_files.sort()
        
        if not self.image_files:
            QMessageBox.warning(self, "Bilgi", "images klasöründe resim bulunamadı.")
            return
            
        self.current_image_idx = 0
        self.load_current_image()

    def load_current_image(self):
        if self.current_image_idx < 0 or self.current_image_idx >= len(self.image_files):
            return
            
        path = self.image_files[self.current_image_idx]
        self.current_image_path = path
        
        pixmap = QPixmap(path)
        if pixmap.isNull():
            QMessageBox.warning(self, "Hata", f"Resim yüklenemedi:\n{path}")
            return
            
        self.viewer.set_image(pixmap)
        self.load_labels()
        self.fit_window()
        
        file_name = os.path.basename(path)
        self.setWindowTitle(f"YOLOv8 Etiketleme - {file_name} ({self.current_image_idx+1}/{len(self.image_files)})")
        
    def prev_image(self):
        if self.image_files and self.current_image_idx > 0:
            self.current_image_idx -= 1
            self.load_current_image()
            
    def next_image(self):
        if self.image_files and self.current_image_idx < len(self.image_files) - 1:
            self.current_image_idx += 1
            self.load_current_image()
            
    def fit_window(self):
        if self.viewer.pixmap_item:
            self.viewer.setTransform(self.viewer.transform().fromScale(1, 1))
            self.viewer.fitInView(self.viewer.scene.sceneRect(), Qt.KeepAspectRatio)

    def delete_current_image(self):
        if not self.image_files or self.current_image_idx < 0:
            return
            
        path = self.image_files[self.current_image_idx]
        
        reply = QMessageBox.question(self, 'Onay', 
                                     f"Bu fotoğrafı ve etiket dosyasını (varsa) kalıcı olarak silmek istediğinize emin misiniz?\n\n{os.path.basename(path)}",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                                     
        if reply == QMessageBox.Yes:
            try:
                os.remove(path)
            except Exception as e:
                QMessageBox.warning(self, "Hata", f"Fotoğraf silinemedi: {e}")
                return
                
            labels_dir = os.path.join(self.dataset_dir, 'labels')
            base_name = os.path.splitext(os.path.basename(path))[0]
            txt_path = os.path.join(labels_dir, f"{base_name}.txt")
            if os.path.exists(txt_path):
                try:
                    os.remove(txt_path)
                except Exception as e:
                    print(f"Etiket silinemedi: {e}")
                    
            del self.image_files[self.current_image_idx]
            
            if not self.image_files:
                self.viewer.scene.clear()
                self.viewer.pixmap_item = None
                self.current_image_idx = -1
                self.setWindowTitle("YOLOv8 Instance Segmentation Etiketleme Aracı")
            else:
                if self.current_image_idx >= len(self.image_files):
                    self.current_image_idx = len(self.image_files) - 1
                self.load_current_image()

    def save_classes(self):
        save_classes_txt(self.dataset_dir, self.classes)

    def on_polygon_completed(self, poly):
        dialog = ClassSelectionDialog(self.classes, self.save_classes, self)
        if dialog.exec_() == QDialog.Accepted:
            cid, cname = dialog.get_selected_class()
            if cid is not None:
                item = PolygonAnnotation(poly, cid, cname, on_right_click=self.on_right_click_item)
                self.viewer.scene.addItem(item)
                self.save_labels()
                
    def on_box_completed(self, rect):
        dialog = ClassSelectionDialog(self.classes, self.save_classes, self)
        if dialog.exec_() == QDialog.Accepted:
            cid, cname = dialog.get_selected_class()
            if cid is not None:
                item = BoxAnnotation(rect, cid, cname, on_right_click=self.on_right_click_item)
                self.viewer.scene.addItem(item)
                self.save_labels()

    def on_right_click_item(self, item, screen_pos):
        if self.viewer.mode != 'edit':
            return
            
        dialog = ClassChangeDialog(item.class_id, self.classes, self.save_classes, self)
        dialog.move(int(screen_pos.x()), int(screen_pos.y()))
        
        if dialog.exec_() == QDialog.Accepted:
            cid, cname = dialog.get_selected_class()
            if cid is not None and (cid != item.class_id):
                item.update_class(cid, cname)

    def save_labels(self):
        if not hasattr(self, 'current_image_path') or not self.dataset_dir:
            return
        
        labels_dir = os.path.join(self.dataset_dir, 'labels')
        base_name = os.path.splitext(os.path.basename(self.current_image_path))[0]
        txt_path = os.path.join(labels_dir, f"{base_name}.txt")
        
        items = self.viewer.scene.items()
        annotations = [it for it in items if isinstance(it, (PolygonAnnotation, BoxAnnotation))]
        
        if not annotations:
            if os.path.exists(txt_path):
                os.remove(txt_path)
            return
            
        with open(txt_path, 'w', encoding='utf-8') as f:
            for item in annotations:
                cid = item.class_id
                
                if isinstance(item, PolygonAnnotation):
                    poly = item.polygon()
                    coords = []
                    for i in range(poly.count()):
                        pt = poly.at(i)
                        nx = pt.x() / self.viewer.img_width
                        ny = pt.y() / self.viewer.img_height
                        nx = max(0.0, min(1.0, nx))
                        ny = max(0.0, min(1.0, ny))
                        coords.extend([f"{nx:.6f}", f"{ny:.6f}"])
                    f.write(f"{cid} " + " ".join(coords) + "\n")
                    
                elif isinstance(item, BoxAnnotation):
                    rect = item.rect()
                    cx = rect.center().x() / self.viewer.img_width
                    cy = rect.center().y() / self.viewer.img_height
                    w = rect.width() / self.viewer.img_width
                    h = rect.height() / self.viewer.img_height
                    
                    cx = max(0.0, min(1.0, cx))
                    cy = max(0.0, min(1.0, cy))
                    w = max(0.0, min(1.0, w))
                    h = max(0.0, min(1.0, h))
                    
                    f.write(f"{cid} {cx:.6f} {cy:.6f} {w:.6f} {h:.6f}\n")

    def load_labels(self):
        if not hasattr(self, 'current_image_path') or not self.dataset_dir:
            return
            
        labels_dir = os.path.join(self.dataset_dir, 'labels')
        base_name = os.path.splitext(os.path.basename(self.current_image_path))[0]
        txt_path = os.path.join(labels_dir, f"{base_name}.txt")
        
        if not os.path.exists(txt_path):
            return
            
        with open(txt_path, 'r', encoding='utf-8') as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) < 5: continue
                
                try:
                    cid = int(parts[0])
                except ValueError:
                    continue
                    
                cname = self.classes.get(cid, f"Class {cid}")
                
                # Check if it's a Box (5 parts) or Polygon (>5 parts)
                if len(parts) == 5:
                    nx = float(parts[1])
                    ny = float(parts[2])
                    nw = float(parts[3])
                    nh = float(parts[4])
                    
                    cx = nx * self.viewer.img_width
                    cy = ny * self.viewer.img_height
                    w = nw * self.viewer.img_width
                    h = nh * self.viewer.img_height
                    
                    rect = QRectF(cx - w/2, cy - h/2, w, h)
                    item = BoxAnnotation(rect, cid, cname, on_right_click=self.on_right_click_item)
                    self.viewer.scene.addItem(item)
                    
                else: # Polygon
                    points = []
                    for i in range(1, len(parts), 2):
                        if i+1 < len(parts):
                            nx = float(parts[i])
                            ny = float(parts[i+1])
                            px = nx * self.viewer.img_width
                            py = ny * self.viewer.img_height
                            points.append(QPointF(px, py))
                            
                    if len(points) >= 3:
                        poly = QPolygonF(points)
                        item = PolygonAnnotation(poly, cid, cname, on_right_click=self.on_right_click_item)
                        self.viewer.scene.addItem(item)
