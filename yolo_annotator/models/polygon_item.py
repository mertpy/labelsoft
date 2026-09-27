import random
from PyQt5.QtWidgets import QGraphicsItem, QGraphicsPolygonItem, QGraphicsEllipseItem
from PyQt5.QtCore import Qt, QPointF
from PyQt5.QtGui import QColor, QBrush, QPen

class VertexHandle(QGraphicsEllipseItem):
    def __init__(self, index, polygon_item, parent=None):
        super().__init__(-4, -4, 8, 8, parent)
        self.index = index
        self.polygon_item = polygon_item
        
        self.setBrush(QBrush(Qt.white))
        self.setPen(QPen(Qt.black, 1))
        
        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self.setCursor(Qt.CrossCursor)
        self.hide()

    def hoverEnterEvent(self, event):
        self.setBrush(QBrush(Qt.red))
        super().hoverEnterEvent(event)
        
    def hoverLeaveEvent(self, event):
        self.setBrush(QBrush(Qt.white))
        super().hoverLeaveEvent(event)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange and self.scene():
            self.polygon_item.update_vertex(self.index, value)
        elif change == QGraphicsItem.ItemPositionHasChanged:
            self.polygon_item.notify_scene_changed()
            
        return super().itemChange(change, value)


class PolygonAnnotation(QGraphicsPolygonItem):
    def __init__(self, poly, class_name, on_right_click=None, parent=None):
        super().__init__(poly, parent)
        self.class_name = class_name
        self.on_right_click = on_right_click
        
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        
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
        if scene and hasattr(scene, 'on_scene_changed'):
            scene.on_scene_changed()

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
