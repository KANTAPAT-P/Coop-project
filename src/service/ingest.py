"""Python service — รับข้อความจาก MQTT ตรวจความถูกต้อง แล้วเขียนลง InfluxDB

เป็นขั้นที่ 3 ของลำดับการพัฒนาใน `docs/data-pipeline-design.md` §8

## หน้าที่ตามลำดับ

1. subscribe `pdm/+/+/+/+/feature` และ `pdm/+/+/+/+/status`
2. ตรวจเวอร์ชันของ schema และตรวจว่าค่าครบและเป็นตัวเลขจำกัด
3. แยก site / area / machine / sensor จาก topic ไปเป็น tag
4. เขียนตัวชี้วัด บริบท และตัวบอกคุณภาพ ลง InfluxDB
5. ประเมินแบบจำลองแล้วส่งผลกลับเข้า topic `alert` — **ยังไม่ทำในขั้นนี้**
   รอขั้นที่ 5 ของลำดับการพัฒนา ดูหมายเหตุในฟังก์ชัน `_evaluate`

## หลักการที่ยึดไว้

**ข้อความเสียหนึ่งข้อความต้องไม่ทำให้บริการทั้งตัวหยุด** ในระบบติดตามสภาพ
เครื่องจักร การที่ระบบเงียบไปเพราะอุปกรณ์ตัวเดียวส่งข้อมูลผิดรูปแบบเป็น
พฤติกรรมที่ยอมรับไม่ได้ ข้อความที่ตรวจไม่ผ่านจึงถูกนับและบันทึกไว้ แล้วข้ามไป

**`rot_quality` เป็น tag ส่วนค่าตัวเลขทั้งหมดเป็น field** เพราะ InfluxDB
สร้างดัชนีให้ tag ทุกตัว ถ้าใส่ค่าที่เปลี่ยนตลอดอย่าง `rot_hz` เป็น tag
จะได้ series ใหม่ทุกครั้งที่ความเร็วเปลี่ยนแม้เพียงทศนิยม ซึ่งทำให้ฐานข้อมูล
ช้าลงจนใช้ไม่ได้ ดู `docs/data-pipeline-design.md` §6

รัน:
    python src/service/ingest.py                 # อ่านค่าตั้งจาก stack/.env
    python src/service/ingest.py --dry-run       # ไม่เขียนฐานข้อมูล ใช้ดูว่าแยก tag ถูกไหม
"""

from __future__ import annotations

import argparse
import json
import os
import signal
import sys
import time
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.paths import repo_root  # noqa: E402
from src.service import schema  # noqa: E402

MEASUREMENT = "vibration"
STATUS_MEASUREMENT = "device_status"

# ค่าใน context ที่เป็น tag ไม่ใช่ field เพราะมีค่าเป็นชุดจำกัดและใช้กรองบ่อย
CONTEXT_TAGS = ("rot_quality",)


def load_env() -> dict:
    """อ่าน stack/.env แบบง่าย ไม่พึ่งไลบรารีเพิ่ม

    ตัวแปรที่ตั้งไว้ใน environment จริงมีความสำคัญกว่าไฟล์เสมอ เพื่อให้ตอนรัน
    ใน container หรือบน Pi สามารถ override ได้โดยไม่ต้องแก้ไฟล์
    """
    env = {}
    path = repo_root() / "stack" / ".env"
    if path.is_file():
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            env[key.strip()] = value.strip()
    env.update({k: v for k, v in os.environ.items() if k in env or k.startswith("INFLUX_")})
    return env


