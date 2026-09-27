"""จำลองอุปกรณ์ปลายทาง โดยเล่นข้อมูลจริงจาก MAFAULDA ออกมาเป็นข้อความ MQTT

**จุดประสงค์** ทดสอบระบบรับส่งและจัดเก็บข้อมูลทั้งเส้น ตั้งแต่ broker จนถึง
แดชบอร์ด **โดยยังไม่ต้องมี ESP32 และเซ็นเซอร์จริง** ซึ่งเป็นขั้นที่ 2 ของ
ลำดับการพัฒนาใน `docs/data-pipeline-design.md` §8

**ข้อมูลที่ใช้เป็นของจริงทั้งหมด** อ่านจาก `data/processed/feature_grid.csv`
ซึ่งเป็นตัวชี้วัดที่สกัดจากไฟล์ MAFAULDA ทั้ง 1,951 ไฟล์ จึงได้ทดสอบระบบด้วย
ค่าที่มีการกระจายเหมือนของจริง ไม่ใช่ตัวเลขสุ่มที่ดูสวยเกินจริง

## เครื่องจักรจำลอง

แมปหนึ่งคลาสความเสียหายเป็นหนึ่งเครื่องจักร เพื่อให้แดชบอร์ดมีหลายเครื่อง
ให้เทียบกัน และได้ทดสอบโครงสร้าง topic ที่รองรับหลายเครื่องจริงๆ

    motor-01  normal                     เครื่องที่ปกติ ใช้เป็นฐานเทียบ
    motor-02  imbalance
    motor-03  horizontal-misalignment
    motor-04  vertical-misalignment
    motor-05  underhang bearing
    motor-06  overhang bearing

## สิ่งที่สังเคราะห์ขึ้น ไม่ได้มาจากชุดข้อมูล

ชุดข้อมูล MAFAULDA ไม่มีข้อมูลเหล่านี้ จึงสร้างขึ้นเพื่อให้ข้อความครบตาม
รูปแบบที่ออกแบบไว้ **ต้องไม่นำตัวเลขเหล่านี้ไปใช้สรุปผลใดๆ**

- `load_pct` และ `temp_c` — สร้างจากความเร็วรอบบวกสัญญาณรบกวน
- `rot_quality` — สุ่มให้เป็น `noisy` และ `lost` บ้างตามสัดส่วนที่พบจริง
  ในชุดข้อมูล (ราว 7% ของไฟล์มี tachometer เสีย) เพื่อให้ได้ทดสอบว่า
  ระบบปลายทางจัดการกรณีนั้นถูกต้อง
- ช่วงที่เครื่องหยุด — จำลองเป็นระยะ เพื่อทดสอบว่าระบบไม่แจ้งเตือนตอนปิดเครื่อง

## ชื่อช่องเซ็นเซอร์

ใช้ชื่อของ MAFAULDA ตามเดิม (`u_axial` `o_tang` ฯลฯ) เพื่อให้ตามรอยกลับไปยัง
ข้อมูลต้นทางได้ พอต่อเซ็นเซอร์จริงในระยะที่ 3 จะเปลี่ยนเป็นชื่อตามแกนของ
อุปกรณ์ที่ใช้จริง

รัน:
    python src/service/simulate.py                       # ส่งสดทุก 1 วินาที
    python src/service/simulate.py --backfill-hours 6    # เติมย้อนหลัง 6 ชั่วโมงก่อน
    python src/service/simulate.py --dry-run --limit 3   # ดูข้อความโดยไม่ต้องมี broker
"""

from __future__ import annotations

import argparse
import json
import math
import random
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.paths import processed_dir  # noqa: E402
from src.service import schema  # noqa: E402

SITE, AREA, SENSOR = "plant1", "press-line", "acc-01"

# (ชื่อเครื่องจักร, คลาสในชุดข้อมูล, subclass ที่เจาะจง)
MACHINES = [
    ("motor-01", "normal", None),
    ("motor-02", "imbalance", None),
    ("motor-03", "horizontal-misalignment", None),
    ("motor-04", "vertical-misalignment", None),
    ("motor-05", "underhang", "ball_fault"),
    ("motor-06", "overhang", "outer_race"),
]

