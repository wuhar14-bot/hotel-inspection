# Findings

## Model Comparison

### Evaluation Criteria
- Pass/fail accuracy on clean rooms (false negative rate)
- Pass/fail accuracy on dirty rooms (false positive rate)
- Quality of issue descriptions (specific vs vague)
- Latency per image
- Cost per image

---

## API Status

| Model | API Name | Status | Notes |
|:--|:--|:--|:--|
| GLM-4.6V | `glm-4.6v` | ✅ Connected + Tested | Reasoning model — requires `max_tokens≥1500`; thinking in `reasoning_content`, answer in `content` |
| Qwen3-VL-Plus | `qwen3-vl-plus` | ✅ Connected + Tested | Most detailed output; best overall so far |
| Kimi K2.5 | `kimi-k2.5` | ✅ Connected + Tested | Prone to 429 overload; retry needed occasionally |
| MiniMax | N/A | ❌ Excluded | 无视觉理解能力，仅有文本和图像生成模型，不支持 image→text |

**Primary model recommendation: `qwen3-vl-plus`**

---

## Preliminary Test — 2026-03-15

**Image**: 衣柜/浴袍区域（test-images/good/微信图片_2026-03-15_084536_867.jpg）

**Prompt**: 检查床铺/地面/桌面/毛巾四项标准，输出 JSON pass/score/issues

| Model | Score | Key Observations |
|:--|:--|:--|
| GLM-4.6V | 40 | 识别场景不全，合理标注无法评估项 |
| Kimi K2.5 | 25 | 额外发现"两件浴袍共用一个衣架、排列不整齐" |
| Qwen3-VL-Plus | 40 | 最细致：注意到浴袍系带松散、右侧挂有丝质拖鞋/袜套 |

**Note**: 此图为衣柜局部，三个模型均正确识别出图中缺少床/地面/桌面场景。真正的准确率测试需要覆盖完整房间场景的图片。

---

## Scene Pairing Analysis — 2026-03-15

**Total**: 10 good + 10 fail = 20 images, 10 matched scene pairs

| # | 场景 | Good 文件 | Fail 文件 | 关键差异 |
|:--|:--|:--|:--|:--|
| 1 | 衣柜/浴袍 | good_1 (084536) | fail_5 (084114) | Good: 2件浴袍+拖鞋完整；Fail: 仅1件浴袍，无拖鞋 |
| 2 | 桌面/茶水 | good_2 (084543) | fail_10 (084139) | Good: 电线收好，整洁；Fail: 电线乱放，桌面有水渍 |
| 3 | 床铺（正面） | good_3 (084547) | fail_4 (084110) | Good: 被单平整；Fail: 大面积褶皱 |
| 4 | 床铺（斜面） | good_4 (084550) | fail_6 (084119) | Good: 床角整齐；Fail: 被单严重褶皱 |
| 5 | 洗手台全景 | good_5 (084555) | fail_2 (084103) | Good: 台面整洁；Fail: 台面有乱扔脏毛巾 |
| 6 | 洗脸盆近景 | good_6 (084559) | fail_7 (084124) | Good: 台面干净；Fail: 台面有用过的纸巾/面巾 |
| 7 | 毛巾架 | good_7 (084613) | fail_8 (084130) | Good: 3条白色毛巾整齐；Fail: 毛巾颜色不一致（灰色混入） |
| 8 | 马桶区 | good_8 (084618) | fail_9 (084134) | Good: 马桶盖关，垃圾桶空；Fail: 马桶盖开，垃圾桶有垃圾 |
| 9 | 淋浴花洒 | good_9 (084622) | fail_1 (084050) | Good: 浴液整齐，花洒归位；Fail: 细节略乱 |
| 10 | 淋浴地板 | good_10 (084626) | fail_3 (084106) | Good: 干燥干净；Fail: 明显积水 |

---

## Scene-Specific Inspection Standards (v1) — 2026-03-15

Derived from visual analysis of paired images above. Used in Qwen3-VL-Plus prompt.

