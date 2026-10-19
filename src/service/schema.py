"""สัญญาของข้อความระหว่างอุปกรณ์ปลายทางกับ Python service

**ไฟล์นี้คือแหล่งความจริงเดียวของรูปแบบ topic และ JSON** ทั้งสคริปต์จำลอง
และตัวรับข้อมูลต้อง import จากที่นี่ ห้ามเขียนรูปแบบซ้ำในที่อื่น มิฉะนั้น
พอแก้รูปแบบข้างหนึ่งแล้วลืมอีกข้าง ระบบจะพังแบบเงียบๆ

รายละเอียดการออกแบบและเหตุผลอยู่ใน `docs/data-pipeline-design.md`

## โครงสร้าง topic มีสองแบบ

    ระดับเซ็นเซอร์ (6 ระดับ)   pdm/<site>/<area>/<machine>/<sensor>/<kind>
                              kind = feature | status | raw
    ระดับเครื่องจักร (5 ระดับ)  pdm/<site>/<area>/<machine>/<kind>
                              kind = assessment

**ความลึกต้องคงที่ภายในชนิดข้อความเดียวกัน** ไม่ใช่คงที่ทั้งระบบ เพราะการ
แจ้งเตือนเป็นเรื่องของเครื่องจักรทั้งเครื่อง ไม่ใช่ของเซ็นเซอร์ตัวใดตัวหนึ่ง
ถ้าบังคับให้ `assessment` ลงลึกถึงเซ็นเซอร์ จะต้องเลือกมาหนึ่งตัวแบบไม่มีเหตุผล
สิ่งที่ห้ามคือให้ `feature` ของบางเครื่องลึก 5 ระดับและบางเครื่องลึก 6 ระดับ
เพราะการ subscribe ด้วย wildcard จะได้ผลไม่ตรงกัน
"""

from __future__ import annotations

import math
import re
from datetime import datetime, timezone

SCHEMA_VERSION = 1
ROOT = "pdm"

SENSOR_KINDS = ("feature", "status", "raw")
# 🚩 เคยชื่อ `alert` จนถึง 2026-10-19 แล้วเปลี่ยนเพราะชื่อนั้นโกหก
# `alert` แปลว่า "การแจ้งเตือน" ซึ่งชวนให้เข้าใจว่ามีเฉพาะตอนมีเรื่อง
# **แต่ระบบส่งทุกข้อความที่ประเมิน ไม่ว่าผลจะปกติหรือไม่** (ดู assessment_message)
# และข้อมูลก้อนเดียวกันเขียนลง InfluxDB ในชื่อ measurement `assessment` อยู่แล้ว
# ของก้อนเดียวกันจึงเคยมีสองชื่อ **ตัวที่บอกว่าควรปลุกคนคือ `severity` ไม่ใช่ชื่อ topic**
MACHINE_KINDS = ("assessment",)
ALL_KINDS = SENSOR_KINDS + MACHINE_KINDS

# สถานะความน่าเชื่อถือของการวัดความเร็วรอบ ดู docs/data-pipeline-design.md §4.3
ROT_QUALITY = ("ok", "noisy", "lost", "stopped")

# ผลการประเมินที่ส่งเข้า topic assessment
#
# 🚩 **ทำไมต้องมี `unknown_anomaly` แยกจาก `fault`**
#
# ออกแบบเดิมมีแค่ "ปกติ" กับ "เสีย" ซึ่งเป็นช่องว่างที่พบตอนทบทวนวรรณกรรม
# เพราะที่หน้างานจริงจะเกิดกรณี **ผิดปกติแต่จำแนกชนิดไม่ได้** แน่นอน
# เนื่องจากเครื่องจักรจริงมีความเสียหายที่ชุดข้อมูลที่ใช้เทรนไม่มี
# (เช่น BPFI ซึ่ง MAFAULDA ไม่มีเลย)
#
# ถ้าไม่มีช่องนี้ ระบบจะถูกบังคับให้ตอบว่าเป็นชนิดใดชนิดหนึ่งที่รู้จัก
# **อย่างมั่นใจแต่ผิด** ซึ่งแย่กว่าการตอบว่าไม่รู้
#
# แนวทางนี้มาจาก Costa et al., IEEE Access 2026 ซึ่งใช้ MAFAULDA ชุดเดียวกับเรา
# ดู `paper/literature-review.md` ฉบับ 02 และ `paper/README.md` คำถามข้อ 5
#
# * `normal`          — อยู่ในขอบเขตของข้อมูลฐาน
# * `unknown_anomaly` — หลุดขอบเขต แต่ยังไม่มีชั้นที่ 2 จึงบอกชนิดไม่ได้
# * `fault`           — หลุดขอบเขต และชั้นที่ 2 จำแนกชนิดได้ (ยังไม่ได้ทำ)
# * `indeterminate`   — ตัดสินไม่ได้ เช่น เครื่องหยุด หรือความเร็วอยู่นอกช่วง
#                       ที่ข้อมูลฐานครอบคลุม **ต้องแยกจาก `normal` ให้ชัด**
#                       เพราะ "ไม่พบความผิดปกติ" กับ "ตรวจไม่ได้" ไม่เหมือนกัน
VERDICTS = ("normal", "unknown_anomaly", "fault", "indeterminate")

