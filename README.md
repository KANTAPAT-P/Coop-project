# edge-pdm — Edge AI-Based Predictive Maintenance

ระบบตรวจจับและพยากรณ์ความผิดปกติของอุปกรณ์ไฟฟ้าและเครื่องจักร โดยประมวลผล AI บน edge device โดยตรง
ไม่ส่งข้อมูลดิบขึ้น cloud ทั้งหมด ระบบเรียนรู้ pattern การทำงานปกติ แล้วแจ้งเตือนเมื่อพบสัญญาณผิดปกติก่อนอุปกรณ์เสียหายจริง

รายละเอียดเชิงลึก ข้อควรระวัง และแผนงานทั้งหมดอยู่ใน [CLAUDE.md](CLAUDE.md)

---

## ติดตั้ง

### Windows (โน้ตบุ๊ก — เครื่องหลักตอนพัฒนา)

```powershell
python -m venv venv
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

ถ้าอยาก activate venv แล้วพิมพ์ `python` สั้นๆ

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass   # มีผลเฉพาะหน้าต่างนี้
.\venv\Scripts\Activate.ps1
```

> **ทำไมต้องมีบรรทัด `Set-ExecutionPolicy`**
> PowerShell บล็อกการรันสคริปต์ `.ps1` เป็นค่าเริ่มต้น ถ้าข้ามไปจะเจอ error
> `Activate.ps1 cannot be loaded because running scripts is disabled on this system`
> การใส่ `-Scope Process` ปลอดภัยกว่าการแก้ระดับเครื่อง เพราะผลหายไปเมื่อปิดหน้าต่าง

### Raspberry Pi 5 (`pi-edge`)

venv อยู่นอกโปรเจกต์ตามที่ตกลงกันไว้

```bash
source ~/venv/bin/activate
pip install -r requirements.txt
```

> **`requirements.txt` ต้องเป็น ASCII ล้วน ห้ามใส่คอมเมนต์ภาษาไทย**
> pip อ่านไฟล์นี้ด้วย encoding ของ locale ไม่ใช่ UTF-8 บน Windows ภาษาไทยคือ cp874
> พอเจออักษรไทยจะพังด้วย `UnicodeDecodeError: 'charmap' codec can't decode byte 0x83`
> คำอธิบายภาษาไทยให้มาอยู่ในไฟล์นี้แทน

---

## เตรียม dataset

MAFAULDA ไม่ขึ้น git (31 GB) ต้องแตกจาก `mafaulda.zip` เอง

```powershell
New-Item -ItemType Directory -Force "data\raw\mafaulda"
tar -xf mafaulda.zip -C data\raw\mafaulda
```

`tar` (bsdtar) มีมาในตัว Windows 10/11 แล้ว เร็วกว่า `Expand-Archive` มาก — ใช้เวลาราว 1.5 นาที

> **`-C` คือส่วนที่ห้ามลืม** archive นี้ไม่มีโฟลเดอร์ครอบ ถ้าแตกโดยไม่ระบุปลายทาง
> ไฟล์ทั้ง 1,951 ไฟล์จะกระจายลง working directory ทันที

ตรวจว่าได้ครบและอ่านได้จริง

```powershell
.\venv\Scripts\python.exe src\data\verify_dataset.py
```

สคริปต์นี้อ่านอย่างเดียว ไม่แตะ `data/raw` และเขียนรายงานลง `experiments/`

**อย่าเอา dataset เต็มชุดลง Pi** microSD 64 GB รับไม่ไหว ให้โอนเฉพาะไฟล์ที่ใช้จริง

```powershell
scp data\raw\mafaulda\normal\28.8768.csv kantapat@pi-edge:~/edge-pdm/data/raw/mafaulda/normal/
```

---

## โครงสร้างโปรเจกต์

