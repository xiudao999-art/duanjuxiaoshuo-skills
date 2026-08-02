# 可复用 CK 字幕强调系统

本文件定义跨视频复用的系统边界。具体评分见 `selection-method.md`，动作见 `template-catalog.md`，字体见 `style-spec.md`，合成与音效时钟见 `integration.md`。

## 单一事实源

每个视频只维护一份 `emphasis-plan.json`。不要直接手写彼此独立的 `accent-plan.json` 与 `highlight-plan.json`；用编译器生成它们，以免等级、基线、音效和替代字幕关系不一致。

```text
核准原文 + 词级时间 + 画面安全区
              ↓
      emphasis-plan.json
        ├─ L1 行内黄色
        └─ L2/L3 CK 事件
              ↓ compile
        accent-plan.json
        highlight-plan.json
        emphasis-audit.json
```

## 五步决策

1. **找候选**：只从结果、反差、新概念、行为落点、价值判断和结论中选择完整短语。
2. **判等级**：按十分制评分；L0 白字、L1 黄色、L2 完整 CK、L3 极少量 Hero。
3. **定语义角色**：记录 `semantic_role` 和自然语言 `reason`，再按角色选择动作，不为丰富模板而轮换。
4. **锁声画锚点**：使用词级时间定位 `phrase_first_word`、`first_stressed_syllable` 或 `payoff_word`；30 fps 下视觉和音效误差不超过一帧。
5. **检查画面承载力**：先锁字幕、PIP、脸、Logo 和 UI 的边界，再选 `same_as_normal` 或显式 CK 基线。

## 通用语义角色

| 语义角色 | 常见内容 | 默认层级 | 首选动作 | 声音策略 |
|---|---|---|---|---|
| `opening_result` | 开场承诺、数字结果 | L2 | `rise_settle` | 无声或干净低上扬 |
| `coined_term_reveal` | 新造词、昵称、笑点 | L2 | `char_toss` | 短促 impact，首字同帧 |
| `action_process` | 操作、行为、去向 | L2 | `stretch_reveal` | 轻空气扩张 |
| `secondary_action` | 补充行为、快速结果 | L1/L2 | `fade_snap` | 通常无声或极轻 click |
| `concept_build` | 多词组成的新概念 | L2 | `type_on` | 轻 tick 或紧凑 build |
| `abstract_value` | 情绪价值、因果洞察 | L2 | `light_sweep` | 扫光边缘同步 airy sweep |
| `final_result` | 商业结果、方法收束 | L2/L3 | `type_on` / `legacy_zoom_streak` | 紧凑 build 或单次 impact |
| `memorable_keyword` | 值得记住但不改变理解的词 | L1 | 稳定黄色 | 无独立音效 |

角色不是固定枚举；新题材可增加角色，但必须说明为什么该短语需要打断普通阅读节奏。

## 声音规则

- 先保证对白清晰，再加入声音触感；SFX 不是节奏底噪。
- `auto` 只用于本地清单中有可靠模板绑定的音效。低置信度参考声使用 `none` 或干净替代声。
- `sfx_offset` 相对 CK 视觉起点；默认 `0.0`。只有扫光边缘或 payoff 明确需要延后时才设置正偏移。
- 默认增益约 `-4 dB`，再按对白响度调整。连续事件共用一个表达节拍时，不重复播放音效。
- 检测音效前置静音；文件开始不等于有效声音开始。有效瞬态仍需满足一帧误差。
- 参考视频分离出的声音只能作为本地重建证据，不进入可分发模板包。

## 布局规则

- `baseline_policy: same_as_normal`：CK 稳定状态与普通字幕同一高度，适合需要位置连续的口播片。
- `baseline_policy: explicit`：CK 使用独立高度，适合中上部金句或需要避开 PIP 的版式。
- 弹出全过程都要检查安全区，不能只检查稳定帧。
- CK 必须替代其 `cue_ids` 对应的普通字幕；同一句不能在两层同时出现。

## 统一计划与编译

从 `assets/emphasis-plan-template.json` 复制任务计划，填写完整视频的真实候选。然后运行：

```powershell
python scripts/compile_emphasis_plan.py `
  --plan D:\job\emphasis-plan.json `
  --out-dir D:\job\captions\plans
```

编译器检查：等级与分数、事件 ID、cue 重复替代、模板、声音声明、起音锚点、保持策略、基线策略和密度。警告需要人工判断，错误必须修复后才能渲染。

## 新视频的最低交付物

- `emphasis-plan.json`：人工判断的单一事实源。
- `accent-plan.json`、`highlight-plan.json`：编译产物。
- `emphasis-audit.json`：所有“为什么强调”的决策记录。
- `highlight-plan-resolved.json`：最终时间、图层与实际 SFX 路径。
- CK 首帧、主落点、稳定帧、结束帧 QC；至少覆盖每种布局模式。