# ระดับความรุนแรงของการแจ้งเตือน
# `warn` คือข้อความเดียวผิดปกติแต่ยังไม่ผ่านด่านยืนยันซ้ำ
# `alarm` คือผ่านด่านแล้ว หรือค่าสูงเกินเกณฑ์เตือนทันที
SEVERITIES = ("info", "warn", "alarm")

# ชื่อทุกระดับของ topic ต้องผ่านรูปแบบนี้ ห้ามเว้นวรรค ห้ามอักษรไทย
# ห้ามตัวพิมพ์ใหญ่ และห้าม + กับ # เพราะเป็นอักขระ wildcard ของ MQTT
NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")


class SchemaError(ValueError):
    """รูปแบบ topic หรือข้อความไม่ถูกต้อง"""


# ---------------------------------------------------------------- topic

def _check_names(**parts: str) -> None:
    for key, value in parts.items():
        if not isinstance(value, str) or not NAME_RE.match(value):
            raise SchemaError(
                f"{key}={value!r} ผิดรูปแบบ ต้องเป็น a-z 0-9 และขีดกลางเท่านั้น "
                "ขึ้นต้นด้วยตัวอักษรหรือตัวเลข"
            )


def sensor_topic(site: str, area: str, machine: str, sensor: str, kind: str) -> str:
    """topic ระดับเซ็นเซอร์ 6 ระดับ"""
    if kind not in SENSOR_KINDS:
        raise SchemaError(f"kind={kind!r} ไม่ใช่ชนิดระดับเซ็นเซอร์ {SENSOR_KINDS}")
    _check_names(site=site, area=area, machine=machine, sensor=sensor)
    return "/".join((ROOT, site, area, machine, sensor, kind))


def machine_topic(site: str, area: str, machine: str,
                  kind: str = "assessment") -> str:
    """topic ระดับเครื่องจักร 5 ระดับ"""
    if kind not in MACHINE_KINDS:
        raise SchemaError(f"kind={kind!r} ไม่ใช่ชนิดระดับเครื่องจักร {MACHINE_KINDS}")
    _check_names(site=site, area=area, machine=machine)
    return "/".join((ROOT, site, area, machine, kind))


def parse_topic(topic: str) -> dict:
    """แยก topic กลับเป็นส่วนประกอบ ใช้ตอนรับข้อความเพื่อทำเป็น tag

    คืน dict ที่มี site, area, machine, kind เสมอ ส่วน sensor มีเฉพาะ
    ชนิดระดับเซ็นเซอร์ ถ้าเป็นชนิดระดับเครื่องจักรจะได้ ``sensor = None``
    """
    parts = topic.split("/")
    if not parts or parts[0] != ROOT:
        raise SchemaError(f"topic ต้องขึ้นต้นด้วย {ROOT!r} แต่ได้ {topic!r}")

    if len(parts) == 6 and parts[5] in SENSOR_KINDS:
        _, site, area, machine, sensor, kind = parts
        _check_names(site=site, area=area, machine=machine, sensor=sensor)
        return {"site": site, "area": area, "machine": machine,
                "sensor": sensor, "kind": kind}

    if len(parts) == 5 and parts[4] in MACHINE_KINDS:
        _, site, area, machine, kind = parts
        _check_names(site=site, area=area, machine=machine)
        return {"site": site, "area": area, "machine": machine,
                "sensor": None, "kind": kind}

    raise SchemaError(
        f"topic {topic!r} ไม่ตรงรูปแบบใดเลย ต้องเป็น 6 ระดับลงท้ายด้วย "
        f"{SENSOR_KINDS} หรือ 5 ระดับลงท้ายด้วย {MACHINE_KINDS}"
    )