CHANNELS = ["u_axial", "u_radial", "u_tang", "o_axial", "o_radial", "o_tang"]

# คาบการส่งที่ระบบออกแบบไว้ ใช้เป็นระยะห่างของ timestamp ตอนเติมย้อนหลัง
DESIGN_PERIOD_S = 10.0

# ความถี่การสุ่มและขนาดหน้าต่างที่ ESP32 จะใช้จริง ดู §9 ของเอกสารออกแบบ
# ว่าค่านี้ยังต้องวัดของจริงก่อน
ESP32_FS, ESP32_N = 20000.0, 8192

# สัดส่วนของข้อความที่ tachometer มีปัญหา อิงจากที่วัดได้ในชุดข้อมูลจริง
P_NOISY, P_LOST = 0.05, 0.02


class Machine:
    """เครื่องจักรจำลองหนึ่งเครื่อง เลือกแถวข้อมูลตามความเร็วรอบที่แกว่งไปมา"""

    def __init__(self, name: str, rows: pd.DataFrame, seed: int):
        self.name = name
        self.device_id = f"esp32-{name}"
        self.rows = rows.reset_index(drop=True)
        self.speeds = self.rows["rot_hz_used"].to_numpy()
        self.rng = random.Random(seed)
        # ให้แต่ละเครื่องแกว่งความเร็วด้วยคาบและเฟสต่างกัน จะได้ไม่ขึ้นลงพร้อมกัน
        self.phase = self.rng.uniform(0, 2 * math.pi)
        self.period = self.rng.uniform(1800, 5400)     # 30 ถึง 90 นาที
        self.lo, self.hi = float(self.speeds.min()), float(self.speeds.max())
        # ช่วงเวลาที่เครื่องหยุด เลือกไว้ล่วงหน้าเพื่อให้ผลซ้ำได้
        self.stop_every = self.rng.uniform(7200, 14400)
        self.stop_len = self.rng.uniform(180, 420)
        # เลื่อนเฟสของช่วงหยุด ไม่งั้นทุกเครื่องจะเริ่มด้วยสถานะหยุดพร้อมกันที่ t = 0
        # และหยุดพร้อมกันตลอด ซึ่งไม่เหมือนโรงงานจริง
        self.stop_phase = self.rng.uniform(self.stop_len, self.stop_every)

    def target_speed(self, t: float) -> float:
        """ความเร็วรอบเป้าหมายที่เวลา t วินาที แกว่งเป็นคลื่นช้าๆ"""
        mid, half = (self.lo + self.hi) / 2, (self.hi - self.lo) / 2 * 0.8
        return mid + half * math.sin(2 * math.pi * t / self.period + self.phase)

    def is_stopped(self, t: float) -> bool:
        return ((t + self.stop_phase) % self.stop_every) < self.stop_len

    def sample(self, t: float) -> tuple[pd.Series, float]:
        """เลือกแถวที่ความเร็วใกล้เป้าหมายที่สุด คืน (แถว, ความเร็วเป้าหมาย)"""
        want = self.target_speed(t)
        return self.rows.iloc[int(np.abs(self.speeds - want).argmin())], want

    def message(self, t: float, ts: str) -> dict:
        row, want = self.sample(t)
        stopped = self.is_stopped(t)

        if stopped:
            rot_hz, rot_quality, scale = 0.0, "stopped", 0.02
        else:
            roll = self.rng.random()
            rot_quality = "lost" if roll < P_LOST else (
                "noisy" if roll < P_LOST + P_NOISY else "ok")
            # ความเร็วที่ "วัดได้" ต่างจากของจริงเล็กน้อย และแกว่งมากขึ้นเมื่อ noisy
            jitter = 0.004 if rot_quality == "ok" else 0.03
            rot_hz = float(row["rot_hz_used"]) * (1 + self.rng.gauss(0, jitter))
            rot_hz = 0.0 if rot_quality == "lost" else round(rot_hz, 3)
            scale = 1.0

        features = {}
        for ch in CHANNELS:
            for feat in ("p2p", "rms", "kurt", "crest", "h1_frac", "r21",
                         "e_low", "e_mid", "e_high", "kurt_band",
                         "env_floor", "env_rel"):
                col = f"{ch}.{feat}"
                if col not in row or pd.isna(row[col]):
                    continue
                value = float(row[col])
                # ตอนเครื่องหยุด เหลือแต่สัญญาณรบกวนพื้นฐาน จึงย่อเฉพาะตัวที่
                # เป็นขนาด ส่วนตัวที่เป็นอัตราส่วนหรือรูปร่างปล่อยไว้
                if feat in ("p2p", "rms", "env_floor"):
                    value *= scale
                features[col] = round(value, 6)

        context = {
            "rot_hz": rot_hz,
            "rot_quality": rot_quality,
            "load_pct": 0.0 if stopped else round(
                min(100.0, max(0.0, 40 + (want - self.lo) / max(self.hi - self.lo, 1e-9)
                               * 50 + self.rng.gauss(0, 3))), 1),
            "temp_c": round(28 + (0 if stopped else want * 0.32)
                            + self.rng.gauss(0, 0.6), 1),
        }
        quality = {
            "clipped_pct": 0.0,
            "tach_jitter_pct": round(
                0.2 if rot_quality == "ok" else self.rng.uniform(2.0, 8.0), 2),
            "uptime_s": int(t),
        }
        return schema.feature_message(self.device_id, ts, ESP32_FS, ESP32_N,
                                      context, features, quality)


