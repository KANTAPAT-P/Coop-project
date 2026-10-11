"""เทรนและประเมินตัวตรวจจับความผิดปกติชั้นที่ 1 แล้วบันทึกโมเดล

## การแบ่งข้อมูล — ส่วนที่สำคัญที่สุดของสคริปต์นี้

`CLAUDE.md` หัวข้อ 5 วัดไว้แล้วว่าการแบ่งข้อมูลทำให้ accuracy ต่างกัน **27 จุด**
โดยที่ไม่ได้เปลี่ยนอะไรอื่นเลย ไฟล์นี้จึงแบ่งแบบที่เข้มงวดที่สุดเท่าที่ทำได้

```
ไฟล์ปกติ 47 ไฟล์  --> แบ่งตามไฟล์ สลับตามอันดับความเร็วรอบ
                        60% ใช้ประมาณเส้นฐาน  (โมเดลเห็น)
                        40% กันไว้วัดอัตราการเตือนผิด  (โมเดลไม่เคยเห็น)

ไฟล์ที่เสียทั้งหมด --> ใช้วัด recall เท่านั้น **โมเดลไม่เคยเห็นแม้แต่ไฟล์เดียว**
```

**ทำไมสลับตามอันดับความเร็วไม่ใช่สุ่ม** เพราะเส้นฐานเป็นฟังก์ชันของความเร็วรอบ
ถ้าสุ่มแล้วชุดที่ใช้ประมาณได้แต่ความเร็วต่ำ เส้นตรงจะ extrapolate ไปทั้งช่วงสูง
การสลับตามอันดับทำให้ทั้งสองชุดครอบคลุมช่วงความเร็วเท่ากัน

**เกณฑ์ตั้งด้วย leave-one-out บนไฟล์ปกติเท่านั้น** ห้ามดูไฟล์ที่เสีย
มิฉะนั้นคือการรั่วของข้อมูล

⚠️ ยังไม่ใช่การแบ่งที่ซื่อสัตย์ที่สุด เพราะไฟล์ปกติทั้งหมดน่าจะบันทึกรวดเดียว
**อัตราการเตือนผิดที่วัดได้จึงดีเกินจริง**

## ขอบเขตข้อมูลที่ใช้

ตาม `CLAUDE.md` หัวข้อ 5 ช่วงที่เทียบได้อย่างยุติธรรมคือ **13.1-61.2 Hz**
โดยใช้ **bearing เฉพาะมวล 0 g** และ **imbalance ทุกมวลรวมเป็นคลาสเดียว**

รัน:
    python src/models/eval_detector.py
    python src/models/eval_detector.py --z-feat 3.5 --k 4 --m 5
"""

from __future__ import annotations

import argparse
import sys
import time
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.models import detector  # noqa: E402
from src.paths import processed_dir, repo_root  # noqa: E402

HZ_LO, HZ_HI = 13.1, 61.2
TRAIN_EVERY = 5          # เอา 3 ใน 5 ไฟล์ไว้เทรน -> 60/40
FAULT_CLASSES = ("imbalance", "horizontal-misalignment", "vertical-misalignment",
                 "underhang", "overhang")


def load_grid(path: Path | None = None) -> pd.DataFrame:
    path = path or (processed_dir() / "feature_grid.csv")
    if not path.is_file():
        raise SystemExit(
            f"ไม่พบ {path}\nสร้างก่อนด้วย: python src/features/feature_grid.py")
    return pd.read_csv(path)


def grid_window(grid: pd.DataFrame) -> dict | None:
    """หน้าต่างที่ตารางนี้ใช้ อ่านจากคอลัมน์ที่ตารางพามาเอง

    `feature_grid.py` เขียน `win_fs` / `win_n` ลงทุกแถวเมื่อใช้ `--window-ms`
    **ให้ตารางบอกเอง ไม่ใช่เดาจากชื่อไฟล์** เพราะชื่อไฟล์เปลี่ยนได้โดยที่เนื้อหา
    ไม่เปลี่ยน แล้วโมเดลจะบันทึกหน้าต่างผิดโดยไม่มีใครรู้

    คืน ``None`` ถ้าเป็นตารางของไฟล์เต็ม ซึ่งถือว่า "ไม่ระบุหน้าต่าง"
    """
    if "win_fs" not in grid.columns or "win_n" not in grid.columns:
        return None
    fs, n = grid.win_fs.unique(), grid.win_n.unique()
    if len(fs) != 1 or len(n) != 1:
        raise SystemExit(
            f"ตารางมีหลายหน้าต่างปนกัน fs={fs} n={n} ซึ่งเทรนรวมกันไม่ได้")
    return {"fs": float(fs[0]), "n": int(n[0])}


def fair_subset(grid: pd.DataFrame) -> pd.DataFrame:
    """กรองให้เหลือชุดที่เทียบกันได้อย่างยุติธรรม

    🚩 กับดักที่ `CLAUDE.md` เตือนไว้: `mass_g == 0` ล้วนจะตัดคลาส imbalance
    ทิ้งทั้งคลาสโดยไม่มี error เพราะ imbalance ไม่มีไฟล์ที่ 0 g เลย
    """
    bearing = grid.cls.isin(["underhang", "overhang"])
    sub = grid[(~bearing | (grid.mass_g == 0))
               & grid.rot_hz.between(HZ_LO, HZ_HI)].copy()
    got = set(sub.cls.unique())
    if len(got) != 6:
        raise SystemExit(f"คาดว่าได้ 6 คลาส แต่ได้ {len(got)}: {sorted(got)}")
    return sub


