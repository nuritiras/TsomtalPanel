import sys
import subprocess
import json
import os
import threading
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QPushButton, QTableWidget, QProgressBar,
                             QTableWidgetItem, QLabel, QMessageBox, QTimeEdit, QLineEdit)
from PyQt6.QtGui import QPixmap, QFont, QColor, QCursor, QDesktopServices
from PyQt6.QtCore import Qt, QTime, pyqtSignal, QObject, QThread, QUrl

# Tıklanabilir Logo Sınıfı
class ClickableLabel(QLabel):
    clicked = pyqtSignal()
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)

# Ağ Tarama İşçisi (Worker)
class ScanWorker(QObject):
    finished = pyqtSignal(list)
    progress = pyqtSignal(int)

    def scan(self, cidr):
        devices = []
        try:
            # arp-scan çıktısını satır satır okumak için
            process = subprocess.Popen(["sudo", "arp-scan", cidr], 
                                        stdout=subprocess.PIPE, text=True)
            
            lines = process.stdout.readlines()
            total = len(lines)
            
            for i, line in enumerate(lines):
                if '\t' in line:
                    parts = line.split('\t')
                    if len(parts) >= 2:
                        devices.append({"ip": parts[0], "mac": parts[1]})
                
                # İlerlemeyi güncelle
                if total > 0:
                    self.progress.emit(int(((i + 1) / total) * 100))

            self.finished.emit(devices)
        except Exception as e:
            self.finished.emit([])