```
Coop-Project/
├── CLAUDE.md                 เอกสารหลัก: โดเมน ข้อควรระวัง แผนงาน
├── README.md
├── config.yaml               path แยกตามเครื่อง + ค่าคงที่ของ dataset
├── requirements.txt          ASCII เท่านั้น
├── mafaulda.zip              ต้นฉบับ ไม่ขึ้น git ไม่ลบทิ้ง
│
├── data/                     ไม่ขึ้น git
│   ├── raw/mafaulda/         ข้อมูลดิบ อ่านอย่างเดียว ห้ามเขียนทับ
│   ├── interim/              ผลระหว่างทาง
│   └── processed/            feature ที่สกัดแล้ว พร้อมเทรน
│
├── notebooks/                สำรวจข้อมูล ลองผิดลองถูก
├── src/
│   ├── paths.py              จุดเดียวที่รู้ว่าไฟล์อยู่ตรงไหน
│   ├── data/                 โหลดไฟล์, ตรวจ dataset, tachometer → rpm
│   ├── features/             RMS, kurtosis, crest factor, FFT, envelope
│   ├── models/               เทรน/ประเมินผล
│   ├── viz/                  ฟังก์ชันพล็อตที่ใช้ซ้ำ
│   └── service/              MQTT subscriber + inference
│
├── models/                   โมเดลที่เทรนแล้ว ไม่ขึ้น git
├── stack/                    Docker Compose: Mosquitto / InfluxDB / Grafana
├── experiments/              บันทึกผลการทดลองแต่ละครั้ง
├── reports/                  กราฟและตารางสำหรับรายงาน
└── docs/
```

---

## เรื่อง path: ห้ามเขียน path เอง

โค้ดต้องรันได้ทั้ง Windows และ Raspberry Pi โมดูลทุกตัวจึงต้องขอ path จาก [src/paths.py](src/paths.py) เท่านั้น

```python
from src.paths import mafaulda_dir, sampling_rate, mafaulda_columns
import pandas as pd

path = mafaulda_dir() / "normal" / "28.8768.csv"
df = pd.read_csv(path, header=None)      # header=None เสมอ CSV ไม่มีหัวตาราง
df.columns = mafaulda_columns()
```

ลำดับความสำคัญในการหาโฟลเดอร์ `data`

| ลำดับ | วิธี | ตัวอย่าง |
|---|---|---|
| 1 | env `EDGE_PDM_DATA` | `EDGE_PDM_DATA=/mnt/usb/data python ...` |
| 2 | env `EDGE_PDM_PROFILE` | `EDGE_PDM_PROFILE=pi python ...` |
| 3 | `active_profile` ใน `config.yaml` | ค่าเริ่มต้น `laptop` |

ดู path ที่ใช้อยู่จริง

```powershell
.\venv\Scripts\python.exe src\paths.py
```

---

## กับดักที่ต้องรู้ก่อนเขียนโค้ดวิเคราะห์

สรุปย่อ รายละเอียดเต็มอยู่ใน [CLAUDE.md](CLAUDE.md) หัวข้อ 5

1. **tachometer** พัลส์กว้างราว 20 แถว ถ้านับทุกแถวที่เกิน threshold จะได้ความถี่เกินจริง ~20 เท่า ต้องนับเฉพาะ rising edge
2. **FFT ธรรมดาหา bearing fault ไม่เจอ** ต้องทำ envelope analysis: bandpass 2–5 kHz → Hilbert → FFT ของ envelope
3. **imbalance ปนใน bearing fault** ไฟล์ bearing fault แบ่งตามมวลถ่วง 0/6/20/35 g ถ้าเทรนด้วยชุดมวล > 0 g เทียบ normal ตรงๆ โมเดลจะเรียนรู้ imbalance แทน — ชุด **0 g** คือโจทย์จริง
4. **MAFAULDA ไม่มีข้อมูล inner race** มีแค่ `ball_fault` / `cage_fault` / `outer_race` ตัวคูณ BPFI = 5.0020 จึงใช้ไม่ได้กับชุดนี้
5. **คอลัมน์ 5 (`o_radial`) สัญญาณต่ำผิดปกติ** ราว 5% ของช่องอื่น อย่าเทียบค่าดิบ underhang กับ overhang ต้อง normalize ก่อน
6. **data leakage** ห้ามสุ่มแบ่ง train/test แบบ random shuffle หลังตัด window ต้องแบ่งตามไฟล์หรือตามเงื่อนไข