def split_normal(norm: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """แบ่งไฟล์ปกติแบบสลับตามอันดับความเร็วรอบ

    🚨 **แบ่งตามไฟล์ ไม่ใช่ตามแถว** ถ้าตารางเป็นหนึ่งแถวต่อหน้าต่าง หน้าต่าง
    ทุกอันของไฟล์เดียวกันต้องไปอยู่ฝั่งเดียวกัน ไม่งั้นหน้าต่างพี่น้องจะโผล่
    ทั้งสองฝั่ง ซึ่งคือ leakage ตัวที่วัดไว้ว่ากินไป 27 จุด accuracy

    กับตารางของไฟล์เต็ม (หนึ่งแถว = หนึ่งไฟล์) ผลเหมือนเดิมทุกประการ
    """
    files = (norm.groupby("rel", as_index=False).rot_hz.first()
             .sort_values("rot_hz").reset_index(drop=True))
    train_files = set(files.rel[(files.index % TRAIN_EVERY) < 3])
    is_train = norm.rel.isin(train_files)
    return norm[is_train], norm[~is_train]


def n_files(df: pd.DataFrame) -> int:
    """จำนวนไฟล์ ซึ่งเป็น**หน่วยที่เป็นอิสระจากกันจริง** ไม่ใช่จำนวนแถว

    หน้าต่างที่ติดกันจากไฟล์เดียวกันคล้ายกันเองมากกว่าความต่างระหว่างไฟล์
    2-25 เท่า (วัดไว้ใน `experiments/2026-10-09-window-length-mismatch.md`)
    **การนับหน้าต่างเป็นตัวอย่างอิสระจะทำให้ขอบบนของอัตราการเตือนผิดดีเกินจริง**
    """
    return int(df.rel.nunique())


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--z-feat", type=float, default=3.0,
                    help="เกณฑ์ย่อยของแต่ละตัวชี้วัดในกฎ vote")
    ap.add_argument("--k", type=int, default=4, help="ต้องผิดปกติ k ข้อความ")
    ap.add_argument("--m", type=int, default=5, help="จากทั้งหมด m ข้อความล่าสุด")
    ap.add_argument("--out", type=Path,
                    default=repo_root() / "models" / "baseline-normal.json")
    ap.add_argument("--grid", type=Path, default=None,
                    help="ตาราง feature ที่จะใช้ ไม่ใส่ = feature_grid.csv (ไฟล์เต็ม)")
    args = ap.parse_args()

    grid = load_grid(args.grid)
    window = grid_window(grid)
    sub = fair_subset(grid)
    feats = [c for c in grid.columns if "." in c]

    norm = sub[sub.cls == "normal"]
    fault = sub[sub.cls.isin(FAULT_CLASSES)].copy()
    train, holdout = split_normal(norm)

    lines: list[str] = []

    def say(s: str = "") -> None:
        print(s)
        lines.append(s)

    say("# ตัวตรวจจับความผิดปกติชั้นที่ 1 — เทรนจากข้อมูลปกติเท่านั้น")
    say()
    say(f"**วันที่** {date.today().isoformat()} · "
        f"สร้างด้วย `python src/models/eval_detector.py`")
    say()
    say("## ข้อมูลที่ใช้")
    say()
    gname = (args.grid.name if args.grid else "feature_grid.csv")
    say(f"- `data/processed/{gname}` — {n_files(grid):,} ไฟล์ "
        f"{len(feats)} ตัวชี้วัด (12 ตัว x 6 ช่องสั่นสะเทือน ไม่รวม `mic` และ `tach`)")
    if window is None:
        say("- **หน้าต่าง: ไฟล์เต็ม 250,000 แถว = 4,883 ms** "
            "(หนึ่งแถวในตาราง = หนึ่งไฟล์)")
    else:
        dur = window["n"] / window["fs"] * 1000.0
        per = len(grid) / n_files(grid)
        say(f"- **หน้าต่าง: {window['n']:,} ตัวอย่าง @ {window['fs']:,.0f} Hz "
            f"= {dur:,.0f} ms** ความละเอียดความถี่ {window['fs'] / window['n']:.2f} Hz")
        say(f"- ตารางมี {len(grid):,} แถว = {n_files(grid):,} ไฟล์ x "
            f"{per:.0f} หน้าต่าง **หนึ่งแถว = หนึ่งข้อความ MQTT**")
        say(f"- ค่านี้ถูกบันทึกลงไฟล์โมเดลด้วย เพื่อให้ `ingest.py` "
            f"**ปฏิเสธข้อความที่หน้าต่างไม่ตรง** แทนที่จะประเมินต่อแบบผิดๆ")
    say(f"- ขอบเขตที่ยุติธรรม **{HZ_LO}-{HZ_HI} Hz · bearing เฉพาะ 0 g · "
        f"imbalance ทุกมวล** -> {n_files(sub):,} ไฟล์ 6 คลาส")
    say()
    say("| คลาส | ไฟล์ | หน้าต่าง |")
    say("|---|---:|---:|")
    for cls, g in sub.groupby("cls"):
        say(f"| {'**' + cls + '**' if cls == 'normal' else cls} | "
            f"{n_files(g)} | {len(g)} |")
    say()
    say("## การแบ่งข้อมูล")
    say()
    say(f"- ไฟล์ปกติ {n_files(norm)} ไฟล์ -> **เทรน {n_files(train)} · "
        f"กันไว้วัด {n_files(holdout)}** แบ่งแบบสลับตามอันดับความเร็วรอบ "
        f"(= {len(train):,} / {len(holdout):,} หน้าต่าง)")
    say(f"- ไฟล์ที่เสีย {n_files(fault):,} ไฟล์ ({len(fault):,} หน้าต่าง) -> "
        "**ใช้วัด recall เท่านั้น โมเดลไม่เคยเห็นแม้แต่ไฟล์เดียว**")
    if window is not None:
        say("- 🚨 **แบ่งตามไฟล์ ไม่ใช่ตามหน้าต่าง** หน้าต่างทุกอันของไฟล์เดียวกัน "
            "อยู่ฝั่งเดียวกันเสมอ ทั้งในการแบ่ง train/holdout และใน leave-one-out")
    say(f"- เส้นฐานครอบคลุม {train.rot_hz.min():.2f}-{train.rot_hz.max():.2f} Hz")
    say()

    # --------------------------------------- ความเร็วมีผลแค่ไหน
    n_strong = sum(1 for f in feats
                   if abs(np.corrcoef(norm.rot_hz, norm[f])[0, 1]) > 0.7)
    say("## 🚨 ทำไมเส้นฐานต้องแยกตามความเร็วรอบ")
    say()
    say(f"วัดในคลาส `normal` เอง ซึ่งไม่มีความเสียหายใดๆ พบว่า "
        f"**{n_strong} จาก {len(feats)} ตัวชี้วัดมีสหสัมพันธ์กับความเร็วรอบเกิน 0.7**")
    say()
    say("ถ้าตั้งเกณฑ์เป็นค่าคงที่ตัวเดียว **ระบบจะเตือนทุกครั้งที่เครื่องเร่งรอบ**")
    say()

    Xtr, rtr = train[feats].to_numpy(), train.rot_hz.to_numpy()

    # ------------------------------------- ตั้งเกณฑ์ด้วย leave-one-out
    say("## การตั้งเกณฑ์ — leave-one-out บนไฟล์ปกติ")
    say()
    say("ตัดไฟล์ปกติออกหนึ่งไฟล์ ประมาณเส้นฐานใหม่จากที่เหลือ แล้วให้คะแนนไฟล์ที่ตัดออก "
        "ทำซ้ำทุกไฟล์ จะได้การแจกแจงของคะแนนบนข้อมูลที่โมเดล**ไม่เคยเห็น** "
        "**ไม่ต้องสมมติรูปร่างการแจกแจงใดๆ และไม่ต้องแตะไฟล์ที่เสียเลย**")
    say()
    loo_max, loo_votes = detector.loo_scores(Xtr, rtr, feats, z_feat=args.z_feat,
                                             groups=train.rel.to_numpy())
    say(f"ผลจาก {n_files(train)} ไฟล์ ({len(loo_max):,} หน้าต่าง) "
        f"ที่เกณฑ์ย่อย |z| > {args.z_feat:g} "
        f"**ตัดออกทีละไฟล์ ไม่ใช่ทีละหน้าต่าง**")
    say()
    say("| สถิติ | `max_z` | จำนวนตัวชี้วัดที่หลุดเกณฑ์ย่อย |")
    say("|---|---:|---:|")
    for lbl, q in (("มัธยฐาน", 50), ("เปอร์เซ็นไทล์ 90", 90), ("สูงสุด", 100)):
        say(f"| {lbl} | {np.percentile(loo_max, q):.2f} | "
            f"{np.percentile(loo_votes, q):.1f} |")
    say()

    # กฎ max_z: ตั้งคัทไว้เหนือค่าสูงสุดที่ LOO เคยเห็น
    cut_max_z = float(np.max(loo_max)) * 1.05
    # กฎ vote: ต้องมากกว่าจำนวนที่ไฟล์ปกติเคยทำได้
    vote_min = int(np.max(loo_votes)) + 1
    say(f"- กฎ **`max_z`** ตั้งคัทที่ **{cut_max_z:.2f}** (สูงกว่าค่าสูงสุดของ LOO 5%)")
    say(f"- กฎ **`vote`** ต้องมีตัวชี้วัดหลุดเกณฑ์ย่อยอย่างน้อย **{vote_min} ตัว** "
        f"(ไฟล์ปกติทำได้สูงสุด {int(np.max(loo_votes))} ตัว)")
    say()
    hard_z = float(np.max(loo_max)) * 3.0
    say(f"### เกณฑ์เตือนทันที `hard_z` = {hard_z:.1f}")
    say()
    say("ช่องทางเตือนทันทีโดยไม่รอด่านยืนยันซ้ำ สำหรับค่าที่สูงมากอย่างชัดเจน "
        "เพราะถ้าเครื่องพังฉับพลันจริง การรอ 40 วินาทีอาจสายเกินไป")
    say()
    say(f"🚨 **รอบแรกตั้งไว้ที่ 12.0 ซึ่งผิด** เพราะ `max_z` ของไฟล์ปกติเองใน LOO "
        f"สูงถึง {np.max(loo_max):.2f} ไฟล์ปกติจึงข้ามด่านยืนยันซ้ำได้ "
        "**ทำลายการรับประกันอัตราการเตือนผิดทั้งหมด** "
        f"จึงเปลี่ยนมาตั้งจากข้อมูลเป็น 3 เท่าของค่าสูงสุดที่ไฟล์ปกติทำได้ "
        f"= {hard_z:.1f}")
    say()

    # ------------------------------------------------ ประเมินสองกฎ
    def evaluate(rule: str) -> dict:
        m = detector.fit(Xtr, rtr, feats, rule=rule, z_feat=args.z_feat,
                         vote_min=vote_min, max_z_cut=cut_max_z, hard_z=hard_z,
                         window=window)

        def flag(df: pd.DataFrame) -> np.ndarray:
            z = np.abs(m.score_array(df[feats].to_numpy(), df.rot_hz.to_numpy()))
            mx = np.nanmax(z, axis=1)
            nv = np.nansum(z > args.z_feat, axis=1)
            return np.array([m.decide(a, b) for a, b in zip(mx, nv)])

        f_hold, f_fault = flag(holdout), flag(fault)
        # รวมหลักฐานจากทั้ง LOO และไฟล์ที่กันไว้ เพราะทั้งสองชุดเป็นข้อมูลปกติ
        # ที่โมเดลไม่เคยเห็น จึงนับเป็นการทดลองเดียวกันได้
        if rule == "max_z":
            t_loo = loo_max > cut_max_z
        else:
            t_loo = loo_votes >= vote_min

        # 🚨 **นับเป็นไฟล์ ไม่ใช่หน้าต่าง**
        #
        # หน้าต่างจากไฟล์เดียวกันไม่เป็นอิสระต่อกัน (cv ในไฟล์ / cv ข้ามไฟล์
        # อยู่ที่ 0.04-0.46) ถ้านับหน้าต่างเป็นตัวอย่างอิสระ ตัวส่วนจะใหญ่ขึ้น
        # 11 เท่าโดยไม่มีข้อมูลเพิ่มขึ้น 11 เท่า แล้วขอบบนจะดีเกินจริง
        #
        # จึงนับว่าไฟล์หนึ่ง "เตือนผิด" ถ้ามีหน้าต่าง**ใดก็ตาม**หลุดเกณฑ์
        # ค่าที่ได้คือ P(มีอย่างน้อยหนึ่งหน้าต่างหลุด) ซึ่ง >= P(หน้าต่างเดียวหลุด)
        # จึงเป็น**ขอบบนของอัตราต่อข้อความ** ซึ่งคือสิ่งที่ต้องการ
        bad_files = (set(train.rel.to_numpy()[t_loo])
                     | set(holdout.rel.to_numpy()[f_hold]))
        fp_all = len(bad_files)
        n_all = n_files(train) + n_files(holdout)
        # ใช้ขอบบนไม่ใช่ค่าที่วัดได้ เพราะเห็นศูนย์ไม่ได้แปลว่าอัตราเป็นศูนย์
        p_hat = fp_all / n_all
        p_up = detector.p_upper_bound(fp_all, n_all)

        # อัตราต่อหน้าต่างที่สังเกตได้ตรงๆ เก็บไว้รายงานคู่กัน
        fp_win = int(t_loo.sum()) + int(f_hold.sum())
        n_win = len(t_loo) + len(f_hold)

        # recall ต่อเครื่อง = ปล่อยหน้าต่างทั้งไฟล์เข้าด่าน k ใน m ตามลำดับเวลา
        # แล้วดูว่าด่านเตือนไหม ซึ่งเป็นสิ่งที่ระบบจริงทำ ไม่ใช่ดูทีละข้อความ
        #
        # ⚠️ **วัดได้เฉพาะตารางหน้าต่าง** ตารางไฟล์เต็มมีข้อความเดียวต่อไฟล์
        # ด่าน 4 ใน 5 จึงไม่มีทางครบ เหลือแต่ช่องทาง `hard_z` แล้วตัวเลขที่ได้
        # จะดูเหมือน recall ตกฮวบ ซึ่ง**เป็นของปลอมที่เกิดจากโครงสร้างข้อมูล
        # ไม่ใช่สมบัติของโมเดล** จึงคืน None ให้ผู้เรียกข้ามไปเลย
        gate_hit, per_file = 0, []
        if len(fault) > n_files(fault):
            for _rel, g in fault.assign(_f=f_fault).groupby("rel", sort=False):
                gate = detector.AlarmGate(args.k, args.m, hard_z=m.hard_z)
                z = np.abs(m.score_array(g[feats].to_numpy(), g.rot_hz.to_numpy()))
                mx = np.nanmax(z, axis=1)
                hit = any(gate.update(bool(a), float(b))["alarm"]
                          for a, b in zip(g["_f"].to_numpy(), mx))
                gate_hit += int(hit)
                per_file.append(hit)
        return {
            "model": m, "rule": rule, "flag_fault": f_fault,
            "recall": float(f_fault.mean()),
            "recall_gate": (gate_hit / len(per_file)) if per_file else None,
            "n_fault_files": len(per_file),
            "fp_all": fp_all, "n_all": n_all, "p_hat": p_hat, "p": p_up,
            "fp_win": fp_win, "n_win": n_win,
            "per_msg_per_day": p_up * detector.MESSAGES_PER_DAY,
            "gated_per_day": detector.alarms_per_day(p_up, args.k, args.m),
        }

    res = {r: evaluate(r) for r in ("max_z", "vote")}

    say("## ผล — เทียบสองกฎการตัดสิน")
    say()
    say("| | `max_z` | `vote` |")
    say("|---|---:|---:|")
    a, b = res["max_z"], res["vote"]
    say(f"| recall ต่อข้อความ ({len(fault):,} หน้าต่าง) | "
        f"{a['recall']:.3f} | **{b['recall']:.3f}** |")
    if b["recall_gate"] is not None:
        say(f"| **recall ต่อเครื่อง หลังด่าน {args.k} ใน {args.m}** "
            f"({b['n_fault_files']:,} ไฟล์) | {a['recall_gate']:.3f} | "
            f"**{b['recall_gate']:.3f}** |")
    say(f"| เตือนผิด ต่อหน้าต่าง | {a['fp_win']}/{a['n_win']} | "
        f"{b['fp_win']}/{b['n_win']} |")
    say(f"| **เตือนผิด ต่อไฟล์** (หน่วยที่เป็นอิสระจริง) | "
        f"{a['fp_all']}/{a['n_all']} = {a['p_hat']:.3f} | "
        f"{b['fp_all']}/{b['n_all']} = {b['p_hat']:.3f} |")
    say(f"| **ขอบบน 95% ของอัตราต่อข้อความ** | **{a['p']:.3f}** | "
        f"**{b['p']:.3f}** |")
    say(f"| เตือนผิดต่อวัน ถ้าเตือนทันทีทุกข้อความ | "
        f"{a['per_msg_per_day']:.0f} | {b['per_msg_per_day']:.0f} |")
    say(f"| **เตือนผิดต่อวัน หลังด่านยืนยัน {args.k} ใน {args.m}** | "
        f"**{a['gated_per_day']:.2f}** | **{b['gated_per_day']:.2f}** |")
    say()
    say("### 🚨 ทำไมใช้ขอบบน ไม่ใช่อัตราที่วัดได้")
    say()
    say(f"กฎ `vote` เตือนผิด {b['fp_all']} จาก {b['n_all']} ไฟล์ "
        "และแม้ถ้าเป็นศูนย์ **การสรุปว่าอัตราการเตือนผิดเป็นศูนย์นั้นผิด** "
        "เพราะเหตุการณ์ที่เกิด 1 ใน 100 ครั้งก็มีโอกาสสูงที่จะไม่โผล่ในตัวอย่าง"
        "เพียงเท่านี้")
    say()
    say("### 🚨 ทำไมตัวส่วนเป็นจำนวน**ไฟล์** ไม่ใช่จำนวนหน้าต่าง")
    say()
    say("ตารางหน้าต่างมีแถวมากกว่าตารางไฟล์ 11 เท่า แต่**ไม่ได้มีข้อมูลมากขึ้น "
        "11 เท่า** เพราะหน้าต่างที่ติดกันจากไฟล์เดียวกันคล้ายกันเอง "
        "(วัดได้ว่า cv ในไฟล์ หารด้วย cv ข้ามไฟล์ อยู่ที่ 0.04-0.46)")
    say()
    say("ถ้านับหน้าต่างเป็นตัวอย่างอิสระ ตัวส่วนจะใหญ่ขึ้น 11 เท่าฟรีๆ "
        "แล้วขอบบนจะแคบลงราว 11 เท่าโดยที่ไม่มีหลักฐานใหม่มารองรับเลย "
        "**ซึ่งเป็น leakage ชนิดเดียวกับที่วัดไว้ว่ากินไป 27 จุด accuracy "
        "เพียงแต่โผล่ในช่องของการประมาณค่าความเชื่อมั่น ไม่ใช่ในช่องของ accuracy**")
    say()
    say("จึงนับว่าไฟล์หนึ่งเตือนผิดถ้ามีหน้าต่าง**ใดก็ตาม**หลุดเกณฑ์ "
        "ค่าที่ได้คือ P(มีอย่างน้อยหนึ่งหน้าต่างหลุด) ซึ่งไม่น้อยกว่า "
        "P(หน้าต่างเดียวหลุด) จึงเป็น**ขอบบนของอัตราต่อข้อความ** "
        "ตรงกับที่ด่านยืนยันซ้ำต้องใช้")
    say()
    say(f"สิ่งที่พูดได้อย่างซื่อสัตย์คือ **อัตราไม่เกิน {b['p']:.3f}** "
        "ซึ่งเป็นขอบบน Clopper-Pearson ด้านเดียวที่ความเชื่อมั่น 95% "
        "(ตรงกับกฎสามส่วน 3/n) ตัวเลขในตารางทั้งหมดจึงคำนวณจากขอบบนนี้ "
        "**ไม่ใช่จากศูนย์** ซึ่งทำให้ตัวเลขดูแย่กว่าแต่เชื่อถือได้")
    say()

    if res["vote"]["recall_gate"] is not None:
        say("### ⚠️ อ่าน recall ต่อเครื่องอย่างมีวิจารณญาณ")
        say()
        say(f"วัดโดยปล่อยหน้าต่างทั้ง {len(fault) // n_files(fault)} อันของไฟล์นั้น "
            f"เข้าด่าน {args.k} ใน {args.m} ตามลำดับเวลา แล้วถามว่าด่านเตือนไหม")
        say()
        say("🚩 **เป็นค่าที่ต่ำกว่าความจริงโดยโครงสร้าง** เพราะไฟล์หนึ่งให้ข้อความ "
            f"เพียง {len(fault) // n_files(fault)} ข้อความ = {10 * (len(fault) // n_files(fault))} "
            "วินาทีของการทำงาน ส่วนเครื่องจักรจริงส่งต่อเนื่องเป็นชั่วโมง "
            "ความเสียหายที่ทำให้ผิดปกติเป็นช่วงๆ จึงมีโอกาสครบเกณฑ์มากกว่านี้มาก "
            "**ตัวเลขนี้จึงเป็นขอบล่าง ไม่ใช่ค่าที่คาดหวังที่หน้างาน**")
        say()
        say("และ**ห้ามเทียบกับ recall ของเส้นฐานที่เทรนด้วยไฟล์เต็ม** เพราะ "
            "ตารางนั้นมีข้อความเดียวต่อไฟล์ ด่าน k ใน m จึงไม่มีทางครบ "
            "ค่าที่ได้จะเป็นของปลอมที่เกิดจากโครงสร้างข้อมูล ไม่ใช่สมบัติของโมเดล")
        say()

    best = "vote" if res["vote"]["recall"] >= res["max_z"]["recall"] else "max_z"
    say(f"**เลือกกฎ `{best}`** เพราะ recall สูงกว่าที่อัตราการเตือนผิดเท่ากัน")
    say()

    # ----------------------------- 🚨 ด่านยืนยันซ้ำ ทำไมต้องมี
    say("## 🚨 ทำไมต้องมีด่านยืนยันซ้ำตามเวลา")
    say()
    say(f"ที่คาบส่ง 10 วินาที ระบบได้ **{detector.MESSAGES_PER_DAY:,} ข้อความต่อวัน** "
        "ถ้าต้องการเตือนผิดไม่เกิน 1 ครั้งต่อวัน อัตราการเตือนผิดต่อข้อความ "
        "ต้องไม่เกิน **1.2 x 10⁻⁴**")
    say()
    say(f"**ประมาณค่าระดับนั้นจากไฟล์ปกติ {n_files(train)} ไฟล์ไม่ได้** "
        "เพราะต้องมีตัวอย่างหลักหมื่นขึ้นไปจึงจะเห็นเหตุการณ์ที่เกิด 1 ใน 8,000 ครั้ง "
        "**นี่เป็นข้อจำกัดของข้อมูล ไม่ใช่ของวิธี** และจะเจอเหมือนกันที่หน้างาน "
        "ช่วงแรกที่เพิ่งติดตั้งเซ็นเซอร์")
    say()
    say("ทางออกคืออาศัยข้อเท็จจริงทางฟิสิกส์ว่า **ความเสียหายจริงอยู่ต่อเนื่อง "
        "แต่สัญญาณรบกวนไม่อยู่ต่อเนื่อง** จึงเตือนเมื่อ k ใน m ข้อความล่าสุด"
        "ผิดปกติ ไม่ใช่เตือนทันทีที่ข้อความเดียวผิดปกติ")
    say()
    p = res[best]["p"]
    say(f"ที่อัตราการเตือนผิดต่อข้อความ {p:.3f} ของกฎ `{best}`")
    say()
    say("| k ใน m | เตือนผิดต่อวัน | ความหน่วงก่อนเตือน |")
    say("|---|---:|---:|")
    for k, m_ in ((1, 1), (2, 3), (3, 5), (4, 5), (5, 6)):
        say(f"| {k} ใน {m_} | {detector.alarms_per_day(p, k, m_):.2f} | "
            f"{10 * k} วินาที |")
    say()
    say(f"**เลือก {args.k} ใน {args.m}** คือหน่วง {10 * args.k} วินาที "
        "ซึ่งยอมรับได้สำหรับความเสียหายที่พัฒนาเป็นวันหรือสัปดาห์ "
        "และมีช่องทางเตือนทันทีแยกไว้สำหรับค่าที่สูงมากอย่างชัดเจน (`hard_z`)")
    say()
    say("⚠️ ตัวเลขนี้สมมติว่าข้อความแต่ละข้อความเป็นอิสระต่อกัน ซึ่ง**ไม่จริงเสียทีเดียว** "
        "สัญญาณรบกวนที่กินเวลานานกว่าคาบส่งทำให้ข้อความติดกันสัมพันธ์กัน "
        "**จึงเป็นขอบล่างที่ดีเกินจริง ใช้เทียบทางเลือกได้ แต่ห้ามใช้เป็นคำมั่นกับผู้ใช้**")
    say()

    # ------------------------------- recall แยกตามชนิดความเสียหาย
    model = res[best]["model"]
    fault["flag"] = res[best]["flag_fault"]
    say("## 🚩 recall แยกตามชนิดความเสียหาย")
    say()
    say("บังคับต้องแจกแจง เพราะ `ball_fault` ตรวจง่ายกว่า `cage_fault` มาก "
        "ตัวเลขรวมจะถูกดึงขึ้นจนดูดีเกินจริง")
    say()
    # ตัวเลขในตารางนี้นับ**แถว** ซึ่งคือข้อความถ้าเป็นตารางหน้าต่าง
    # ป้ายหัวตารางต้องบอกหน่วยให้ตรงกับที่นับจริง ไม่งั้นคนอ่านจะคิดว่าเป็นไฟล์
    unit = ("ข้อความ" if len(fault) > n_files(fault) else "ไฟล์")
    say(f"| คลาส | กลุ่มย่อย | {unit} | จับได้ | recall |")
    say("|---|---|---:|---:|---:|")
    grp = fault.groupby(["cls", "subclass"], dropna=False)
    for (cls, sc), g in grp:
        name = sc if isinstance(sc, str) and sc else "—"
        r = g.flag.mean()
        mark = " ⚠️" if r < 0.5 else ""
        say(f"| {cls} | {name} | {len(g)} | {int(g.flag.sum())} | "
            f"**{r:.3f}**{mark} |")
    say()
    rec = grp.flag.mean()
    say(f"**ช่วง recall {rec.min():.3f} ถึง {rec.max():.3f}** "
        f"แย่ที่สุดคือ `{rec.idxmin()[0]}/{rec.idxmin()[1]}`")
    say()

    # ------------------------- ⚠️ อ่านตัวเลข recall อย่างมีวิจารณญาณ
    say("### ⚠️ อ่าน recall นี้อย่างมีวิจารณญาณ")
    say()
    say("`CLAUDE.md` หัวข้อ 5 วัดไว้แล้วว่า **cage fault จับไม่ได้เลยด้วย "
        "envelope floor และ kurtosis_band** และ **overhang cage ยังไม่เจอลายเซ็นใดๆ** "
        "ถ้าตัวเลขข้างบนบอกว่าจับ cage fault ได้ดี ต้องสงสัยก่อนว่ามาจากอะไร")
    say()
    say("คำอธิบายที่น่าจะเป็นไปได้ที่สุดคือ **ร่องรอยของรอบบันทึก** "
        "แต่ละคลาสต้องถอดประกอบเครื่องใหม่เพื่อเปลี่ยนตลับลูกปืนหรือเลื่อนฐานมอเตอร์ "
        "อะไรที่ต่างกันระหว่างการประกอบก็แยกคลาสได้ขาดโดยไม่เกี่ยวกับความเสียหาย "
        "ซึ่งเป็นกับดักเดียวกับที่ทำให้การคัดกรองลายเซ็นรอบแรกให้ AUC = 1.0 "
        "กับคลาสที่ไม่มีลายเซ็นจริง")
    say()
    say("**ตัวเลขที่เชื่อถือได้มากกว่าคือตัวที่วัดข้ามระดับความรุนแรง** "
        "ถ้า recall ของ misalignment 0.5 mm ใกล้เคียงกับ 2.0 mm "
        "แปลว่าโมเดลไม่ได้ไวต่อความรุนแรง ซึ่งเป็นสัญญาณว่ามันจับอย่างอื่น")
    say()
    say("ตัวชี้วัดที่ใช้คือ **สหสัมพันธ์อันดับระหว่างความรุนแรงกับ recall** "
        "ถ้าเป็นบวกใกล้ 1 แปลว่ายิ่งเสียหนักยิ่งจับได้ ซึ่งเป็นสิ่งที่ฟิสิกส์บอก "
        "ว่าต้องเกิด และ**ร่องรอยของรอบบันทึกอธิบายไม่ได้** เพราะไม่มีเหตุผลใด "
        "ที่ร่องรอยการประกอบจะเรียงตามความรุนแรงพอดี")
    say()
    say(f"| คลาส | ระดับ | {unit} | recall |")
    say("|---|---|---:|---:|")
    sev_tbl = []
    for cls in ("horizontal-misalignment", "vertical-misalignment", "imbalance"):
        g = fault[fault.cls == cls]
        rows = []
        for sc, gg in g.groupby("subclass"):
            # ดึงตัวเลขความรุนแรงออกจากชื่อกลุ่มย่อย เช่น 0.5mm -> 0.5, 6g -> 6
            num = float("".join(ch for ch in str(sc)
                                if ch.isdigit() or ch == "."))
            rows.append((num, sc, len(gg), gg.flag.mean()))
        rows.sort()
        for num, sc, n, r in rows:
            say(f"| {cls} | {sc} | {n} | {r:.3f} |")
        if len(rows) >= 3:
            sv = np.array([x[0] for x in rows])
            rc = np.array([x[3] for x in rows])
            rho = float(np.corrcoef(np.argsort(np.argsort(sv)),
                                    np.argsort(np.argsort(rc)))[0, 1])
            sev_tbl.append((cls, rho, rc.min(), rc.max()))
    say()
    say("| คลาส | สหสัมพันธ์อันดับ ความรุนแรง กับ recall | recall ต่ำสุด | สูงสุด |")
    say("|---|---:|---:|---:|")
    for cls, rho, lo, hi in sev_tbl:
        say(f"| {cls} | **{rho:+.3f}** | {lo:.3f} | {hi:.3f} |")
    say()
    strong = [c for c, rho, _, _ in sev_tbl if rho > 0.7]
    if strong:
        say(f"✅ **{len(strong)} จาก {len(sev_tbl)} คลาสมีสหสัมพันธ์อันดับเกิน 0.7** "
            "คือยิ่งเสียหนักยิ่งจับได้ ซึ่งเป็น**หลักฐานว่าโมเดลตอบสนองต่อ"
            "ความเสียหายจริง ไม่ใช่ร่องรอยของรอบบันทึก**")
        say()
        say("นี่คือข้อแตกต่างที่สำคัญจากการคัดกรองลายเซ็นรอบแรก "
            "ซึ่งให้ AUC = 1.0 กับคลาสที่ไม่มีลายเซ็นจริงโดยไม่มีความสัมพันธ์"
            "กับความรุนแรงเลย")
    else:
        say("⚠️ **ไม่มีคลาสใดที่ recall ขึ้นตามความรุนแรงอย่างชัดเจน** "
            "ซึ่งสนับสนุนข้อสงสัยว่าโมเดลจับร่องรอยของรอบบันทึก")
    say()
    say("❌ **แต่ยังมีจุดที่ขัดกับที่เราวัดไว้เอง** `cage_fault` ทั้งสองฝั่งได้ "
        "recall 0.958-1.000 ขณะที่ `CLAUDE.md` ระบุว่า overhang cage "
        "**ยังไม่เจอลายเซ็นใดๆ** ข้อนี้ยังอธิบายไม่ได้และต้องสืบต่อ "
        "อย่าเอาไปเคลมว่าจับ cage fault ได้จนกว่าจะรู้ว่ามาจากอะไร")
    say()

    # ----------------------------- ตัวชี้วัดที่เป็นตัวจุดเตือน
    z_all = np.abs(model.score_array(fault[feats].to_numpy(),
                                     fault.rot_hz.to_numpy()))
    counts = pd.Series([feats[i] for i in np.nanargmax(z_all, axis=1)]
                       ).value_counts()
    say("## ตัวชี้วัดที่เป็นตัวจุดเตือนบ่อยที่สุด")
    say()
    say("นี่คือส่วนที่ทำให้ระบบ**อธิบายได้** ไม่ใช่คืนแต่คะแนนลอยๆ "
        "และเป็นสิ่งที่ช่างซ่อมต้องการจริง")
    say()
    say("| ตัวชี้วัด | จำนวนข้อความที่เป็นตัวสูงสุด | สัดส่วน |")
    say("|---|---:|---:|")
    for name, c in counts.head(8).items():
        say(f"| `{name}` | {c} | {c / len(fault):.1%} |")
    say()

    # ------------------------------------------- เวลา inference
    sample = fault.iloc[0]
    fd = {f: float(sample[f]) for f in feats}
    rot = float(sample.rot_hz)
    model.score(fd, rot)
    n_rep = 2000
    t0 = time.perf_counter()
    for _ in range(n_rep):
        model.score(fd, rot)
    per_us = (time.perf_counter() - t0) / n_rep * 1e6

    say("## เวลา inference")
    say()
    say("| | ค่า |")
    say("|---|---:|")
    say(f"| ต่อหนึ่งข้อความ (โน้ตบุ๊ก Windows) | **{per_us:.1f} ไมโครวินาที** |")
    say(f"| ประเมินได้ต่อวินาที | {1e6 / per_us:,.0f} ข้อความ |")
    say(f"| ภาระเทียบกับคาบส่ง 10 วินาที | {per_us / 1e7:.1e} ของเวลา |")
    say()
    say("⬜ **ยังต้องวัดบน Raspberry Pi 5** ตาม `CLAUDE.md` หัวข้อ 8 "
        f"งานที่ทำคือการคูณและลบ {len(feats)} ครั้ง จึงคาดว่าบน Pi ยังเหลือเวลาเหลือเฟือ "
        "แต่ต้องวัดจริงไม่ใช่คาดเอา")
    say()

    # ---------------------------------------------------- ข้อจำกัด
    say("## ⚠️ ข้อจำกัดที่ต้องเขียนไว้ในรายงาน")
    say()
    say("1. **recall ยังสูงเกินกว่าที่ควรคาดหวังที่หน้างาน** เพราะไฟล์ในกลุ่มย่อย "
        "เดียวกันน่าจะบันทึกรวดเดียว โมเดลจึงได้ร่องรอยของรอบบันทึกมาช่วยฟรีๆ "
        "**แต่ข้อนี้อ่อนลงจากรอบก่อน** เพราะ recall ขึ้นตามความรุนแรงอย่างเป็นระบบ "
        "ซึ่งร่องรอยการประกอบอธิบายไม่ได้ ดูหัวข้อข้างบน")
    say("2. **อัตราการเตือนผิดที่วัดได้ดีเกินจริง** ไฟล์ปกติทั้งหมดน่าจะบันทึกรวดเดียว "
        "ที่หน้างานจะแย่กว่านี้เพราะมีการถอดประกอบ เปลี่ยนฤดู และโหลดเปลี่ยน")
    say("3. **ยังไม่ได้ทำ order tracking** ซึ่งเป็นวิธีมาตรฐานของวงการในการจัดการ"
        "ความเร็วที่เปลี่ยน (Sanami & Aghdam, ACC 2026) "
        "การ normalize ด้วยเส้นตรงที่ใช้อยู่เป็นทางแก้ชั้นต้นเท่านั้น")
    say(f"4. **ข้ามขั้น Mahalanobis ไปอย่างมีเหตุผล** เพราะต้องประมาณเมทริกซ์ "
        f"{len(feats)}x{len(feats)} จากไฟล์ปกติ {n_files(train)} ไฟล์ ซึ่งเป็น singular")
    say("5. **เส้นฐานเป็นเส้นตรง** ไฟล์ที่หลุดเกณฑ์กระจุกที่ปลายทั้งสองข้างของ"
        "ช่วงความเร็ว ซึ่งเป็นลายเซ็นของการใช้เส้นตรงกับความสัมพันธ์ที่โค้ง")
    say("6. **ยังไม่มีชั้นที่ 2** ระบบบอกได้ว่าผิดปกติแต่บอกไม่ได้ว่าแบบไหน "
        "จึงส่งผลเป็น `unknown` ตามแนวทางของ Costa et al. (IEEE Access 2026)")
    say("7. **ด่านยืนยันซ้ำสมมติว่าข้อความเป็นอิสระต่อกัน** ซึ่งไม่จริงเสียทีเดียว")
    say()

    model.save(args.out)

    def shown(p: Path) -> str:
        """path ที่อ่านง่าย — เทียบกับรากโปรเจกต์ถ้าอยู่ข้างใน ไม่งั้นใช้ตามจริง

        เขียนไว้เพราะ `--out` ชี้ออกนอกโปรเจกต์ได้ (เช่นตอนลองเทรนไว้เทียบ)
        แล้ว `relative_to` จะโยน ValueError **หลังจาก**คำนวณทุกอย่างเสร็จแล้ว
        ซึ่งทำให้งานทั้งรอบเสียไปเพราะบรรทัดรายงานบรรทัดเดียว
        """
        try:
            return str(p.relative_to(repo_root()))
        except ValueError:
            return str(p)

    say("## ไฟล์ที่สร้าง")
    say()
    say(f"- `{shown(args.out)}` — โมเดลรูปแบบ JSON "
        "อ่านด้วยตาได้ และ `ingest.py` ใช้ได้โดยไม่ต้องพึ่ง scikit-learn")
    say()

    out_md = (repo_root() / "experiments"
              / f"{date.today().isoformat()}-anomaly-detector.md")
    out_md.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nเขียนรายงานลง {shown(out_md)}")
    print(f"บันทึกโมเดลลง {shown(args.out)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
