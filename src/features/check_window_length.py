"""วัดว่าความยาวหน้าต่างมีผลต่อ feature แต่ละตัวมากแค่ไหน

## ทำไมต้องมี

โมเดลใน `models/baseline-normal.json` เทรนด้วย feature ที่คำนวณจาก **ไฟล์เต็ม
250,000 แถว = 4,883 ms** แต่ `docs/data-pipeline-design.md` §4.1 ออกแบบให้ ESP32
ส่ง feature ที่คำนวณจาก **8,192 ตัวอย่าง = 410 ms** ต่างกัน ~12 เท่า

ไม่มีใครสังเกตเห็นเพราะ **ความยาว 4,883 ms ไม่เคยถูกตัดสินใจ มันแถมมากับ dataset**
`feature_grid.py` แค่โหลดไฟล์ทั้งไฟล์แล้วโยนเข้า `channel_features()` จึงไม่มี
บรรทัดไหนในโค้ดที่เขียนว่า "เลือกหน้าต่าง 4,883 ms" ให้ใครไปเห็น

> **ค่าที่ไม่เคยถูกเลือก คือค่าที่ไม่มีใครตรวจ**

## คุมตัวแปรให้เหลือตัวเดียว

สคริปต์นี้ **ตรึง fs ไว้ที่ 51,200 Hz ทั้งสองฝั่ง** เปลี่ยนเฉพาะจำนวนตัวอย่าง `n`
ถ้าเปลี่ยน fs ไปเป็น 20,000 ด้วยจะมีสองตัวแปรเปลี่ยนพร้อมกัน แล้วแยกไม่ออกว่า
ส่วนต่างที่เห็นมาจากอะไร (ส่วน fs ที่ไม่ตรงกันเป็นปัญหาแยกอีกข้อ ดูบันทึกการทดลอง)

## วัดสองแบบ เพื่อแยกบั๊กออกจากฟิสิกส์

`channel_features` มี `tol_hz` สำหรับความกว้างหน้าต่างค้นพีค 1x/2x ค่าเริ่มต้น
`None` = 2% ของความเร็วรอบ ซึ่งที่ 30 Hz คือ +-0.6 Hz **แคบกว่าหนึ่งช่องความถี่
ของหน้าต่าง 410 ms (2.44 Hz)** หน้าต่างค้นจะว่างและได้ 0

- `naive` -- ไม่ส่ง `tol_hz` คือสิ่งที่จะเกิดถ้าย้ายโค้ดไปตรงๆ
- `fixed`  -- ส่ง `tol_hz` เป็น Hz สัมบูรณ์ตามที่ docstring บอก

ส่วนต่างระหว่างสองแบบ = ขนาดของบั๊ก · ที่เหลือใน `fixed` = ผลของความยาวจริงๆ

รัน:
    python src/features/check_window_length.py --limit 4     # ลองจับเวลา
    python src/features/check_window_length.py               # เต็มชุด
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.data import mafaulda as mf  # noqa: E402
from src.features.screen_signatures import channel_features  # noqa: E402
from src.paths import processed_dir, repo_root, sampling_rate  # noqa: E402
from src.viz.explore_raw_channels import CHANNELS  # noqa: E402

FS = float(sampling_rate())
N_FULL = 250_000
DESIGN_MS = 8_192 / 20_000 * 1000.0      # 410 ms ตามที่ออกแบบไว้ใน §4.1
HZ_LO, HZ_HI = 13.1, 61.2                # ขอบเขตเดียวกับ eval_detector
TRAIN_EVERY = 5

# feature ที่ channel_features คืนมา (ไม่รวม p2p ที่ feature_grid คำนวณเพิ่มเอง)
FEATS = ["rms", "kurt", "crest", "h1_frac", "r21",
         "e_low", "e_mid", "e_high", "kurt_band", "env_floor", "env_rel"]


def train_files() -> pd.DataFrame:
    """ไฟล์ปกติ 29 ไฟล์ชุดเดียวกับที่ใช้เทรนเส้นฐาน"""
    idx = mf.build_index()
    norm = idx[(idx.cls == "normal") & idx.rot_hz.between(HZ_LO, HZ_HI)]
    ordered = norm.sort_values("rot_hz").reset_index(drop=True)
    return ordered[(ordered.index % TRAIN_EVERY) < 3]


def slice_features(x: np.ndarray, rot: float, n: int,
                   tol_hz: float | None) -> list[dict[str, float]]:
    """feature ของทุกหน้าต่างย่อยที่ตัดได้จากสัญญาณก้อนนี้"""
    out = []
    for s in range(0, len(x) - n + 1, n):
        out.append(channel_features(x[s:s + n], rot, tol_hz=tol_hz))
    return out


def measure(files: pd.DataFrame, n_short: int) -> pd.DataFrame:
    rows, t0 = [], time.time()
    speeds = mf.speed_hz(files)
    for i, (idx_i, r) in enumerate(files.iterrows(), start=1):
        rot = float(speeds.loc[idx_i])
        d = mf.load(r["path"], CHANNELS)
        for ch in CHANNELS:
            x = d[ch].to_numpy()
            full = channel_features(x, rot)
            for mode, tol in (("naive", None), ("fixed", 3.0 * FS / n_short)):
                for w, f in enumerate(slice_features(x, rot, n_short, tol)):
                    rows.append({"rel": r["rel"], "ch": ch, "rot_hz": rot,
                                 "mode": mode, "win": w,
                                 **{f"full.{k}": full[k] for k in FEATS},
                                 **{f"short.{k}": f[k] for k in FEATS}})
        done = time.time() - t0
        print(f"  {i}/{len(files)}  ผ่านไป {done/60:.1f} นาที  "
              f"เหลืออีกราว {(done/i)*(len(files)-i)/60:.1f} นาที", flush=True)
    return pd.DataFrame(rows)


def bias_table(tab: pd.DataFrame, mode: str) -> pd.DataFrame:
    """ส่วนต่างของค่าจากหน้าต่างสั้นเทียบกับไฟล์เต็ม แยกตาม feature"""
    t = tab[tab["mode"] == mode]
    out = []
    for k in FEATS:
        s, f = t[f"short.{k}"], t[f"full.{k}"]
        ok = s.notna() & f.notna() & (f != 0)
        ratio = s[ok] / f[ok]
        # cv ภายในไฟล์: กระจายตัวของหน้าต่างย่อยในไฟล์+ช่องเดียวกัน
        g = t[ok].groupby(["rel", "ch"])[f"short.{k}"]
        cv_in = (g.std() / g.mean().abs()).median()
        # cv ข้ามไฟล์: กระจายตัวที่โมเดลใช้ตั้งเส้นฐาน
        gf = t[ok].groupby(["rel", "ch"])[f"full.{k}"].first()
        cv_across = gf.std() / abs(gf.mean())
        out.append({"feature": k,
                    "คำนวณได้ %": 100.0 * ok.sum() / len(s),
                    "bias %": 100.0 * (ratio.median() - 1.0),
                    "cv ในไฟล์": cv_in,
                    "cv ข้ามไฟล์": cv_across,
                    "cv ใน/ข้าม": cv_in / cv_across if cv_across else np.nan})
    return pd.DataFrame(out).set_index("feature")


def z_impact(tab: pd.DataFrame, model: dict) -> pd.DataFrame:
    """ถ้าป้อนค่าจากหน้าต่างสั้นเข้าโมเดลที่เทรนด้วยไฟล์เต็ม z จะเป็นเท่าไร"""
    names = model["features"]
    pos = {nm: j for j, nm in enumerate(names)}
    t = tab[tab["mode"] == "fixed"]
    rows = []
    for ch in sorted(t["ch"].unique()):
        s = t[t["ch"] == ch]
        for k in FEATS:
            nm = f"{ch}.{k}"
            if nm not in pos:
                continue
            j = pos[nm]
            v, r = s[f"short.{k}"], s["rot_hz"]
            ok = v.notna()
            if not ok.any():
                continue
            val = v[ok].to_numpy()
            if model["use_log"][j]:
                val = np.log(np.maximum(val, 1e-12))
            exp = model["intercept"][j] + model["slope"][j] * r[ok].to_numpy()
            z = np.abs(val - exp) / model["scale"][j]
            rows.append({"feature": nm, "median |z|": float(np.median(z))})
    out = pd.DataFrame(rows).sort_values("median |z|", ascending=False)
    return out.set_index("feature")


def main() -> int:
    ap = argparse.ArgumentParser(description="ผลของความยาวหน้าต่างต่อ feature")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--window-ms", type=float, default=DESIGN_MS)
    ap.add_argument("--model", type=Path,
                    default=repo_root() / "models" / "baseline-normal.json")
    args = ap.parse_args()

    n_short = int(round(args.window_ms / 1000.0 * FS))
    files = train_files()
    if args.limit:
        files = files.head(args.limit)
    print(f"ไฟล์ปกติ {len(files)} ไฟล์ | fs ตรึงไว้ที่ {FS:,.0f} Hz ทั้งสองฝั่ง")
    print(f"ไฟล์เต็ม {N_FULL:,} ตัวอย่าง = {N_FULL / FS * 1000:,.0f} ms")
    print(f"หน้าต่างสั้น {n_short:,} ตัวอย่าง = {args.window_ms:.0f} ms "
          f"-> ตัดได้ {N_FULL // n_short} หน้าต่างต่อไฟล์ต่อช่อง")
    print(f"ความละเอียดความถี่ {FS / N_FULL:.4f} Hz -> {FS / n_short:.2f} Hz\n")

    tab = measure(files, n_short)
    out = processed_dir() / "window_length_check.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    tab.to_csv(out, index=False)
    print(f"\nเขียน {len(tab):,} แถว ลง {out.relative_to(repo_root())}\n")

    for mode in ("naive", "fixed"):
        print(f"=== {mode} ===")
        print(bias_table(tab, mode).round(3).to_string(), "\n")

    if args.model.is_file():
        model = json.loads(args.model.read_text(encoding="utf-8"))
        z = z_impact(tab, model)
        print("=== z ที่โมเดลเดิมจะให้กับค่าจากหน้าต่างสั้น (mode=fixed) ===")
        print(z.head(15).round(2).to_string())
        n_trip = int((z["median |z|"] > model["z_feat"]).sum())
        n_hard = int((z["median |z|"] > model["hard_z"]).sum())
        print(f"\nติดเกณฑ์ |z| > {model['z_feat']}: {n_trip} จาก {len(z)} ตัว "
              f"(ต้องการ {model['vote_min']} ตัวจึงจะเตือน)")
        print(f"ทะลุ hard_z = {model['hard_z']:.1f}: {n_hard} ตัว "
              f"{'<- ข้ามด่านยืนยันซ้ำได้' if n_hard else ''}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
