import math
import os
import json
from PyQt5.QtWidgets import QMainWindow, QToolBar, QAction, QFileDialog, QMessageBox, QDialog, QStatusBar
from PyQt5.QtCore import Qt, QPointF, QRectF, QTimer
from PyQt5.QtGui import QPixmap, QPolygonF, QPen

from .viewer import Viewer
from .dialogs import ClassSelectionDialog, ClassChangeDialog, CameraSettingsDialog
from ..models.polygon_item import PolygonAnnotation
from ..models.box_item import BoxAnnotation
from ..utils.file_io import scan_classes_from_jsons
from ..utils.updater import UpdateWorker

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Labelsoft")
        self.resize(1024, 768)
        
        self.dataset_dir = ""
        self.image_files = []
        self.current_image_idx = -1
        self.classes = []
        self.last_used_class = None
        
        self.camera_settings = {
            'camera_height_m': 1.20,
            'fov_h_deg': 82,
            'ref_width': 3840.0,
            'ref_height': 2160.0
        }
        
        self.viewer = Viewer(self)
        self.viewer.on_polygon_completed = self.on_polygon_completed
        self.viewer.on_box_completed = self.on_box_completed
        self.viewer.on_scene_changed = self.on_scene_changed_handler
        self.viewer.on_right_click_item = self.on_right_click_item
        self.viewer.on_selection_changed = self.calculate_and_display_dimensions
        self.viewer.on_drawing_progress = self.on_drawing_progress_handler
        self.setCentralWidget(self.viewer)
        
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Çizim bekleniyor...")
        
        self.init_toolbar()
        self.set_mode('draw_box')
        
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
        self.btn_draw.triggered.connect(lambda: self.set_mode('draw'))
        toolbar.addAction(self.btn_draw)
        
        self.btn_draw_box = QAction("🔲 Kutu Çiz (B)", self)
        self.btn_draw_box.setShortcut("B")
        self.btn_draw_box.setCheckable(True)
        self.btn_draw_box.setChecked(True)
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
        
        toolbar.addSeparator()
        
        btn_camera = QAction("⚙️ Kamera Ayarları", self)
        btn_camera.triggered.connect(self.open_camera_settings)
        toolbar.addAction(btn_camera)
        
        toolbar.addSeparator()
        
        self.btn_update = QAction("🔄 Güncelle", self)
        self.btn_update.triggered.connect(self.start_update)
        toolbar.addAction(self.btn_update)
        
    def start_update(self):
        reply = QMessageBox.question(
            self, 'Güncelleme',
            'GitHub\'dan son sürümü indirmek istiyor musunuz?\n\n'
            'Güncelleme sonrası uygulamanın yeniden başlatılması gerekir.',
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply != QMessageBox.Yes:
            return
            
        install_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        
        self.btn_update.setEnabled(False)
        self.btn_update.setText("🔄 Güncelleniyor...")
        self.status_bar.showMessage("Güncelleme başlatıldı...")
        
        self._update_worker = UpdateWorker(install_dir, self)
        self._update_worker.progress.connect(self._on_update_progress)
        self._update_worker.finished_ok.connect(self._on_update_ok)
        self._update_worker.finished_err.connect(self._on_update_err)
        self._update_worker.start()
        
    def _on_update_progress(self, msg):
        self.status_bar.showMessage(msg)
        
    def _on_update_ok(self):
        self.btn_update.setEnabled(True)
        self.btn_update.setText("🔄 Güncelle")
        QMessageBox.information(
            self, 'Güncelleme Tamamlandı',
            'Güncelleme başarıyla tamamlandı!\n\n'
            'Değişikliklerin geçerli olması için uygulamayı yeniden başlatın.'
        )
        
    def _on_update_err(self, err_msg):
        self.btn_update.setEnabled(True)
        self.btn_update.setText("🔄 Güncelle")
        self.status_bar.showMessage("Güncelleme başarısız.")
        QMessageBox.warning(self, 'Güncelleme Hatası', f'Güncelleme sırasında hata oluştu:\n\n{err_msg}')

    def open_camera_settings(self):
        dialog = CameraSettingsDialog(self.camera_settings, self)
        if dialog.exec_() == QDialog.Accepted:
            self.camera_settings.update(dialog.get_settings())
            # Yeniden hesapla
            selected = self.viewer.scene.selectedItems()
            if selected:
                for item in selected:
                    if isinstance(item, (PolygonAnnotation, BoxAnnotation)):
                        self.calculate_and_display_dimensions(item)
                        break
                        
    def on_scene_changed_handler(self):
        self.save_labels()
        selected = self.viewer.scene.selectedItems()
        if selected:
            for item in selected:
                if isinstance(item, (PolygonAnnotation, BoxAnnotation)):
                    self.calculate_and_display_dimensions(item)
                    break
        else:
            self.calculate_and_display_dimensions(None)
            
    def on_drawing_progress_handler(self, rect):
        if not rect:
            self.status_bar.showMessage("Çizim bekleniyor...")
            return
            
        px_w = rect.width()
        px_h = rect.height()
        
        cam_h = self.camera_settings.get('camera_height_m', 0.90)
        fov_deg = self.camera_settings.get('fov_h_deg', 120.0)
        ref_w = self.camera_settings.get('ref_width', 3840.0)
        
        if ref_w <= 0: ref_w = 3840.0
        
        fov_rad = math.radians(fov_deg)
        real_ground_width_m = 2 * cam_h * math.tan(fov_rad / 2)
        m_per_px = real_ground_width_m / ref_w
        
        real_w_cm = (px_w * m_per_px) * 100
        real_h_cm = (px_h * m_per_px) * 100
        
        if self.viewer.temp_box_item:
            if real_w_cm > 3.0 and real_h_cm > 3.0:
                self.viewer.temp_box_item.setPen(QPen(Qt.green, 2))
            else:
                self.viewer.temp_box_item.setPen(QPen(Qt.red, 2))
        
        
        msg = f"Çiziliyor... | Gerçek Boyut: {real_w_cm:.1f}x{real_h_cm:.1f} cm | Piksel: {int(px_w)}x{int(px_h)} px"
        self.status_bar.showMessage(msg)
            
    def calculate_and_display_dimensions(self, item):
        if not item:
            self.status_bar.showMessage("Çizim bekleniyor...")
            return
            
        rect = item.sceneBoundingRect()
        px_w = rect.width()
        px_h = rect.height()
        
        cam_h = self.camera_settings.get('camera_height_m', 1.60)
        fov_deg = self.camera_settings.get('fov_h_deg', 70.0)
        ref_w = self.camera_settings.get('ref_width', 3840.0)
        
        if ref_w <= 0: ref_w = 3840.0
        
        fov_rad = math.radians(fov_deg)
        real_ground_width_m = 2 * cam_h * math.tan(fov_rad / 2)
        m_per_px = real_ground_width_m / ref_w
        
        # Original scaling
        real_w_cm = (px_w * m_per_px) * 100
        real_h_cm = (px_h * m_per_px) * 100
        
        cname = item.class_name
        msg = f"Seçilen: {cname} | Gerçek Boyut: {real_w_cm:.1f}x{real_h_cm:.1f} cm | Piksel: {int(px_w)}x{int(px_h)} px"
        self.status_bar.showMessage(msg)
        
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
        self.classes = scan_classes_from_jsons(self.dataset_dir)
        
        supported_exts = ('.jpg', '.jpeg', '.png', '.bmp')
        self.image_files = []
        for file in os.listdir(self.dataset_dir):
            if file.lower().endswith(supported_exts):
                self.image_files.append(os.path.join(self.dataset_dir, file))
                
        self.image_files.sort()
        
        if not self.image_files:
            QMessageBox.warning(self, "Bilgi", "Seçilen klasörde resim bulunamadı.")
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
        QTimer.singleShot(50, self.fit_window)
        
        file_name = os.path.basename(path)
        self.setWindowTitle(f"Labelsoft - {file_name} ({self.current_image_idx+1}/{len(self.image_files)})")
        
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
                
            base_name = os.path.splitext(os.path.basename(path))[0]
            json_path = os.path.join(self.dataset_dir, f"{base_name}.json")
            if os.path.exists(json_path):
                try:
                    os.remove(json_path)
                except Exception as e:
                    print(f"Etiket silinemedi: {e}")
                    
            del self.image_files[self.current_image_idx]
            self.classes = scan_classes_from_jsons(self.dataset_dir)
            
            if not self.image_files:
                self.viewer.scene.clear()
                self.viewer.pixmap_item = None
                self.current_image_idx = -1
                self.setWindowTitle("Labelsoft")
            else:
                if self.current_image_idx >= len(self.image_files):
                    self.current_image_idx = len(self.image_files) - 1
                self.load_current_image()

    def on_polygon_completed(self, poly):
        dialog = ClassSelectionDialog(self.classes, self.last_used_class, self)
        if dialog.exec_() == QDialog.Accepted:
            cname = dialog.get_selected_class()
            if cname:
                self.last_used_class = cname
                if cname not in self.classes:
                    self.classes.append(cname)
                item = PolygonAnnotation(poly, cname, on_right_click=self.on_right_click_item)
                self.viewer.scene.addItem(item)
                self.save_labels()
                
    def on_box_completed(self, rect):
        dialog = ClassSelectionDialog(self.classes, self.last_used_class, self)
        if dialog.exec_() == QDialog.Accepted:
            cname = dialog.get_selected_class()
            if cname:
                self.last_used_class = cname
                if cname not in self.classes:
                    self.classes.append(cname)
                item = BoxAnnotation(rect, cname, on_right_click=self.on_right_click_item)
                self.viewer.scene.addItem(item)
                self.save_labels()

    def on_right_click_item(self, item, screen_pos):
        if self.viewer.mode != 'edit':
            return
            
        dialog = ClassChangeDialog(item.class_name, self.classes, self)
        dialog.move(int(screen_pos.x()), int(screen_pos.y()))
        
        if dialog.exec_() == QDialog.Accepted:
            cname = dialog.get_selected_class()
            if cname and (cname != item.class_name):
                item.update_class(cname)

    def save_labels(self):
        if not hasattr(self, 'current_image_path') or not self.dataset_dir:
            return
        
        base_name = os.path.splitext(os.path.basename(self.current_image_path))[0]
        json_path = os.path.join(self.dataset_dir, f"{base_name}.json")
        
        items = self.viewer.scene.items()
        annotations = [it for it in items if isinstance(it, (PolygonAnnotation, BoxAnnotation))]
        
        if not annotations:
            if os.path.exists(json_path):
                os.remove(json_path)
            return
            
        data = {
            "version": "5.0.0",
            "flags": {},
            "shapes": [],
            "imagePath": os.path.basename(self.current_image_path),
            "imageData": None,
            "imageHeight": int(self.viewer.img_height),
            "imageWidth": int(self.viewer.img_width)
        }
            
        for item in annotations:
            shape = {
                "label": item.class_name,
                "points": [],
                "group_id": None,
                "shape_type": "",
                "flags": {}
            }
            
            if isinstance(item, PolygonAnnotation):
                shape["shape_type"] = "polygon"
                poly = item.polygon()
                for i in range(poly.count()):
                    pt = item.mapToScene(poly.at(i))
                    shape["points"].append([pt.x(), pt.y()])
                
            elif isinstance(item, BoxAnnotation):
                shape["shape_type"] = "rectangle"
                rect = item.sceneBoundingRect()
                shape["points"].append([rect.left(), rect.top()])
                shape["points"].append([rect.right(), rect.bottom()])
                
            data["shapes"].append(shape)
            
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def load_labels(self):
        if not hasattr(self, 'current_image_path') or not self.dataset_dir:
            return
            
        base_name = os.path.splitext(os.path.basename(self.current_image_path))[0]
        json_path = os.path.join(self.dataset_dir, f"{base_name}.json")
        
        if not os.path.exists(json_path):
            return
            
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception as e:
            print(f"JSON okuma hatası: {e}")
            return
            
        if "shapes" not in data:
            return
            
        for shape in data["shapes"]:
            cname = shape.get("label", "Unknown")
            shape_type = shape.get("shape_type", "polygon")
            points = shape.get("points", [])
            
            if cname not in self.classes:
                self.classes.append(cname)
            
            if shape_type == "rectangle" and len(points) >= 2:
                xmin, ymin = points[0]
                xmax, ymax = points[1]
                w = xmax - xmin
                h = ymax - ymin
                rect = QRectF(xmin, ymin, w, h)
                item = BoxAnnotation(rect, cname, on_right_click=self.on_right_click_item)
                self.viewer.scene.addItem(item)
            elif shape_type == "polygon" and len(points) >= 3:
                qpoints = [QPointF(pt[0], pt[1]) for pt in points]
                poly = QPolygonF(qpoints)
                item = PolygonAnnotation(poly, cname, on_right_click=self.on_right_click_item)
                self.viewer.scene.addItem(item)
