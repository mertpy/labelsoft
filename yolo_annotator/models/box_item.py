import random
from PyQt5.QtWidgets import QGraphicsItem, QGraphicsRectItem, QGraphicsEllipseItem
from PyQt5.QtCore import Qt, QRectF, QPointF
from PyQt5.QtGui import QColor, QBrush, QPen

class BoxHandle(QGraphicsEllipseItem):
    """
    Kutunun köşelerini temsil eder ve yeniden boyutlandırmayı sağlar.
    """
    OPPOSITE_MAP = {'TL': 'BR', 'TR': 'BL', 'BL': 'TR', 'BR': 'TL'}
    
    def __init__(self, position_type, box_item, parent=None):
        super().__init__(-6, -6, 12, 12, parent)
        self.position_type = position_type # 'TL', 'TR', 'BL', 'BR'
        self.box_item = box_item
        
        self.setBrush(QBrush(Qt.white))
        self.setPen(QPen(Qt.black, 1))
        
        self.setAcceptHoverEvents(True)
        self.setCursor(Qt.CrossCursor)
        self.hide()
        
        self._is_dragging = False
        self._drag_anchor = None  # Sürükleme başlangıcında çapraz köşenin pozisyonu

    def hoverEnterEvent(self, event):
        self.setBrush(QBrush(Qt.red))
        super().hoverEnterEvent(event)
        
    def hoverLeaveEvent(self, event):
        self.setBrush(QBrush(Qt.white))
        super().hoverLeaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._is_dragging = True
            # Sürükleme başladığında çapraz köşenin pozisyonunu kaydet
            opposite_type = self.OPPOSITE_MAP[self.position_type]
            self._drag_anchor = QPointF(self.box_item.handles[opposite_type].pos())
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._is_dragging:
            new_pos = self.mapToParent(event.pos())
            self.box_item.update_handle_position(new_pos, self._drag_anchor)
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._is_dragging = False
            self._drag_anchor = None
            self.box_item.notify_scene_changed()
            event.accept()
        else:
            super().mouseReleaseEvent(event)


class BoxAnnotation(QGraphicsRectItem):
    """
    Çizilen her bir kutuyu (Bounding Box) temsil eden sınıf.
    """
    def __init__(self, rect, class_name, on_right_click=None, parent=None):
        super().__init__(rect, parent)
        self.class_name = class_name
        self.on_right_click = on_right_click
        
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        
        # Sınıfa özel kalıcı rastgele renk oluştur
        self.base_color = self.get_color(class_name)
        
        # Yarı saydam dolgu ve belirgin kenarlık
        self.setBrush(QBrush(QColor(self.base_color.red(), self.base_color.green(), self.base_color.blue(), 100)))
        self.setPen(QPen(self.base_color, 2, Qt.SolidLine))
        
        self._updating_handles = False
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
        
    def update_handle_position(self, new_pos, anchor_pos):
        if self._updating_handles: return
        self._updating_handles = True
        
        # anchor_pos: sürükleme başında kaydedilen çapraz köşe (sabit)
        # new_pos: sürüklenen köşenin yeni pozisyonu
        x1, y1 = new_pos.x(), new_pos.y()
        x2, y2 = anchor_pos.x(), anchor_pos.y()
        
        corners = {
            'TL': QPointF(min(x1, x2), min(y1, y2)),
            'TR': QPointF(max(x1, x2), min(y1, y2)),
            'BL': QPointF(min(x1, x2), max(y1, y2)),
            'BR': QPointF(max(x1, x2), max(y1, y2)),
        }
        
        new_rect = QRectF(corners['TL'], corners['BR'])
        self.setRect(new_rect)
        
        # Tüm handle pozisyonlarını güncelle
        for key, corner in corners.items():
            self.handles[key].setPos(corner)
        
        self._updating_handles = False
        
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
        # Öğe seçildiğinde (Edit modunda) kenarlığı belirgin yap ve tutamaçları göster
        if change == QGraphicsItem.ItemSelectedChange:
            if value:
                self.setPen(QPen(Qt.white, 3, Qt.DashLine))
                for h in self.handles.values(): h.show()
            else:
                self.setPen(QPen(self.base_color, 2, Qt.SolidLine))
                for h in self.handles.values(): h.hide()
        elif change == QGraphicsItem.ItemPositionHasChanged:
            self.notify_scene_changed()
        return super().itemChange(change, value)
        
    def contextMenuEvent(self, event):
        if self.on_right_click:
            self.on_right_click(self, event.screenPos())
        super().contextMenuEvent(event)