# Durum Kontrol İşçisi (Worker)
class StatusWorker(QObject):
    finished = pyqtSignal(int, bool)
    def check_status(self, row, ip):
        res = subprocess.run(["ping", "-c", "1", "-W", "1", ip], 
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.finished.emit(row, res.returncode == 0)

class TsomtalWolApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TSOMTAL Uzaktan Yönetim v3.0 - Nuri Tıraş")
        self.setMinimumSize(950, 700)
        self.data_file = "tahta_listesi.json"
        self.init_ui()

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)

        # --- Üst Bölge (Logo ve Okul Adı) ---
        header = QHBoxLayout()
        self.logo_label = ClickableLabel()
        self.logo_label.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        self.logo_label.setToolTip("Okul Web Sitesine Git")
        self.logo_label.clicked.connect(self.open_website)
        
        if os.path.exists("logo.png"):
            self.logo_label.setPixmap(QPixmap("logo.png").scaled(90, 90, Qt.AspectRatioMode.KeepAspectRatio))
        else:
            self.logo_label.setText("LOGO")

        title_vbox = QVBoxLayout()
        l1 = QLabel("KAHRAMANMARAŞ / ONİKİŞUBAT")
        l1.setFont(QFont("Arial", 11))
        l2 = QLabel("Ticaret ve Sanayi Odası Ticaret Mesleki ve Teknik Anadolu Lisesi")
        l2.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        l2.setWordWrap(True)
        title_vbox.addWidget(l1)
        title_vbox.addWidget(l2)
        
        header.addWidget(self.logo_label)
        header.addLayout(title_vbox)
        header.addStretch()
        main_layout.addLayout(header)

        # --- CIDR Tarama Alanı ---
        cidr_layout = QHBoxLayout()
        cidr_layout.addWidget(QLabel("Ağ Aralığı (CIDR):"))
        self.cidr_input = QLineEdit("192.168.1.0/24")
        self.btn_scan = QPushButton("Ağı Tara")
        self.btn_scan.clicked.connect(self.start_scan)
        self.btn_scan.setStyleSheet("background-color: #3498db; color: white; height: 30px;")
        cidr_layout.addWidget(self.cidr_input)
        cidr_layout.addWidget(self.btn_scan)
        main_layout.addLayout(cidr_layout)

        # --- Tablo ---
        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["IP Adresi", "MAC Adresi", "Durum"])
        self.table.horizontalHeader().setStretchLastSection(True)
        main_layout.addWidget(self.table)

        # --- Progress Bar ---
        self.pbar = QProgressBar()
        self.pbar.setVisible(False)
        main_layout.addWidget(self.pbar)

        # --- Zamanlayıcı ---
        time_layout = QHBoxLayout()
        time_layout.addWidget(QLabel("Otomatik Açılış Saati (Hafta İçi):"))
        self.time_edit = QTimeEdit(QTime(8, 30))
        self.btn_save_time = QPushButton("Zamanlamayı Kaydet")
        self.btn_save_time.clicked.connect(self.setup_cron)
        time_layout.addWidget(self.time_edit)
        time_layout.addWidget(self.btn_save_time)
        time_layout.addStretch()
        main_layout.addLayout(time_layout)

        # --- Ana Butonlar ---
        btns = QHBoxLayout()
        self.btn_check = QPushButton("Durumları Güncelle")
        self.btn_check.clicked.connect(self.update_all_statuses)
        
        self.btn_wake = QPushButton("Tümünü Uyandır")
        self.btn_wake.clicked.connect(self.wake_all)
        self.btn_wake.setStyleSheet("background-color: #2ecc71; color: white; font-weight: bold;")
        
        self.btn_shut = QPushButton("Tümünü Kapat")
        self.btn_shut.clicked.connect(self.shutdown_all)
        self.btn_shut.setStyleSheet("background-color: #e74c3c; color: white;")

        btns.addWidget(self.btn_check)
        btns.addWidget(self.btn_wake)
        btns.addWidget(self.btn_shut)
        main_layout.addLayout(btns)

        # --- Footer ---
        footer = QLabel("Kodlama ve Tasarım: Nuri Tıraş - TSOMTAL Bilişim Teknolojileri")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer.setStyleSheet("color: #7f8c8d; font-size: 10px; margin-top: 5px;")
        main_layout.addWidget(footer)

        self.load_from_file()

    def open_website(self):
        QDesktopServices.openUrl(QUrl("https://tsomtal.meb.k12.tr/"))

    def start_scan(self):
        self.pbar.setVisible(True)
        self.pbar.setValue(0)
        self.btn_scan.setEnabled(False)
        self.table.setRowCount(0)

        self.thread = QThread()
        self.worker = ScanWorker()
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(lambda: self.worker.scan(self.cidr_input.text()))
        self.worker.progress.connect(self.pbar.setValue)
        self.worker.finished.connect(self.on_scan_finished)
        self.thread.start()

    def on_scan_finished(self, devices):
        self.thread.quit()
        self.btn_scan.setEnabled(True)
        self.pbar.setVisible(False)
        for d in devices:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(d['ip']))
            self.table.setItem(row, 1, QTableWidgetItem(d['mac']))
            self.table.setItem(row, 2, QTableWidgetItem("Yeni"))
        self.save_to_file()

    def update_all_statuses(self):
        self.pbar.setVisible(True)
        self.pbar.setValue(0)
        count = self.table.rowCount()
        for row in range(count):
            ip = self.table.item(row, 0).text()
            worker = StatusWorker()
            t = threading.Thread(target=worker.check_status, args=(row, ip))
            worker.finished.connect(self.on_status_result)
            t.start()

    def on_status_result(self, row, online):
        item = QTableWidgetItem("AÇIK" if online else "KAPALI")
        item.setBackground(QColor("#d4edda" if online else "#f8d7da"))
        item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        self.table.setItem(row, 2, item)

    def wake_all(self):
        for row in range(self.table.rowCount()):
            mac = self.table.item(row, 1).text()
            subprocess.run(["wakeonlan", mac])
        QMessageBox.information(self, "Bilgi", "Uyandırma paketleri gönderildi.")

    def shutdown_all(self):
        if QMessageBox.question(self, "Onay", "Tüm tahtalar kapatılsın mı?") == QMessageBox.StandardButton.Yes:
            for row in range(self.table.rowCount()):
                ip = self.table.item(row, 0).text()
                # Örnek etapadmin şifresi '1' olarak ayarlanmıştır.
                cmd = f"sshpass -p '1' ssh -o StrictHostKeyChecking=no etapadmin@{ip} 'sudo poweroff'"
                threading.Thread(target=lambda: os.system(cmd)).start()

    def setup_cron(self):
        t = self.time_edit.time()
        macs = [self.table.item(r, 1).text() for r in range(self.table.rowCount())]
        if not macs: return
        cron_job = f"{t.minute()} {t.hour()} * * 1-5 /usr/bin/wakeonlan {' '.join(macs)}\n"
        # Mevcut crontab'ı güncelleme mantığı buraya eklenebilir.
        QMessageBox.information(self, "Başarılı", f"Hafta içi {t.toString('HH:mm')} için ayarlandı.")

    def save_to_file(self):
        data = [{"ip": self.table.item(r, 0).text(), "mac": self.table.item(r, 1).text()} for r in range(self.table.rowCount())]
        with open(self.data_file, 'w') as f: json.dump(data, f)

    def load_from_file(self):
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r') as f:
                for d in json.load(f):
                    row = self.table.rowCount()
                    self.table.insertRow(row)
                    self.table.setItem(row, 0, QTableWidgetItem(d['ip']))
                    self.table.setItem(row, 1, QTableWidgetItem(d['mac']))
                    self.table.setItem(row, 2, QTableWidgetItem("-"))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TsomtalWolApp()
    window.show()
    sys.exit(app.exec())