class Ingestor:
    def __init__(self, env: dict, dry_run: bool):
        self.dry_run = dry_run
        self.stats = Counter()
        self.by_machine = Counter()
        self.problems: list[tuple[str, list[str]]] = []
        self.write_api = None
        self.influx = None
        self.bucket = env.get("INFLUX_BUCKET", "pdm_live")
        self.org = env.get("INFLUX_ORG", "coop")
        if not dry_run:
            self._open_influx(env)

    def _open_influx(self, env: dict) -> None:
        from influxdb_client import InfluxDBClient
        from influxdb_client.client.write_api import SYNCHRONOUS, WriteOptions

        url = env.get("INFLUX_URL", "http://localhost:8086")
        token = env.get("INFLUX_TOKEN")
        if not token:
            raise SystemExit(
                "ไม่พบ INFLUX_TOKEN\nสร้าง stack/.env จาก stack/.env.example ก่อน")
        self.influx = InfluxDBClient(url=url, token=token, org=self.org)
        health = self.influx.ping()
        if not health:
            raise SystemExit(f"ต่อ InfluxDB ที่ {url} ไม่ได้ — ยก stack ขึ้นหรือยัง")
        # เขียนเป็นก้อน ลดจำนวนครั้งที่เขียนลงดิสก์ ซึ่งสำคัญมากกับ microSD
        self.write_api = self.influx.write_api(
            write_options=WriteOptions(batch_size=500, flush_interval=2000,
                                       max_retries=3))
        _ = SYNCHRONOUS
        print(f"ต่อ InfluxDB ที่ {url} org={self.org} bucket={self.bucket} แล้ว")

    # ------------------------------------------------------ แปลงข้อความ

    def _point(self, parts: dict, msg: dict):
        from influxdb_client import Point

        ctx = msg.get("context", {})
        p = Point(MEASUREMENT)
        for key in ("site", "area", "machine", "sensor"):
            if parts.get(key):
                p = p.tag(key, parts[key])
        p = p.tag("device_id", msg["device_id"])
        for key in CONTEXT_TAGS:
            if key in ctx:
                p = p.tag(key, str(ctx[key]))

        for key, value in msg.get("features", {}).items():
            p = p.field(key, float(value))
        for key, value in ctx.items():
            if key not in CONTEXT_TAGS and isinstance(value, (int, float)):
                p = p.field(f"ctx_{key}", float(value))
        for key, value in msg.get("quality", {}).items():
            if isinstance(value, (int, float)):
                p = p.field(f"q_{key}", float(value))

        window = msg.get("window", {})
        p = p.field("win_fs", float(window.get("fs", 0)))
        p = p.field("win_n", float(window.get("n", 0)))
        return p.time(msg["ts"])

    def _status_point(self, parts: dict, msg: dict):
        from influxdb_client import Point

        p = Point(STATUS_MEASUREMENT)
        for key in ("site", "area", "machine", "sensor"):
            if parts.get(key):
                p = p.tag(key, parts[key])
        p = p.tag("device_id", msg.get("device_id", "unknown"))
        p = p.tag("state", str(msg.get("state", "unknown")))
        p = p.field("online", 1.0 if msg.get("state") == "online" else 0.0)
        for key in ("rssi_dbm", "free_heap"):
            if isinstance(msg.get(key), (int, float)):
                p = p.field(key, float(msg[key]))
        return p.time(msg.get("ts") or schema.now_iso())

    # -------------------------------------------------- การประเมินผล

    def _evaluate(self, msg: dict) -> None:
        """ประเมินแบบจำลองแล้วส่งผลเข้า topic alert

        **ยังไม่ทำในขั้นนี้โดยเจตนา** เพราะยังไม่มีแบบจำลองที่เทรนแล้ว
        และเกณฑ์การแจ้งเตือนต้องกำหนดจากการกระจายของข้อมูลฐานของเครื่องจักรจริง
        ซึ่งยังเก็บไม่ได้ ดู `docs/coop-proposal.md` §5.6.1 และ §7.4.4

        สิ่งที่ฟังก์ชันนี้ต้องทำเมื่อถึงขั้นที่ 5
            1. ถ้า `machine_is_running` เป็นเท็จ ให้ข้ามทั้งหมด
               มิฉะนั้นระบบจะแจ้งเตือนทุกครั้งที่ปิดเครื่องตามปกติ
            2. ถ้า `usable_for_speed_features` เป็นเท็จ ห้ามใช้ h1_frac และ r21
            3. เทียบกับขอบเขตของข้อมูลฐาน **แยกตามช่วงความเร็วรอบ**
            4. ถ้าเกินเกณฑ์ ให้ publish เข้า `machine_topic(..., "alert")`
        """
        if not schema.machine_is_running(msg):
            self.stats["skipped_stopped"] += 1
        elif not schema.usable_for_speed_features(msg):
            self.stats["speed_features_unusable"] += 1

    # ------------------------------------------------------- callback

    def on_message(self, _client, _userdata, mqtt_msg) -> None:
        self.stats["received"] += 1
        try:
            parts = schema.parse_topic(mqtt_msg.topic)
        except schema.SchemaError as e:
            self.stats["bad_topic"] += 1
            self._note(mqtt_msg.topic, [str(e)])
            return

        try:
            payload = json.loads(mqtt_msg.payload.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as e:
            self.stats["bad_json"] += 1
            self._note(mqtt_msg.topic, [f"อ่าน JSON ไม่ได้: {e}"])
            return

        if parts["kind"] == "status":
            self.stats["status"] += 1
            if self.write_api:
                self.write_api.write(self.bucket, self.org,
                                     self._status_point(parts, payload))
            return

        problems = schema.validate_feature(payload)
        if problems:
            self.stats["invalid"] += 1
            self._note(mqtt_msg.topic, problems)
            return

        self._evaluate(payload)
        self.by_machine[parts["machine"]] += 1
        if self.write_api:
            self.write_api.write(self.bucket, self.org, self._point(parts, payload))
        self.stats["written"] += 1

    def _note(self, topic: str, problems: list[str]) -> None:
        if len(self.problems) < 20:
            self.problems.append((topic, problems))

    # ----------------------------------------------------------- สรุป

    def report(self) -> None:
        print("\n" + "=" * 64)
        print("สรุปการทำงาน")
        for key in ("received", "written", "status", "invalid", "bad_json",
                    "bad_topic", "skipped_stopped", "speed_features_unusable"):
            if self.stats[key]:
                print(f"  {key:26s} {self.stats[key]:>8,d}")
        if self.by_machine:
            print("\n  ข้อความที่เขียนสำเร็จ แยกตามเครื่องจักร")
            for name, count in sorted(self.by_machine.items()):
                print(f"    {name:12s} {count:>8,d}")
        if self.problems:
            print(f"\n  ตัวอย่างข้อความที่มีปัญหา ({len(self.problems)} รายการแรก)")
            for topic, problems in self.problems[:5]:
                print(f"    {topic}\n      {problems}")
        print("=" * 64)

    def close(self) -> None:
        if self.write_api:
            self.write_api.close()
        if self.influx:
            self.influx.close()


def main() -> int:
    ap = argparse.ArgumentParser(description="รับข้อความ MQTT แล้วเขียนลง InfluxDB")
    ap.add_argument("--host", default="localhost")
    ap.add_argument("--port", type=int, default=1883)
    ap.add_argument("--dry-run", action="store_true",
                    help="ไม่เขียนฐานข้อมูล ใช้ตรวจว่าแยก tag และตรวจข้อความถูกไหม")
    ap.add_argument("--seconds", type=float, default=0.0,
                    help="ทำงานกี่วินาทีแล้วหยุด (0 = จนกว่าจะกด Ctrl-C)")
    args = ap.parse_args()

    import paho.mqtt.client as mqtt

    ing = Ingestor(load_env(), args.dry_run)
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="pdm-ingest")

    def on_connect(c, _u, _f, reason, _p):
        if reason != 0:
            print(f"ต่อ broker ไม่สำเร็จ: {reason}", file=sys.stderr)
            return
        c.subscribe([(schema.SUB_FEATURE, 1), (schema.SUB_STATUS, 1)])
        print(f"subscribe แล้ว: {schema.SUB_FEATURE} และ {schema.SUB_STATUS}")

    client.on_connect = on_connect
    client.on_message = ing.on_message
    client.connect(args.host, args.port, keepalive=60)
    print(f"ต่อ broker ที่ {args.host}:{args.port} แล้ว"
          + ("  (โหมดไม่เขียนฐานข้อมูล)" if args.dry_run else ""))

    stop_at = time.time() + args.seconds if args.seconds else None
    running = True

    def handle_stop(_sig, _frame):
        nonlocal running
        running = False

    signal.signal(signal.SIGINT, handle_stop)

    client.loop_start()
    last = 0
    try:
        while running and (stop_at is None or time.time() < stop_at):
            time.sleep(0.5)
            if ing.stats["received"] - last >= 200:
                last = ing.stats["received"]
                print(f"รับแล้ว {last:,} · เขียนแล้ว {ing.stats['written']:,} "
                      f"· ไม่ผ่าน {ing.stats['invalid']:,}", flush=True)
    finally:
        client.loop_stop()
        client.disconnect()
        ing.report()
        ing.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