| 场景 | 合格条件 | 不合格条件 |
|:--|:--|:--|
| 床铺 | 被单基本平整，枕头对称 | 大面积褶皱（超过1/3床面），枕头歪斜 |
| 毛巾架 | 3条白色毛巾整齐叠放 | 颜色不统一，叠放乱，数量不足 |
| 洗手台 | 台面整洁，杯具摆好 | 台面有用过的纸巾/毛巾乱放 |
| 马桶区 | 马桶盖关，垃圾桶空 | 马桶盖未关，垃圾桶有垃圾 |
| 淋浴地板 | 干燥或少量水迹 | 明显积水 |
| 淋浴花洒 | 花洒归位，浴液整齐 | 花洒/浴液未归位 |
| 衣柜/浴袍 | 2件浴袍+拖鞋完整挂好 | 浴袍数量不足，缺拖鞋 |
| 桌面/茶水 | 电线收好，台面干净 | 电线乱放，台面有水渍 |

---

## Prompt Accuracy Test — Round 2 (scene-specific prompt, 2026-03-15)

**Prompt version**: v6 (场景自动识别 + 逐场景合格标准)
**Model**: qwen3-vl-plus

**Result: 15/20 = 75%**

| Image | Scene | Expected | Result | Correct? |
|:--|:--|:--|:--|:--|
| good_1 | 衣柜/浴袍 | pass=true | pass=true | ✓ |
| good_2 | 桌面/茶水 | pass=true | pass=false | ✗ — 误判电线/桌面，已简化为只检水瓶数 |
| good_3 | 床铺 | pass=true | pass=false | ✗ — 床铺识别难（见已知局限） |
| good_4 | 床铺 | pass=true | pass=false | ✗ — 床铺识别难 |
| good_5 | 洗手台 | pass=true | pass=true | ✓ |
| good_6 | 洗手台 | pass=true | pass=true | ✓ |
| good_7 | 毛巾架 | pass=true | pass=true | ✓ |
| good_8 | 马桶区 | pass=true | pass=true | ✓ |
| good_9 | 淋浴花洒 | pass=true | (API空响应) | ✗ — 网络问题 |
| good_10 | 淋浴地板 | pass=true | pass=true | ✓ |
| fail_1 | 淋浴花洒 | pass=false | pass=true | ✗ — 花洒正反面模型无法区分 |
| fail_2 | 洗手台 | pass=false | pass=false | ✓ |
| fail_3 | 淋浴地板 | pass=false | pass=true | ✗ — 积水与石材纹理难以区分 |
| fail_4 | 床铺 | pass=false | pass=false | ✓ |
| fail_5 | 衣柜/浴袍 | pass=false | pass=false | ✓ |
| fail_6 | 床铺 | pass=false | pass=false | ✓ |
| fail_7 | 洗手台 | pass=false | pass=false | ✓ |
| fail_8 | 毛巾架 | pass=false | pass=false | ✓ |
| fail_9 | 马桶区 | pass=false | pass=false | ✓ |
| fail_10 | 桌面/茶水 | pass=false | pass=false | ✓ |

---

## Known Model Limitations (qwen3-vl-plus)

记录 Qwen3-VL-Plus 在本任务中确认的识别局限，已暂时搁置或接受：

| 场景 | 问题 | 状态 |
|:--|:--|:--|
| 床铺 | 整理后的折叠压痕 vs 睡过的杂乱皱纹，模型难以稳定区分 | 已搁置，接受误判 |
| 淋浴花洒 | 花洒正反面（出水方向）无法可靠识别 | 已搁置，接受误判 |
| 淋浴地板 | 深色石材纹理 vs 积水反光，边界场景难区分 | 已搁置，接受误判 |
| 桌面/茶水 | 电线判断不稳定（误判已插入插座的电线） | 已解决：只检水瓶数量，不检电线 |

---

## Prompt Version Log

| Version | Key Change | Accuracy |
|:--|:--|:--|
| v1 | 通用整洁判断（无阈值） | 0/20 — 全部 pass=false |
| v2 | 加入逐场景合格标准 | ~60% |
| v3–v5 | 床铺/马桶/毛巾逐步优化 | ~75% |
| v6 | 淋浴地板石材注意、马桶垃圾桶颜色注意 | 15/20 = 75% |
| v7 | 床铺改为"中央区域"判断（调整中） | TBD |
| v8（当前） | 桌面只检水瓶数量，移除电线检查 | TBD |

---

## Results Table

| Model | Clean Room Accuracy | Dirty Room Accuracy | Avg Latency | Cost/img | Notes |
|:--|:--|:--|:--|:--|:--|
| qwen3-vl-plus | — | — | — | — | v1 prompt: 0/20 correct; v2 scene-specific: TBD |
| glm-4.6v | — | — | — | — | needs max_tokens≥1500 |
| kimi-k2.5 | — | — | — | — | occasional 429 |
| minimax | — | — | — | — | ❌ no vision capability |
