# Progress Log

## 2026-03-15 — Session 1

### Done
- Project concept defined (AI photo-based hotel room QA)
- System architecture designed (小程序 → backend → storage → Vision AI → dashboard)
- Batch upload logic designed (sequential photos, door sign = room delimiter)
- Confirmed: no model fine-tuning needed, prompt engineering sufficient
- Identified 4 Vision API providers to test: Qwen, GLM, Kimi, MiniMax
- Created project folder structure
- Created task_plan.md, findings.md, progress.md
- GLM API key created, confirmed GLM-4.6V works ✅

---

## 2026-03-15 — Session 2

### Done
- Confirmed Qwen3-VL-Plus, Kimi K2.5 APIs working; MiniMax excluded (no vision)
- User provided 20 test images (10 good + 10 fail), matched into 10 scene pairs
- Visually analyzed all 20 images, generated scene-specific inspection standards
- Built H5 demo (阿姨端 + 经理看板) deployed to Railway
- Prompt engineering: v1 → v8 (iterative refinement)
  - v1: 0/20 (too strict, all fail)
  - v6: 15/20 = 75%
  - v8: +电线fix (桌面只检水瓶), estimated 16+/20
- Parallel AI calls: ThreadPoolExecutor(10) + asyncio.gather → 10 images in ~15–20s
- Confirmed Qwen concurrency: 10 simultaneous requests, no errors
- Added JSON file persistence (records survive restart, reset on redeploy)
- Fixed mobile bug: removed `capture="environment"` that blocked gallery multi-select on iOS

### Known Limitations (accepted)
- 床铺：折叠压痕 vs 睡皱纹难以区分（搁置）
- 淋浴花洒：出水方向识别不可靠（搁置）
- 淋浴地板：石材纹理 vs 积水（搁置）

### Public URLs
- 阿姨端: https://laudable-art-production.up.railway.app
- 经理看板: https://laudable-art-production.up.railway.app/manager

### Next Steps
- Run full 20-image test with v8 prompt
- Design production DB schema
- Build 微信小程序
