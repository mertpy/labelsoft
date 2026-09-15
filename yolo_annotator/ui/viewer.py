import math
from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QMessageBox
from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QPainter, QPen, QBrush, QPolygonF

from ..models.polygon_item import PolygonAnnotation

class Viewer(QGraphicsView):
    """
    Görüntüleme, yakınlaştırma, kaydırma ve çizim işlemlerini yöneten ana görünüm sınıfı.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        
        self.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        
        self.mode = 'draw'  # 'draw' veya 'edit'
        self.pixmap_item = None
        self.img_width = 0
        self.img_height = 0
        
        # Panning Değişkenleri
        self._is_panning = False
        self._pan_start = None
        
        # Drawing Değişkenleri
        self.current_points = []
        self.temp_lines = []
        self.temp_points = []
        self.first_point_item = None
        self.floating_line = None
        self.snap_threshold = 4
        
        # Callback'ler
        self.on_polygon_completed = None
        self.on_scene_changed = None
        self.on_right_click_polygon = None

    def set_image(self, pixmap):
        self.scene.clear()
        self.pixmap_item = QGraphicsPixmapItem(pixmap)
        self.scene.addItem(self.pixmap_item)
        
        self.img_width = pixmap.width()
        self.img_height = pixmap.height()
        self.scene.setSceneRect(QRectF(pixmap.rect()))
        self.cancel_drawing()

    def wheelEvent(self, event):
        if not self.pixmap_item: return
        zoomInFactor = 1.15
        zoomOutFactor = 1 / zoomInFactor
        
        if event.angleDelta().y() > 0:
            zoomFactor = zoomInFactor
        else:
            zoomFactor = zoomOutFactor
            
        self.scale(zoomFactor, zoomFactor)

    def mousePressEvent(self, event):
        if event.button() == Qt.MiddleButton:
            self._is_panning = True
            self._pan_start = event.pos()
            self.viewport().setCursor(Qt.ClosedHandCursor)
            return

        if event.button() == Qt.LeftButton:
            if self.mode == 'draw':
                self.handle_draw_press(event)
            elif self.mode == 'edit':
                super().mousePressEvent(event)
                
    def mouseMoveEvent(self, event):
        if self._is_panning:
            delta = event.pos() - self._pan_start
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
            self._pan_start = event.pos()
            return
            
        if self.mode == 'draw' and self.current_points:
            self.handle_draw_move(event)
            
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MiddleButton:
            self._is_panning = False
            self.viewport().setCursor(Qt.ArrowCursor)
            return
        super().mouseReleaseEvent(event)

    def handle_draw_press(self, event):
        if not self.pixmap_item: return
        scene_pos = self.mapToScene(event.pos())
        
        scene_pos.setX(max(0, min(self.img_width, scene_pos.x())))
        scene_pos.setY(max(0, min(self.img_height, scene_pos.y())))

        if self.current_points:
            view_pt0 = self.mapFromScene(self.current_points[0])
            dist = math.hypot(event.pos().x() - view_pt0.x(), event.pos().y() - view_pt0.y())
            if dist <= self.snap_threshold:
                self.finish_polygon()
                return
                
        self.current_points.append(scene_pos)
        
        pt_item = self.scene.addEllipse(scene_pos.x()-2, scene_pos.y()-2, 4, 4, QPen(Qt.red), QBrush(Qt.red))
        self.temp_points.append(pt_item)
        
        if len(self.current_points) == 1:
            self.first_point_item = pt_item
            
        if len(self.current_points) > 1:
            p1 = self.current_points[-2]
            p2 = self.current_points[-1]
            line = self.scene.addLine(p1.x(), p1.y(), p2.x(), p2.y(), QPen(Qt.red, 2))
            self.temp_lines.append(line)
            
        if not self.floating_line:
            self.floating_line = self.scene.addLine(scene_pos.x(), scene_pos.y(), scene_pos.x(), scene_pos.y(), QPen(Qt.red, 2, Qt.DashLine))
        else:
            self.floating_line.setLine(scene_pos.x(), scene_pos.y(), scene_pos.x(), scene_pos.y())
            self.floating_line.show()

    def handle_draw_move(self, event):
        scene_pos = self.mapToScene(event.pos())
        if self.floating_line:
            last_pt = self.current_points[-1]
            self.floating_line.setLine(last_pt.x(), last_pt.y(), scene_pos.x(), scene_pos.y())
            
        view_pt0 = self.mapFromScene(self.current_points[0])
        dist = math.hypot(event.pos().x() - view_pt0.x(), event.pos().y() - view_pt0.y())
        if dist <= self.snap_threshold:
            self.first_point_item.setRect(self.current_points[0].x()-4, self.current_points[0].y()-4, 8, 8)
            self.first_point_item.setBrush(QBrush(Qt.green))
        else:
            self.first_point_item.setRect(self.current_points[0].x()-2, self.current_points[0].y()-2, 4, 4)
            self.first_point_item.setBrush(QBrush(Qt.red))

    def undo_last_point(self):
        """Çizim sırasında son eklenen noktayı geri alır (Ctrl+Z)"""
        if not self.current_points:
            return
            
        self.current_points.pop()
        
        if self.temp_points:
            item = self.temp_points.pop()
            self.scene.removeItem(item)
            if item == self.first_point_item:
                self.first_point_item = None
                
        if self.temp_lines:
            item = self.temp_lines.pop()
            self.scene.removeItem(item)
            
        if not self.current_points:
            if self.floating_line:
                self.scene.removeItem(self.floating_line)
                self.floating_line = None
        else:
            # Floating line update
            cursor_pos = self.mapFromGlobal(self.cursor().pos())
            scene_pos = self.mapToScene(cursor_pos)
            last_pt = self.current_points[-1]
            self.floating_line.setLine(last_pt.x(), last_pt.y(), scene_pos.x(), scene_pos.y())

    def finish_polygon(self):
        if len(self.current_points) < 3:
            self.cancel_drawing()
            return
            
        poly = QPolygonF(self.current_points)
        self.cancel_drawing()
        
        if self.on_polygon_completed:
            self.on_polygon_completed(poly)

    def cancel_drawing(self):
        for item in self.temp_lines:
            self.scene.removeItem(item)
        for item in self.temp_points:
            self.scene.removeItem(item)
        if self.floating_line:
            self.scene.removeItem(self.floating_line)
            self.floating_line = None
            
        self.current_points = []
        self.temp_lines = []
        self.temp_points = []
        self.first_point_item = None

    def keyPressEvent(self, event):
        # Ctrl+Z ile geri alma
        if event.key() == Qt.Key_Z and (event.modifiers() & Qt.ControlModifier):
            if self.mode == 'draw':
                self.undo_last_point()
                return

        if event.key() == Qt.Key_Escape and self.mode == 'draw':
            self.cancel_drawing()
            
        elif event.key() == Qt.Key_Delete and self.mode == 'edit':
            selected = self.scene.selectedItems()
            deleted_poly = False
            for item in selected:
                # VertexHandle silinmesini engellemek için sadece PolygonAnnotation'ları siliyoruz
                if isinstance(item, PolygonAnnotation):
                    self.scene.removeItem(item)
                    deleted_poly = True
            
            if deleted_poly and self.on_scene_changed:
                self.on_scene_changed()
                    
        super().keyPressEvent(event)
