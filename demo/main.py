import os
import base64
import json
import asyncio
import psycopg2
import psycopg2.extras
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI

executor = ThreadPoolExecutor(max_workers=10)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

QWEN_API_KEY = os.environ.get("QWEN_API_KEY", "sk-a8e9de55030f40ea9e8c3cc6ac427b76")

client = OpenAI(
    api_key=QWEN_API_KEY,
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)

PROMPT = """你是酒店客房质检员。请先识别这张照片属于哪个场景，然后按对应标准判断。

【场景识别与合格标准】

▸ 床铺：
  关键区分：正常整理好的床，皱纹只出现在【边缘压痕/中缝折叠线】处，是直线状的；
  睡过未整理的床，皱纹覆盖【床面中央大片区域】，方向随机、交叉杂乱、表面凹凸。
  pass=false 仅当：床面中央区域有大片杂乱皱纹（被单中间部分凹凸起伏，明显有人睡过）；或枕头明显歪斜
  pass=true 如果：床面中央区域基本平整，边缘/折叠线处有直线状压印属正常；枕头对称

▸ 毛巾架：
  pass=false 如果（满足任一）：
  - 毛巾中有灰色或蓝色毛巾（应全部为白色）
  - 毛巾叠放散乱未对齐
  - 毛巾总数少于3条
  pass=true 如果：全部白色，整齐叠放，共3条

▸ 洗手台/洗脸盆：
  pass=false 如果（满足任一）：
  - 台面或洗脸盆旁边有揉皱的纸巾、用过的面巾纸、脏毛巾
  - 洗脸盆内壁有污渍
  pass=true 如果：台面整洁，洗浴用品整齐，无散乱纸巾

▸ 马桶区：
  pass=false 如果（满足任一）：
  - 马桶盖处于打开状态（可见马桶内部）
  - 垃圾桶内有明显可辨认的垃圾（如纸巾、食物、包装袋等废弃物）
  注意：深色垃圾桶内壁或黑色垃圾袋衬里颜色深是正常的，不算有垃圾
  pass=true 如果：马桶盖关闭，垃圾桶空或只有袋衬

▸ 淋浴间地板：
  注意：深色石材的纹理（白色/灰色线条图案）不是积水，不要误判。
  pass=false 仅当：地板上有明显积水水坑（水面有光泽反光，水面清晰可见）
  pass=true 如果：地板干燥，或仅有轻微水迹，或只是石材花纹

▸ 淋浴间花洒：
  pass=false 如果：花洒头出水面朝向墙壁（反装，背面对着使用者）
  pass=true 如果：花洒头出水面朝前（正对使用者），软管自然垂落

▸ 衣柜/浴袍（重要：必须数清楚件数）：
  pass=false 如果（满足任一）：
  - 衣架上浴袍数量只有1件（应为2件）
  - 完全没有配套拖鞋挂在衣柜内
  pass=true 如果：能看到2件浴袍挂好，并有拖鞋

▸ 桌面/茶水区（必须数瓶数）：
  只检查矿泉水数量，不检查电线。
  pass=false 如果：农夫山泉矿泉水瓶数少于4瓶（标准为4瓶）
  pass=true 如果：能看到4瓶或以上矿泉水摆放在桌面

▸ 其他场景：按整洁干净程度判断，有明显卫生问题则pass=false

【评分规则】
- 90-100：完全达标
- 75-89：基本合格，有轻微瑕疵
- 50-74：不合格，有明显问题
- 50以下：严重不合格

只输出JSON，不要其他文字：
{"pass": true或false, "score": 0到100整数, "scene": "场景名称", "observations": ["描述1", "描述2"], "issues": ["问题描述，无则空数组"]}"""


# ---------- Database ----------

def get_conn():
    return psycopg2.connect(os.environ["DATABASE_URL"], sslmode="require")


def init_db():
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS inspections (
                    room_number TEXT PRIMARY KEY,
                    record      JSONB NOT NULL,
                    submitted_at TIMESTAMP DEFAULT NOW()
                )
            """)
        conn.commit()


def save_record(record: dict):
    with get_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO inspections (room_number, record, submitted_at)
                VALUES (%s, %s, NOW())
                ON CONFLICT (room_number) DO UPDATE
                  SET record = EXCLUDED.record,
                      submitted_at = NOW()
            """, (record["room_number"], json.dumps(record, ensure_ascii=False)))
        conn.commit()


def load_all_records() -> list:
    with get_conn() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT record FROM inspections ORDER BY submitted_at DESC")
            return [row["record"] for row in cur.fetchall()]


init_db()


# ---------- AI ----------

def inspect_image(image_bytes: bytes, filename: str) -> dict:
    img_b64 = base64.b64encode(image_bytes).decode()
    ext = filename.rsplit(".", 1)[-1].lower()
    mime = "image/jpeg" if ext in ("jpg", "jpeg") else f"image/{ext}"

    response = client.chat.completions.create(
        model="qwen3-vl-plus",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{img_b64}"}},
                    {"type": "text", "text": PROMPT},
                ],
            }
        ],
        max_tokens=1500,
    )

    content = response.choices[0].message.content.strip()
    try:
        start = content.find("{")
        end = content.rfind("}") + 1
        parsed = json.loads(content[start:end])
        parsed["filename"] = filename
        return parsed
    except Exception:
        return {"filename": filename, "pass": False, "score": 0, "observations": [], "issues": [f"解析失败: {content[:100]}"]}


# ---------- Routes ----------

@app.get("/", response_class=HTMLResponse)
async def root():
    html_path = os.path.join(os.path.dirname(__file__), "index.html")
    with open(html_path, "r", encoding="utf-8") as f:
        return f.read()


@app.get("/manager", response_class=HTMLResponse)
async def manager():
    html_path = os.path.join(os.path.dirname(__file__), "manager.html")
    with open(html_path, "r", encoding="utf-8") as f:
        return f.read()


@app.get("/api/results")
async def get_results():
    rooms = load_all_records()
    total = len(rooms)
    failed = sum(1 for r in rooms if not r.get("overall_pass"))
    passed = total - failed
    return JSONResponse({
        "rooms": rooms,
        "stats": {"total": total, "passed": passed, "failed": failed},
    })


@app.post("/inspect")
async def inspect(
    room_number: str = Form(...),
    files: list[UploadFile] = File(...),
):
    file_data = []
    for file in files:
        image_bytes = await file.read()
        file_data.append((image_bytes, file.filename))

    loop = asyncio.get_event_loop()
    tasks = [
        loop.run_in_executor(executor, inspect_image, image_bytes, filename)
        for image_bytes, filename in file_data
    ]
    results = await asyncio.gather(*tasks)

    passing = [r for r in results if r.get("pass")]
    overall_score = round(sum(r.get("score", 0) for r in results) / len(results)) if results else 0
    overall_pass = len(passing) == len(results)

    record = {
        "room_number": room_number,
        "images": results,
        "overall_pass": overall_pass,
        "overall_score": overall_score,
        "summary": f"{len(passing)}/{len(results)} 张照片通过",
        "submitted_at": datetime.now().strftime("%m-%d %H:%M"),
    }

    save_record(record)

    return JSONResponse(record)
