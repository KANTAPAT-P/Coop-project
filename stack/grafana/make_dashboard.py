"""สร้างไฟล์แดชบอร์ดของ Grafana

รัน:
    python stack/grafana/make_dashboard.py

Grafana โหลดไฟล์ใหม่เองทุก 30 วินาที จึงไม่ต้องรีสตาร์ทคอนเทนเนอร์

เขียนด้วยสคริปต์แทนการพิมพ์ JSON มือ เพราะ JSON ของ Grafana ยาวและซ้ำซาก
การประกอบด้วยฟังก์ชันทำให้ทุกแผงมีโครงเดียวกันและแก้ทีเดียวได้ทั้งหมด
"""
import json, pathlib, sys

DS = {"type": "influxdb", "uid": "influxdb"}
BUCKET = "pdm_live"

# เกณฑ์เตือนที่ใช้วาดเส้นแดงบนแผงคะแนน
#
# อ่านจากไฟล์โมเดลถ้ามี เพื่อให้เส้นบนแดชบอร์ด**ตรงกับเกณฑ์ที่ระบบใช้จริงเสมอ**
# ถ้าเขียนเลขตายตัวไว้แล้วเทรนโมเดลใหม่จนเกณฑ์เปลี่ยน เส้นบนกราฟจะโกหก
# ซึ่งแย่กว่าไม่มีเส้นเลย
def _vote_min(default: int = 11) -> int:
    path = pathlib.Path(__file__).resolve().parents[2] / "models" / "baseline-normal.json"
    try:
        return int(json.loads(path.read_text(encoding="utf-8"))["vote_min"])
    except Exception:
        print(f"⚠️ อ่านเกณฑ์จาก {path.name} ไม่ได้ ใช้ค่าปริยาย {default}",
              file=sys.stderr)
        return default


VOTE_MIN = _vote_min()


def flux(field: str, fn: str = "mean", extra: str = "") -> str:
    return (f'from(bucket: "{BUCKET}")\n'
            f'  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)\n'
            f'  |> filter(fn: (r) => r._measurement == "vibration" '
            f'and r._field == "{field}")\n'
            f'{extra}'
            f'  |> group(columns: ["machine"])\n'
            f'  |> aggregateWindow(every: v.windowPeriod, fn: {fn}, '
            f'createEmpty: false)\n'
            f'  |> keep(columns: ["_time", "_value", "machine"])')


def assess(field: str, fn: str = "max", extra: str = "") -> str:
    """query จาก measurement `assessment` ซึ่งเก็บผลการประเมิน

    ใช้ `max` เป็นค่าปริยายไม่ใช่ `mean` เพราะแดชบอร์ดติดตามสภาพ
    **ต้องเปิดเผยปัญหา ไม่ใช่กลบด้วยค่าเฉลี่ย** ถ้าในช่วงย่อยหนึ่งมีข้อความ
    ที่ผิดปกติอยู่ข้อความเดียว ต้องเห็นมัน ไม่ใช่ให้ค่าเฉลี่ยกดมันหายไป
    """
    return (f'from(bucket: "{BUCKET}")\n'
            f'  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)\n'
            f'  |> filter(fn: (r) => r._measurement == "assessment" '
            f'and r._field == "{field}")\n'
            f'{extra}'
            f'  |> group(columns: ["machine"])\n'
            f'  |> aggregateWindow(every: v.windowPeriod, fn: {fn}, '
            f'createEmpty: false)\n'
            f'  |> keep(columns: ["_time", "_value", "machine"])')


def hourly_anomaly_count() -> str:
    """นับข้อความที่ผิดปกติรวมรายชั่วโมง สำหรับแผงดูแนวโน้ม

    ตรึง `every: 1h` ไม่ใช้ `v.windowPeriod` เพราะ**หน่วยของแกนต้องคงที่**
    ถ้าปล่อยให้เปลี่ยนตามช่วงเวลาที่ผู้ใช้เลือก ความสูงของแท่งจะเปลี่ยนไปด้วย
    ทั้งที่ข้อมูลเท่าเดิม แล้วการเทียบว่าแนวโน้มสูงขึ้นหรือไม่จะเชื่อถือไม่ได้
    """
    return (f'from(bucket: "{BUCKET}")\n'
            f'  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)\n'
            f'  |> filter(fn: (r) => r._measurement == "assessment" '
            f'and r._field == "is_anomaly")\n'
            f'  |> group(columns: ["machine"])\n'
            f'  |> aggregateWindow(every: 1h, fn: sum, createEmpty: true)\n'
            f'  |> keep(columns: ["_time", "_value", "machine"])')


def target(query: str, ref: str = "A") -> dict:
    return {"datasource": DS, "query": query, "refId": ref}


