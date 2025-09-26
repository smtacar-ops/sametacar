"""İhracat firmalarının altın ve USD alacaklarını takip etmeye yarayan yardımcı program.

Programın temel özellikleri:

* Müşteriler bazında "pure gold" (gram has altın) ve USD cinsinden borç/alacak kayıt edebilirsiniz.
* Her gün için geçerli has altın (gram) USD fiyatını saklayabilirsiniz.
* USD cinsinden borçları, kayıtlı oldukları günün has altın USD fiyatıyla gram altın cinsine
  dönüştürür ve toplamda müşteriye ait altın karşılığını hesaplar.
* Veriler `ledger.json` dosyasında saklanır; böylece programdan çıktığınızda bilgileriniz korunur.

Program etkileşimli bir menü ile çalışır ve tamamen Türkçe olarak tasarlanmıştır.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from datetime import date, datetime
from decimal import Decimal, InvalidOperation, getcontext
from pathlib import Path
from typing import Dict, Iterable, List, Optional

# Ondalık işlemlerinde hassasiyet kaybı olmaması için yüksek bir hassasiyet tanımlıyoruz.
getcontext().prec = 28


DATA_FILE = Path("ledger.json")


@dataclass
class DebtEntry:
    """Her bir müşteri borç kaydı için kullanılan veri yapısı."""

    customer: str
    currency: str  # "PURE_GOLD" veya "USD"
    amount: Decimal
    booking_date: date

    def to_dict(self) -> Dict[str, str]:
        return {
            "customer": self.customer,
            "currency": self.currency,
            "amount": format(self.amount, "f"),
            "booking_date": self.booking_date.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> "DebtEntry":
        return cls(
            customer=data["customer"],
            currency=data["currency"],
            amount=Decimal(data["amount"]),
            booking_date=datetime.strptime(data["booking_date"], "%Y-%m-%d").date(),
        )


class DebtLedger:
    """Müşteri borçlarını ve günlük altın fiyatlarını yöneten sınıf."""

    def __init__(self, data_file: Path = DATA_FILE) -> None:
        self.data_file = data_file
        self.gold_prices: Dict[date, Decimal] = {}
        self.debts: List[DebtEntry] = []
        self._load()

    # ------------------------------------------------------------------
    # Veri yönetimi
    # ------------------------------------------------------------------
    def _load(self) -> None:
        if not self.data_file.exists():
            return
        with self.data_file.open("r", encoding="utf-8") as fh:
            raw = json.load(fh)
        self.gold_prices = {
            datetime.strptime(day, "%Y-%m-%d").date(): Decimal(value)
            for day, value in raw.get("gold_prices", {}).items()
        }
        self.debts = [DebtEntry.from_dict(item) for item in raw.get("debts", [])]

    def save(self) -> None:
        payload = {
            "gold_prices": {day.isoformat(): format(price, "f") for day, price in self.gold_prices.items()},
            "debts": [entry.to_dict() for entry in self.debts],
        }
        with self.data_file.open("w", encoding="utf-8") as fh:
            json.dump(payload, fh, ensure_ascii=False, indent=2)

    # ------------------------------------------------------------------
    # Altın fiyatı yönetimi
    # ------------------------------------------------------------------
    def set_gold_price(self, pricing_date: date, usd_price_per_gram: Decimal) -> None:
        self.gold_prices[pricing_date] = usd_price_per_gram

    def get_gold_price(self, pricing_date: date) -> Optional[Decimal]:
        return self.gold_prices.get(pricing_date)

    # ------------------------------------------------------------------
    # Borç işlemleri
    # ------------------------------------------------------------------
    def add_debt(self, entry: DebtEntry) -> None:
        if entry.currency not in {"PURE_GOLD", "USD"}:
            raise ValueError("currency 'PURE_GOLD' veya 'USD' olmalıdır")
        self.debts.append(entry)

    def list_debts(self, customer: Optional[str] = None) -> Iterable[DebtEntry]:
        for entry in self.debts:
            if customer is None or entry.customer == customer:
                yield entry

    # ------------------------------------------------------------------
    # Raporlama
    # ------------------------------------------------------------------
    def compute_totals(self, customer: Optional[str] = None) -> Dict[str, Decimal]:
        usd_total = Decimal("0")
        pure_gold_total = Decimal("0")
        usd_as_gold_total = Decimal("0")

        for entry in self.list_debts(customer):
            if entry.currency == "USD":
                usd_total += entry.amount
                gold_price = self.get_gold_price(entry.booking_date)
                if gold_price is None or gold_price == 0:
                    raise ValueError(
                        f"{entry.booking_date.isoformat()} tarihi için has altın USD fiyatı tanımlı değil"
                    )
                usd_as_gold_total += entry.amount / gold_price
            else:
                pure_gold_total += entry.amount

        return {
            "usd_total": usd_total,
            "pure_gold_total": pure_gold_total,
            "usd_as_gold_total": usd_as_gold_total,
            "grand_total_gold": pure_gold_total + usd_as_gold_total,
        }


def prompt_date(message: str) -> date:
    while True:
        raw = input(message).strip()
        try:
            return datetime.strptime(raw, "%Y-%m-%d").date()
        except ValueError:
            print("Tarih formatı hatalı. Örnek kullanım: 2024-09-21")


def prompt_decimal(message: str) -> Decimal:
    while True:
        raw = input(message).strip().replace(",", ".")
        try:
            return Decimal(raw)
        except InvalidOperation:
            print("Lütfen sayısal bir değer girin.")


def prompt_currency() -> str:
    while True:
        raw = input("Para birimi (pure gold / usd): ").strip().upper()
        if raw in {"PURE GOLD", "PURE_GOLD", "GOLD"}:
            return "PURE_GOLD"
        if raw in {"USD", "$"}:
            return "USD"
        print("Geçersiz para birimi. 'pure gold' veya 'usd' giriniz.")


def render_totals(ledger: DebtLedger, customer: Optional[str] = None) -> None:
    try:
        totals = ledger.compute_totals(customer=customer)
    except ValueError as exc:
        print(f"Hata: {exc}")
        return

    header = "Tüm müşteriler" if customer is None else f"Müşteri: {customer}"
    print("\n===", header, "===")
    print(f"Toplam USD alacağı       : {totals['usd_total']:.2f} USD")
    print(f"Toplam Pure Gold alacağı  : {totals['pure_gold_total']:.4f} gram")
    print(f"USD alacakların altın karşılığı: {totals['usd_as_gold_total']:.4f} gram")
    print(f"GENEL TOPLAM (altın)      : {totals['grand_total_gold']:.4f} gram\n")


def list_debts(ledger: DebtLedger, customer: Optional[str] = None) -> None:
    rows = list(ledger.list_debts(customer))
    if not rows:
        print("Kayıt bulunamadı.")
        return
    for entry in rows:
        currency = "Pure Gold" if entry.currency == "PURE_GOLD" else "USD"
        print(
            f"{entry.booking_date.isoformat()} | {entry.customer:20} | "
            f"{entry.amount:12.4f} {currency}"
        )


def ensure_price_for_date(ledger: DebtLedger, price_date: date) -> None:
    if ledger.get_gold_price(price_date) is not None:
        return
    print(
        f"{price_date.isoformat()} tarihi için has altın USD fiyatı bulunamadı."
        " Lütfen fiyat giriniz."
    )
    price = prompt_decimal("Has altın USD fiyatı (1 gram için): ")
    ledger.set_gold_price(price_date, price)


def main() -> None:
    ledger = DebtLedger()

    MENU = {
        "1": "Has altın fiyatı ekle/güncelle",
        "2": "Borç kaydı ekle",
        "3": "Genel toplamları göster",
        "4": "Müşteriye özel toplamları göster",
        "5": "Kayıtlı borçları listele",
        "6": "Kaydet ve çık",
    }

    while True:
        print("\n=== BORÇ TAKİP MENÜSÜ ===")
        for key, label in MENU.items():
            print(f"{key}. {label}")
        choice = input("Seçiminiz: ").strip()

        if choice == "1":
            price_date = prompt_date("Fiyat tarihi (YYYY-AA-GG): ")
            price = prompt_decimal("Has altın USD fiyatı (1 gram için): ")
            ledger.set_gold_price(price_date, price)
            ledger.save()
            print("Fiyat kaydedildi.")
        elif choice == "2":
            customer = input("Müşteri adı: ").strip()
            booking_date = prompt_date("Borç tarihi (YYYY-AA-GG): ")
            ensure_price_for_date(ledger, booking_date)
            currency = prompt_currency()
            amount = prompt_decimal("Tutar: ")
            entry = DebtEntry(
                customer=customer,
                currency=currency,
                amount=amount,
                booking_date=booking_date,
            )
            ledger.add_debt(entry)
            ledger.save()
            print("Borç kaydı başarıyla eklendi.")
        elif choice == "3":
            render_totals(ledger)
        elif choice == "4":
            customer = input("Müşteri adı: ").strip()
            render_totals(ledger, customer=customer)
        elif choice == "5":
            customer_name = input("(Opsiyonel) Müşteri adı: ").strip() or None
            list_debts(ledger, customer=customer_name)
        elif choice == "6":
            ledger.save()
            print("Veriler kaydedildi. Program sonlandırılıyor.")
            break
        else:
            print("Geçersiz seçim. Lütfen menüdeki seçeneklerden birini girin.")


if __name__ == "__main__":
    main()
