from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QComboBox, QLabel, QPushButton, QLineEdit, QMessageBox

class ClassSelectionDialog(QDialog):
    def __init__(self, classes, save_classes_cb, parent=None):
        super().__init__(parent)
        self.classes = classes
        self.save_classes_cb = save_classes_cb
        self.setWindowTitle("Sınıf Seç")
        self.resize(300, 150)
        
        layout = QVBoxLayout()
        
        self.combo = QComboBox()
        self.update_combo()
        layout.addWidget(QLabel("Mevcut Sınıflar:"))
        layout.addWidget(self.combo)
        
        layout.addWidget(QLabel("--- VEYA YENİ SINIF EKLE ---"))
        
        new_layout = QHBoxLayout()
        self.id_input = QLineEdit()
        self.id_input.setPlaceholderText("ID (örn: 0)")
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Sınıf Adı (örn: araba)")
        self.add_btn = QPushButton("Ekle")
        self.add_btn.clicked.connect(self.add_class)
        
        new_layout.addWidget(self.id_input)
        new_layout.addWidget(self.name_input)
        new_layout.addWidget(self.add_btn)
        layout.addLayout(new_layout)
        
        btn_layout = QHBoxLayout()
        self.ok_btn = QPushButton("Tamam")
        self.ok_btn.clicked.connect(self.check_accept)
        self.cancel_btn = QPushButton("İptal")
        self.cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(self.ok_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
        
    def update_combo(self):
        self.combo.clear()
        for cid, cname in sorted(self.classes.items()):
            self.combo.addItem(f"{cid}: {cname}", cid)
            
    def add_class(self):
        cid_str = self.id_input.text().strip()
        cname = self.name_input.text().strip()
        if not cid_str or not cname:
            QMessageBox.warning(self, "Hata", "ID ve İsim boş olamaz.")
            return
        try:
            cid = int(cid_str)
        except ValueError:
            QMessageBox.warning(self, "Hata", "ID tam sayı olmalıdır.")
            return
            
        if cid in self.classes:
            QMessageBox.warning(self, "Hata", f"{cid} ID'si zaten kullanımda.")
            return
            
        self.classes[cid] = cname
        self.update_combo()
        
        if self.save_classes_cb:
            self.save_classes_cb()
            
        index = self.combo.findData(cid)
        if index >= 0:
            self.combo.setCurrentIndex(index)
            
        self.id_input.clear()
        self.name_input.clear()
        
    def check_accept(self):
        if self.combo.count() == 0:
            QMessageBox.warning(self, "Uyarı", "Lütfen önce bir sınıf ekleyin.")
            return
        self.accept()
        
    def get_selected_class(self):
        if self.combo.count() == 0:
            return None, None
        cid = self.combo.currentData()
        return cid, self.classes[cid]


class ClassChangeDialog(QDialog):
    def __init__(self, current_cid, classes, save_classes_cb, parent=None):
        super().__init__(parent)
        self.classes = classes
        self.save_classes_cb = save_classes_cb
        self.setWindowTitle("Sınıfı Değiştir")
        self.resize(300, 150)
        
        layout = QVBoxLayout()
        
        self.combo = QComboBox()
        self.update_combo()
        
        idx = self.combo.findData(current_cid)
        if idx >= 0:
            self.combo.setCurrentIndex(idx)
            
        layout.addWidget(QLabel("Yeni Sınıf Seç:"))
        layout.addWidget(self.combo)
        
        layout.addWidget(QLabel("--- VEYA YENİ SINIF EKLE ---"))
        
        new_layout = QHBoxLayout()
        self.id_input = QLineEdit()
        self.id_input.setPlaceholderText("ID (örn: 0)")
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Sınıf Adı")
        self.add_btn = QPushButton("Ekle")
        self.add_btn.clicked.connect(self.add_class)
        
        new_layout.addWidget(self.id_input)
        new_layout.addWidget(self.name_input)
        new_layout.addWidget(self.add_btn)
        layout.addLayout(new_layout)
        
        btn_layout = QHBoxLayout()
        self.ok_btn = QPushButton("Tamam")
        self.ok_btn.clicked.connect(self.accept)
        self.cancel_btn = QPushButton("İptal")
        self.cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(self.ok_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)

    def update_combo(self):
        self.combo.clear()
        for cid, cname in sorted(self.classes.items()):
            self.combo.addItem(f"{cid}: {cname}", cid)
            
    def add_class(self):
        cid_str = self.id_input.text().strip()
        cname = self.name_input.text().strip()
        if not cid_str or not cname:
            QMessageBox.warning(self, "Hata", "ID ve İsim boş olamaz.")
            return
        try:
            cid = int(cid_str)
        except ValueError:
            QMessageBox.warning(self, "Hata", "ID tam sayı olmalıdır.")
            return
            
        if cid in self.classes:
            QMessageBox.warning(self, "Hata", f"{cid} ID'si zaten kullanımda.")
            return
            
        self.classes[cid] = cname
        self.update_combo()
        
        if self.save_classes_cb:
            self.save_classes_cb()
            
        index = self.combo.findData(cid)
        if index >= 0:
            self.combo.setCurrentIndex(index)
            
        self.id_input.clear()
        self.name_input.clear()

    def get_selected_class(self):
        if self.combo.count() == 0:
            return None, None
        cid = self.combo.currentData()
        return cid, self.classes[cid]
