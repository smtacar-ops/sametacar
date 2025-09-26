# Altın ve USD Alacak Takip Programı

`debt_tracker.py`, ihracat firmalarının müşterilerinden olan alacaklarını hem USD hem de gram has altın cinsinden takip etmelerini sağlayan basit bir komut satırı uygulamasıdır.

## Özellikler

- Müşteriler bazında USD veya "pure gold" (gram has altın) cinsinden borç/alacak kaydı ekleme
- Günlük has altın USD fiyatını (1 gram altın için USD) saklama
- USD cinsinden alacakları, kaydın yapıldığı gündeki has altın fiyatına göre gram altın karşılığına çevirme
- Genel toplam ve müşteri bazında rapor oluşturma
- Verileri `ledger.json` dosyasına kaydederek oturumlar arasında saklama

## Kurulum

Python 3.9+ sürümüne sahip olmanız yeterlidir. Ek bir bağımlılık gerekmemektedir.

## Kullanım

Programı başlatmak için terminalden aşağıdaki komutu çalıştırın:

```bash
python debt_tracker.py
```

Uygulama size menü üzerinden şu işlemleri yapma imkânı verir:

1. **Has altın fiyatı ekle/güncelle:** Bir tarih için 1 gram has altının USD fiyatını girin.
2. **Borç kaydı ekle:** Müşteri adı, tarih, para birimi (usd veya pure gold) ve tutarı girerek yeni bir borç kaydı oluşturun. Borç tarihi için altın fiyatı kayıtlı değilse program sizi fiyat girmeye yönlendirir.
3. **Genel toplamları göster:** Tüm müşterilerin USD toplamı, pure gold toplamı ve USD borçlarının altın karşılığı ile genel toplamı (gram) görüntüler.
4. **Müşteriye özel toplamları göster:** Belirli bir müşteri için aynı özetleri verir.
5. **Kayıtlı borçları listele:** Tüm borçları veya belirlediğiniz müşteriye ait borçları listeler.
6. **Kaydet ve çık:** Verileri `ledger.json` dosyasına kaydedip programdan çıkmanızı sağlar.

## Veri Dosyası

Program, çalışma dizininde `ledger.json` adlı bir dosya oluşturur ve verileri bu dosyada saklar. Dosya yapısı örneği:

```json
{
  "gold_prices": {
    "2024-09-21": "74.50"
  },
  "debts": [
    {
      "customer": "Acme Ltd",
      "currency": "USD",
      "amount": "10000",
      "booking_date": "2024-09-21"
    },
    {
      "customer": "Acme Ltd",
      "currency": "PURE_GOLD",
      "amount": "150.25",
      "booking_date": "2024-09-22"
    }
  ]
}
```

## Notlar

- Fiyatlar ve tutarlar `Decimal` kullanılarak yüksek hassasiyetle saklanır.
- USD borçlarının altın karşılığını hesaplayabilmek için ilgili tarihe ait has altın USD fiyatının girilmiş olması gerekir.
- Menüdeki tüm metinler Türkçe olduğundan uygulamayı günlük operasyonlarınıza kolayca adapte edebilirsiniz.
