from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build transparent Chinese caption and CK quote layers.")
    parser.add_argument("--srt", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--duration", type=float)
    parser.add_argument("--speed", type=float, default=1.0)
    parser.add_argument("--width", type=int, default=720)
    parser.add_argument("--height", type=int, default=1280)
    parser.add_argument("--fps", type=int, default=24)
    parser.add_argument("--scale", type=int, default=2)
    parser.add_argument("--font", type=Path, required=True)
    parser.add_argument("--weight", type=int, default=850)
    parser.add_argument("--normal-size", type=int, default=42)
    parser.add_argument("--accent-size", type=int, default=60)
    parser.add_argument("--highlight-size", type=int, default=52)
    parser.add_argument("--max-width", type=int, default=650)
    parser.add_argument("--line-gap", type=int, default=72)
    parser.add_argument("--normal-baseline", type=int, default=1150)
    parser.add_argument("--highlight-baselines", default="1035,1110")
    parser.add_argument("--accent-plan", type=Path)
    parser.add_argument("--highlight-plan", type=Path)
    parser.add_argument(
        "--skip-normal-layer",
        action="store_true",
        help="Build only CK replacement clips/SFX when normal captions are rendered from the locked ASS layer.",
    )
    parser.add_argument(
        "--style-profile",
        choices=("legacy", "bogouwei_reference", "shenzhai_recap_1080"),
        default="legacy",
    )
    return parser.parse_args()


def srt_time(value: str) -> float:
    hours, minutes, rest = value.strip().replace(".", ",").split(":")
    seconds, millis = rest.split(",")
    return int(hours) * 3600 + int(minutes) * 60 + int(seconds) + int(millis) / 1000


def load_srt(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8-sig").strip()
    cues = []
    for block in re.split(r"\r?\n\s*\r?\n", text):
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        if len(lines) < 3 or "-->" not in lines[1]:
            continue
        start, end = [part.strip() for part in lines[1].split("-->", 1)]
        cues.append({
            "index": int(lines[0]),
            "start": srt_time(start),
            "end": srt_time(end),
            "text": " ".join(lines[2:]),
        })
    if not cues:
        raise ValueError(f"No SRT cues found in {path}")
    return cues


def load_json(path: Path | None, default):
    if path is None:
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def variable_font(path: Path, size: int, weight: int, scale: int) -> ImageFont.FreeTypeFont:
    font = ImageFont.truetype(str(path), size * scale)
    try:
        font.set_variation_by_axes([weight])
    except (AttributeError, OSError):
        pass
    return font


def accent_flags(text: str, phrases: list[str]) -> list[bool]:
    flags = [False] * len(text)
    for phrase in phrases:
        cursor = 0
        while phrase and (found := text.find(phrase, cursor)) >= 0:
            for index in range(found, found + len(phrase)):
                flags[index] = True
            cursor = found + len(phrase)
    return flags


@lru_cache(maxsize=512)
def segment_words(text: str) -> tuple[str, ...]:
    """Segment Chinese captions into wrapping units without changing visible text."""
    script = (
        "const t=process.argv[1];"
        "const s=new Intl.Segmenter('zh-CN',{granularity:'word'});"
        "process.stdout.write(JSON.stringify(Array.from(s.segment(t),x=>x.segment)));"
    )
    try:
        result = subprocess.run(
            ["node", "-e", script, text], check=True, capture_output=True,
            text=True, encoding="utf-8",
        )
        tokens = json.loads(result.stdout)
        if "".join(tokens) == text:
            return tuple(tokens)
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError):
        pass
    return tuple(text)


def units_from_flags(text: str, flags: list[bool]) -> list[list[tuple[str, bool]]]:
    units: list[list[tuple[str, bool]]] = []
    cursor = 0
    for token in segment_words(text):
        end = cursor + len(token)
        unit = [(char, flags[index]) for index, char in enumerate(text[cursor:end], cursor)]
        # Grammatical suffixes and punctuation stay attached to the preceding word.
        if units and (token in "的地得了着过们性化者" or all(char in "，。！？；：、,.!?;:" for char in token)):
            units[-1].extend(unit)
            # Intl.Segmenter may split result complements such as “递 / 到 / 了”.
            # Keep the short verb-complement-aspect cluster on one rendered line.
            if token in "了着过" and len(units) >= 2 and len(units[-1]) <= 2 and len(units[-2]) <= 2:
                units[-2].extend(units.pop())
        elif units and len(unit) <= 3 and token[0] in "到起下上出进回开住" and len(units[-1]) <= 2:
            units[-1].extend(unit)
        else:
            units.append(unit)
        cursor = end
    return units


def wrap_characters(
    text: str,
    flags: list[bool],
    normal_font: ImageFont.FreeTypeFont,
    accent_font: ImageFont.FreeTypeFont,
    max_width: int,
    scale: int,
) -> list[list[tuple[str, bool]]]:
    limit = max_width * scale
    units = units_from_flags(text, flags)
    lines: list[list[tuple[str, bool]]] = []
    current: list[tuple[str, bool]] = []
    current_width = 0.0

    def item_width(item: tuple[str, bool]) -> float:
        char, accent = item
        return (accent_font if accent else normal_font).getlength(char)

    for unit in units:
        unit_width = sum(item_width(item) for item in unit)
        if current and current_width + unit_width > limit:
            lines.append(current)
            current, current_width = [], 0.0
        if unit_width > limit:
            for item in unit:
                width = item_width(item)
                if current and current_width + width > limit:
                    lines.append(current)
                    current, current_width = [], 0.0
                current.append(item)
                current_width += width
        else:
            current.extend(unit)
            current_width += unit_width
    if current:
        lines.append(current)

    if len(lines) > 1 and len(lines[-1]) == 1 and len(lines[-2]) > 1:
        lines[-1].insert(0, lines[-2].pop())
    if len(lines) > 2:
        raise ValueError(f"Caption exceeds two lines after pixel wrapping: {text}")
    return lines


def draw_text(mask: Image.Image, x: float, baseline: float, text: str, font, *, stroke=0, fill=255) -> None:
    ImageDraw.Draw(mask).text(
        (round(x), round(baseline)), text, font=font, anchor="ls", fill=fill,
        stroke_width=stroke, stroke_fill=fill,
    )


def render_caption(cue: dict, accents: list[str], cfg: argparse.Namespace, fonts: dict) -> Image.Image:
    canvas_size = (cfg.width * cfg.scale, cfg.height * cfg.scale)
    overlay = Image.new("RGBA", canvas_size, (0, 0, 0, 0))
    flags = accent_flags(cue["text"], accents)
    lines = wrap_characters(
        cue["text"], flags, fonts["normal"], fonts["accent"],
        cfg.max_width, cfg.scale,
    )
    line_gap = cfg.line_gap * cfg.scale
    first_baseline = cfg.normal_baseline * cfg.scale - line_gap * (len(lines) - 1)
    masks = {name: Image.new("L", canvas_size, 0) for name in ("shadow", "edge", "normal", "accent")}

    for line_index, line in enumerate(lines):
        baseline = first_baseline + line_index * line_gap
        widths = [(fonts["accent"] if accent else fonts["normal"]).getlength(char) for char, accent in line]
        x = (cfg.width * cfg.scale - sum(widths)) / 2
        for (char, accent), width in zip(line, widths):
            font = fonts["accent"] if accent else fonts["normal"]
            draw_text(masks["shadow"], x + 2 * cfg.scale, baseline + 4 * cfg.scale, char, font,
                      stroke=round(1.5 * cfg.scale), fill=cfg.shadow_alpha)
            draw_text(masks["edge"], x, baseline, char, font, stroke=round(1.15 * cfg.scale))
            draw_text(masks["accent" if accent else "normal"], x, baseline, char, font)
            x += width

    masks["shadow"] = masks["shadow"].filter(ImageFilter.GaussianBlur(0.85 * cfg.scale))
    for name, color in (
        ("shadow", (*cfg.shadow_rgb, 0)),
        ("edge", (*cfg.edge_rgb, 0)),
        ("normal", (*cfg.normal_rgb, 255)),
        ("accent", (*cfg.accent_rgb, 255)),
    ):
        layer = Image.new("RGBA", canvas_size, color)
        layer.putalpha(masks[name])
        overlay.alpha_composite(layer)
    rendered = overlay.resize((cfg.width, cfg.height), Image.Resampling.LANCZOS)
    return transformed(rendered, cfg.text_scale_x, scale_y=1.0, dx=cfg.text_center_dx)


def smoothstep(edge0: float, edge1: float, value: float) -> float:
    if edge0 == edge1:
        return 1.0 if value >= edge1 else 0.0
    x = max(0.0, min(1.0, (value - edge0) / (edge1 - edge0)))
    return x * x * (3.0 - 2.0 * x)


def interpolate_keyframes(value: float, keys: list[tuple[float, float]]) -> float:
    if value <= keys[0][0]:
        return keys[0][1]
    for (t0, v0), (t1, v1) in zip(keys, keys[1:]):
        if value <= t1:
            p = smoothstep(t0, t1, value)
            return v0 + (v1 - v0) * p
    return keys[-1][1]


def vertical_gradient(size, top, bottom) -> Image.Image:
    layer = Image.new("RGBA", size)
    draw = ImageDraw.Draw(layer)
    for y in range(size[1]):
        ratio = y / max(1, size[1] - 1)
        color = tuple(round(top[i] * (1 - ratio) + bottom[i] * ratio) for i in range(4))
        draw.line((0, y, size[0], y), fill=color)
    return layer


def quote_layer(lines: list[str], cfg: argparse.Namespace, font, baselines: list[int], force_white=False) -> Image.Image:
    canvas_size = (cfg.width * cfg.scale, cfg.height * cfg.scale)
    overlay = Image.new("RGBA", canvas_size, (0, 0, 0, 0))
    masks = {name: Image.new("L", canvas_size, 0) for name in ("shadow", "edge", "fill")}
    for text, baseline_value in zip(lines, baselines):
        baseline = baseline_value * cfg.scale
        width = font.getlength(text)
        x = (cfg.width * cfg.scale - width) / 2
        draw_text(masks["shadow"], x + 2 * cfg.scale, baseline + 3 * cfg.scale, text, font,
                  stroke=round(1.4 * cfg.scale), fill=cfg.highlight_shadow_alpha)
        draw_text(masks["edge"], x, baseline, text, font, stroke=round(1.05 * cfg.scale))
        draw_text(masks["fill"], x, baseline, text, font)

    masks["shadow"] = masks["shadow"].filter(ImageFilter.GaussianBlur(0.8 * cfg.scale))
    shadow = Image.new("RGBA", canvas_size, (*cfg.highlight_shadow_rgb, 0)); shadow.putalpha(masks["shadow"])
    edge = Image.new("RGBA", canvas_size, (*cfg.highlight_edge_rgb, 0)); edge.putalpha(masks["edge"])
    overlay.alpha_composite(shadow); overlay.alpha_composite(edge)
    colors = cfg.highlight_white_gradient if force_white else cfg.highlight_yellow_gradient
    fill = vertical_gradient(canvas_size, *colors); fill.putalpha(masks["fill"]); overlay.alpha_composite(fill)
    rendered = overlay.resize((cfg.width, cfg.height), Image.Resampling.LANCZOS)
    return transformed(rendered, cfg.text_scale_x, scale_y=1.0, dx=cfg.text_center_dx)


def transformed(layer: Image.Image, scale_x: float, opacity=1.0, blur=0.0, scale_y=None,
                rotate=0.0, dx=0.0, dy=0.0) -> Image.Image:
    bbox = layer.getchannel("A").getbbox()
    result = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    if not bbox or scale_x <= 0:
        return result
    crop = layer.crop(bbox)
    scale_y = scale_x if scale_y is None else scale_y
    crop = crop.resize((max(1, round(crop.width * scale_x)), max(1, round(crop.height * scale_y))), Image.Resampling.LANCZOS)
    if rotate:
        crop = crop.rotate(rotate, resample=Image.Resampling.BICUBIC, expand=True)
    if blur > 0:
        crop = crop.filter(ImageFilter.GaussianBlur(blur))
    if opacity < 1:
        crop.putalpha(crop.getchannel("A").point(lambda p: round(p * max(0.0, min(1.0, opacity)))))
    cx, cy = (bbox[0] + bbox[2]) / 2, (bbox[1] + bbox[3]) / 2
    result.alpha_composite(crop, (round(cx - crop.width / 2 + dx), round(cy - crop.height / 2 + dy)))
    return result


def reveal_mask(layer: Image.Image, progress: float, feather: int = 0, glow=False) -> Image.Image:
    bbox = layer.getchannel("A").getbbox()
    result = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    if not bbox or progress <= 0:
        return result
    x1, y1, x2, y2 = bbox
    edge = x1 + round((x2 - x1) * min(1.0, progress))
    mask = Image.new("L", layer.size, 0)
    ImageDraw.Draw(mask).rectangle((x1, y1, edge, y2), fill=255)
    if feather:
        mask = mask.filter(ImageFilter.GaussianBlur(feather))
    visible = layer.copy()
    visible.putalpha(Image.composite(layer.getchannel("A"), Image.new("L", layer.size, 0), mask))
    result.alpha_composite(visible)
    if glow and 0 < progress < 1:
        glow_mask = Image.new("L", layer.size, 0)
        ImageDraw.Draw(glow_mask).rectangle((edge - 18, y1 - 5, edge + 18, y2 + 5), fill=170)
        glow_mask = glow_mask.filter(ImageFilter.GaussianBlur(10))
        glow_layer = Image.new("RGBA", layer.size, (255, 252, 190, 0)); glow_layer.putalpha(glow_mask)
        result.alpha_composite(glow_layer)
    return result


def character_slices(layer: Image.Image, count: int) -> list[Image.Image]:
    bbox = layer.getchannel("A").getbbox()
    if not bbox or count <= 1:
        return [layer]
    x1, y1, x2, y2 = bbox
    width = (x2 - x1) / count
    slices = []
    for index in range(count):
        left = round(x1 + index * width - 3)
        right = round(x1 + (index + 1) * width + 3)
        mask = Image.new("L", layer.size, 0)
        ImageDraw.Draw(mask).rectangle((left, y1 - 8, right, y2 + 8), fill=255)
        part = layer.copy(); part.putalpha(Image.composite(layer.getchannel("A"), Image.new("L", layer.size, 0), mask))
        slices.append(part)
    return slices


def ck_frame(elapsed: float, yellow: Image.Image, white: Image.Image, template: str, char_count: int) -> Image.Image:
    result = Image.new("RGBA", yellow.size, (0, 0, 0, 0))
    if template == "rise_settle":
        p = smoothstep(0, .20, elapsed)
        scale = interpolate_keyframes(elapsed, [(0, .92), (.14, 1.04), (.24, 1)])
        result.alpha_composite(transformed(yellow, scale, p, dy=(1-p)*58))
        return result
    if template == "char_toss":
        yellow_parts = character_slices(yellow, char_count)
        white_parts = character_slices(white, char_count)
        for index, (ypart, wpart) in enumerate(zip(yellow_parts, white_parts)):
            local = elapsed - index * .045
            if local <= 0:
                continue
            p = smoothstep(0, .18, local)
            scale = interpolate_keyframes(local, [(0, .30), (.13, 1.08), (.24, 1)])
            angle = (1-p) * (-28 + index * 13)
            dx = (1-p) * (-22 + index * 12)
            dy = (1-p) * (46 + index * 4)
            result.alpha_composite(transformed(ypart, scale, p, rotate=angle, dx=dx, dy=dy))
            if local < .11:
                result.alpha_composite(transformed(wpart, scale, (1-p)*.7, rotate=angle, dx=dx, dy=dy))
        return result
    if template == "stretch_reveal":
        p = smoothstep(0, .23, elapsed)
        result.alpha_composite(transformed(yellow, .24 + .76*p, p, blur=(1-p)*3.5, scale_y=.92 + .08*p))
        return result
    if template == "fade_snap":
        p = smoothstep(0, .15, elapsed)
        scale = interpolate_keyframes(elapsed, [(0, .86), (.11, 1.035), (.20, 1)])
        result.alpha_composite(transformed(yellow, scale, p, blur=(1-p)*1.6))
        return result
    if template == "light_sweep":
        p = smoothstep(0, .36, elapsed)
        result.alpha_composite(reveal_mask(yellow, p, feather=2, glow=True))
        return result
    if template == "type_on":
        slot = .036
        parts = character_slices(yellow, char_count)
        for index, part in enumerate(parts):
            local = elapsed - index * slot
            if local <= 0:
                continue
            p = smoothstep(0, .10, local)
            scale = interpolate_keyframes(local, [(0, .72), (.075, 1.06), (.14, 1)])
            result.alpha_composite(transformed(part, scale, p, blur=(1-p)*1.2))
        return result
    # Legacy CK zoom-streak template.
    scale = interpolate_keyframes(elapsed, [(0, .05), (.06, .18), (.12, .43), (.18, .76), (.23, 1), (.28, 1.055), (.36, 1)])
    opacity = smoothstep(0, .10, elapsed)
    envelope = math.sin(math.pi * smoothstep(.05, .43, elapsed)) if elapsed < .43 else 0.0
    for index, base_opacity in reversed(list(enumerate((.42, .31, .21, .13), start=1))):
        result.alpha_composite(transformed(
            yellow,
            scale + envelope * (.075 + index * .085),
            base_opacity * envelope,
            .65 + index * .72,
            scale + envelope * (.010 + index * .018),
        ))
    result.alpha_composite(transformed(yellow, scale, opacity))
    white_mix = (1 - smoothstep(.11, .27, elapsed)) * opacity
    if white_mix > 0:
        result.alpha_composite(transformed(white, scale, white_mix))
    return result


def run(command: list[str]) -> None:
    subprocess.run(command, check=True)


def render_highlight(output: Path, duration: float, lines: list[str], baselines: list[int], cfg, font, template: str) -> None:
    yellow = quote_layer(lines, cfg, font, baselines)
    white = quote_layer(lines, cfg, font, baselines, force_white=True)
    command = [
        "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
        "-f", "rawvideo", "-pix_fmt", "rgba", "-s", f"{cfg.width}x{cfg.height}",
        "-r", str(cfg.fps), "-i", "pipe:0", "-t", f"{duration:.6f}",
        "-an", "-c:v", "qtrle", "-pix_fmt", "argb", str(output),
    ]
    process = subprocess.Popen(command, stdin=subprocess.PIPE)
    assert process.stdin is not None
    try:
        for frame_number in range(max(1, round(duration * cfg.fps))):
            process.stdin.write(ck_frame((frame_number + .5) / cfg.fps, yellow, white, template, sum(len(x) for x in lines)).tobytes())
    finally:
        process.stdin.close()
    if process.wait():
        raise RuntimeError(f"Failed to render {output}")


def main() -> None:
    cfg = parse_args()
    user_normal_size = cfg.normal_size != 42
    user_accent_size = cfg.accent_size != 60
    user_highlight_size = cfg.highlight_size != 52
    user_max_width = cfg.max_width != 650
    user_line_gap = cfg.line_gap != 72
    user_normal_baseline = cfg.normal_baseline != 1150
    user_highlight_baselines = cfg.highlight_baselines != "1035,1110"
    if cfg.style_profile in {"bogouwei_reference", "shenzhai_recap_1080"}:
        cfg.weight = 825
        if cfg.style_profile == "shenzhai_recap_1080":
            # Fixed 1080x1920 profile validated for the illustrated-audiobook
            # workflow. Do not silently inherit 720-wide defaults.
            cfg.width = 1080
            cfg.height = 1920
            cfg.fps = 25
            cfg.normal_size = 88
            cfg.accent_size = 88
            cfg.highlight_size = 88
            # The locked 88 px face measures an 11-Han line at about 966 px.
            # Keep a small canvas margin and let the caption-frame audit reject
            # any actual glyph box that crosses the 1080 px frame.
            cfg.max_width = 970
            cfg.line_gap = 154
            cfg.normal_baseline = 1720
            cfg.highlight_baselines = "1566,1720"
        else:
            if not user_normal_size:
                cfg.normal_size = 59
            if not user_accent_size:
                cfg.accent_size = cfg.normal_size
            if not user_highlight_size:
                cfg.highlight_size = cfg.normal_size
            if not user_max_width:
                cfg.max_width = 560
            if not user_line_gap:
                cfg.line_gap = 70
            if not user_normal_baseline:
                cfg.normal_baseline = 1021
            if not user_highlight_baselines:
                cfg.highlight_baselines = str(cfg.normal_baseline)
        cfg.normal_rgb = (255, 255, 255)
        cfg.accent_rgb = (254, 255, 158)
        cfg.edge_rgb = (43, 42, 38)
        cfg.shadow_rgb = (48, 46, 39)
        cfg.shadow_alpha = 170
        cfg.highlight_shadow_rgb = (34, 33, 30)
        cfg.highlight_shadow_alpha = 105
        cfg.highlight_edge_rgb = (95, 86, 53)
        cfg.highlight_yellow_gradient = ((254, 255, 158, 255), (254, 255, 158, 255))
        cfg.highlight_white_gradient = ((255, 255, 255, 255), (246, 246, 244, 255))
        cfg.text_scale_x = .988
        cfg.text_center_dx = 5.0
    else:
        cfg.normal_rgb = (255, 255, 255)
        cfg.accent_rgb = (255, 228, 64)
        cfg.edge_rgb = (35, 34, 36)
        cfg.shadow_rgb = (12, 12, 14)
        cfg.shadow_alpha = 190
        cfg.highlight_shadow_rgb = cfg.shadow_rgb
        cfg.highlight_shadow_alpha = cfg.shadow_alpha
        cfg.highlight_edge_rgb = (68, 65, 57)
        cfg.highlight_yellow_gradient = ((255, 245, 151, 255), (198, 174, 62, 255))
        cfg.highlight_white_gradient = ((255, 254, 250, 255), (224, 223, 218, 255))
        cfg.text_scale_x = 1.0
        cfg.text_center_dx = 0.0
    if cfg.speed <= 0:
        raise ValueError("--speed must be positive")
    if not cfg.font.exists():
        raise FileNotFoundError(cfg.font)
    if not shutil.which("ffmpeg"):
        raise RuntimeError("ffmpeg is required")
    cfg.out_dir.mkdir(parents=True, exist_ok=True)
    highlight_dir = cfg.out_dir / "highlights"; highlight_dir.mkdir(exist_ok=True)
    cue_dir = cfg.out_dir / "cues"
    if not cfg.skip_normal_layer:
        cue_dir.mkdir(exist_ok=True)

    cues = load_srt(cfg.srt)
    accent_data = load_json(cfg.accent_plan, {"accents": {}})
    accent_map = accent_data.get("accents", accent_data)
    highlight_data = load_json(cfg.highlight_plan, {"highlights": []})
    highlights = highlight_data if isinstance(highlight_data, list) else highlight_data.get("highlights", [])
    suppressed = {int(cue_id) for item in highlights for cue_id in item["cue_ids"]}
    fonts = {
        "normal": variable_font(cfg.font, cfg.normal_size, cfg.weight, cfg.scale),
        "accent": variable_font(cfg.font, cfg.accent_size, cfg.weight, cfg.scale),
        "highlight": variable_font(cfg.font, cfg.highlight_size, cfg.weight, cfg.scale),
    }
    blank = Image.new("RGBA", (cfg.width, cfg.height), (0, 0, 0, 0))
    blank_path = cue_dir / "blank.png"
    if not cfg.skip_normal_layer:
        blank.save(blank_path)

    plan = []
    cue_paths = {}
    for cue in cues:
        accents = list(accent_map.get(str(cue["index"]), accent_map.get(cue["index"], [])))
        if not cfg.skip_normal_layer:
            path = cue_dir / f"cue-{cue['index']:03d}.png"
            (blank if cue["index"] in suppressed else render_caption(cue, accents, cfg, fonts)).save(path)
            cue_paths[cue["index"]] = path
        plan.append({
            "cue": cue["index"], "text": cue["text"],
            "start": round(cue["start"] / cfg.speed, 6),
            "end": round(cue["end"] / cfg.speed, 6),
            "accents": accents, "replaced_by_ck_highlight": cue["index"] in suppressed,
        })

    duration = cfg.duration if cfg.duration is not None else max(item["end"] for item in plan)
    caption_layer = None
    if not cfg.skip_normal_layer:
        segments = []
        cursor = 0.0
        for item in plan:
            if item["start"] > cursor + .001:
                segments.append((item["start"] - cursor, blank_path))
            segments.append((max(.001, item["end"] - item["start"]), cue_paths[item["cue"]]))
            cursor = item["end"]
        if cursor < duration:
            segments.append((duration - cursor, blank_path))
        concat = cfg.out_dir / "caption-images.txt"
        lines = []
        for segment_duration, path in segments:
            lines.extend([f"file '{path.resolve().as_posix()}'", f"duration {segment_duration:.6f}"])
        lines.append(f"file '{segments[-1][1].resolve().as_posix()}'")
        concat.write_text("\n".join(lines) + "\n", encoding="utf-8")
        caption_layer = cfg.out_dir / "caption-layer.mov"
        run([
            "ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
            "-f", "concat", "-safe", "0", "-i", str(concat),
            "-vf", f"fps={float(os.environ.get('CK_CAPTION_LAYER_FPS', cfg.fps)):g},format=argb", "-t", f"{duration:.6f}",
            "-an", "-c:v", "qtrle", "-pix_fmt", "argb", str(caption_layer),
        ])

    cue_by_id = {cue["index"]: cue for cue in cues}
    default_baselines = [int(value.strip()) for value in cfg.highlight_baselines.split(",") if value.strip()]
    resolved = []
    reference_sfx_dir = Path(__file__).resolve().parent.parent / "assets" / "sfx" / "bogouwei-reference"
    reference_sfx = {
        "rise_settle": reference_sfx_dir / "rise_settle.wav",
        "char_toss": reference_sfx_dir / "char_toss.wav",
        "stretch_reveal": reference_sfx_dir / "stretch_reveal.wav",
        "fade_snap": reference_sfx_dir / "fade_snap.wav",
        "light_sweep": reference_sfx_dir / "light_sweep.wav",
        "type_on": reference_sfx_dir / "type_on.wav",
    }
    for item in highlights:
        selected = [cue_by_id[int(index)] for index in item["cue_ids"]]
        start = min(cue["start"] for cue in selected) / cfg.speed
        end = max(cue["end"] for cue in selected) / cfg.speed
        quote_lines = list(item["lines"])
        if item.get("baselines") is not None:
            baselines = list(item["baselines"])
        elif cfg.style_profile == "shenzhai_recap_1080":
            baselines = [1720] if len(quote_lines) == 1 else [1566, 1720]
        else:
            baselines = list(default_baselines)
            if len(quote_lines) == 1 and len(baselines) > 1:
                baselines = [round(sum(baselines) / len(baselines))]
        if len(quote_lines) != len(baselines):
            raise ValueError(f"Highlight {item['id']} has {len(quote_lines)} lines but {len(baselines)} baselines")
        output = highlight_dir / f"{item['id']}.mov"
        template = item.get("template", "legacy_zoom_streak")
        render_highlight(output, end - start, quote_lines, baselines, cfg, fonts["highlight"], template)
        sfx_value = item.get("sfx")
        if sfx_value in (None, "auto") and cfg.style_profile in {"bogouwei_reference", "shenzhai_recap_1080"}:
            candidate = reference_sfx.get(template)
            sfx_value = str(candidate) if candidate and candidate.exists() else None
        elif sfx_value in (False, "none", "off"):
            sfx_value = None
        resolved.append({
            **item, "template": template, "start": round(start, 6), "end": round(end, 6),
            "duration": round(end - start, 6), "file": str(output),
            "file_sha256": sha256(output),
            "sfx_file": sfx_value, "sfx_offset": float(item.get("sfx_offset", 0.0)),
            "sfx_sha256": sha256(Path(sfx_value)) if sfx_value and Path(sfx_value).is_file() else None,
            "sfx_gain_db": float(item.get("sfx_gain_db", 0.0)),
        })

    (cfg.out_dir / "caption-plan.json").write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
    (cfg.out_dir / "highlight-plan-resolved.json").write_text(json.dumps(resolved, ensure_ascii=False, indent=2), encoding="utf-8")
    manifest = {
        "schema": "ck-caption-overlay-inputs-v2",
        "width": cfg.width, "height": cfg.height, "fps": cfg.fps,
        "duration": duration, "speed": cfg.speed,
        "font": str(cfg.font.resolve()), "font_sha256": sha256(cfg.font),
        "srt": str(cfg.srt.resolve()), "srt_sha256": sha256(cfg.srt),
        "accent_plan": str(cfg.accent_plan.resolve()) if cfg.accent_plan else None,
        "accent_plan_sha256": sha256(cfg.accent_plan) if cfg.accent_plan else None,
        "highlight_plan": str(cfg.highlight_plan.resolve()) if cfg.highlight_plan else None,
        "highlight_plan_sha256": sha256(cfg.highlight_plan) if cfg.highlight_plan else None,
        "style_profile": cfg.style_profile,
        "normal_baseline": cfg.normal_baseline,
        "line_gap": cfg.line_gap,
        "highlight_baselines": [int(value.strip()) for value in cfg.highlight_baselines.split(",") if value.strip()],
        "typography": {
            "weight": cfg.weight,
            "normal_size": cfg.normal_size,
            "accent_size": cfg.accent_size,
            "highlight_size": cfg.highlight_size,
            "normal_rgb": list(cfg.normal_rgb),
            "accent_rgb": list(cfg.accent_rgb),
            "highlight_fill_mode": "flat" if cfg.highlight_yellow_gradient[0] == cfg.highlight_yellow_gradient[1] else "gradient",
            "highlight_edge_rgb": list(cfg.highlight_edge_rgb),
            "highlight_shadow_rgb": list(cfg.highlight_shadow_rgb),
            "highlight_shadow_alpha": cfg.highlight_shadow_alpha,
            "text_scale_x": cfg.text_scale_x,
            "text_center_dx": cfg.text_center_dx,
            "optical_center_x": cfg.width / 2 + cfg.text_center_dx,
            "max_width": cfg.max_width,
        },
        "caption_layer": str(caption_layer) if caption_layer else None,
        "normal_caption_source": "locked_ass" if cfg.skip_normal_layer else "transparent_qtrle_layer",
        "highlights": resolved,
    }
    (cfg.out_dir / "overlay-inputs.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"ok": True, "caption_layer": str(caption_layer) if caption_layer else None, "highlights": len(resolved), "duration": duration}, ensure_ascii=False))


if __name__ == "__main__":
    main()