def load_machines(seed: int) -> list[Machine]:
    path = processed_dir() / "feature_grid.csv"
    if not path.is_file():
        raise FileNotFoundError(
            f"ไม่พบ {path}\nสร้างก่อนด้วย  python src/features/feature_grid.py")
    tab = pd.read_csv(path, keep_default_na=False, na_values=[""])

    out = []
    for i, (name, cls, sub) in enumerate(MACHINES):
        rows = tab[tab["cls"] == cls]
        if sub is not None:
            rows = rows[rows["subclass"] == sub]
        # bearing ใช้มวลถ่วง 0 g เพื่อไม่ให้ imbalance ที่เติมเข้าไปปนมา
        if cls in ("underhang", "overhang"):
            rows = rows[rows["mass_g"] == 0]
        if rows.empty:
            raise ValueError(f"ไม่มีข้อมูลสำหรับ {name} ({cls}/{sub})")
        out.append(Machine(name, rows, seed + i))
    return out


class Publisher:
    """ห่อ MQTT client เพื่อไม่ให้ข้อความหายตอนส่งเป็นก้อนใหญ่

    🚨 **ปัญหาที่เจอจริงและเป็นที่มาของคลาสนี้** ครั้งแรกที่ทดสอบ สคริปต์ส่ง
    4,440 ข้อความ แต่ตัวรับได้เพียง 2,262 ข้อความ **หายไปครึ่งหนึ่ง**
    ทั้งที่ใช้ QoS 1 ซึ่งควรรับประกันว่าถึงอย่างน้อยหนึ่งครั้ง

    สาเหตุมีสองข้อ และเป็นคนละชั้นกัน

    1. **ฝั่งผู้ส่ง** `client.publish()` เพียงแค่เอาข้อความเข้าคิวในหน่วยความจำ
       แล้วคืนค่าทันที ไม่ได้แปลว่าส่งถึง broker แล้ว ถ้า `disconnect()`
       ก่อนที่คิวจะระบายหมด ข้อความที่เหลือในคิว**หายไปเงียบๆ ไม่มี error**
    2. **ฝั่ง broker** Mosquitto จำกัดคิวของผู้รับแต่ละรายไว้ที่ 1,000 ข้อความ
       โดยค่าเริ่มต้น ถ้าผู้ส่งยิงเร็วกว่าที่ผู้รับประมวลผลไหว ข้อความส่วนเกิน
       จะถูกทิ้ง

    คลาสนี้แก้ข้อที่ 1 โดยนับจำนวนที่ broker ตอบรับแล้ว (`on_publish`)
    เทียบกับจำนวนที่ส่งไป แล้ว

    - **หน่วงผู้ส่งเมื่อคิวยาวเกิน `BACKLOG`** ทำให้ความเร็วในการส่งปรับตาม
       ความเร็วที่ปลายทางรับไหวโดยอัตโนมัติ ซึ่งแก้ข้อที่ 2 ไปในตัว
    - **รอให้คิวระบายหมดก่อนตัดการเชื่อมต่อ** ด้วย `drain()`

    บทเรียนนี้ใช้กับเฟิร์มแวร์ ESP32 ในระยะที่ 3 ด้วย เพราะบอร์ดมีหน่วยความจำ
    จำกัดกว่ามาก และเครือข่าย WiFi ในโรงงานไม่เสถียร
    """

    BACKLOG = 400          # จำนวนข้อความที่ยอมให้ค้างในคิวได้

    def __init__(self, host: str, port: int, lwt_topic: str, lwt_payload: str):
        import paho.mqtt.client as mqtt

        self.sent = 0
        self.acked = 0
        self.client = mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION2,
            client_id=f"pdm-simulator-{random.randint(1000, 9999)}")
        self.client.on_publish = self._on_publish
        self.client.will_set(lwt_topic, lwt_payload, qos=1, retain=True)
        self.client.connect(host, port, keepalive=60)
        self.client.loop_start()

    def _on_publish(self, *_args, **_kwargs) -> None:
        # รับ argument แบบยืดหยุ่น เพราะรูปแบบ callback ต่างกันระหว่างรุ่นของ paho
        self.acked += 1

    def publish(self, topic: str, payload: str, qos: int = 1,
                retain: bool = False) -> None:
        while self.sent - self.acked > self.BACKLOG:
            time.sleep(0.005)
        self.client.publish(topic, payload, qos=qos, retain=retain)
        self.sent += 1

    def drain(self, timeout: float = 60.0) -> int:
        """รอให้ broker ตอบรับครบ คืนจำนวนที่ยังค้างอยู่ (0 = ส่งถึงครบ)"""
        deadline = time.time() + timeout
        while self.sent > self.acked and time.time() < deadline:
            time.sleep(0.05)
        return self.sent - self.acked

    def close(self) -> int:
        left = self.drain()
        self.client.loop_stop()
        self.client.disconnect()
        return left


