# MiniMax Chinese voice selection reference

## Official inventory

MiniMax currently documents 34 Chinese (Mandarin) system voices. The authoritative inventory is the official System Voice ID List, and the current account-visible inventory can be retrieved through `POST /v1/get_voice` with `voice_type: system`.

- System voice list: https://platform.minimax.io/docs/faq/system-voice-id
- Get Voice API: https://platform.minimax.io/docs/api-reference/voice-management-get
- T2A HTTP: https://platform.minimax.io/docs/api-reference/speech-t2a-http
- Models: https://platform.minimax.io/docs/guides/models-intro
- MiniMax MCP emotion compatibility: https://platform.minimax.io/docs/guides/mcp-guide

## Production grouping

### Stable and professional

`Reliable_Executive`, `News_Anchor`, `Gentleman`, `Male_Announcer`, `Radio_Host`, `Sincere_Adult`, `Mature_Woman`.

### Young and conversational

`Unrestrained_Young_Man`, `Stubborn_Friend`, `Southern_Young_Man`, `Gentle_Youth`, `Straightforward_Boy`, `Pure-hearted_Boy`, `Warm_Bestie`, `Laid_BackGirl`, `Crisp_Girl`, `ExplorativeGirl`.

### Warm and emotional

`Kind-hearted_Antie`, `Kind-hearted_Elder`, `Gentle_Senior`, `Wise_Women`, `Warm_Girl`, `Warm_HeartedGirl`, `Warm-HeartedAunt`, `Soft_Girl`, `IntellectualGirl`.

### Strong character identity

`Humorous_Elder`, `Arrogant_Miss`, `HK_Flight_Attendant`, `Sweet_Lady`, `BashfulGirl`, `Cute_Spirit`, `Lyrical_Voice`, `Robot_Armor`.

These are workflow groupings inferred from the official names. They are not official MiniMax rankings and must be confirmed with a controlled audition for high-value production.

## Selection matrix

| Content | Primary | Alternatives | Avoid by default |
|---|---|---|---|
| General Chinese stand-up | `Sincere_Adult` | `Radio_Host`, `Straightforward_Boy` | announcer, robot, lyrical |
| Workplace mock-rant | `Stubborn_Friend` | `Radio_Host`, `Sincere_Adult` | repeated `angry` calls |
| Science-comedy | `Radio_Host` | `Sincere_Adult`, `Gentle_Youth` | news-anchor stiffness |
| Warm life story | `Sincere_Adult` | `Mature_Woman`, `Warm_Bestie` | extreme character voices |
| Older-person comedy | `Humorous_Elder` | `Kind-hearted_Elder` | young voice forced older |
| Young female chat | `Laid_BackGirl` | `Warm_Bestie`, `Crisp_Girl` | formal announcer voices |
| Commercial authority | `Reliable_Executive` | `Gentleman`, `News_Anchor` | shy or cute voices |

## Stability principles

1. Base timbre selection has higher priority than emotion labels.
2. A voice that works without explicit emotion is safer than one that needs continuous correction.
3. Use one coherent request whenever possible; independent T2A calls can differ because the service is stateless.
4. Keep emotional markings for analysis even when they are not converted into separate API calls.
5. Use documented pause markers `<#x#>` to shape comic timing.
6. Use sound tags sparingly and only when the script contains an actual audible action.
7. Normalize loudness after synthesis. Do not use `vol` as a substitute for mastering.

## Model note

MiniMax documentation currently presents capability information in more than one place. The Models page describes Speech 2.8 as supporting emotions and sound tags, while the MCP guide lists explicit `emotion` compatibility through Speech 2.6 and earlier families. Treat explicit emotion behavior as model-specific, test it with the selected voice, and prefer documented HTTP fields for production stability.