def timeseries(title, x, y, w, h, query, unit="", desc="", minv=None,
               log=False, fill=8):
    custom = {"lineWidth": 1.6, "fillOpacity": fill, "showPoints": "never",
              "spanNulls": False, "axisSoftMin": minv}
    if log:
        custom["scaleDistribution"] = {"type": "log", "log": 10}
    return {
        "type": "timeseries", "title": title, "description": desc,
        "datasource": DS, "gridPos": {"x": x, "y": y, "w": w, "h": h},
        "targets": [target(query)],
        "fieldConfig": {
            "defaults": {
                "unit": unit,
                "displayName": "${__field.labels.machine}",
                "custom": custom,
                "color": {"mode": "palette-classic"},
            },
            "overrides": [],
        },
        "options": {
            "legend": {"displayMode": "table", "placement": "right",
                       "showLegend": True, "calcs": ["lastNotNull", "mean"]},
            "tooltip": {"mode": "multi", "sort": "desc"},
        },
    }


def stat(title, x, y, w, h, query, unit="", desc="", thresholds=None,
         text_mode="value_and_name", reducer="lastNotNull"):
    steps = thresholds or [{"color": "green", "value": None}]
    return {
        "type": "stat", "title": title, "description": desc,
        "datasource": DS, "gridPos": {"x": x, "y": y, "w": w, "h": h},
        "targets": [target(query)],
        "fieldConfig": {
            "defaults": {
                "unit": unit,
                "displayName": "${__field.labels.machine}",
                "thresholds": {"mode": "absolute", "steps": steps},
                "color": {"mode": "thresholds"},
            },
            "overrides": [],
        },
        "options": {
            "reduceOptions": {"calcs": [reducer], "fields": "", "values": False},
            "textMode": text_mode, "colorMode": "background",
            "graphMode": "none", "justifyMode": "auto", "orientation": "horizontal",
        },
    }


panels = []
y = 0

# ---------- แถวบน: สถานะรวม ----------
panels.append(stat(
    "สถานะการวัดความเร็วรอบล่าสุด", 0, y, 12, 4,
    f'from(bucket: "{BUCKET}")\n'
    f'  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)\n'
    f'  |> filter(fn: (r) => r._measurement == "vibration" '
    f'and r._field == "ctx_rot_hz")\n'
    f'  |> group(columns: ["machine"])\n'
    f'  |> last()\n'
    f'  |> keep(columns: ["_time", "_value", "machine"])',
    unit="rothz",
    desc="ความเร็วรอบล่าสุดของแต่ละเครื่อง ถ้าเป็น 0 แปลว่าเครื่องหยุด "
         "หรือวัดความเร็วไม่ได้ ดูแผงคุณภาพสัญญาณด้านล่างประกอบ",
    thresholds=[{"color": "text", "value": None}]))

panels.append(stat(
    "อุณหภูมิล่าสุด", 12, y, 12, 4,
    flux("ctx_temp_c", "last").replace(
        "|> aggregateWindow(every: v.windowPeriod, fn: last, createEmpty: false)",
        "|> last()"),
    unit="celsius",
    desc="อุณหภูมิเป็นค่าที่สังเคราะห์ขึ้นในสคริปต์จำลอง ยังไม่ใช่ของจริง",
    thresholds=[{"color": "green", "value": None},
                {"color": "orange", "value": 55},
                {"color": "red", "value": 70}]))
y += 4

# ---------- ความเร็วรอบ คู่กับความแรง ----------
panels.append(timeseries(
    "ความเร็วรอบ (Hz)", 0, y, 12, 8, flux("ctx_rot_hz"), unit="rothz",
    desc="ต้องดูแผงนี้คู่กับแผงความแรงเสมอ เพราะการทดลองในช่วงที่ 1 พบว่า "
         "ตัวชี้วัดความแรงกระโดด 4 เท่าเมื่อความเร็วรอบข้ามเส้นหนึ่ง "
         "โดยที่ความเสียหายไม่ได้เปลี่ยน", minv=0))

panels.append(timeseries(
    "ความแรงการสั่น u_radial.rms (g)", 12, y, 12, 8, flux("u_radial.rms"),
    desc="ตัวชี้วัดตระกูลความแรง ขึ้นกับความไวของเซ็นเซอร์และความเร็วรอบ "
         "ห้ามตีความโดยไม่ดูความเร็วรอบประกอบ", minv=0))
y += 8

# ---------- ลายเซ็น ----------
panels.append(timeseries(
    "ลายเซ็น imbalance — u_radial.h1_frac", 0, y, 12, 8, flux("u_radial.h1_frac"),
    desc="สัดส่วนพลังงานที่ความถี่การหมุน (1x) เป็นลายเซ็นของความไม่สมดุล "
         "ที่ยืนยันแล้วว่าเพิ่มตามมวลถ่วง 2.9 ถึง 13.6 เท่า "
         "motor-02 คือเครื่องที่จำลองความไม่สมดุล จึงควรสูงกว่าเพื่อนชัดเจน",
    minv=0))

