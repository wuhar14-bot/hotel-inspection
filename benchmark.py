"""
Hotel Inspection Vision API Benchmark
测试 5 个 API Provider 在 1 / 3 / 10 张图时的响应速度和质量
"""
import os, base64, json, time, sys
from pathlib import Path
from openai import OpenAI

# ─────────────────────────────────────────────────────────────────────────────
# API 配置
# ─────────────────────────────────────────────────────────────────────────────
PROVIDERS = {
    "qwen": {
        "name": "通义千问 Qwen3-VL-Plus",
        "base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "api_key": "sk-a8e9de55030f40ea9e8c3cc6ac427b76",
        "model": "qwen3-vl-plus",
        "max_tokens": 1500,
    },
    "glm": {
        "name": "智谱 GLM-4.6V",
        "base_url": "https://open.bigmodel.cn/api/paas/v4/",
        "api_key": "d1786741d41b457a90de8a94fdc68ddb.Ou1dcrbPfndsTH48",
        "model": "glm-4.6v",
        "max_tokens": 2000,
    },
    "kimi": {
        "name": "Kimi moonshot-v1-8k-vision",
        "base_url": "https://api.moonshot.cn/v1",
        "api_key": "sk-TY1ed1tHEe1w7UUJYuIspWh3rKl6pGLQYrrVbHuaBXhPIZji",
        "model": "moonshot-v1-8k-vision-preview",
        "max_tokens": 1500,
    },
    "minimax": {
        "name": "MiniMax VL-01",
        "base_url": "https://api.minimaxi.com/v1",
        "api_key": "sk-api-zZeBBtA8WIzrnffaLI4aD9_mMYEK7iFvO-5PfVdyCocUP0PZCQ1A59xkqDbel9Hdn_zkB4zY1kCdm2NdyTMEVQsjaO1-nJQ2-Tpopo-n_cuX1EG9gigM6bE",
        "model": "MiniMax-VL-01",
        "max_tokens": 1500,
    },
    "packy": {
        "name": "PackyAPI Gemini-2.5-Flash",
        "base_url": "https://www.packyapi.com/v1",
        "api_key": "sk-CKVB5C3ZAtPmbwwBTo8xMzx3Oy60okBLEMvdgrG32zlQKpPK",
        "model": "gemini-2.5-flash",
        "max_tokens": 1500,
    },
}

# ─────────────────────────────────────────────────────────────────────────────
# 测试图片集 (来自 findings.md 的场景配对)
# ─────────────────────────────────────────────────────────────────────────────
BASE = Path("E:/claude-code/hotel-inspection/test-images")
TEST_IMAGES = [
    # (文件路径, 预期 pass, 场景)
    (BASE / "good/微信图片_2026-03-15_084536_867.jpg", True,  "衣柜/浴袍-好"),
    (BASE / "fail/微信图片_2026-03-15_084114_450.jpg",  False, "衣柜/浴袍-坏"),
    (BASE / "good/微信图片_2026-03-15_084613_067.jpg",  True,  "毛巾架-好"),
    (BASE / "fail/微信图片_2026-03-15_084130_383.jpg",  False, "毛巾架-坏"),
    (BASE / "good/微信图片_2026-03-15_084618_282.jpg",  True,  "马桶区-好"),
    (BASE / "fail/微信图片_2026-03-15_084134_155.jpg",  False, "马桶区-坏"),
    (BASE / "good/微信图片_2026-03-15_084555_403.jpg",  True,  "洗手台-好"),
    (BASE / "fail/微信图片_2026-03-15_084103_295.jpg",  False, "洗手台-坏"),
    (BASE / "good/微信图片_2026-03-15_084543_160.jpg",  True,  "桌面茶水-好"),
    (BASE / "fail/微信图片_2026-03-15_084139_302.jpg",  False, "桌面茶水-坏"),
]
# 测试批次: 1张/3张/10张
BATCHES = {
    1:  TEST_IMAGES[:1],
    3:  TEST_IMAGES[:3],
    10: TEST_IMAGES[:10],
}

