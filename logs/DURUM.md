# DURUM
Aktif faz: 2 — Keşifsel Analiz (EDA)
Aktif adım: 2.1 eda.py (başlanacak)
Döngü: 0/8 · Yeniden tasarım: 0/2 · Bu hata için deneme: 0/3
## Notlar
- Kapılar `./make <hedef>` ile çalıştırılır (K-002). Python: .venv/Scripts/python.exe (3.12).
- data/raw: 52 dosya tam (2000-2025 Base+Advanced). oyuncu_sezon.csv: 12.810 satır.
- Konsol cp1254: ad-hoc python çıktısında PYTHONIOENCODING=utf-8 kullan.
## Plan (Faz 2)
- [ ] 2.1 eda.py: yaş eğrisi (delta, GP>=20 & MIN>=10 her iki sezonda? — hedef sezonda GP bilgisi için t+1 satırına bak), ortalamaya dönüş, ardışık korelasyon (PTS/MIN/PTS_36)
- [ ] 2.2 grafikler + eda_bulgular.md
- [ ] 2.3 test_eda (sentetik) ; kapılar: make eda, tepe yaş 24-30, K10
## Son kapı sonuçları (2026-10-04)
Faz 0: K1 ✅ K2 ✅ K3 ✅ K9 ✅ · Faz 1: make veri ✅, make test 22 passed, make test-veri 13 passed, lint ✅
## KISMİ işaretli maddeler
(yok)