def make_client(host: str, port: int, machines: list[Machine]) -> Publisher:
    """สร้างตัวส่งพร้อมตั้ง Last Will

    ในระบบจริงอุปกรณ์แต่ละตัวมี client ของตัวเองและตั้ง LWT ของตัวเอง
    สคริปต์นี้จำลองหลายเครื่องจาก process เดียว จึงตั้ง LWT ได้เพียงตัวเดียว
    ซึ่งเพียงพอสำหรับการทดสอบว่ากลไก LWT ทำงาน
    """
    first = machines[0]
    return Publisher(
        host, port,
        schema.sensor_topic(SITE, AREA, first.name, SENSOR, "status"),
        json.dumps(schema.lwt_message(first.device_id)))


def publish_status(pub: Publisher, machines: list[Machine], state: str) -> None:
    for m in machines:
        pub.publish(
            schema.sensor_topic(SITE, AREA, m.name, SENSOR, "status"),
            json.dumps(schema.status_message(
                m.device_id, state, fw="sim-0.1.0", rssi_dbm=-55)),
            qos=1, retain=True)


def main() -> int:
    ap = argparse.ArgumentParser(description="จำลองอุปกรณ์ส่งข้อมูลเข้า MQTT")
    ap.add_argument("--host", default="localhost")
    ap.add_argument("--port", type=int, default=1883)
    ap.add_argument("--interval", type=float, default=1.0,
                    help="วินาทีระหว่างรอบการส่ง (ของจริงคือ 10 วินาที)")
    ap.add_argument("--backfill-hours", type=float, default=0.0,
                    help="เติมข้อมูลย้อนหลังกี่ชั่วโมงก่อนเริ่มส่งสด")
    ap.add_argument("--limit", type=int, default=0,
                    help="ส่งกี่รอบแล้วหยุด (0 = ไม่จำกัด)")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--dry-run", action="store_true",
                    help="พิมพ์ข้อความออกจอแทนการส่ง ใช้ดูรูปแบบโดยไม่ต้องมี broker")
    args = ap.parse_args()

    machines = load_machines(args.seed)
    print(f"เครื่องจักรจำลอง {len(machines)} เครื่อง: "
          + ", ".join(f"{m.name}({len(m.rows)} แถว)" for m in machines))

    pub = None
    if not args.dry_run:
        pub = make_client(args.host, args.port, machines)
        publish_status(pub, machines, "online")
        print(f"ต่อ broker ที่ {args.host}:{args.port} แล้ว")

    sent = bad = 0
    t = 0.0

    # ---- เติมย้อนหลัง ----
    if args.backfill_hours > 0:
        n_ticks = int(args.backfill_hours * 3600 / DESIGN_PERIOD_S)
        start = datetime.now(timezone.utc) - timedelta(hours=args.backfill_hours)
        print(f"เติมย้อนหลัง {args.backfill_hours} ชั่วโมง = "
              f"{n_ticks} รอบ × {len(machines)} เครื่อง "
              f"= {n_ticks * len(machines):,} ข้อความ")
        for k in range(n_ticks):
            ts = (start + timedelta(seconds=k * DESIGN_PERIOD_S)).isoformat(
                timespec="milliseconds").replace("+00:00", "Z")
            for m in machines:
                msg = m.message(k * DESIGN_PERIOD_S, ts)
                bad += bool(schema.validate_feature(msg))
                if pub:
                    pub.publish(
                        schema.sensor_topic(SITE, AREA, m.name, SENSOR, "feature"),
                        json.dumps(msg), qos=1)
                sent += 1
            if k and k % 200 == 0:
                backlog = (pub.sent - pub.acked) if pub else 0
                print(f"  ย้อนหลัง {k}/{n_ticks} รอบ · คิวค้าง {backlog}", flush=True)
        t = n_ticks * DESIGN_PERIOD_S
        print(f"เติมย้อนหลังเสร็จ ส่งไป {sent:,} ข้อความ")

    # ---- ส่งสด ----
    try:
        tick = 0
        while args.limit == 0 or tick < args.limit:
            ts = schema.now_iso()
            for m in machines:
                msg = m.message(t, ts)
                problems = schema.validate_feature(msg)
                bad += bool(problems)
                if problems:
                    print(f"  ⚠️ {m.name}: {problems}", file=sys.stderr)
                topic = schema.sensor_topic(SITE, AREA, m.name, SENSOR, "feature")
                if args.dry_run:
                    print(f"\n--- {topic} ---")
                    print(json.dumps(msg, ensure_ascii=False, indent=2)[:1400])
                else:
                    pub.publish(topic, json.dumps(msg), qos=1)
                sent += 1
            tick += 1
            t += DESIGN_PERIOD_S
            if not args.dry_run and tick % 10 == 0:
                state = ", ".join(
                    f"{m.name}:{m.message(t, ts)['context']['rot_hz']:.1f}Hz"
                    for m in machines[:3])
                print(f"รอบที่ {tick} · ส่งแล้ว {sent:,} ข้อความ · {state} ...",
                      flush=True)
            if args.limit == 0 or tick < args.limit:
                time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\nหยุดด้วย Ctrl-C")
    finally:
        if pub:
            publish_status(pub, machines, "offline")
            # ต้องรอให้คิวระบายก่อนตัดการเชื่อมต่อ ไม่งั้นข้อความที่ยังค้าง
            # ในคิวจะหายไปเงียบๆ ดูคำอธิบายในคลาส Publisher
            left = pub.close()
            if left:
                print(f"⚠️ ยังมีข้อความค้างในคิว {left:,} ข้อความตอนปิดการเชื่อมต่อ",
                      file=sys.stderr)

    if pub:
        print(f"\nส่ง {pub.sent:,} ข้อความ · broker ตอบรับ {pub.acked:,} "
              f"({pub.acked / max(pub.sent, 1) * 100:.1f}%)")
    print(f"ข้อความที่ตรวจไม่ผ่าน {bad}")
    return 1 if bad or (pub and pub.acked < pub.sent) else 0


if __name__ == "__main__":
    raise SystemExit(main())
