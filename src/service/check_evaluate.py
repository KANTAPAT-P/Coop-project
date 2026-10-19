"""ตรวจว่า `_evaluate` ตัดสินถูกทั้งสี่กรณี โดยไม่ต้องมี broker หรือฐานข้อมูล

## ทำไมต้องมีสคริปต์นี้

การทดสอบทั้งเส้นทางต้องเปิด Docker, Mosquitto, InfluxDB และรออย่างน้อยหลายนาที
ซึ่งช้าเกินกว่าจะรันทุกครั้งที่แก้โค้ด และถ้าผลออกมาผิดก็แยกไม่ออกว่าผิดที่
ตรรกะการตัดสิน ที่การเชื่อมต่อ หรือที่ฐานข้อมูล

สคริปต์นี้แทน MQTT client ด้วยตัวเก็บข้อความปลอม แล้วป้อน**ข้อมูลจริงจาก
`feature_grid.csv`** เข้าไปตรงๆ จึงตรวจได้เฉพาะตรรกะการตัดสิน
รันเสร็จในไม่ถึงวินาที และไม่ต้องพึ่งบริการใดเลย

## สิ่งที่ตรวจ

1. ไฟล์ปกติในช่วงความเร็วที่ครอบคลุม -> `normal`
2. ไฟล์ที่เสีย -> ผ่านด่านแล้วได้ `unknown_anomaly` ไม่ใช่ `fault`
   เพราะยังไม่มีชั้นที่ 2
3. เครื่องหยุด -> `indeterminate` **ไม่ใช่** `normal`
4. ความเร็วนอกช่วงข้อมูลฐาน -> `indeterminate` **ไม่ใช่** `unknown_anomaly`
5. tachometer เสีย -> ยังประเมินได้ แต่ตัด `h1_frac` และ `r21` ออก
   และใส่หมายเหตุไว้
6. ด่านยืนยันซ้ำ -> ไม่เตือนก่อนครบ k ข้อความ และประวัติของแต่ละเครื่องจักร
   แยกกัน

รัน:
    python src/service/check_evaluate.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.features.feature_grid import require_grid_for_window  # noqa: E402
from src.paths import repo_root  # noqa: E402
from src.service import schema  # noqa: E402
from src.service.ingest import Ingestor  # noqa: E402

MODEL = repo_root() / "models" / "baseline-normal.json"
PARTS = {"site": "plant1", "area": "test", "machine": "motor-01"}


class FakeMqtt:
    """เก็บข้อความที่ถูก publish ไว้ดูแทนการส่งออกจริง"""

    def __init__(self) -> None:
        self.sent: list[tuple[str, dict]] = []

    def publish(self, topic: str, payload: str, qos: int = 0) -> None:
        self.sent.append((topic, json.loads(payload)))

    def last(self) -> dict:
        return self.sent[-1][1]


def model_window() -> tuple[float, int]:
    """หน้าต่างที่โมเดลปัจจุบันถูกเทรน

    🚨 **ต้องอ่านจากไฟล์โมเดล ไม่ใช่เขียนเลขตายตัวใน fixture** เดิมเขียนไว้ว่า
    `fs=51200, n=32768` (640 ms) ซึ่งไม่ตรงกับหน้าต่างที่เทรนเลย
    **ไม่มีใครรู้ เพราะตอนนั้น `ingest.py` ยังไม่ได้ตรวจฟิลด์ `window`**
    พอเพิ่มด่านตรวจ ชุดทดสอบล้ม 7 จาก 15 ข้อทันที ซึ่งเป็นสัญญาณที่ถูกต้อง

    > **fixture ที่ไม่มีใครตรวจ ก็ล้าหลังได้เหมือนเอกสาร**
    """
    w = json.loads(MODEL.read_text(encoding="utf-8")).get("window")
    if not w:
        # โมเดลเก่าที่ไม่ได้บันทึกหน้าต่าง -> ด่านจะข้ามการตรวจไปเอง
        return 51200.0, 250_000
    return float(w["fs"]), int(w["n"])


def make_msg(row: pd.Series, feats: list[str], *, rot_quality: str = "ok",
             rot_hz: float | None = None,
             window: tuple[float, int] | None = None) -> dict:
    fs, n = window or model_window()
    return schema.feature_message(
        device_id="esp32-test-a", ts=schema.now_iso(), fs=fs, n=n,
        context={"rot_hz": float(row.rot_hz if rot_hz is None else rot_hz),
                 "rot_quality": rot_quality},
        features={f: float(row[f]) for f in feats},
        quality={"clipped_pct": 0.0, "tach_jitter_pct": 0.2, "uptime_s": 10},
    )


def new_ingestor(k: int = 4, m: int = 5,
                 hard_z: float | None = "keep") -> tuple[Ingestor, FakeMqtt]:
    """``hard_z=None`` ปิดช่องทางเตือนทันที เพื่อทดสอบด่านยืนยันซ้ำแยกเดี่ยว"""
    ing = Ingestor({}, dry_run=True, model_path=MODEL, gate_k=k, gate_m=m)
    if hard_z != "keep":
        ing.model.hard_z = hard_z
    fake = FakeMqtt()
    ing.mqtt = fake
    return ing, fake


def feed(ing: Ingestor, fake: FakeMqtt, msg: dict, n: int = 1,
         machine: str = "motor-01") -> dict:
    parts = dict(PARTS, machine=machine)
    for _ in range(n):
        ing._evaluate(parts, msg)
    return fake.last()


def main() -> int:
    if not MODEL.is_file():
        raise SystemExit(f"ไม่พบโมเดลที่ {MODEL}\n"
                         f"สร้างก่อนด้วย: python src/models/eval_detector.py")
    # ตารางต้องเป็นตัวเดียวกับที่เทรนโมเดล ไม่งั้นค่าของ feature จะมาจาก
    # หน้าต่างคนละขนาดกับเส้นฐาน แล้วไฟล์ปกติจะถูกตัดสินว่าผิดปกติ
    #
    # 🚩 **ด่านตรวจ `window` จับกรณีนี้ไม่ได้** เพราะมันเทียบแค่สิ่งที่ข้อความ
    # **ประกาศ** ไม่ได้วัดจากค่าจริง อุปกรณ์ที่ประกาศหน้าต่างผิดจะผ่านด่านไปได้
    # ด่านนี้จับการตั้งค่าผิดอย่างซื่อสัตย์ ไม่ได้จับอุปกรณ์ที่โกหก
    fs_m, n_m = model_window()
    gpath = require_grid_for_window({"fs": fs_m, "n": n_m})
    print(f"ใช้ตาราง {gpath.name} ให้ตรงกับหน้าต่างที่โมเดลเทรน "
          f"({n_m / fs_m * 1000:.0f} ms)")
    grid = pd.read_csv(gpath)
    feats = [c for c in grid.columns if "." in c]

    ing0, _ = new_ingestor()
    lo, hi = ing0.model.speed_lo, ing0.model.speed_hi
    mid = (lo + hi) / 2

    # เลือกไฟล์ที่ความเร็วใกล้กลางช่วง เพื่อไม่ให้ติดปัญหาปลายช่วง
    def pick(mask: pd.Series) -> pd.Series:
        g = grid[mask & grid.rot_hz.between(lo, hi)]
        return g.iloc[(g.rot_hz - mid).abs().argsort().iloc[0]]

    normal = pick(grid.cls == "normal")
    bad = pick((grid.cls == "underhang") & (grid.subclass == "ball_fault")
               & (grid.mass_g == 0))

    checks: list[tuple[str, bool, str]] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        checks.append((name, ok, detail))
        print(f"  {'✅' if ok else '❌'} {name}" + (f"  — {detail}" if detail else ""))

    print(f"โมเดล {MODEL.name} ครอบคลุม {lo:.2f}-{hi:.2f} Hz "
          f"กฎ {ing0.model.rule} ต้องหลุดเกณฑ์ย่อย {ing0.model.vote_min} ตัว")
    print()

    # 1 — ไฟล์ปกติต้องได้ normal
    ing, fake = new_ingestor()
    out = feed(ing, fake, make_msg(normal, feats), n=5)
    check("ไฟล์ปกติ -> normal", out["verdict"] == "normal",
          f"rot={normal.rot_hz:.2f} Hz  verdict={out['verdict']} "
          f"n_exceed={out['n_exceed']}")

    # 2 — ไฟล์ที่เสียต้องได้ unknown_anomaly ไม่ใช่ fault
    ing, fake = new_ingestor()
    out = feed(ing, fake, make_msg(bad, feats), n=5)
    check("ไฟล์ที่เสีย -> unknown_anomaly",
          out["verdict"] == "unknown_anomaly" and out["severity"] == "alarm",
          f"rot={bad.rot_hz:.2f} Hz  score={out['score']} "
          f"n_exceed={out['n_exceed']}")
    check("ยังไม่ตอบ fault เพราะไม่มีชั้นที่ 2", out["verdict"] != "fault")
    check("มีหลักฐานกำกับว่าตัวชี้วัดไหนผิดปกติ", len(out["evidence"]) > 0,
          ", ".join(f"{e['feature']}={e['z']}" for e in out["evidence"][:3]))

    # 3 — เครื่องหยุด
    ing, fake = new_ingestor()
    out = feed(ing, fake, make_msg(bad, feats, rot_quality="stopped"))
    check("เครื่องหยุด -> indeterminate ไม่ใช่ normal",
          out["verdict"] == "indeterminate"
          and "machine_stopped" in out["caveats"])

    # 4 — ความเร็วนอกช่วง
    ing, fake = new_ingestor()
    out = feed(ing, fake, make_msg(bad, feats, rot_hz=hi + 15.0), n=5)
    check("ความเร็วนอกช่วงข้อมูลฐาน -> indeterminate",
          out["verdict"] == "indeterminate"
          and "speed_out_of_baseline_range" in out["caveats"],
          f"rot={hi + 15:.2f} Hz > {hi:.2f} Hz")

    # 5 — tachometer เสีย
    ing, fake = new_ingestor()
    out = feed(ing, fake, make_msg(bad, feats, rot_quality="noisy"), n=5)
    check("tach เสียแต่ยังประเมินได้", out["verdict"] != "indeterminate")
    # `noisy` = วัดความเร็วได้แต่แกว่ง ซึ่ง schema ถือว่ายังเชื่อถือได้
    # จึงต้องประเมินครบทุกตัวชี้วัด ไม่ตัดอะไรออก
    ing, fake = new_ingestor()
    out = feed(ing, fake, make_msg(bad, feats, rot_quality="noisy"), n=5)
    check("tach แกว่ง -> ประเมินครบทุกตัวชี้วัด ไม่ตัดอะไรออก",
          "speed_features_excluded" not in out["caveats"], str(out["caveats"]))
    # 🚨 ข้อนี้จับบั๊กได้จริงรอบแรก เดิมยังประเมินต่อทั้งที่ไม่รู้ความเร็ว
    ing, fake = new_ingestor()
    out = feed(ing, fake, make_msg(bad, feats, rot_quality="lost"), n=5)
    check("tach หายสิ้นเชิง -> indeterminate เพราะเส้นฐานทั้งก้อนอิง rot_hz",
          out["verdict"] == "indeterminate"
          and "rot_hz_lost" in out["caveats"],
          f"verdict={out['verdict']} caveats={out['caveats']}")

    # 5.5 — ด่านตรวจหน้าต่าง ทดสอบสองทาง
    #
    # 🚨 ต้องทดสอบทั้งทางที่ควรผ่านและทางที่ควรไม่ผ่าน เพราะด่านที่ไม่เคย
    # ปฏิเสธอะไรเลยก็เหมือนไม่มีด่าน และด่านที่ปฏิเสธทุกอย่างก็ใช้งานไม่ได้
    # ฟิลด์ `window` อยู่ใน schema มาตั้งแต่เวอร์ชันแรกแต่ไม่มีใครอ่าน
    # จึงป้องกันอะไรไม่ได้เลยจนกระทั่งมีด่านนี้
    fs_ok, n_ok = model_window()
    for label, win, want_block in (
        ("หน้าต่างตรงกับที่เทรน -> ประเมินปกติ", (fs_ok, n_ok), False),
        ("หน้าต่างสั้นกว่าที่เทรน -> indeterminate", (fs_ok, n_ok // 4), True),
        ("หน้าต่างยาวกว่าที่เทรน -> indeterminate", (fs_ok, 250_000), True),
        ("fs ไม่ตรงกับที่เทรน -> indeterminate", (20000.0, 8192), True),
    ):
        ing, fake = new_ingestor()
        out = feed(ing, fake, make_msg(normal, feats, window=win), n=5)
        blocked = any(c.startswith("window_mismatch") for c in out["caveats"])
        ok = (blocked == want_block
              and (out["verdict"] == "indeterminate" if want_block else True)
              # 🚩 severity ต้องเป็น warn ไม่ใช่ info เพราะเป็นการตั้งค่าผิด
              # ที่ไม่หายเอง ต่างจากเครื่องหยุดหรือ tacho หลุดซึ่งเป็นชั่วคราว
              and (out["severity"] == "warn" if want_block else True))
        check(label, ok,
              f"window={win} verdict={out['verdict']} "
              f"severity={out['severity']} caveats={out['caveats']}")

    # 6 — ด่านยืนยันซ้ำ
    ing, fake = new_ingestor(k=4, m=5, hard_z=None)
    seq = []
    parts = dict(PARTS)
    msg_bad = make_msg(bad, feats)
    for _ in range(4):
        ing._evaluate(parts, msg_bad)
        seq.append(fake.last()["severity"])
    check("ด่านไม่เตือนก่อนครบ 4 ข้อความ",
          seq[:3] == ["warn", "warn", "warn"] and seq[3] == "alarm",
          " -> ".join(seq))

    # 7 — ประวัติแยกตามเครื่องจักร
    ing, fake = new_ingestor(k=4, m=5, hard_z=None)
    for _ in range(3):
        feed(ing, fake, msg_bad, machine="motor-01")
    out_b = feed(ing, fake, msg_bad, machine="motor-02")
    check("ประวัติของแต่ละเครื่องจักรแยกกัน",
          out_b["severity"] == "warn",
          "motor-01 สะสม 3 ครั้งแล้ว แต่ motor-02 ต้องเริ่มนับใหม่")

    # 8 — ส่งทุกครั้งแม้ผลเป็นปกติ
    ing, fake = new_ingestor()
    feed(ing, fake, make_msg(normal, feats), n=3)
    check("ส่งข้อความ assessment ทุกครั้งแม้ผลเป็นปกติ", len(fake.sent) == 3,
          f"ส่งไป {len(fake.sent)} ข้อความจากการประเมิน 3 ครั้ง")

    # 9 — topic ถูกรูปแบบ 5 ระดับ
    ing, fake = new_ingestor()
    feed(ing, fake, make_msg(normal, feats))
    topic = fake.sent[-1][0]
    ok_topic = schema.parse_topic(topic)["kind"] == "assessment"
    check("topic เป็นรูปแบบระดับเครื่องจักร 5 ระดับ", ok_topic, topic)

    # 10 — 🚨 hard_z ต้องสูงกว่าที่ไฟล์ปกติทำได้ ไม่งั้นข้ามด่านได้
    ing, _ = new_ingestor()
    hz = ing.model.hard_z
    norm_scores = []
    for _, row in grid[(grid.cls == "normal")
                       & grid.rot_hz.between(lo, hi)].iterrows():
        r = ing.model.score({f: float(row[f]) for f in feats},
                            float(row.rot_hz))
        norm_scores.append(r["score"])
    worst_norm = max(norm_scores)
    check("hard_z สูงกว่า max_z ที่ไฟล์ปกติทำได้",
          hz is not None and hz > worst_norm,
          f"hard_z={hz:.1f} vs ไฟล์ปกติแย่สุด {worst_norm:.1f}")

    # 11 — ช่องทางเตือนทันทีทำงานเมื่อค่าสูงจริง
    ing, fake = new_ingestor(k=4, m=5)
    out = feed(ing, fake, msg_bad, n=1)
    fired = out["severity"] == "alarm"
    check("ค่าสูงเกิน hard_z เตือนทันทีไม่ต้องรอด่าน",
          fired == (out["score"] > hz),
          f"score={out['score']} hard_z={hz:.1f} severity={out['severity']}")

    print()
    failed = [n for n, ok, _ in checks if not ok]
    if failed:
        print(f"❌ ไม่ผ่าน {len(failed)} จาก {len(checks)} ข้อ: {failed}")
        return 1
    print(f"✅ ผ่านครบ {len(checks)} ข้อ")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
