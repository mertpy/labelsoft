import math
from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QMessageBox
from PyQt5.QtCore import Qt, QRectF, QPointF
from PyQt5.QtGui import QPainter, QPen, QBrush, QPolygonF

from ..models.polygon_item import PolygonAnnotation
from ..models.box_item import BoxAnnotation

class Viewer(QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        
        self.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        
        # Mouse takibi (crosshair için)
        self.setMouseTracking(True)
        
        self.mode = 'draw'  # 'draw', 'draw_box' veya 'edit'
        self.pixmap_item = None
        self.img_width = 0
        self.img_height = 0
        
        self._is_panning = False
        self._pan_start = None
        
        # Drawing Polygon
        self.current_points = []
        self.temp_lines = []
        self.temp_points = []
        self.first_point_item = None
        self.floating_line = None
        self.snap_threshold = 4
        
        # Drawing Box
        self.box_start_pt = None
        self.temp_box_item = None
        
        # Crosshair
        pen = QPen(Qt.white, 1, Qt.DashLine)
        self.crosshair_v = self.scene.addLine(0,0,0,0, pen)
        self.crosshair_h = self.scene.addLine(0,0,0,0, pen)
        self.crosshair_v.hide()
        self.crosshair_h.hide()
        
        self.on_polygon_completed = None
        self.on_box_completed = None
        self.on_scene_changed = None
        self.on_right_click_item = None

    def set_image(self, pixmap):
        self.scene.clear()
        
        # Re-add crosshairs because clear() deleted them
        pen = QPen(Qt.white, 1, Qt.DashLine)
        self.crosshair_v = self.scene.addLine(0,0,0,0, pen)
        self.crosshair_h = self.scene.addLine(0,0,0,0, pen)
        self.crosshair_v.setZValue(9999) # Always on top
        self.crosshair_h.setZValue(9999)
        self.crosshair_v.hide()
        self.crosshair_h.hide()
        
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
        
    def update_crosshair(self, scene_pos):
        if self.pixmap_item and 0 <= scene_pos.x() <= self.img_width and 0 <= scene_pos.y() <= self.img_height:
            self.crosshair_v.setLine(scene_pos.x(), 0, scene_pos.x(), self.img_height)
            self.crosshair_h.setLine(0, scene_pos.y(), self.img_width, scene_pos.y())
            self.crosshair_v.show()
            self.crosshair_h.show()
        else:
            self.crosshair_v.hide()
            self.crosshair_h.hide()

    def mousePressEvent(self, event):
        if event.button() == Qt.MiddleButton:
            self._is_panning = True
            self._pan_start = event.pos()
            self.viewport().setCursor(Qt.ClosedHandCursor)
            return

        if event.button() == Qt.LeftButton:
            if self.mode == 'draw':
                self.handle_draw_press(event)
            elif self.mode == 'draw_box':
                self.handle_box_press(event)
            elif self.mode == 'edit':
                super().mousePressEvent(event)
                
    def mouseMoveEvent(self, event):
        scene_pos = self.mapToScene(event.pos())
        self.update_crosshair(scene_pos)
        
        if self._is_panning:
            delta = event.pos() - self._pan_start
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
            self._pan_start = event.pos()
            return
            
        if self.mode == 'draw' and self.current_points:
            self.handle_draw_move(event)
        elif self.mode == 'draw_box' and self.box_start_pt is not None:
            self.handle_box_move(event)
            
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MiddleButton:
            self._is_panning = False
            self.viewport().setCursor(Qt.ArrowCursor)
            return
        
        if event.button() == Qt.LeftButton and self.mode == 'draw_box' and self.box_start_pt is not None:
            self.handle_box_release(event)
            
        super().mouseReleaseEvent(event)

    def leaveEvent(self, event):
        self.crosshair_v.hide()
        self.crosshair_h.hide()
        super().leaveEvent(event)

    # --- POLYGON DRAWING ---
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

    # --- BOX DRAWING ---
    def handle_box_press(self, event):
        if not self.pixmap_item: return
        scene_pos = self.mapToScene(event.pos())
        scene_pos.setX(max(0, min(self.img_width, scene_pos.x())))
        scene_pos.setY(max(0, min(self.img_height, scene_pos.y())))
        
        self.box_start_pt = scene_pos
        self.temp_box_item = self.scene.addRect(QRectF(scene_pos, scene_pos), QPen(Qt.red, 2), QBrush(Qt.transparent))
        
    def handle_box_move(self, event):
        if not self.temp_box_item: return
        scene_pos = self.mapToScene(event.pos())
        scene_pos.setX(max(0, min(self.img_width, scene_pos.x())))
        scene_pos.setY(max(0, min(self.img_height, scene_pos.y())))
        
        rect = QRectF(self.box_start_pt, scene_pos).normalized()
        self.temp_box_item.setRect(rect)
        
    def handle_box_release(self, event):
        if not self.temp_box_item: return
        
        rect = self.temp_box_item.rect()
        self.cancel_drawing()
        
        if rect.width() > 2 and rect.height() > 2:
            if self.on_box_completed:
                self.on_box_completed(rect)

    def cancel_drawing(self):
        # Polygon cancels
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
        
        # Box cancels
        self.box_start_pt = None
        if self.temp_box_item:
            self.scene.removeItem(self.temp_box_item)
            self.temp_box_item = None

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Z and (event.modifiers() & Qt.ControlModifier):
            if self.mode == 'draw':
                self.undo_last_point()
                return

        if event.key() == Qt.Key_Escape and self.mode in ['draw', 'draw_box']:
            self.cancel_drawing()
            
        elif event.key() == Qt.Key_Delete and self.mode == 'edit':
            selected = self.scene.selectedItems()
            deleted_item = False
            for item in selected:
                if isinstance(item, (PolygonAnnotation, BoxAnnotation)):
                    self.scene.removeItem(item)
                    deleted_item = True
            
            if deleted_item and self.on_scene_changed:
                self.on_scene_changed()
                    
        super().keyPressEvent(event)
