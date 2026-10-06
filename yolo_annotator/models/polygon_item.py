import random
from PyQt5.QtWidgets import QGraphicsItem, QGraphicsPolygonItem, QGraphicsEllipseItem
from PyQt5.QtCore import Qt, QPointF
from PyQt5.QtGui import QColor, QBrush, QPen

class VertexHandle(QGraphicsEllipseItem):
    def __init__(self, index, polygon_item, parent=None):
        super().__init__(-6, -6, 12, 12, parent)
        self.index = index
        self.polygon_item = polygon_item
        
        self.setBrush(QBrush(Qt.white))
        self.setPen(QPen(Qt.black, 1))
        
        self.setAcceptHoverEvents(True)
        self.setCursor(Qt.CrossCursor)
        self.hide()
        
        self._is_dragging = False

    def hoverEnterEvent(self, event):
        self.setBrush(QBrush(Qt.red))
        super().hoverEnterEvent(event)
        
    def hoverLeaveEvent(self, event):
        self.setBrush(QBrush(Qt.white))
        super().hoverLeaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._is_dragging = True
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._is_dragging:
            new_pos = self.mapToParent(event.pos())
            self.polygon_item.update_vertex(self.index, new_pos)
            self.setPos(new_pos)
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._is_dragging = False
            self.polygon_item.notify_scene_changed()
            event.accept()
        else:
            super().mouseReleaseEvent(event)


class PolygonAnnotation(QGraphicsPolygonItem):
    def __init__(self, poly, class_name, on_right_click=None, parent=None):
        super().__init__(poly, parent)
        self.class_name = class_name
        self.on_right_click = on_right_click
        
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self.setZValue(10)
        
        self.base_color = self.get_color(class_name)
        
        self.setBrush(QBrush(QColor(self.base_color.red(), self.base_color.green(), self.base_color.blue(), 100)))
        self.setPen(QPen(self.base_color, 2, Qt.SolidLine))
        
        self.handles = []
        self.create_handles()
        
    def get_color(self, name):
        rng = random.Random(name)
        r = rng.randint(50, 255)
        g = rng.randint(50, 255)
        b = rng.randint(50, 255)
        return QColor(r, g, b)
        
    def create_handles(self):
        poly = self.polygon()
        for i in range(poly.count()):
            handle = VertexHandle(i, self, self)
            handle.setPos(poly.at(i))
            self.handles.append(handle)
            
    def update_vertex(self, index, new_pos):
        poly = self.polygon()
        poly.replace(index, new_pos)
        self.setPolygon(poly)
        
    def notify_scene_changed(self):
        scene = self.scene()
        if scene:
            for view in scene.views():
                if hasattr(view, 'on_scene_changed') and view.on_scene_changed:
                    view.on_scene_changed()
                    return

    def update_class(self, new_class_name):
        self.class_name = new_class_name
        self.base_color = self.get_color(new_class_name)
        self.setBrush(QBrush(QColor(self.base_color.red(), self.base_color.green(), self.base_color.blue(), 100)))
        if self.isSelected():
            self.setPen(QPen(Qt.white, 3, Qt.DashLine))
        else:
            self.setPen(QPen(self.base_color, 2, Qt.SolidLine))
        self.notify_scene_changed()

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemSelectedChange:
            if value:
                self.setPen(QPen(Qt.white, 3, Qt.DashLine))
                for h in self.handles: h.show()
            else:
                self.setPen(QPen(self.base_color, 2, Qt.SolidLine))
                for h in self.handles: h.hide()
        elif change == QGraphicsItem.ItemPositionHasChanged:
            self.notify_scene_changed()
        return super().itemChange(change, value)
        
    def contextMenuEvent(self, event):
        if self.on_right_click:
            self.on_right_click(self, event.screenPos())
        super().contextMenuEvent(event)
