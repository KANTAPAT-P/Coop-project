# stack — ระบบรับส่งและจัดเก็บข้อมูล

ไฟล์ Docker Compose ไฟล์เดียวรันครบทั้งระบบ ใช้ได้ทั้งบนโน้ตบุ๊ก Windows
และ Raspberry Pi 5 เพราะอิมเมจทั้งสามตัวมีรุ่น arm64 ครบ

การออกแบบและเหตุผลอยู่ใน `docs/data-pipeline-design.md`
ผลการทดสอบอยู่ใน `experiments/2026-09-28-pipeline-end-to-end.md`

## ครั้งแรก

```bash
cp stack/.env.example stack/.env
```

แล้ว**แก้ทุกบรรทัดใน `stack/.env`** โดยเฉพาะรหัสผ่านและ token
ไฟล์นี้ไม่ขึ้น git ตอนย้ายไป Raspberry Pi ต้องสร้างใหม่ที่เครื่องนั้น

## คำสั่งที่ใช้บ่อย

```bash
# ยกขึ้น
docker compose -f stack/docker-compose.yml --env-file stack/.env up -d

# ดูสถานะ
docker compose -f stack/docker-compose.yml --env-file stack/.env ps

# ดู log
docker compose -f stack/docker-compose.yml --env-file stack/.env logs -f mosquitto

# หยุด (ข้อมูลยังอยู่)
docker compose -f stack/docker-compose.yml --env-file stack/.env down

# หยุดและลบข้อมูลทิ้งทั้งหมด
docker compose -f stack/docker-compose.yml --env-file stack/.env down -v
```

## บริการและพอร์ต

| บริการ | พอร์ต | เข้าถึง |
|---|---|---|
| Mosquitto | 1883 | MQTT broker |
| InfluxDB 2 | 8086 | http://localhost:8086 |
| Grafana | 3000 | http://localhost:3000 |

เข้า InfluxDB และ Grafana ด้วยชื่อผู้ใช้และรหัสผ่านที่ตั้งไว้ใน `.env`

## ทดสอบว่าระบบทำงาน

เปิดสองหน้าต่าง

```bash
# หน้าต่างที่ 1 — ตัวรับข้อมูล
python src/service/ingest.py --seconds 180

# หน้าต่างที่ 2 — ตัวจำลองอุปกรณ์ เล่นข้อมูลจริงจาก MAFAULDA
python src/service/simulate.py --backfill-hours 2 --limit 10 --interval 0.5
```

ผลที่ควรได้คือ **จำนวนที่ส่งเท่ากับจำนวนที่ broker ตอบรับ และเท่ากับจำนวนที่
ผู้รับได้รับ** ถ้าไม่เท่ากันแปลว่ามีข้อความหาย ดูสาเหตุที่เป็นไปได้ในบันทึก
การทดลองวันที่ 2026-09-28

ดูรูปแบบข้อความโดยไม่ต้องยก stack ขึ้น

```bash
python src/service/simulate.py --dry-run --limit 1
```

## แดชบอร์ด

Grafana ตั้งค่า**แหล่งข้อมูลและแดชบอร์ดให้อัตโนมัติ**ตอนคอนเทนเนอร์ขึ้น
จากไฟล์ใน `stack/grafana/` ไม่ต้องกดสร้างในหน้าเว็บ

เข้าที่ http://localhost:3000 แล้วเปิดโฟลเดอร์ **Predictive Maintenance**
จะเจอแดชบอร์ด **ภาพรวมสภาพเครื่องจักร** ซึ่งมี 7 แผง

| แผง | แสดงอะไร |
|---|---|
| สถานะการวัดความเร็วรอบล่าสุด | ความเร็วล่าสุดของทุกเครื่อง |
| อุณหภูมิล่าสุด | (ค่าสังเคราะห์จากสคริปต์จำลอง) |
| ความเร็วรอบ | **ต้องดูคู่กับแผงความแรงเสมอ** |
| ความแรงการสั่น `u_radial.rms` | ตัวชี้วัดตระกูลความแรง |
| ลายเซ็น imbalance `u_radial.h1_frac` | motor-02 ควรสูงกว่าเพื่อนชัดเจน |
| ลายเซ็น misalignment `o_tang.r21` | motor-03 และ motor-04 |
| คุณภาพการวัดความเร็วรอบ | แถบเวลาแสดง ok / noisy / lost / stopped |

**แก้แดชบอร์ด** ให้แก้สคริปต์แล้วสร้างไฟล์ใหม่ ไม่ควรแก้ในหน้าเว็บ
เพราะการแก้ในหน้าเว็บจะหายเมื่อ provisioning โหลดไฟล์ทับ

```bash
python stack/grafana/make_dashboard.py
```

Grafana โหลดไฟล์ใหม่เองทุก 30 วินาที ไม่ต้องรีสตาร์ทคอนเทนเนอร์

## ⚠️ ข้อควรระวัง

- **การตั้งค่าปัจจุบันเปิดให้เชื่อมต่อ MQTT โดยไม่ต้องยืนยันตัวตน**
  ใช้ได้เฉพาะในเครือข่ายภายในตอนพัฒนา ก่อนขึ้นระบบจริงต้องตั้ง
  `allow_anonymous false` พร้อมไฟล์รหัสผ่าน และพิจารณาเปิด TLS
- `down -v` **ลบข้อมูลในฐานข้อมูลทิ้งทั้งหมด** ใช้เฉพาะตอนต้องการเริ่มใหม่
- บน Raspberry Pi ให้ระวังเรื่องการเขียนลง microSD ดู
  `docs/data-pipeline-design.md` §5.5