panels.append(timeseries(
    "ลายเซ็น misalignment — o_tang.r21", 12, y, 12, 8, flux("o_tang.r21"),
    desc="อัตราส่วนความสูงพีคที่ 2x ต่อ 1x เป็นลายเซ็นของการเยื้องศูนย์ "
         "ไม่ขึ้นกับความไวของเซ็นเซอร์ motor-03 และ motor-04 คือเครื่องที่ "
         "จำลองการเยื้องศูนย์ ⚠️ พื้นความคลาดเคลื่อนของค่านี้กว้าง 0.34 ถึง 2.06 เท่า "
         "จึงต้องดูแนวโน้มระยะยาว ไม่ใช่ค่าจุดเดียว", minv=0))
y += 8

# ---------- คุณภาพข้อมูล ----------
panels.append({
    "type": "state-timeline",
    "title": "คุณภาพการวัดความเร็วรอบ",
    "description": "ok = ใช้ได้ · noisy = แกว่ง ลดน้ำหนักตัวชี้วัดที่อิงความเร็ว · "
                   "lost = วัดไม่ได้ ห้ามใช้ h1_frac และ r21 · "
                   "stopped = เครื่องหยุด ต้องข้ามการประเมินทั้งหมด "
                   "ไม่งั้นระบบจะแจ้งเตือนทุกครั้งที่ปิดเครื่องตามปกติ "
                   "⚠️ แผงนี้ย่อข้อมูลด้วย min ดังนั้นถ้ามีตัวอย่างเดียวในช่วงนั้น "
                   "ที่คุณภาพต่ำ ทั้งช่วงจะแสดงเป็นค่าต่ำสุด ตั้งใจให้เป็นแบบนี้ "
                   "เพราะแดชบอร์ดติดตามสภาพต้องเปิดเผยปัญหา ไม่ใช่กลบด้วยค่าเฉลี่ย "
                   "ผลคือ lost และ stopped จะดูเกิดบ่อยกว่าสัดส่วนจริง",
    "datasource": DS,
    "gridPos": {"x": 0, "y": y, "w": 24, "h": 8},
    "targets": [target(
        f'from(bucket: "{BUCKET}")\n'
        f'  |> range(start: v.timeRangeStart, stop: v.timeRangeStop)\n'
        f'  |> filter(fn: (r) => r._measurement == "vibration" '
        f'and r._field == "ctx_rot_hz")\n'
        f'  |> map(fn: (r) => ({{ r with _value: '
        f'if r.rot_quality == "ok" then 3 '
        f'else if r.rot_quality == "noisy" then 2 '
        f'else if r.rot_quality == "lost" then 1 '
        f'else 0 }}))\n'
        f'  |> group(columns: ["machine"])\n'
        f'  |> aggregateWindow(every: v.windowPeriod, fn: min, createEmpty: false)\n'
        f'  |> keep(columns: ["_time", "_value", "machine"])')],
    "fieldConfig": {
        "defaults": {
            "displayName": "${__field.labels.machine}",
            "mappings": [{"type": "value", "options": {
                "0": {"text": "stopped", "color": "dark-blue", "index": 0},
                "1": {"text": "lost", "color": "red", "index": 1},
                "2": {"text": "noisy", "color": "orange", "index": 2},
                "3": {"text": "ok", "color": "green", "index": 3}}}],
            "custom": {"lineWidth": 0, "fillOpacity": 90},
            "color": {"mode": "thresholds"},
            "thresholds": {"mode": "absolute",
                           "steps": [{"color": "text", "value": None}]},
        },
        "overrides": [],
    },
    "options": {"showValue": "never", "mergeValues": True,
                "legend": {"displayMode": "list", "placement": "bottom",
                           "showLegend": True},
                "tooltip": {"mode": "single"}},
})
y += 8

# ---------- ผลการประเมิน ----------
#
# แผงกลุ่มนี้คือสิ่งที่แดชบอร์ดเดิมไม่มีเลย เดิมแสดงแต่ค่าดิบ
# คนดูจึงต้องตีความเอาเองว่าค่าที่เห็นผิดปกติหรือยัง ซึ่งเป็นงานของระบบ

panels.append({
    "type": "row", "title": "ผลการประเมิน", "collapsed": False,
    "gridPos": {"x": 0, "y": y, "w": 24, "h": 1}, "panels": [],
})
y += 1

