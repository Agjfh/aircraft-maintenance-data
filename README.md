# Aircraft Maintenance Data – Airbus A320 (Graduation Project)

بيانات جاهزة لتطبيق صيانة طائرات Airbus A320: قاعدة بيانات للـ Backend + داتا معالجة لموديلات Machine Learning.

## الهيكل
```
db/                 a320_maintenance.db (SQLite جاهزة) · schema.sql (PK/FK/CHECK) · seed.py · queries.sql
data/raw/           الداتا الأصلية (NASA C-MAPSS حقيقي · FAA SDR حقيقي · أسطول A320 اصطناعي)
data/processed/     داتا جاهزة للتدريب (cmapss: مُطبَّعة + RUL · sdr: train/val/test)
ml/                 rul_baseline.py · sdr_classifier.py
DATA_SOURCES.md     المصادر والرخص وأي تحذيرات (اقرأه قبل ما تكتب التقرير)
```

## Backend
```bash
sqlite3 db/a320_maintenance.db < db/queries.sql    # أمثلة استعلامات للـ Dashboard
python db/seed.py                                    # إعادة بناء القاعدة من الـ CSV
```
`db/schema.sql` متوافق تقريبًا مع PostgreSQL/MySQL (ممكن تحتاج تعديل بسيط في `PRAGMA` و`CHECK`).
الجداول: `aircraft, engines, technicians, parts_inventory, maintenance_schedule, defect_reports, work_orders, engine_sensor_data, faa_sdr_reports`.

## Machine Learning
```bash
pip install -r requirements.txt
python ml/rul_baseline.py FD001        # توقع العمر المتبقي للمحرك (FD001..FD004)
python ml/sdr_classifier.py hazard_binary   # تصنيف بلاغات الأعطال (أو hazard_category)
```
| المهمة | الداتا | Baseline |
|---|---|---|
| توقع RUL | NASA C-MAPSS | RMSE 15.5–19.9 (RUL مقصوص عند 125) |
| تصنيف خطورة البلاغ (Yes/No) | FAA SDR | Macro-F1 ≈ 0.76 |
| تصنيف نوع البلاغ (16 فئة) | FAA SDR | Accuracy ≈ 0.88 / Macro-F1 ≈ 0.60 (الفئات غير متوازنة: التآكل 72%) |

> ملاحظة: داتا `data/raw/a320_synthetic` **اصطناعية**، وداتا C-MAPSS محاكاة لمحرك توربوفان عام (مش محرك A320 بالتحديد). التفاصيل في `DATA_SOURCES.md`.

## Direct access from Python (GitHub Raw)

Install pandas:

```bash
pip install pandas
```

Load the complete synthetic A320 tables:

```python
from data.load_remote_data import load_a320_data

tables = load_a320_data()
aircraft = tables["aircraft"]
sensor_data = tables["engine_sensor_data"]
defects = tables["defects"]
work_orders = tables["work_orders"]
```

Load a NASA C-MAPSS compressed file:

```python
from data.load_remote_data import load_nasa_cmapss
fd001 = load_nasa_cmapss("train", "FD001")
```

Raw URL pattern:
`https://raw.githubusercontent.com/Agjfh/aircraft-maintenance-data/main/<path>`

**Data caveats:** A320 fleet and maintenance records are synthetic, C-MAPSS is a general turbofan simulation (not A320-specific), and the `a320_extra` flight-operations file is marked unverified. Consult `DATA_SOURCES.md` before citing or using the datasets.
