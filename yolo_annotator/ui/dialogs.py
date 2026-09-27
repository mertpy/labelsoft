from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QComboBox, QLabel, QPushButton, QLineEdit, QMessageBox

class ClassSelectionDialog(QDialog):
    def __init__(self, classes, last_used_class=None, parent=None):
        super().__init__(parent)
        self.classes = classes
        self.last_used_class = last_used_class
        self.setWindowTitle("Sınıf Seç")
        self.resize(300, 150)
        
        layout = QVBoxLayout()
        
        self.combo = QComboBox()
        self.update_combo()
        layout.addWidget(QLabel("Mevcut Sınıflar:"))
        layout.addWidget(self.combo)
        
        layout.addWidget(QLabel("--- VEYA YENİ SINIF EKLE ---"))
        
        new_layout = QHBoxLayout()
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Sınıf Adı (örn: araba)")
        self.add_btn = QPushButton("Ekle")
        self.add_btn.clicked.connect(self.add_class)
        
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
        for cname in sorted(self.classes):
            self.combo.addItem(cname, cname)
            
        if self.last_used_class:
            idx = self.combo.findText(self.last_used_class)
            if idx >= 0:
                self.combo.setCurrentIndex(idx)
            
    def add_class(self):
        cname = self.name_input.text().strip()
        if not cname:
            QMessageBox.warning(self, "Hata", "İsim boş olamaz.")
            return
            
        if cname in self.classes:
            QMessageBox.warning(self, "Hata", "Bu sınıf zaten mevcut.")
            return
            
        self.classes.append(cname)
        self.last_used_class = cname
        self.update_combo()
            
        self.name_input.clear()
        
    def check_accept(self):
        if self.combo.count() == 0:
            QMessageBox.warning(self, "Uyarı", "Lütfen önce bir sınıf ekleyin.")
            return
        self.accept()
        
    def get_selected_class(self):
        if self.combo.count() == 0:
            return None
        return self.combo.currentData()


class ClassChangeDialog(QDialog):
    def __init__(self, current_cname, classes, parent=None):
        super().__init__(parent)
        self.classes = classes
        self.setWindowTitle("Sınıfı Değiştir")
        self.resize(300, 150)
        
        layout = QVBoxLayout()
        
        self.combo = QComboBox()
        self.update_combo()
        
        idx = self.combo.findData(current_cname)
        if idx >= 0:
            self.combo.setCurrentIndex(idx)
            
        layout.addWidget(QLabel("Yeni Sınıf Seç:"))
        layout.addWidget(self.combo)
        
        layout.addWidget(QLabel("--- VEYA YENİ SINIF EKLE ---"))
        
        new_layout = QHBoxLayout()
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Sınıf Adı")
        self.add_btn = QPushButton("Ekle")
        self.add_btn.clicked.connect(self.add_class)
        
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
        for cname in sorted(self.classes):
            self.combo.addItem(cname, cname)
            
    def add_class(self):
        cname = self.name_input.text().strip()
        if not cname:
            QMessageBox.warning(self, "Hata", "İsim boş olamaz.")
            return
            
        if cname in self.classes:
            QMessageBox.warning(self, "Hata", "Bu sınıf zaten mevcut.")
            return
            
        self.classes.append(cname)
        self.update_combo()
            
        index = self.combo.findData(cname)
        if index >= 0:
            self.combo.setCurrentIndex(index)
            
        self.name_input.clear()

    def get_selected_class(self):
        if self.combo.count() == 0:
            return None
        return self.combo.currentData()

class CameraSettingsDialog(QDialog):
    def __init__(self, current_settings, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Kamera ve Hesaplama Ayarları")
        self.resize(300, 200)
        
        layout = QVBoxLayout()
        
        self.inputs = {}
        fields = [
            ("Kamera Yüksekliği (m):", "camera_height_m"),
            ("Yatay Görüş Açısı (FOV Derece):", "fov_h_deg"),
            ("Referans Genişlik (px):", "ref_width"),
            ("Referans Yükseklik (px):", "ref_height")
        ]
        
        for label_text, key in fields:
            row = QHBoxLayout()
            row.addWidget(QLabel(label_text))
            line_edit = QLineEdit(str(current_settings.get(key, "")))
            row.addWidget(line_edit)
            self.inputs[key] = line_edit
            layout.addLayout(row)
            
        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("Kaydet")
        ok_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("İptal")
        cancel_btn.clicked.connect(self.reject)
        
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
        
    def get_settings(self):
        settings = {}
        for key, line_edit in self.inputs.items():
            try:
                settings[key] = float(line_edit.text().strip())
            except ValueError:
                settings[key] = 0.0
        return settings
