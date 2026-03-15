# Hotel Room AI Inspection System — Task Plan

## Project Background

A hotel wants to replace manual room inspection (manager physically walking each room) with an AI-powered photo-based QA system.

### Current Flow
阿姨做完卫生 → 主管实地走查 → 判断是否通过 → 系统标记房间可售

### Target Flow
阿姨拍照上传 → AI 自动打分 → 主管仅复核被标记为"不合格"的房间 → 系统标记可售

---

## Core Users

- **Primary**: 阿姨（客房服务员）— photo capture, upload, instant feedback
- **Secondary**: 客房经理 / 主管 — review AI reports, handle flagged rooms

---

## Demo (H5) — LIVE ✅

**Public URL**: https://laudable-art-production.up.railway.app

| Portal | URL | Status |
|:--|:--|:--|
| 阿姨端 | `/` | ✅ Live |
| 经理看板 | `/manager` | ✅ Live |
| 数据接口 | `/api/results` | ✅ Live |

### Demo Stack
- **Frontend**: H5 (Tailwind CDN, mobile-responsive, no build step)
- **Backend**: FastAPI (Python) on Railway
- **AI**: Qwen3-VL-Plus via Dashscope API
- **Storage**: JSON file on Railway server (persists within deploy, resets on redeploy)
- **Concurrency**: All images processed in parallel (ThreadPoolExecutor × 10)

### Demo Flow
1. 阿姨打开阿姨端 → 输入房间号 → 选多张照片（相册/摄像头）→ 提交
2. AI 并行分析所有照片（~15–20s for 10 images）
3. 阿姨端显示每张照片的场景/评分/问题
4. 经理看板实时更新（自动刷新 15s），可按合格/不合格筛选，点击查看详情

---

## Per-Room Upload Flow

1. 阿姨打开小程序 → 手动输入房间号
2. 拍摄该房间照片（床铺、卫生间、桌面等，按规定场景）
3. 提交 → AI 实时打分 → **立即返回结果给阿姨**
4. 阿姨查看反馈：通过则完成；不通过则整改后重拍重提交
5. 最终结果同步到经理端

---

## AI Model

**Selected**: `qwen3-vl-plus` (Dashscope / 阿里云)

**Prompt version**: v8 (current, deployed)
- 场景自动识别（8个场景）
- 逐场景合格/不合格判断标准
- 只检水瓶数量（不检电线）

**Accuracy on test set (20 images)**: ~75–80% (v6: 15/20, v8: +电线fix)

### Known Model Limitations (accepted, not pursuing further)
| Scene | Issue |
|:--|:--|
| 床铺 | 折叠压痕 vs 睡过皱纹难以稳定区分 |
| 淋浴花洒 | 出水方向（正反面）无法可靠识别 |
| 淋浴地板 | 深色石材纹理 vs 积水边界难区分 |

---

## Task Status

- [x] Collect test images (10 good + 10 fail, 10 matched pairs)
- [x] Set up API keys: GLM-4.6V ✅ Kimi K2.5 ✅ Qwen3-VL-Plus ✅ MiniMax ❌
- [x] Test Vision APIs + prompt engineering (v1→v8)
- [x] Build H5 demo — 阿姨端 + 经理看板
- [x] Deploy to Railway (public URL, accessible from any phone)
- [x] Parallel AI calls (ThreadPoolExecutor, confirmed 10 concurrent OK)
- [x] JSON file persistence (survives container restart, resets on redeploy)
- [x] Mobile compatibility fix (removed `capture` attr that blocked gallery multi-select)
- [ ] Run full 20-image test with v8 prompt, record final accuracy
- [ ] Design production DB schema (rooms, uploads, scores, issues)
- [ ] Build 微信小程序（per-room flow）
- [ ] Build production manager dashboard with DB

---

## Open Questions

1. **Liability**: If AI passes a dirty room and guest complains — who is responsible?
2. **Accuracy threshold**: What false-positive rate is acceptable before hotel trusts AI?
3. **Scene coverage**: How many photos per room? Which scenes are mandatory?
4. **Offline handling**: What if 阿姨 has no signal on upper floors?
5. **Production persistence**: Demo uses JSON file; production needs proper DB (Postgres / Supabase)

---

## File Structure

```
hotel-inspection/
├── task_plan.md        ← this file
├── findings.md         ← model comparison, accuracy test results, known limitations
├── progress.md         ← session-by-session log
├── test-images/        ← 10 good + 10 fail matched scene pairs
└── demo/
    ├── main.py         ← FastAPI backend (prompt v8, parallel AI, JSON persistence)
    ├── index.html      ← 阿姨端 H5
    ├── manager.html    ← 经理看板 H5
    ├── requirements.txt
    └── Procfile
```
