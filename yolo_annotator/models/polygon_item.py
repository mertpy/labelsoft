import random
from PyQt5.QtWidgets import QGraphicsItem, QGraphicsPolygonItem, QGraphicsEllipseItem
from PyQt5.QtCore import Qt, QPointF
from PyQt5.QtGui import QColor, QBrush, QPen

class VertexHandle(QGraphicsEllipseItem):
    """
    Çokgenin köşe noktalarını (tutamaçlarını) temsil eder.
    Sürükle-bırak ile çokgenin şeklini değiştirmeyi sağlar.
    """
    def __init__(self, index, polygon_item, parent=None):
        # Merkez noktası (0,0) olacak şekilde -4, -4, 8, 8 boyutlarında bir daire
        super().__init__(-4, -4, 8, 8, parent)
        self.index = index
        self.polygon_item = polygon_item
        
        self.setBrush(QBrush(Qt.white))
        self.setPen(QPen(Qt.black, 1))
        
        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsItem.ItemIsMovable, True)
        # self.setFlag(QGraphicsItem.ItemIsSelectable, True) # Kaldırıldı: Seçim ebeveynde kalmalı
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges, True)
        self.setCursor(Qt.CrossCursor)
        self.hide() # Başlangıçta gizli, çokgen seçilince görünür olur

    def hoverEnterEvent(self, event):
        self.setBrush(QBrush(Qt.red))
        super().hoverEnterEvent(event)
        
    def hoverLeaveEvent(self, event):
        self.setBrush(QBrush(Qt.white))
        super().hoverLeaveEvent(event)

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemPositionChange and self.scene():
            # Nokta sürüklendikçe çokgenin ilgili köşesini güncelle
            self.polygon_item.update_vertex(self.index, value)
        elif change == QGraphicsItem.ItemPositionHasChanged:
            # Sürükleme bittiğinde (veya devam ederken) auto-save tetikle
            self.polygon_item.notify_scene_changed()
            
        return super().itemChange(change, value)


class PolygonAnnotation(QGraphicsPolygonItem):
    """
    Çizilen her bir çokgeni (etiketi) temsil eden sınıf.
    """
    def __init__(self, poly, class_id, class_name, on_right_click=None, parent=None):
        super().__init__(poly, parent)
        self.class_id = class_id
        self.class_name = class_name
        self.on_right_click = on_right_click
        
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)
        
        # Sınıfa özel kalıcı rastgele renk oluştur
        self.base_color = self.get_color(class_name)
        
        # Yarı saydam dolgu ve belirgin kenarlık
        self.setBrush(QBrush(QColor(self.base_color.red(), self.base_color.green(), self.base_color.blue(), 100)))
        self.setPen(QPen(self.base_color, 2, Qt.SolidLine))
        
        self.handles = []
        self.create_handles()
        
    def get_color(self, name):
        # Sınıf adına göre seed belirleyerek rengin hep aynı kalmasını sağlıyoruz
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
                for h in self.handles: h.show()
            else:
                self.setPen(QPen(self.base_color, 2, Qt.SolidLine))
                for h in self.handles: h.hide()
        return super().itemChange(change, value)
        
    def contextMenuEvent(self, event):
        if self.on_right_click:
            # Right click event'i Viewer'a veya Main'e ilet
            self.on_right_click(self, event.screenPos())
        super().contextMenuEvent(event)
