import sys
from datetime import datetime
import sqlite3
from contextlib import contextmanager
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QTableWidget, QTableWidgetItem, QDialog, QLabel,
    QLineEdit, QComboBox, QMessageBox, QTabWidget, QFrame, QTextEdit,
    QHeaderView, QDateEdit
)
from PyQt5.QtCore import Qt, QTimer, QDate
from PyQt5.QtGui import QFont


# ============ DATABASE MANAGER ============

class DatabaseManager:
    def __init__(self, db_name="hospital.db"):
        self.db_name = db_name
        self.create_tables()

    @contextmanager
    def get_connection(self):
        conn = sqlite3.connect(self.db_name)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def create_tables(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()

            # Kullanıcı tablosu (LOGIN için)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS kullanicilar (
                    kullanici_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    kullanici_adi TEXT UNIQUE NOT NULL,
                    sifre TEXT NOT NULL,
                    ad TEXT NOT NULL,
                    soyad TEXT NOT NULL,
                    rol TEXT DEFAULT 'user',
                    olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS hastalar (
                    hasta_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ad TEXT NOT NULL,
                    soyad TEXT NOT NULL,
                    tc TEXT UNIQUE NOT NULL,
                    telefon TEXT NOT NULL,
                    olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS doktorlar (
                    doktor_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ad TEXT NOT NULL,
                    soyad TEXT NOT NULL,
                    uzmanlik TEXT NOT NULL,
                    uygun_saatler TEXT NOT NULL,
                    olusturma_tarihi TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS randevular (
                    randevu_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    hasta_id INTEGER NOT NULL,
                    doktor_id INTEGER NOT NULL,
                    tarih TEXT NOT NULL,
                    saat TEXT NOT NULL,
                    durum TEXT DEFAULT 'Aktif',
                    olusturma_zamani TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (hasta_id) REFERENCES hastalar (hasta_id) ON DELETE CASCADE,
                    FOREIGN KEY (doktor_id) REFERENCES doktorlar (doktor_id)
                )
            ''')

            # Varsayılan admin kullanıcısı oluştur
            cursor.execute('SELECT COUNT(*) FROM kullanicilar WHERE kullanici_adi = "admin"')
            if cursor.fetchone()[0] == 0:
                cursor.execute('''
                    INSERT INTO kullanicilar (kullanici_adi, sifre, ad, soyad, rol)
                    VALUES ('admin', 'admin123', 'Admin', 'Kullanıcı', 'admin')
                ''')

            # Varsayılan normal kullanıcı oluştur
            cursor.execute('SELECT COUNT(*) FROM kullanicilar WHERE kullanici_adi = "user"')
            if cursor.fetchone()[0] == 0:
                cursor.execute('''
                    INSERT INTO kullanicilar (kullanici_adi, sifre, ad, soyad, rol)
                    VALUES ('user', 'user123', 'Normal', 'Kullanıcı', 'user')
                ''')

    # Kullanıcı işlemleri
    def kullanici_kontrol(self, kullanici_adi, sifre):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM kullanicilar
                WHERE kullanici_adi = ? AND sifre = ?
            ''', (kullanici_adi, sifre))
            result = cursor.fetchone()
            return dict(result) if result else None

    def kullanici_ekle(self, kullanici_adi, sifre, ad, soyad, rol='user'):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO kullanicilar (kullanici_adi, sifre, ad, soyad, rol)
                VALUES (?, ?, ?, ?, ?)
            ''', (kullanici_adi, sifre, ad, soyad, rol))
            return cursor.lastrowid

    def kullanicilari_getir(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM kullanicilar ORDER BY kullanici_id')
            return [dict(row) for row in cursor.fetchall()]

    def kullanici_sil(self, kullanici_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM kullanicilar WHERE kullanici_id = ?', (kullanici_id,))

    # Hasta işlemleri
    def hasta_ekle(self, ad, soyad, tc, telefon):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO hastalar (ad, soyad, tc, telefon)
                VALUES (?, ?, ?, ?)
            ''', (ad, soyad, tc, telefon))
            return cursor.lastrowid

    def hastalari_getir(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM hastalar ORDER BY hasta_id')
            return [dict(row) for row in cursor.fetchall()]

    def hasta_sil(self, hasta_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Önce hastanın randevularını iptal et (sil değil, durumu güncelle)
            cursor.execute('UPDATE randevular SET durum = "İptal" WHERE hasta_id = ? AND durum = "Aktif"', (hasta_id,))
            # Sonra hastayı sil
            cursor.execute('DELETE FROM hastalar WHERE hasta_id = ?', (hasta_id,))

    # Doktor işlemleri
    def doktor_ekle(self, ad, soyad, uzmanlik, uygun_saatler):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO doktorlar (ad, soyad, uzmanlik, uygun_saatler)
                VALUES (?, ?, ?, ?)
            ''', (ad, soyad, uzmanlik, uygun_saatler))
            return cursor.lastrowid

    def doktorlari_getir(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM doktorlar ORDER BY doktor_id')
            return [dict(row) for row in cursor.fetchall()]

    def doktor_sil(self, doktor_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Önce doktorun randevularını iptal et
            cursor.execute('UPDATE randevular SET durum = "İptal" WHERE doktor_id = ? AND durum = "Aktif"', (doktor_id,))
            # Sonra doktoru sil
            cursor.execute('DELETE FROM doktorlar WHERE doktor_id = ?', (doktor_id,))

    # Randevu işlemleri
    def randevu_ekle(self, hasta_id, doktor_id, tarih, saat):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO randevular (hasta_id, doktor_id, tarih, saat, durum)
                VALUES (?, ?, ?, ?, 'Aktif')
            ''', (hasta_id, doktor_id, tarih, saat))
            return cursor.lastrowid

    def randevu_iptal(self, randevu_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE randevular SET durum = "İptal" WHERE randevu_id = ?', (randevu_id,))

    def randevulari_getir(self, durum=None):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if durum:
                cursor.execute('''
                    SELECT r.*, h.ad as hasta_ad, h.soyad as hasta_soyad, h.tc,
                           d.ad as doktor_ad, d.soyad as doktor_soyad, d.uzmanlik
                    FROM randevular r
                    JOIN hastalar h ON r.hasta_id = h.hasta_id
                    JOIN doktorlar d ON r.doktor_id = d.doktor_id
                    WHERE r.durum = ?
                    ORDER BY r.tarih, r.saat
                ''', (durum,))
            else:
                cursor.execute('''
                    SELECT r.*, h.ad as hasta_ad, h.soyad as hasta_soyad, h.tc,
                           d.ad as doktor_ad, d.soyad as doktor_soyad, d.uzmanlik
                    FROM randevular r
                    JOIN hastalar h ON r.hasta_id = h.hasta_id
                    JOIN doktorlar d ON r.doktor_id = d.doktor_id
                    ORDER BY r.tarih, r.saat
                ''')
            return [dict(row) for row in cursor.fetchall()]

    def gunluk_randevular(self, tarih):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT r.*, h.ad as hasta_ad, h.soyad as hasta_soyad, h.tc,
                       d.ad as doktor_ad, d.soyad as doktor_soyad, d.uzmanlik
                FROM randevular r
                JOIN hastalar h ON r.hasta_id = h.hasta_id
                JOIN doktorlar d ON r.doktor_id = d.doktor_id
                WHERE r.tarih = ? AND r.durum = 'Aktif'
                ORDER BY r.saat
            ''', (tarih,))
            return [dict(row) for row in cursor.fetchall()]

    def toplam_randevu_sayisi(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) as count FROM randevular WHERE durum = "Aktif"')
            return cursor.fetchone()['count']


# ============ LOGIN DIALOG ============

class LoginDialog(QDialog):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("Giriş Yap")
        self.setGeometry(400, 300, 400, 350)
        self.setStyleSheet("background-color: #f0f0f0;")
        self.init_ui()
        self.kullanici = None

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        # Başlık
        baslik = QLabel("Hastane Randevu Sistemi")
        baslik_font = QFont("Arial", 16, QFont.Bold)
        baslik.setFont(baslik_font)
        baslik.setAlignment(Qt.AlignCenter)
        baslik.setStyleSheet("color: #1976D2;")

        # Kullanıcı adı
        kadi_label = QLabel("Kullanıcı Adı:")
        kadi_label.setFont(QFont("Arial", 11, QFont.Bold))
        kadi_label.setStyleSheet("color: #1a1a1a;")
        self.kadi_input = QLineEdit()
        self.kadi_input.setStyleSheet("padding: 10px; border: 1px solid #ccc; border-radius: 5px; background-color: white; color: #1a1a1a; font-size: 12px;")
        self.kadi_input.setPlaceholderText("Kullanıcı adınızı girin")

        # Şifre
        sifre_label = QLabel("Şifre:")
        sifre_label.setFont(QFont("Arial", 11, QFont.Bold))
        sifre_label.setStyleSheet("color: #1a1a1a;")
        self.sifre_input = QLineEdit()
        self.sifre_input.setEchoMode(QLineEdit.Password)
        self.sifre_input.setStyleSheet("padding: 10px; border: 1px solid #ccc; border-radius: 5px; background-color: white; color: #1a1a1a; font-size: 12px;")
        self.sifre_input.setPlaceholderText("Şifrenizi girin")
        self.sifre_input.returnPressed.connect(self.giris_yap)

        # Butonlar
        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        giris_btn = QPushButton("Giriş Yap")
        giris_btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 12px; border-radius: 5px; font-weight: bold; font-size: 12px; min-width: 120px;")
        giris_btn.clicked.connect(self.giris_yap)

        iptal_btn = QPushButton("Çıkış")
        iptal_btn.setStyleSheet("background-color: #f44336; color: white; padding: 12px; border-radius: 5px; font-weight: bold; font-size: 12px; min-width: 120px;")
        iptal_btn.clicked.connect(self.reject)

        button_layout.addWidget(giris_btn)
        button_layout.addWidget(iptal_btn)

        # Bilgi
        bilgi_label = QLabel("Demo Hesap: admin / admin123")
        bilgi_label.setAlignment(Qt.AlignCenter)
        bilgi_label.setStyleSheet("color: #666; font-size: 11px;")

        layout.addWidget(baslik)
        layout.addSpacing(20)
        layout.addWidget(kadi_label)
        layout.addWidget(self.kadi_input)
        layout.addWidget(sifre_label)
        layout.addWidget(self.sifre_input)
        layout.addSpacing(20)
        layout.addLayout(button_layout)
        layout.addWidget(bilgi_label)

        self.setLayout(layout)

    def giris_yap(self):
        kadi = self.kadi_input.text().strip()
        sifre = self.sifre_input.text().strip()

        if not kadi or not sifre:
            QMessageBox.warning(self, "Hata", "Kullanıcı adı ve şifre giriniz!")
            return

        kullanici = self.db.kullanici_kontrol(kadi, sifre)
        if kullanici:
            self.kullanici = kullanici
            self.accept()
        else:
            QMessageBox.warning(self, "Hata", "Kullanıcı adı veya şifre hatalı!")


# ============ KULLANICI EKLEME DIALOG ============

class KullaniciEkleDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Yeni Kullanıcı Ekle")
        self.setGeometry(200, 200, 400, 500)
        self.setStyleSheet("background-color: #f0f0f0;")
        self.init_ui()
        self.result = None

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)

        ad_label = QLabel("Ad:")
        ad_label.setFont(QFont("Arial", 11, QFont.Bold))
        ad_label.setStyleSheet("color: #1a1a1a;")
        self.ad_input = QLineEdit()
        self.ad_input.setStyleSheet("padding: 10px; border: 1px solid #ccc; border-radius: 5px; background-color: white; color: #1a1a1a;")

        soyad_label = QLabel("Soyad:")
        soyad_label.setFont(QFont("Arial", 11, QFont.Bold))
        soyad_label.setStyleSheet("color: #1a1a1a;")
        self.soyad_input = QLineEdit()
        self.soyad_input.setStyleSheet("padding: 10px; border: 1px solid #ccc; border-radius: 5px; background-color: white; color: #1a1a1a;")

        kadi_label = QLabel("Kullanıcı Adı:")
        kadi_label.setFont(QFont("Arial", 11, QFont.Bold))
        kadi_label.setStyleSheet("color: #1a1a1a;")
        self.kadi_input = QLineEdit()
        self.kadi_input.setStyleSheet("padding: 10px; border: 1px solid #ccc; border-radius: 5px; background-color: white; color: #1a1a1a;")

        sifre_label = QLabel("Şifre:")
        sifre_label.setFont(QFont("Arial", 11, QFont.Bold))
        sifre_label.setStyleSheet("color: #1a1a1a;")
        self.sifre_input = QLineEdit()
        self.sifre_input.setEchoMode(QLineEdit.Password)
        self.sifre_input.setStyleSheet("padding: 10px; border: 1px solid #ccc; border-radius: 5px; background-color: white; color: #1a1a1a;")

        rol_label = QLabel("Rol:")
        rol_label.setFont(QFont("Arial", 11, QFont.Bold))
        rol_label.setStyleSheet("color: #1a1a1a;")
        self.rol_combo = QComboBox()
        self.rol_combo.addItems(["user", "admin"])
        self.rol_combo.setStyleSheet("padding: 10px; border: 1px solid #ccc; border-radius: 5px; background-color: white; color: #1a1a1a;")

        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        ekle_btn = QPushButton("Ekle")
        ekle_btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 12px; border-radius: 5px; font-weight: bold;")
        ekle_btn.clicked.connect(self.ekle)
        iptal_btn = QPushButton("İptal")
        iptal_btn.setStyleSheet("background-color: #f44336; color: white; padding: 12px; border-radius: 5px; font-weight: bold;")
        iptal_btn.clicked.connect(self.reject)
        button_layout.addWidget(ekle_btn)
        button_layout.addWidget(iptal_btn)

        layout.addWidget(ad_label)
        layout.addWidget(self.ad_input)
        layout.addWidget(soyad_label)
        layout.addWidget(self.soyad_input)
        layout.addWidget(kadi_label)
        layout.addWidget(self.kadi_input)
        layout.addWidget(sifre_label)
        layout.addWidget(self.sifre_input)
        layout.addWidget(rol_label)
        layout.addWidget(self.rol_combo)
        layout.addLayout(button_layout)
        self.setLayout(layout)

    def ekle(self):
        if (self.ad_input.text().strip() and self.soyad_input.text().strip() and
            self.kadi_input.text().strip() and self.sifre_input.text().strip()):
            self.result = (
                self.kadi_input.text().strip(),
                self.sifre_input.text().strip(),
                self.ad_input.text().strip(),
                self.soyad_input.text().strip(),
                self.rol_combo.currentText()
            )
            self.accept()
        else:
            QMessageBox.warning(self, "Hata", "Tüm alanları doldurun!")


# ============ DIALOG PENCERELERİ ==========

class HastaEkleDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Hasta Ekle")
        self.setGeometry(200, 200, 400, 450)
        self.setStyleSheet("background-color: #f0f0f0;")
        self.init_ui()
        self.result = None

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)

        ad_label = QLabel("Ad:")
        ad_label.setFont(QFont("Arial", 11, QFont.Bold))
        ad_label.setStyleSheet("color: #1a1a1a;")
        self.ad_input = QLineEdit()
        self.ad_input.setStyleSheet("padding: 10px; border: 1px solid #ccc; border-radius: 5px; background-color: white; color: #1a1a1a;")

        soyad_label = QLabel("Soyad:")
        soyad_label.setFont(QFont("Arial", 11, QFont.Bold))
        soyad_label.setStyleSheet("color: #1a1a1a;")
        self.soyad_input = QLineEdit()
        self.soyad_input.setStyleSheet("padding: 10px; border: 1px solid #ccc; border-radius: 5px; background-color: white; color: #1a1a1a;")

        tc_label = QLabel("TC Kimlik No (11 hane):")
        tc_label.setFont(QFont("Arial", 11, QFont.Bold))
        tc_label.setStyleSheet("color: #1a1a1a;")
        self.tc_input = QLineEdit()
        self.tc_input.setMaxLength(11)
        self.tc_input.setStyleSheet("padding: 10px; border: 1px solid #ccc; border-radius: 5px; background-color: white; color: #1a1a1a;")

        tel_label = QLabel("Telefon (10 hane):")
        tel_label.setFont(QFont("Arial", 11, QFont.Bold))
        tel_label.setStyleSheet("color: #1a1a1a;")
        self.tel_input = QLineEdit()
        self.tel_input.setMaxLength(10)
        self.tel_input.setStyleSheet("padding: 10px; border: 1px solid #ccc; border-radius: 5px; background-color: white; color: #1a1a1a;")

        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        ekle_btn = QPushButton("Ekle")
        ekle_btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 12px; border-radius: 5px; font-weight: bold;")
        ekle_btn.clicked.connect(self.ekle)
        iptal_btn = QPushButton("İptal")
        iptal_btn.setStyleSheet("background-color: #f44336; color: white; padding: 12px; border-radius: 5px; font-weight: bold;")
        iptal_btn.clicked.connect(self.reject)
        button_layout.addWidget(ekle_btn)
        button_layout.addWidget(iptal_btn)

        layout.addWidget(ad_label)
        layout.addWidget(self.ad_input)
        layout.addWidget(soyad_label)
        layout.addWidget(self.soyad_input)
        layout.addWidget(tc_label)
        layout.addWidget(self.tc_input)
        layout.addWidget(tel_label)
        layout.addWidget(self.tel_input)
        layout.addLayout(button_layout)
        self.setLayout(layout)

    def ekle(self):
        tc = self.tc_input.text().strip()
        tel = self.tel_input.text().strip()

        if not tc.isdigit() or len(tc) != 11:
            QMessageBox.warning(self, "Hata", "TC 11 haneli ve sadece sayı olmalıdır!")
            return
        if not tel.isdigit() or len(tel) != 10:
            QMessageBox.warning(self, "Hata", "Telefon 10 haneli ve sadece sayı olmalıdır!")
            return
        if self.ad_input.text().strip() and self.soyad_input.text().strip():
            self.result = (
                self.ad_input.text().strip(),
                self.soyad_input.text().strip(),
                tc,
                tel
            )
            self.accept()
        else:
            QMessageBox.warning(self, "Hata", "Tüm alanları doldurun!")


class DoktorEkleDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Doktor Ekle")
        self.setGeometry(200, 200, 400, 500)
        self.setStyleSheet("background-color: #f0f0f0;")
        self.init_ui()
        self.result = None

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)

        ad_label = QLabel("Ad:")
        ad_label.setFont(QFont("Arial", 11, QFont.Bold))
        ad_label.setStyleSheet("color: #1a1a1a;")
        self.ad_input = QLineEdit()
        self.ad_input.setStyleSheet("padding: 10px; border: 1px solid #ccc; border-radius: 5px; background-color: white; color: #1a1a1a;")

        soyad_label = QLabel("Soyad:")
        soyad_label.setFont(QFont("Arial", 11, QFont.Bold))
        soyad_label.setStyleSheet("color: #1a1a1a;")
        self.soyad_input = QLineEdit()
        self.soyad_input.setStyleSheet("padding: 10px; border: 1px solid #ccc; border-radius: 5px; background-color: white; color: #1a1a1a;")

        uzmanlik_label = QLabel("Uzmanlık:")
        uzmanlik_label.setFont(QFont("Arial", 11, QFont.Bold))
        uzmanlik_label.setStyleSheet("color: #1a1a1a;")
        self.uzmanlik_input = QLineEdit()
        self.uzmanlik_input.setStyleSheet("padding: 10px; border: 1px solid #ccc; border-radius: 5px; background-color: white; color: #1a1a1a;")

        saatler_label = QLabel("Uygun Saatler (virgülle ayırın):")
        saatler_label.setFont(QFont("Arial", 11, QFont.Bold))
        saatler_label.setStyleSheet("color: #1a1a1a;")
        self.saatler_input = QLineEdit()
        self.saatler_input.setPlaceholderText("Örn: 09:00,10:00,11:00,14:00")
        self.saatler_input.setStyleSheet("padding: 10px; border: 1px solid #ccc; border-radius: 5px; background-color: white; color: #1a1a1a;")

        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        ekle_btn = QPushButton("Ekle")
        ekle_btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 12px; border-radius: 5px; font-weight: bold;")
        ekle_btn.clicked.connect(self.ekle)
        iptal_btn = QPushButton("İptal")
        iptal_btn.setStyleSheet("background-color: #f44336; color: white; padding: 12px; border-radius: 5px; font-weight: bold;")
        iptal_btn.clicked.connect(self.reject)
        button_layout.addWidget(ekle_btn)
        button_layout.addWidget(iptal_btn)

        layout.addWidget(ad_label)
        layout.addWidget(self.ad_input)
        layout.addWidget(soyad_label)
        layout.addWidget(self.soyad_input)
        layout.addWidget(uzmanlik_label)
        layout.addWidget(self.uzmanlik_input)
        layout.addWidget(saatler_label)
        layout.addWidget(self.saatler_input)
        layout.addLayout(button_layout)
        self.setLayout(layout)

    def ekle(self):
        if (self.ad_input.text().strip() and self.soyad_input.text().strip() and
            self.uzmanlik_input.text().strip() and self.saatler_input.text().strip()):
            self.result = (
                self.ad_input.text().strip(),
                self.soyad_input.text().strip(),
                self.uzmanlik_input.text().strip(),
                self.saatler_input.text().strip()
            )
            self.accept()
        else:
            QMessageBox.warning(self, "Hata", "Tüm alanları doldurun!")


class RandevuDialog(QDialog):
    def __init__(self, hastalar, doktorlar, parent=None):
        super().__init__(parent)
        self.hastalar = hastalar
        self.doktorlar = doktorlar
        self.setWindowTitle("Randevu Oluştur")
        self.setGeometry(200, 200, 450, 500)
        self.setStyleSheet("background-color: #f0f0f0;")
        self.init_ui()
        self.result = None

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(15)

        hasta_label = QLabel("Hasta Seçin:")
        hasta_label.setFont(QFont("Arial", 11, QFont.Bold))
        hasta_label.setStyleSheet("color: #1a1a1a;")
        self.hasta_combo = QComboBox()
        self.hasta_combo.setStyleSheet("padding: 10px; border: 1px solid #ccc; border-radius: 5px; background-color: white; color: #1a1a1a;")
        for h in self.hastalar:
            self.hasta_combo.addItem(f"{h['ad']} {h['soyad']} - {h['tc']}", h['hasta_id'])

        doktor_label = QLabel("Doktor Seçin:")
        doktor_label.setFont(QFont("Arial", 11, QFont.Bold))
        doktor_label.setStyleSheet("color: #1a1a1a;")
        self.doktor_combo = QComboBox()
        self.doktor_combo.setStyleSheet("padding: 10px; border: 1px solid #ccc; border-radius: 5px; background-color: white; color: #1a1a1a;")
        for d in self.doktorlar:
            self.doktor_combo.addItem(f"Dr. {d['ad']} {d['soyad']} - {d['uzmanlik']}", d['doktor_id'])
        self.doktor_combo.currentIndexChanged.connect(self.doktor_degisti)

        self.saat_label = QLabel("Uygun Saatler:")
        self.saat_label.setFont(QFont("Arial", 10, QFont.Bold))
        self.saat_label.setStyleSheet("color: #1a1a1a; margin-top: 5px;")
        self.saat_combo = QComboBox()
        self.saat_combo.setStyleSheet("padding: 10px; border: 1px solid #ccc; border-radius: 5px; background-color: white; color: #1a1a1a;")

        tarih_label = QLabel("Tarih:")
        tarih_label.setFont(QFont("Arial", 11, QFont.Bold))
        tarih_label.setStyleSheet("color: #1a1a1a;")
        self.tarih_input = QDateEdit()
        self.tarih_input.setCalendarPopup(True)
        self.tarih_input.setDate(QDate.currentDate())
        self.tarih_input.setStyleSheet("padding: 10px; border: 1px solid #ccc; border-radius: 5px; background-color: white; color: #1a1a1a;")

        button_layout = QHBoxLayout()
        button_layout.setSpacing(15)
        ekle_btn = QPushButton("Randevu Oluştur")
        ekle_btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 12px; border-radius: 5px; font-weight: bold;")
        ekle_btn.clicked.connect(self.ekle)
        iptal_btn = QPushButton("İptal")
        iptal_btn.setStyleSheet("background-color: #f44336; color: white; padding: 12px; border-radius: 5px; font-weight: bold;")
        iptal_btn.clicked.connect(self.reject)
        button_layout.addWidget(ekle_btn)
        button_layout.addWidget(iptal_btn)

        layout.addWidget(hasta_label)
        layout.addWidget(self.hasta_combo)
        layout.addWidget(doktor_label)
        layout.addWidget(self.doktor_combo)
        layout.addWidget(self.saat_label)
        layout.addWidget(self.saat_combo)
        layout.addWidget(tarih_label)
        layout.addWidget(self.tarih_input)
        layout.addLayout(button_layout)
        self.setLayout(layout)

        self.doktor_degisti()

    def doktor_degisti(self):
        doktor_id = self.doktor_combo.currentData()
        for d in self.doktorlar:
            if d['doktor_id'] == doktor_id:
                saatler = d['uygun_saatler'].split(',')
                self.saat_combo.clear()
                for s in saatler:
                    self.saat_combo.addItem(s.strip())
                break

    def ekle(self):
        hasta_id = self.hasta_combo.currentData()
        doktor_id = self.doktor_combo.currentData()
        saat = self.saat_combo.currentText()
        tarih = self.tarih_input.date().toString("yyyy-MM-dd")

        if hasta_id and doktor_id and saat:
            self.result = (hasta_id, doktor_id, tarih, saat)
            self.accept()
        else:
            QMessageBox.warning(self, "Hata", "Geçerli seçim yapınız!")


# ============ ANA PENCERE ==========

class HastaneMainWindow(QMainWindow):
    def __init__(self, kullanici):
        super().__init__()
        self.kullanici = kullanici
        self.setWindowTitle(f"Hastane Randevu Yönetim Sistemi - Hoşgeldiniz, {kullanici['ad']} {kullanici['soyad']}")
        self.setGeometry(50, 50, 1300, 750)
        self.setStyleSheet("background-color: #e8e8e8;")
        self.db = DatabaseManager()
        self.init_ui()
        self.load_data()

    def load_data(self):
        self.hasta_listele()
        self.doktor_listele()
        self.randevu_listele()
        self.kullanici_listele()
        self.refresh_all()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Üst bilgi paneli
        ust_panel = QFrame()
        ust_panel.setStyleSheet("background-color: white; border-radius: 10px;")
        ust_layout = QHBoxLayout()
        ust_layout.setContentsMargins(20, 10, 20, 10)

        # Başlık
        header = QLabel("Hastane Randevu Yönetim Sistemi")
        header_font = QFont("Arial", 18, QFont.Bold)
        header.setFont(header_font)
        header.setStyleSheet("color: #1976D2;")

        # Kullanıcı bilgisi
        kullanici_label = QLabel(f"👤 {self.kullanici['ad']} {self.kullanici['soyad']} ({self.kullanici['rol']})")
        kullanici_label.setFont(QFont("Arial", 11))
        kullanici_label.setStyleSheet("color: #1a1a1a;")

        cikis_btn = QPushButton("Çıkış Yap")
        cikis_btn.setStyleSheet("background-color: #f44336; color: white; padding: 8px 20px; border-radius: 5px; font-weight: bold;")
        cikis_btn.clicked.connect(self.cikis_yap)

        ust_layout.addWidget(header)
        ust_layout.addStretch()
        ust_layout.addWidget(kullanici_label)
        ust_layout.addWidget(cikis_btn)
        ust_panel.setLayout(ust_layout)

        # Dashboard Kartları
        dashboard_layout = QHBoxLayout()
        dashboard_layout.setSpacing(15)

        hasta_card = self.create_stat_card("Toplam Hasta", "0", "#1976D2")
        doktor_card = self.create_stat_card("Toplam Doktor", "0", "#388E3C")
        randevu_card = self.create_stat_card("Aktif Randevular", "0", "#F57C00")
        kullanici_card = self.create_stat_card("Toplam Kullanıcı", "0", "#9C27B0")

        dashboard_layout.addWidget(hasta_card)
        dashboard_layout.addWidget(doktor_card)
        dashboard_layout.addWidget(randevu_card)
        dashboard_layout.addWidget(kullanici_card)

        self.hasta_label = hasta_card.findChild(QLabel, "value_label")
        self.doktor_label = doktor_card.findChild(QLabel, "value_label")
        self.randevu_label = randevu_card.findChild(QLabel, "value_label")
        self.kullanici_label = kullanici_card.findChild(QLabel, "value_label")

        # Sekmeler
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #ccc;
                border-radius: 5px;
                background-color: white;
            }
            QTabBar::tab {
                background-color: #d0d0d0;
                padding: 10px 30px;
                margin-right: 2px;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
                font-weight: bold;
                font-size: 13px;
                color: #1a1a1a;
            }
            QTabBar::tab:selected {
                background-color: #1976D2;
                color: white;
            }
        """)

        self.hasta_tab = self.create_hasta_tab()
        self.doktor_tab = self.create_doktor_tab()
        self.randevu_tab = self.create_randevu_tab()
        self.gunluk_tab = self.create_gunluk_tab()
        self.kullanici_tab = self.create_kullanici_tab()

        self.tabs.addTab(self.hasta_tab, "  Hastalar  ")
        self.tabs.addTab(self.doktor_tab, "  Doktorlar  ")
        self.tabs.addTab(self.randevu_tab, "  Randevular  ")
        self.tabs.addTab(self.gunluk_tab, "  Günlük Randevular  ")
        self.tabs.addTab(self.kullanici_tab, "  Kullanıcılar  ")

        main_layout.addWidget(ust_panel)
        main_layout.addLayout(dashboard_layout)
        main_layout.addWidget(self.tabs)
        central_widget.setLayout(main_layout)

        # Timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.refresh_all)
        self.timer.start(1000)

    def cikis_yap(self):
        reply = QMessageBox.question(self, "Çıkış", "Oturumu kapatmak istediğinize emin misiniz?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.close()
            self.login_tekrar()

    def login_tekrar(self):
        login = LoginDialog(self.db)
        if login.exec_() == QDialog.Accepted and login.kullanici:
            self.kullanici = login.kullanici
            self.setWindowTitle(f"Hastane Randevu Yönetim Sistemi - Hoşgeldiniz, {self.kullanici['ad']} {self.kullanici['soyad']}")
            # Ana penceredeki kullanıcı bilgisini güncelle
            for widget in self.centralWidget().findChildren(QLabel):
                if "👤" in widget.text():
                    widget.setText(f"👤 {self.kullanici['ad']} {self.kullanici['soyad']} ({self.kullanici['rol']})")
            self.load_data()
        else:
            sys.exit()

    def create_stat_card(self, title, value, color):
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {color};
                border-radius: 10px;
                padding: 15px;
                min-width: 180px;
            }}
        """)
        layout = QVBoxLayout()
        layout.setSpacing(5)

        title_label = QLabel(title)
        title_font = QFont("Arial", 12, QFont.Bold)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("color: white;")

        value_label = QLabel(value)
        value_font = QFont("Arial", 22, QFont.Bold)
        value_label.setFont(value_font)
        value_label.setAlignment(Qt.AlignCenter)
        value_label.setStyleSheet("color: white;")
        value_label.setObjectName("value_label")

        layout.addWidget(title_label)
        layout.addWidget(value_label)
        card.setLayout(layout)
        return card

    def create_hasta_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(10)

        button_layout = QHBoxLayout()
        ekle_btn = QPushButton("Yeni Hasta Ekle")
        ekle_btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 10px 20px; border-radius: 5px; font-weight: bold;")
        ekle_btn.clicked.connect(self.hasta_ekle)
        sil_btn = QPushButton("Seçili Hastayı Sil")
        sil_btn.setStyleSheet("background-color: #f44336; color: white; padding: 10px 20px; border-radius: 5px; font-weight: bold;")
        sil_btn.clicked.connect(self.hasta_sil)
        yenile_btn = QPushButton("Yenile")
        yenile_btn.setStyleSheet("background-color: #2196F3; color: white; padding: 10px 20px; border-radius: 5px; font-weight: bold;")
        yenile_btn.clicked.connect(self.hasta_listele)
        button_layout.addWidget(ekle_btn)
        button_layout.addWidget(sil_btn)
        button_layout.addWidget(yenile_btn)
        button_layout.addStretch()

        self.hasta_table = QTableWidget()
        self.hasta_table.setColumnCount(5)
        self.hasta_table.setHorizontalHeaderLabels(["ID", "Ad", "Soyad", "TC", "Telefon"])
        self.hasta_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #ccc;
                border-radius: 5px;
                background-color: white;
                alternate-background-color: #f9f9f9;
            }
            QTableWidget::item {
                padding: 8px;
                color: #1a1a1a;
            }
            QHeaderView::section {
                background-color: #1976D2;
                color: white;
                font-weight: bold;
                padding: 8px;
            }
        """)
        self.hasta_table.setAlternatingRowColors(True)
        self.hasta_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        layout.addLayout(button_layout)
        layout.addWidget(self.hasta_table)
        widget.setLayout(layout)
        return widget

    def create_doktor_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(10)

        button_layout = QHBoxLayout()
        ekle_btn = QPushButton("Yeni Doktor Ekle")
        ekle_btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 10px 20px; border-radius: 5px; font-weight: bold;")
        ekle_btn.clicked.connect(self.doktor_ekle)
        sil_btn = QPushButton("Seçili Doktoru Sil")
        sil_btn.setStyleSheet("background-color: #f44336; color: white; padding: 10px 20px; border-radius: 5px; font-weight: bold;")
        sil_btn.clicked.connect(self.doktor_sil)
        yenile_btn = QPushButton("Yenile")
        yenile_btn.setStyleSheet("background-color: #2196F3; color: white; padding: 10px 20px; border-radius: 5px; font-weight: bold;")
        yenile_btn.clicked.connect(self.doktor_listele)
        button_layout.addWidget(ekle_btn)
        button_layout.addWidget(sil_btn)
        button_layout.addWidget(yenile_btn)
        button_layout.addStretch()

        self.doktor_table = QTableWidget()
        self.doktor_table.setColumnCount(5)
        self.doktor_table.setHorizontalHeaderLabels(["ID", "Ad", "Soyad", "Uzmanlık", "Uygun Saatler"])
        self.doktor_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #ccc;
                border-radius: 5px;
                background-color: white;
                alternate-background-color: #f9f9f9;
            }
            QTableWidget::item {
                padding: 8px;
                color: #1a1a1a;
            }
            QHeaderView::section {
                background-color: #388E3C;
                color: white;
                font-weight: bold;
                padding: 8px;
            }
        """)
        self.doktor_table.setAlternatingRowColors(True)
        self.doktor_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        layout.addLayout(button_layout)
        layout.addWidget(self.doktor_table)
        widget.setLayout(layout)
        return widget

    def create_randevu_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(10)

        button_layout = QHBoxLayout()
        ekle_btn = QPushButton("Yeni Randevu Oluştur")
        ekle_btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 10px 20px; border-radius: 5px; font-weight: bold;")
        ekle_btn.clicked.connect(self.randevu_ekle)
        iptal_btn = QPushButton("Seçili Randevuyu İptal Et")
        iptal_btn.setStyleSheet("background-color: #f44336; color: white; padding: 10px 20px; border-radius: 5px; font-weight: bold;")
        iptal_btn.clicked.connect(self.randevu_iptal)
        yenile_btn = QPushButton("Yenile")
        yenile_btn.setStyleSheet("background-color: #2196F3; color: white; padding: 10px 20px; border-radius: 5px; font-weight: bold;")
        yenile_btn.clicked.connect(self.randevu_listele)
        button_layout.addWidget(ekle_btn)
        button_layout.addWidget(iptal_btn)
        button_layout.addWidget(yenile_btn)
        button_layout.addStretch()

        self.randevu_table = QTableWidget()
        self.randevu_table.setColumnCount(8)
        self.randevu_table.setHorizontalHeaderLabels(["ID", "Hasta", "Doktor", "Uzmanlık", "Tarih", "Saat", "Durum", "Oluşturma"])
        self.randevu_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #ccc;
                border-radius: 5px;
                background-color: white;
                alternate-background-color: #f9f9f9;
            }
            QTableWidget::item {
                padding: 8px;
                color: #1a1a1a;
            }
            QHeaderView::section {
                background-color: #F57C00;
                color: white;
                font-weight: bold;
                padding: 8px;
            }
        """)
        self.randevu_table.setAlternatingRowColors(True)
        self.randevu_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        layout.addLayout(button_layout)
        layout.addWidget(self.randevu_table)
        widget.setLayout(layout)
        return widget

    def create_gunluk_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(10)

        gunluk_layout = QHBoxLayout()
        gunluk_layout.setSpacing(10)

        tarih_label = QLabel("Tarih Seçin:")
        tarih_label.setFont(QFont("Arial", 11, QFont.Bold))
        tarih_label.setStyleSheet("color: #1a1a1a;")
        self.gunluk_tarih = QDateEdit()
        self.gunluk_tarih.setCalendarPopup(True)
        self.gunluk_tarih.setDate(QDate.currentDate())
        self.gunluk_tarih.setStyleSheet("padding: 8px; border: 1px solid #ccc; border-radius: 5px; background-color: white; color: #1a1a1a;")

        ara_btn = QPushButton("Göster")
        ara_btn.setStyleSheet("background-color: #2196F3; color: white; padding: 8px 20px; border-radius: 5px; font-weight: bold;")
        ara_btn.clicked.connect(self.gunluk_listele)

        gunluk_layout.addWidget(tarih_label)
        gunluk_layout.addWidget(self.gunluk_tarih)
        gunluk_layout.addWidget(ara_btn)
        gunluk_layout.addStretch()

        self.gunluk_table = QTableWidget()
        self.gunluk_table.setColumnCount(7)
        self.gunluk_table.setHorizontalHeaderLabels(["ID", "Hasta", "Doktor", "Uzmanlık", "Saat", "Durum", "TC"])
        self.gunluk_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #ccc;
                border-radius: 5px;
                background-color: white;
                alternate-background-color: #f9f9f9;
            }
            QTableWidget::item {
                padding: 8px;
                color: #1a1a1a;
            }
            QHeaderView::section {
                background-color: #9C27B0;
                color: white;
                font-weight: bold;
                padding: 8px;
            }
        """)
        self.gunluk_table.setAlternatingRowColors(True)
        self.gunluk_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        layout.addLayout(gunluk_layout)
        layout.addWidget(self.gunluk_table)
        widget.setLayout(layout)
        return widget

    def create_kullanici_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(10)

        button_layout = QHBoxLayout()
        ekle_btn = QPushButton("Yeni Kullanıcı Ekle")
        ekle_btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 10px 20px; border-radius: 5px; font-weight: bold;")
        ekle_btn.clicked.connect(self.kullanici_ekle)
        sil_btn = QPushButton("Seçili Kullanıcıyı Sil")
        sil_btn.setStyleSheet("background-color: #f44336; color: white; padding: 10px 20px; border-radius: 5px; font-weight: bold;")
        sil_btn.clicked.connect(self.kullanici_sil)
        yenile_btn = QPushButton("Yenile")
        yenile_btn.setStyleSheet("background-color: #2196F3; color: white; padding: 10px 20px; border-radius: 5px; font-weight: bold;")
        yenile_btn.clicked.connect(self.kullanici_listele)
        button_layout.addWidget(ekle_btn)
        button_layout.addWidget(sil_btn)
        button_layout.addWidget(yenile_btn)
        button_layout.addStretch()

        self.kullanici_table = QTableWidget()
        self.kullanici_table.setColumnCount(6)
        self.kullanici_table.setHorizontalHeaderLabels(["ID", "Kullanıcı Adı", "Ad", "Soyad", "Rol", "Oluşturma"])
        self.kullanici_table.setStyleSheet("""
            QTableWidget {
                border: 1px solid #ccc;
                border-radius: 5px;
                background-color: white;
                alternate-background-color: #f9f9f9;
            }
            QTableWidget::item {
                padding: 8px;
                color: #1a1a1a;
            }
            QHeaderView::section {
                background-color: #9C27B0;
                color: white;
                font-weight: bold;
                padding: 8px;
            }
        """)
        self.kullanici_table.setAlternatingRowColors(True)
        self.kullanici_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        layout.addLayout(button_layout)
        layout.addWidget(self.kullanici_table)
        widget.setLayout(layout)
        return widget

    # Hasta metodları
    def hasta_ekle(self):
        try:
            dialog = HastaEkleDialog(self)
            if dialog.exec_() == QDialog.Accepted and dialog.result:
                self.db.hasta_ekle(*dialog.result)
                QMessageBox.information(self, "Başarılı", "Hasta eklendi!")
                self.hasta_listele()
        except sqlite3.IntegrityError:
            QMessageBox.warning(self, "Hata", "Bu TC ile kayıtlı hasta zaten var!")

    def hasta_sil(self):
        row = self.hasta_table.currentRow()
        if row >= 0:
            hasta_id = int(self.hasta_table.item(row, 0).text())
            hasta_ad = self.hasta_table.item(row, 1).text()
            # Hastanın aktif randevuları var mı kontrol et
            aktif_randevular = [r for r in self.db.randevulari_getir('Aktif') if r['hasta_id'] == hasta_id]
            if aktif_randevular:
                reply = QMessageBox.question(self, "Uyarı",
                    f"{hasta_ad} hastasının {len(aktif_randevular)} aktif randevusu var.\n"
                    "Hasta silinirse bu randevular iptal edilecek.\nDevam etmek istiyor musunuz?",
                    QMessageBox.Yes | QMessageBox.No)
                if reply == QMessageBox.No:
                    return
            else:
                reply = QMessageBox.question(self, "Onay", f"{hasta_ad} silinsin mi?", QMessageBox.Yes | QMessageBox.No)
                if reply == QMessageBox.No:
                    return

            self.db.hasta_sil(hasta_id)
            QMessageBox.information(self, "Başarılı", "Hasta silindi!")
            self.hasta_listele()
            self.randevu_listele()
        else:
            QMessageBox.warning(self, "Hata", "Lütfen silinecek hastayı seçin!")

    def hasta_listele(self):
        self.hasta_table.setRowCount(0)
        for h in self.db.hastalari_getir():
            row = self.hasta_table.rowCount()
            self.hasta_table.insertRow(row)
            self.hasta_table.setItem(row, 0, QTableWidgetItem(str(h['hasta_id'])))
            self.hasta_table.setItem(row, 1, QTableWidgetItem(h['ad']))
            self.hasta_table.setItem(row, 2, QTableWidgetItem(h['soyad']))
            self.hasta_table.setItem(row, 3, QTableWidgetItem(h['tc']))
            self.hasta_table.setItem(row, 4, QTableWidgetItem(h['telefon']))

    # Doktor metodları
    def doktor_ekle(self):
        try:
            dialog = DoktorEkleDialog(self)
            if dialog.exec_() == QDialog.Accepted and dialog.result:
                self.db.doktor_ekle(*dialog.result)
                QMessageBox.information(self, "Başarılı", "Doktor eklendi!")
                self.doktor_listele()
        except Exception as e:
            QMessageBox.warning(self, "Hata", str(e))

    def doktor_sil(self):
        row = self.doktor_table.currentRow()
        if row >= 0:
            doktor_id = int(self.doktor_table.item(row, 0).text())
            doktor_ad = self.doktor_table.item(row, 1).text()
            # Doktorun aktif randevuları var mı kontrol et
            aktif_randevular = [r for r in self.db.randevulari_getir('Aktif') if r['doktor_id'] == doktor_id]
            if aktif_randevular:
                QMessageBox.warning(self, "Uyarı",
                    f"Dr. {doktor_ad}'ın {len(aktif_randevular)} aktif randevusu var.\n"
                    "Önce randevuları iptal etmelisiniz!")
                return
            else:
                reply = QMessageBox.question(self, "Onay", f"Dr. {doktor_ad} silinsin mi?", QMessageBox.Yes | QMessageBox.No)
                if reply == QMessageBox.Yes:
                    self.db.doktor_sil(doktor_id)
                    QMessageBox.information(self, "Başarılı", "Doktor silindi!")
                    self.doktor_listele()
        else:
            QMessageBox.warning(self, "Hata", "Lütfen silinecek doktoru seçin!")

    def doktor_listele(self):
        self.doktor_table.setRowCount(0)
        for d in self.db.doktorlari_getir():
            row = self.doktor_table.rowCount()
            self.doktor_table.insertRow(row)
            self.doktor_table.setItem(row, 0, QTableWidgetItem(str(d['doktor_id'])))
            self.doktor_table.setItem(row, 1, QTableWidgetItem(d['ad']))
            self.doktor_table.setItem(row, 2, QTableWidgetItem(d['soyad']))
            self.doktor_table.setItem(row, 3, QTableWidgetItem(d['uzmanlik']))
            self.doktor_table.setItem(row, 4, QTableWidgetItem(d['uygun_saatler']))

    # Randevu metodları
    def randevu_ekle(self):
        hastalar = self.db.hastalari_getir()
        doktorlar = self.db.doktorlari_getir()
        if not hastalar:
            QMessageBox.warning(self, "Hata", "Önce hasta eklemelisiniz!")
            return
        if not doktorlar:
            QMessageBox.warning(self, "Hata", "Önce doktor eklemelisiniz!")
            return
        dialog = RandevuDialog(hastalar, doktorlar, self)
        if dialog.exec_() == QDialog.Accepted and dialog.result:
            hasta_id, doktor_id, tarih, saat = dialog.result
            self.db.randevu_ekle(hasta_id, doktor_id, tarih, saat)
            QMessageBox.information(self, "Başarılı", "Randevu oluşturuldu!")
            self.randevu_listele()

    def randevu_iptal(self):
        row = self.randevu_table.currentRow()
        if row >= 0:
            randevu_id = int(self.randevu_table.item(row, 0).text())
            hasta_ad = self.randevu_table.item(row, 1).text()
            reply = QMessageBox.question(self, "Onay", f"{hasta_ad} için randevu iptal edilsin mi?",
                                         QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.db.randevu_iptal(randevu_id)
                QMessageBox.information(self, "Başarılı", "Randevu iptal edildi!")
                self.randevu_listele()
        else:
            QMessageBox.warning(self, "Hata", "Lütfen iptal edilecek randevuyu seçin!")

    def randevu_listele(self):
        self.randevu_table.setRowCount(0)
        for r in self.db.randevulari_getir():
            row = self.randevu_table.rowCount()
            self.randevu_table.insertRow(row)
            self.randevu_table.setItem(row, 0, QTableWidgetItem(str(r['randevu_id'])))
            self.randevu_table.setItem(row, 1, QTableWidgetItem(f"{r['hasta_ad']} {r['hasta_soyad']}"))
            self.randevu_table.setItem(row, 2, QTableWidgetItem(f"Dr. {r['doktor_ad']} {r['doktor_soyad']}"))
            self.randevu_table.setItem(row, 3, QTableWidgetItem(r['uzmanlik']))
            self.randevu_table.setItem(row, 4, QTableWidgetItem(r['tarih']))
            self.randevu_table.setItem(row, 5, QTableWidgetItem(r['saat']))
            self.randevu_table.setItem(row, 6, QTableWidgetItem(r['durum']))
            self.randevu_table.setItem(row, 7, QTableWidgetItem(r['olusturma_zamani']))

    def gunluk_listele(self):
        tarih = self.gunluk_tarih.date().toString("yyyy-MM-dd")
        randevular = self.db.gunluk_randevular(tarih)
        self.gunluk_table.setRowCount(0)
        for r in randevular:
            row = self.gunluk_table.rowCount()
            self.gunluk_table.insertRow(row)
            self.gunluk_table.setItem(row, 0, QTableWidgetItem(str(r['randevu_id'])))
            self.gunluk_table.setItem(row, 1, QTableWidgetItem(f"{r['hasta_ad']} {r['hasta_soyad']}"))
            self.gunluk_table.setItem(row, 2, QTableWidgetItem(f"Dr. {r['doktor_ad']} {r['doktor_soyad']}"))
            self.gunluk_table.setItem(row, 3, QTableWidgetItem(r['uzmanlik']))
            self.gunluk_table.setItem(row, 4, QTableWidgetItem(r['saat']))
            self.gunluk_table.setItem(row, 5, QTableWidgetItem(r['durum']))
            self.gunluk_table.setItem(row, 6, QTableWidgetItem(r['tc']))

    # Kullanıcı metodları
    def kullanici_ekle(self):
        try:
            dialog = KullaniciEkleDialog(self)
            if dialog.exec_() == QDialog.Accepted and dialog.result:
                self.db.kullanici_ekle(*dialog.result)
                QMessageBox.information(self, "Başarılı", "Kullanıcı eklendi!")
                self.kullanici_listele()
        except sqlite3.IntegrityError:
            QMessageBox.warning(self, "Hata", "Bu kullanıcı adı zaten var!")

    def kullanici_sil(self):
        row = self.kullanici_table.currentRow()
        if row >= 0:
            kullanici_id = int(self.kullanici_table.item(row, 0).text())
            kullanici_adi = self.kullanici_table.item(row, 1).text()

            if kullanici_adi == "admin":
                QMessageBox.warning(self, "Hata", "Admin kullanıcısı silinemez!")
                return
            if kullanici_adi == self.kullanici['kullanici_adi']:
                QMessageBox.warning(self, "Hata", "Kendi hesabınızı silemezsiniz!")
                return

            reply = QMessageBox.question(self, "Onay", f"{kullanici_adi} kullanıcısı silinsin mi?",
                                         QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.db.kullanici_sil(kullanici_id)
                QMessageBox.information(self, "Başarılı", "Kullanıcı silindi!")
                self.kullanici_listele()
        else:
            QMessageBox.warning(self, "Hata", "Lütfen silinecek kullanıcıyı seçin!")

    def kullanici_listele(self):
        self.kullanici_table.setRowCount(0)
        for k in self.db.kullanicilari_getir():
            row = self.kullanici_table.rowCount()
            self.kullanici_table.insertRow(row)
            self.kullanici_table.setItem(row, 0, QTableWidgetItem(str(k['kullanici_id'])))
            self.kullanici_table.setItem(row, 1, QTableWidgetItem(k['kullanici_adi']))
            self.kullanici_table.setItem(row, 2, QTableWidgetItem(k['ad']))
            self.kullanici_table.setItem(row, 3, QTableWidgetItem(k['soyad']))
            self.kullanici_table.setItem(row, 4, QTableWidgetItem(k['rol']))
            self.kullanici_table.setItem(row, 5, QTableWidgetItem(k['olusturma_tarihi']))

    def refresh_all(self):
        hastalar = self.db.hastalari_getir()
        doktorlar = self.db.doktorlari_getir()
        kullanicilar = self.db.kullanicilari_getir()
        self.hasta_label.setText(str(len(hastalar)))
        self.doktor_label.setText(str(len(doktorlar)))
        self.randevu_label.setText(str(self.db.toplam_randevu_sayisi()))
        self.kullanici_label.setText(str(len(kullanicilar)))


# ============ MAIN ==========

def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')

    db = DatabaseManager()

    # Login ekranını göster
    login = LoginDialog(db)
    if login.exec_() == QDialog.Accepted and login.kullanici:
        window = HastaneMainWindow(login.kullanici)
        window.show()
        sys.exit(app.exec_())
    else:
        sys.exit()


if __name__ == "__main__":
    main()