# รูปแบบ subscribe ที่ service ใช้
SUB_FEATURE = f"{ROOT}/+/+/+/+/feature"
SUB_STATUS = f"{ROOT}/+/+/+/+/status"
SUB_ASSESSMENT = f"{ROOT}/+/+/+/assessment"


# -------------------------------------------------------------- ข้อความ

def now_iso() -> str:
    """เวลาปัจจุบันแบบ UTC ISO 8601 ลงท้ายด้วย Z

    **ห้ามใช้เวลาท้องถิ่น** เพราะข้อความจากอุปกรณ์หลายตัวต้องเรียงลำดับ
    เทียบกันได้ และ InfluxDB เก็บเวลาเป็น UTC อยู่แล้ว
    """
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace(
        "+00:00", "Z")


def feature_message(device_id: str, ts: str, fs: float, n: int,
                    context: dict, features: dict, quality: dict) -> dict:
    """ประกอบข้อความชนิด feature ตามรูปแบบใน docs/data-pipeline-design.md §4.1"""
    return {
        "schema": SCHEMA_VERSION,
        "device_id": device_id,
        "ts": ts,
        "window": {"fs": fs, "n": n},
        "context": context,
        "features": features,
        "quality": quality,
    }


def status_message(device_id: str, state: str, **extra) -> dict:
    """ข้อความชนิด status ส่งเป็น heartbeat และใช้เป็น Last Will and Testament"""
    msg = {"schema": SCHEMA_VERSION, "device_id": device_id,
           "ts": now_iso(), "state": state}
    msg.update(extra)
    return msg


def assessment_message(machine: str, verdict: str, severity: str, *,
                  device_id: str | None = None, score: float = 0.0,
                  n_exceed: int = 0, evidence: list[dict] | None = None,
                  gate: dict | None = None, context: dict | None = None,
                  model: dict | None = None, trend: dict | None = None,
                  caveats: list[str] | None = None) -> dict:
    """ประกอบข้อความชนิด `assessment` ที่ส่งเข้า ``machine_topic(...)``

    **ส่งทุกครั้งที่ประเมิน ไม่ใช่ส่งเฉพาะตอนผิดปกติ** เพราะผู้ที่สมัครรับ
    ต้องแยกออกได้ระหว่าง "ประเมินแล้วปกติ" กับ "ไม่มีใครประเมินอยู่"
    ถ้าส่งเฉพาะตอนผิดปกติ ความเงียบจะกำกวม ซึ่งเป็นปัญหาเดียวกับที่
    Last Will and Testament แก้ไว้ในระดับอุปกรณ์ (ดู §3.5 ของเอกสารออกแบบ)

    ``evidence`` คือตัวชี้วัดที่หลุดเกณฑ์พร้อมค่า z **เป็นส่วนที่สำคัญที่สุด
    ของข้อความนี้** เพราะระบบที่บอกได้แค่คะแนนลอยๆ จะไม่มีใครเชื่อถือหน้างาน
    ช่างซ่อมต้องรู้ว่าให้ไปดูอะไร

    ``trend`` คือผลการทดสอบแนวโน้มรายวัน ซึ่งตอบคนละคำถามกับ ``verdict``
    ``verdict`` บอกว่า**ตอนนี้**ผิดปกติไหม ส่วน ``trend`` บอกว่า**แย่ลงเรื่อยๆ**
    ไหม การเตือนที่กระจัดกระจายโดยไม่มีทิศทางเป็นเรื่องที่คนหน้างานทนได้
    แต่การเตือนที่ถี่ขึ้นเรื่อยๆ คือสิ่งที่ทำให้เขาตัดสินใจหยุดเครื่องเข้าซ่อม
    """
    if verdict not in VERDICTS:
        raise SchemaError(f"verdict={verdict!r} ต้องเป็นหนึ่งใน {VERDICTS}")
    if severity not in SEVERITIES:
        raise SchemaError(f"severity={severity!r} ต้องเป็นหนึ่งใน {SEVERITIES}")
    msg = {
        "schema": SCHEMA_VERSION,
        "machine": machine,
        "ts": now_iso(),
        "verdict": verdict,
        "severity": severity,
        "score": round(float(score), 3),
        "n_exceed": int(n_exceed),
        "evidence": evidence or [],
        "gate": gate or {},
        "context": context or {},
        "model": model or {},
        "trend": trend or {},
        "caveats": caveats or [],
    }
    if device_id:
        msg["device_id"] = device_id
    return msg