PROMPT = """你是酒店客房质检员。请先识别这张照片属于哪个场景，然后按对应标准判断。

【场景识别与合格标准】

▸ 床铺：
  关键区分：正常整理好的床，皱纹只出现在【边缘压痕/中缝折叠线】处，是直线状的；
  睡过未整理的床，皱纹覆盖【床面中央大片区域】，方向随机、交叉杂乱、表面凹凸。
  pass=false 仅当：床面中央区域有大片杂乱皱纹（被单中间部分凹凸起伏，明显有人睡过）；或枕头明显歪斜
  pass=true 如果：床面中央区域基本平整，边缘/折叠线处有直线状压印属正常；枕头对称

▸ 毛巾架：
  pass=false 如果（满足任一）：毛巾中有灰色或蓝色毛巾（应全部为白色）；毛巾叠放散乱未对齐；毛巾总数少于3条
  pass=true 如果：全部白色，整齐叠放，共3条

▸ 洗手台/洗脸盆：
  pass=false 如果（满足任一）：台面或洗脸盆旁边有揉皱的纸巾、用过的面巾纸、脏毛巾；洗脸盆内壁有污渍
  pass=true 如果：台面整洁，洗浴用品整齐，无散乱纸巾

▸ 马桶区：
  pass=false 如果（满足任一）：马桶盖处于打开状态（可见马桶内部）；垃圾桶内有明显可辨认的垃圾（如纸巾、食物、包装袋等废弃物）
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
  pass=false 如果（满足任一）：衣架上浴袍数量只有1件（应为2件）；完全没有配套拖鞋挂在衣柜内
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


def encode_image(path: Path) -> tuple[str, str]:
    ext = path.suffix.lower().lstrip(".")
    mime = "image/jpeg" if ext in ("jpg", "jpeg") else f"image/{ext}"
    b64 = base64.b64encode(path.read_bytes()).decode()
    return b64, mime


def build_single_image_message(b64: str, mime: str, prompt: str) -> list:
    return [
        {
            "role": "user",
            "content": [
                {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}},
                {"type": "text", "text": prompt},
            ],
        }
    ]


def parse_result(content: str, filename: str) -> dict:
    content = content.strip()
    try:
        start = content.find("{")
        end = content.rfind("}") + 1
        if start >= 0 and end > start:
            parsed = json.loads(content[start:end])
            parsed["filename"] = filename
            return parsed
    except Exception as e:
        pass
    return {
        "filename": filename,
        "pass": None,
        "score": None,
        "scene": "解析失败",
        "observations": [],
        "issues": [f"JSON解析失败: {content[:80]}"],
        "_raw": content[:200],
    }


def test_provider_batch(provider_key: str, cfg: dict, images: list) -> dict:
    """对一个 provider 测试一批图片，逐张顺序调用，返回结果 + 耗时"""
    client = OpenAI(api_key=cfg["api_key"], base_url=cfg["base_url"])
    results = []
    errors = []
    t_start = time.time()

    for img_path, expected_pass, scene_label in images:
        t0 = time.time()
        try:
            b64, mime = encode_image(img_path)
            messages = build_single_image_message(b64, mime, PROMPT)
            resp = client.chat.completions.create(
                model=cfg["model"],
                messages=messages,
                max_tokens=cfg["max_tokens"],
                timeout=60,
            )
            content = resp.choices[0].message.content or ""
            elapsed = time.time() - t0
            parsed = parse_result(content, img_path.name)
            parsed["_expected"] = expected_pass
            parsed["_scene_label"] = scene_label
            parsed["_elapsed"] = round(elapsed, 2)
            parsed["_correct"] = (parsed.get("pass") == expected_pass)
            results.append(parsed)
        except Exception as e:
            elapsed = time.time() - t0
            err = {
                "filename": img_path.name,
                "pass": None,
                "score": None,
                "scene": "ERROR",
                "observations": [],
                "issues": [str(e)],
                "_expected": expected_pass,
                "_scene_label": scene_label,
                "_elapsed": round(elapsed, 2),
                "_correct": False,
                "_error": str(e),
            }
            results.append(err)
            errors.append(str(e))

    total_elapsed = round(time.time() - t_start, 2)
    correct = sum(1 for r in results if r.get("_correct"))
    accuracy = round(correct / len(results) * 100) if results else 0

    return {
        "provider": cfg["name"],
        "n_images": len(images),
        "total_elapsed": total_elapsed,
        "avg_per_image": round(total_elapsed / len(images), 2),
        "accuracy": accuracy,
        "correct": correct,
        "total": len(results),
        "errors": errors,
        "results": results,
    }


def print_summary(all_results: dict):
    print("\n" + "=" * 80)
    print("  BENCHMARK SUMMARY")
    print("=" * 80)

    header = f"{'Provider':<32} {'N':>4}  {'Total(s)':>9}  {'Avg/img(s)':>11}  {'Accuracy':>9}"
    print(header)
    print("-" * 80)

    for provider_key, batch_results in all_results.items():
        for batch_n, result in sorted(batch_results.items()):
            name = result["provider"][:30]
            n = result["n_images"]
            total = result["total_elapsed"]
            avg = result["avg_per_image"]
            acc = result["accuracy"]
            print(f"  {name:<30} {n:>4}  {total:>9.2f}  {avg:>11.2f}  {acc:>8}%")
        print()

    print("=" * 80)
    print("\nDETAILED RESULTS per image:\n")
    for provider_key, batch_results in all_results.items():
        for batch_n, br in sorted(batch_results.items()):
            print(f"\n── {br['provider']} | {batch_n} 张图 ──")
            for r in br["results"]:
                expected = "✓" if r.get("_expected") else "✗"
                got = "✓" if r.get("pass") is True else ("✗" if r.get("pass") is False else "?")
                correct_mark = "✅" if r.get("_correct") else "❌"
                scene = r.get("scene", "?")[:15]
                elapsed = r.get("_elapsed", "?")
                score = r.get("score", "?")
                issues_count = len(r.get("issues", []))
                label = r.get("_scene_label", "?")
                print(f"  [{label:<12}] 预期{expected} 得{got} {correct_mark}  场景:{scene:<15}  分:{score}  问题:{issues_count}条  耗时:{elapsed}s")
                if r.get("issues"):
                    for iss in r["issues"][:2]:
                        print(f"    ↳ {iss[:80]}")


def main():
    # 限制只测试指定 provider (可选: python benchmark.py qwen packy)
    target_providers = sys.argv[1:] if len(sys.argv) > 1 else list(PROVIDERS.keys())
    target_batches = [1, 3, 10]

    all_results = {}
    total_tests = len(target_providers) * len(target_batches)
    done = 0

    for pkey in target_providers:
        if pkey not in PROVIDERS:
            print(f"[WARN] Unknown provider: {pkey}")
            continue
        cfg = PROVIDERS[pkey]
        all_results[pkey] = {}
        print(f"\n{'='*60}")
        print(f"  Testing: {cfg['name']}")
        print(f"{'='*60}")

        for n in target_batches:
            images = BATCHES[n]
            print(f"\n  → {n} 张图 ...", end=" ", flush=True)
            result = test_provider_batch(pkey, cfg, images)
            all_results[pkey][n] = result
            done += 1
            acc_str = f"{result['accuracy']}% ({result['correct']}/{result['total']})"
            print(f"完成  总耗时: {result['total_elapsed']}s  准确率: {acc_str}")
            if result["errors"]:
                print(f"  [ERROR] {result['errors'][0][:100]}")

    print_summary(all_results)

    # 保存完整结果到 JSON
    out_path = Path("E:/claude-code/hotel-inspection/benchmark_results.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2, default=str)
    print(f"\n完整结果已保存: {out_path}")


if __name__ == "__main__":
    main()
