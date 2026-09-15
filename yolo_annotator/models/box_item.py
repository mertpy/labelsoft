import random
from PyQt5.QtWidgets import QGraphicsItem, QGraphicsRectItem, QGraphicsEllipseItem
from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QColor, QBrush, QPen

class BoxHandle(QGraphicsEllipseItem):
    """
    Kutunun köşelerini temsil eder ve yeniden boyutlandırmayı sağlar.
    """
    def __init__(self, position_type, box_item, parent=None):
        super().__init__(-4, -4, 8, 8, parent)
        self.position_type = position_type # 'TL', 'TR', 'BL', 'BR'
        self.box_item = box_item
        
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
            self.box_item.update_handle_position(self.position_type, value)
        elif change == QGraphicsItem.ItemPositionHasChanged:
            self.box_item.notify_scene_changed()
            
        return super().itemChange(change, value)


class BoxAnnotation(QGraphicsRectItem):
    """
    Çizilen her bir kutuyu (Bounding Box) temsil eden sınıf.
    """
    def __init__(self, rect, class_id, class_name, on_right_click=None, parent=None):
        super().__init__(rect, parent)
        self.class_id = class_id
        self.class_name = class_name
        self.on_right_click = on_right_click
        
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        
        # Sınıfa özel kalıcı rastgele renk oluştur
        self.base_color = self.get_color(class_name)
        
        # Yarı saydam dolgu ve belirgin kenarlık
        self.setBrush(QBrush(QColor(self.base_color.red(), self.base_color.green(), self.base_color.blue(), 100)))
        self.setPen(QPen(self.base_color, 2, Qt.SolidLine))
        
        self.handles = {}
        self.create_handles()
        
    def get_color(self, name):
        rng = random.Random(name)
        r = rng.randint(50, 255)
        g = rng.randint(50, 255)
        b = rng.randint(50, 255)
        return QColor(r, g, b)
        
    def create_handles(self):
        positions = ['TL', 'TR', 'BL', 'BR']
        for pos in positions:
            handle = BoxHandle(pos, self, self)
            self.handles[pos] = handle
        self.update_handles_pos()
            
    def update_handles_pos(self):
        rect = self.rect()
        if 'TL' in self.handles: self.handles['TL'].setPos(rect.topLeft())
        if 'TR' in self.handles: self.handles['TR'].setPos(rect.topRight())
        if 'BL' in self.handles: self.handles['BL'].setPos(rect.bottomLeft())
        if 'BR' in self.handles: self.handles['BR'].setPos(rect.bottomRight())
        
    def update_handle_position(self, pos_type, new_pos):
        rect = self.rect()
        if pos_type == 'TL':
            rect.setTopLeft(new_pos)
        elif pos_type == 'TR':
            rect.setTopRight(new_pos)
        elif pos_type == 'BL':
            rect.setBottomLeft(new_pos)
        elif pos_type == 'BR':
            rect.setBottomRight(new_pos)
            
        self.setRect(rect.normalized())
        
        normalized = self.rect()
        if pos_type != 'TL': self.handles['TL'].setPos(normalized.topLeft())
        if pos_type != 'TR': self.handles['TR'].setPos(normalized.topRight())
        if pos_type != 'BL': self.handles['BL'].setPos(normalized.bottomLeft())
        if pos_type != 'BR': self.handles['BR'].setPos(normalized.bottomRight())
        
    def notify_scene_changed(self):
        scene = self.scene()
        if scene and hasattr(scene, 'on_scene_changed'):
            scene.on_scene_changed()

    def update_class(self, new_class_id, new_class_name):
        self.class_id = new_class_id
        self.class_name = new_class_name
        self.base_color = self.get_color(new_class_name)
        self.setBrush(QBrush(QColor(self.base_color.red(), self.base_color.green(), self.base_color.blue(), 100)))
        if self.isSelected():
            self.setPen(QPen(Qt.white, 3, Qt.DashLine))
        else:
            self.setPen(QPen(self.base_color, 2, Qt.SolidLine))
        self.notify_scene_changed()

    def itemChange(self, change, value):
        # Öğe seçildiğinde (Edit modunda) kenarlığı belirgin yap ve tutamaçları göster
        if change == QGraphicsItem.ItemSelectedChange:
            if value:
                self.setPen(QPen(Qt.white, 3, Qt.DashLine))
                for h in self.handles.values(): h.show()
            else:
                self.setPen(QPen(self.base_color, 2, Qt.SolidLine))
                for h in self.handles.values(): h.hide()
        return super().itemChange(change, value)
        
    def contextMenuEvent(self, event):
        if self.on_right_click:
            self.on_right_click(self, event.screenPos())
        super().contextMenuEvent(event)
