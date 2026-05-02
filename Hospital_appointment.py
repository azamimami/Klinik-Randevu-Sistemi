from datetime import datetime

# ================= GLOBAL IDS =================
global_hasta_id = 1
global_doktor_id = 1
global_randevu_id = 1


# ================= VALIDATION =================
def get_valid_tc():
    while True:
        tc = input("TC (11 hane): ")
        if tc.isdigit() and len(tc) == 11:
            return tc
        print("Hata: TC 11 haneli ve sadece sayı olmalıdır.")


def get_valid_phone():
    while True:
        phone = input("Telefon (10 hane): ")
        if phone.isdigit() and len(phone) == 10:
            return phone
        print("Hata: Telefon 10 haneli ve sadece sayı olmalıdır.")


def safe_date(value):
    formats = ["%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d"]

    for fmt in formats:
        try:
            return datetime.strptime(value, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue

    raise ValueError("Tarih formatı hatalı! Örnek: 2026-12-12")


# ================= HASTA =================
class Hasta:
    def __init__(self, ad, soyad, tc, telefon):
        global global_hasta_id

        self.hasta_id = global_hasta_id
        global_hasta_id += 1

        self.ad = ad
        self.soyad = soyad
        self.tc = tc
        self.telefon = telefon


# ================= DOKTOR =================
class Doktor:
    def __init__(self, ad, soyad, uzmanlik, uygun_saatler):
        global global_doktor_id

        self.doktor_id = global_doktor_id
        global_doktor_id += 1

        self.ad = ad
        self.soyad = soyad
        self.uzmanlik = uzmanlik
        self.uygun_saatler = uygun_saatler

    def uygunluk_kontrol(self, saat):
        return saat in self.uygun_saatler


# ================= RANDEVU =================
class Randevu:
    def __init__(self, hasta, doktor, tarih, saat):
        global global_randevu_id

        self.randevu_id = global_randevu_id
        global_randevu_id += 1

        self.tarih = tarih
        self.saat = saat
        self.hasta = hasta
        self.doktor = doktor
        self.olusturma_zamani = datetime.now()

    # UPDATED DISPLAY (created time added)
    def __str__(self):
        return (
            f"[{self.randevu_id}] "
            f"{self.tarih} {self.saat} | "
            f"{self.hasta.ad} {self.hasta.soyad} -> "
            f"Dr.{self.doktor.ad} {self.doktor.soyad} | "
            f"Oluşturma: {self.olusturma_zamani.strftime('%Y-%m-%d %H:%M')}"
        )


# ================= SISTEM =================
class RandevuSistemi:
    def __init__(self):
        self.hastalar = []
        self.doktorlar = []
        self.randevular = []

    def randevu_olustur(self, hasta, doktor, tarih, saat):

        if not doktor.uygunluk_kontrol(saat):
            return "Doktor bu saatte uygun değil."

        r = Randevu(hasta, doktor, tarih, saat)
        self.randevular.append(r)
        return r

    def randevu_iptal(self, randevu_id):
        self.randevular = [
            r for r in self.randevular if r.randevu_id != randevu_id
        ]

    def gunluk_randevular(self, tarih):
        return [r for r in self.randevular if r.tarih == tarih]

    def hasta_ekle(self, hasta):
        self.hastalar.append(hasta)

    def doktor_ekle(self, doktor):
        self.doktorlar.append(doktor)

    def tum_hastalar(self):
        return self.hastalar

    def tum_doktorlar(self):
        return self.doktorlar


# ================= MENU =================
def menu():
    sistem = RandevuSistemi()

    while True:
        print("\n===== HASTANE SİSTEMİ =====")
        print("1- Hasta Ekle")
        print("2- Doktor Ekle")
        print("3- Randevu Oluştur")
        print("4- Randevu İptal")
        print("5- Günlük Randevu Listesi")
        print("6- Tüm Hastalar")
        print("7- Tüm Doktorlar")
        print("8- Çıkış")

        secim = input("Seçim: ")

        # ---------- HASTA ----------
        if secim == "1":
            ad = input("Ad: ")
            soyad = input("Soyad: ")
            tc = get_valid_tc()
            tel = get_valid_phone()

            h = Hasta(ad, soyad, tc, tel)
            sistem.hasta_ekle(h)

            print(f"Hasta eklendi ID: {h.hasta_id}")

        # ---------- DOKTOR ----------
        elif secim == "2":
            ad = input("Ad: ")
            soyad = input("Soyad: ")
            uzm = input("Uzmanlık: ")
            saatler = input("Uygun saatler (örn: 09:10,11:12): ").split(",")

            d = Doktor(ad, soyad, uzm, saatler)
            sistem.doktor_ekle(d)

            print(f"Doktor eklendi ID: {d.doktor_id}")

        # ---------- RANDEVU ----------
        elif secim == "3":
            print("\nHastalar:")
            for h in sistem.hastalar:
                print(f"{h.hasta_id} - {h.ad} {h.soyad}")

            hid = int(input("Hasta ID: "))

            print("\nDoktorlar:")
            for d in sistem.doktorlar:
                print(f"{d.doktor_id} - {d.ad} {d.soyad}")

            did = int(input("Doktor ID: "))

            doktor = next(d for d in sistem.doktorlar if d.doktor_id == did)

            print("\nUygun saatler:")
            print(", ".join(doktor.uygun_saatler))

            tarih = safe_date(input("Tarih (YYYY-AA-GG): "))
            saat = input("Saat: ")

            hasta = next(h for h in sistem.hastalar if h.hasta_id == hid)

            sonuc = sistem.randevu_olustur(hasta, doktor, tarih, saat)
            print(sonuc)

        # ---------- İPTAL ----------
        elif secim == "4":
            if not sistem.randevular:
                print("Henüz randevu yok.")
                continue

            print("\n--- MEVCUT RANDEVULAR ---")
            for r in sistem.randevular:
                print(r)

            try:
                rid = int(input("\nİptal edilecek Randevu ID: "))
                sistem.randevu_iptal(rid)
                print("Randevu silindi")
            except ValueError:
                print("Geçersiz ID")

        # ---------- GÜNLÜK ----------
        elif secim == "5":
            tarih = input("Tarih (YYYY-AA-GG): ")
            tarih = safe_date(tarih)

            liste = sistem.gunluk_randevular(tarih)

            print(f"\n--- {tarih} GÜNLÜK RANDEVULAR ---")

            if len(liste) == 0:
                print("Bugün herhangi bir randevu yok.")
            else:
                for r in liste:
                    print(r)

        # ---------- HASTA LİSTE ----------
        elif secim == "6":
            for h in sistem.tum_hastalar():
                print(f"{h.hasta_id} | {h.ad} {h.soyad} | {h.tc} | {h.telefon}")

        # ---------- DOKTOR LİSTE ----------
        elif secim == "7":
            for d in sistem.tum_doktorlar():
                print(f"{d.doktor_id} | {d.ad} {d.soyad} | {d.uzmanlik} | {','.join(d.uygun_saatler)}")

        # ---------- EXIT ----------
        elif secim == "8":
            print("Çıkış yapıldı")
            break

        else:
            print("Geçersiz seçim")


# ================= RUN =================
menu()