def lwt_message(device_id: str) -> dict:
    """ข้อความที่ broker จะประกาศแทนเมื่ออุปกรณ์หลุดแบบไม่ได้บอกลา

    ถ้าไม่ตั้งค่านี้ ระบบจะแยกไม่ออกระหว่าง "เครื่องจักรปกติ ไม่มีอะไรผิด"
    กับ "อุปกรณ์ตายไปแล้ว ไม่มีใครวัดอยู่"
    """
    return status_message(device_id, "offline", reason="lwt")


# ------------------------------------------------------------ ตรวจสอบ

def _finite(x) -> bool:
    return isinstance(x, (int, float)) and not isinstance(x, bool) and math.isfinite(x)


def validate_feature(msg: dict) -> list[str]:
    """ตรวจข้อความชนิด feature คืนรายการปัญหา ถ้าไม่มีปัญหาคืนลิสต์ว่าง

    **คืนรายการแทนการ raise โดยเจตนา** เพราะ service ต้องทำงานต่อได้แม้เจอ
    ข้อความเสีย การหยุดทั้งระบบเพราะอุปกรณ์ตัวเดียวส่งข้อมูลผิดเป็นพฤติกรรม
    ที่ยอมรับไม่ได้ในระบบติดตามเครื่องจักร
    """
    problems: list[str] = []

    if not isinstance(msg, dict):
        return ["payload ไม่ใช่ JSON object"]

    ver = msg.get("schema")
    if ver != SCHEMA_VERSION:
        problems.append(f"schema={ver!r} ไม่ตรงกับที่รองรับ ({SCHEMA_VERSION})")

    for key in ("device_id", "ts"):
        if not isinstance(msg.get(key), str) or not msg[key]:
            problems.append(f"ไม่มีฟิลด์ {key} หรือไม่ใช่สตริง")

    window = msg.get("window")
    if not isinstance(window, dict):
        problems.append("ไม่มีฟิลด์ window")
    else:
        if not _finite(window.get("fs")) or window["fs"] <= 0:
            problems.append("window.fs ต้องเป็นตัวเลขบวก")
        if not isinstance(window.get("n"), int) or window["n"] <= 0:
            problems.append("window.n ต้องเป็นจำนวนเต็มบวก")

    ctx = msg.get("context")
    if not isinstance(ctx, dict):
        problems.append("ไม่มีฟิลด์ context")
    else:
        quality_flag = ctx.get("rot_quality")
        if quality_flag not in ROT_QUALITY:
            problems.append(f"context.rot_quality={quality_flag!r} ต้องเป็นหนึ่งใน {ROT_QUALITY}")
        # ความเร็วรอบต้องมีเสมอ แม้ตอนวัดไม่ได้ก็ต้องส่ง 0 มา ไม่ใช่ละไว้
        if not _finite(ctx.get("rot_hz")) or ctx["rot_hz"] < 0:
            problems.append("context.rot_hz ต้องเป็นตัวเลขไม่ติดลบ")

    feats = msg.get("features")
    if not isinstance(feats, dict) or not feats:
        problems.append("ไม่มีฟิลด์ features หรือว่างเปล่า")
    else:
        bad = [k for k, v in feats.items() if not _finite(v)]
        if bad:
            problems.append(f"features มีค่าที่ไม่ใช่ตัวเลขจำกัด {len(bad)} ตัว "
                            f"เช่น {bad[:3]}")

    qual = msg.get("quality")
    if not isinstance(qual, dict):
        problems.append("ไม่มีฟิลด์ quality")
    elif "clipped_pct" in qual and not (_finite(qual["clipped_pct"])
                                        and 0 <= qual["clipped_pct"] <= 100):
        problems.append("quality.clipped_pct ต้องอยู่ระหว่าง 0 ถึง 100")

    return problems


def usable_for_speed_features(msg: dict) -> bool:
    """ตัวชี้วัดที่อิงความเร็วรอบ (h1_frac, r21) ใช้ได้หรือไม่

    ใช้ได้เฉพาะเมื่อ tachometer ยังเชื่อถือได้ ถ้าเครื่องหยุดหรือวัดไม่ได้
    ค่าเหล่านั้นไม่มีความหมาย และห้ามนำไปแจ้งเตือน
    """
    return msg.get("context", {}).get("rot_quality") in ("ok", "noisy")


def machine_is_running(msg: dict) -> bool:
    """เครื่องจักรกำลังหมุนอยู่หรือไม่

    ถ้าหยุด ต้องข้ามการประเมินทั้งหมด มิฉะนั้นระบบจะแจ้งเตือนทุกครั้ง
    ที่ปิดเครื่องตามปกติ
    """
    return msg.get("context", {}).get("rot_quality") != "stopped"