# แผงหลักที่อาจารย์ขอ — คะแนนเทียบกับเส้นเกณฑ์
panels.append(timeseries(
    "คะแนนความผิดปกติ เทียบกับเกณฑ์", 0, y, 16, 9,
    assess("n_exceed", "max"),
    desc="จำนวนตัวชี้วัดที่หลุดเส้นฐาน จากทั้งหมด 72 ตัว "
         "เส้นแดงแนวนอนคือเกณฑ์เตือน ถ้าเส้นของเครื่องไหนขึ้นเหนือเส้นแดง "
         "แปลว่าข้อความนั้นผิดปกติ "
         "ย่อด้วย max ไม่ใช่ mean เพราะแดชบอร์ดติดตามสภาพต้องเปิดเผยปัญหา "
         "ไม่ใช่กลบด้วยค่าเฉลี่ย",
    minv=0, fill=4))
# วาดเส้นเกณฑ์ด้วย threshold ของ Grafana เพื่อให้เห็นเส้นจริงบนกราฟ
# ไม่ใช่ให้คนดูเดาเอาเองว่าเท่าไรถึงจะผิดปกติ
panels[-1]["fieldConfig"]["defaults"]["custom"]["thresholdsStyle"] = {
    "mode": "line"}
panels[-1]["fieldConfig"]["defaults"]["thresholds"] = {
    "mode": "absolute",
    "steps": [{"color": "green", "value": None},
              {"color": "red", "value": VOTE_MIN}]}

panels.append(stat(
    "สถานะล่าสุดของแต่ละเครื่อง", 16, y, 8, 9,
    assess("is_anomaly", "max"),
    desc="1 = ข้อความล่าสุดผิดปกติ · 0 = อยู่ในเกณฑ์ "
         "ถ้าแผงว่างแปลว่าไม่มีใครส่งข้อมูลเข้ามา ซึ่ง**ต่างจากปกติ** "
         "และเป็นสถานะที่ต้องรีบตรวจ ไม่ใช่ปล่อยผ่าน",
    thresholds=[{"color": "green", "value": None},
                {"color": "red", "value": 0.5}]))
y += 9

# แผงแนวโน้ม — ที่อาจารย์ชี้ว่าสำคัญกว่าจำนวนครั้ง
panels.append(timeseries(
    "จำนวนข้อความที่ผิดปกติ รวมรายชั่วโมง", 0, y, 12, 8,
    hourly_anomaly_count(),
    desc="อาจารย์ที่ปรึกษาชี้ว่าการเตือนผิดไม่เป็นไร แต่ต้องมีแนวโน้ม "
         "แผงนี้คือตัวที่ใช้ดูทิศทาง ถ้าค่าสูงขึ้นเรื่อยๆ คือเครื่องแย่ลงจริง "
         "ถ้ากระจัดกระจายโดยไม่มีทิศทางคือการเตือนผิดซึ่งยอมรับได้ "
         "ส่วนตัวเลขที่ใช้ตัดสินอยู่ในแผงถัดไป",
    minv=0, fill=25))

panels.append(timeseries(
    "ค่าสถิติแนวโน้ม Mann-Kendall (tau)", 12, y, 12, 8,
    assess("trend_tau", "last"),
    desc="tau อยู่ระหว่าง -1 ถึง +1 ค่าบวกมากแปลว่าแย่ลงเรื่อยๆ "
         "ค่าใกล้ศูนย์แปลว่าไม่มีทิศทาง ซึ่งคือการเตือนผิดที่ยอมรับได้ "
         "ระบบถือว่ามีแนวโน้มเมื่อ p < 0.05 ไม่ใช่ดูจาก tau อย่างเดียว "
         "⚠️ ต้องมีข้อมูลอย่างน้อย 4 วันจึงคำนวณได้ "
         "ถ้าเพิ่งเริ่มเก็บแผงนี้จะยังว่าง ซึ่งไม่ใช่ความผิดพลาด",
    minv=-1))
y += 8

dashboard = {
    "uid": "pdm-overview",
    "title": "ภาพรวมสภาพเครื่องจักร",
    "description": "แดชบอร์ดหลักของระบบบำรุงรักษาเชิงพยากรณ์ "
                   "ข้อมูลมาจาก MAFAULDA ผ่านสคริปต์จำลอง ยังไม่ใช่เครื่องจักรจริง",
    "tags": ["pdm", "edge-ai"],
    "timezone": "browser",
    "editable": True,
    "schemaVersion": 39,
    "version": 1,
    "refresh": "10s",
    "time": {"from": "now-3h", "to": "now"},
    "panels": panels,
}

out = pathlib.Path(__file__).resolve().parent / "dashboards" / "pdm-overview.json"
out.write_text(json.dumps(dashboard, ensure_ascii=False, indent=2) + "\n",
               encoding="utf-8")
print(f"เขียน {out.name}: {len(panels)} แผง, {len(out.read_text(encoding='utf-8')):,} ไบต์")
for p in panels:
    print(f"  {p['type']:16s} {p['title']}")
json.loads(out.read_text(encoding="utf-8"))
print("JSON ถูกต้อง")
