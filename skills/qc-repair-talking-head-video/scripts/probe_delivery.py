#!/usr/bin/env python3
import argparse, json, re, subprocess, tempfile
from pathlib import Path

def run(cmd):
    return subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def main():
    ap=argparse.ArgumentParser(description="Decode and probe a final talking-head delivery.")
    ap.add_argument("video", type=Path)
    ap.add_argument("--target-lufs", type=float, default=-22.0)
    ap.add_argument("--true-peak", type=float, default=-1.5)
    ap.add_argument("--loudness-tolerance", type=float, default=1.0)
    ap.add_argument("--black-min", type=float, default=0.25)
    ap.add_argument("--silence-min", type=float, default=0.30)
    ap.add_argument("--json-out", type=Path)
    args=ap.parse_args(); video=args.video.resolve()
    probe=run(["ffprobe","-v","error","-show_streams","-show_format","-of","json",str(video)])
    meta=json.loads(probe.stdout) if probe.returncode==0 else {}
    decode=run(["ffmpeg","-v","error","-i",str(video),"-f","null","-"])
    analysis=run(["ffmpeg","-hide_banner","-nostats","-i",str(video),"-af",
                  f"loudnorm=I={args.target_lufs}:TP={args.true_peak}:LRA=7:print_format=json,"
                  f"silencedetect=n=-45dB:d={args.silence_min}",
                  "-vf",f"blackdetect=d={args.black_min}:pix_th=0.10","-f","null","-"])
    text=analysis.stderr
    blocks=re.findall(r"\{\s*\"input_i\".*?\}",text,re.S)
    loud=json.loads(blocks[-1]) if blocks else {}
    def num(key):
        try:return float(loud[key])
        except:return None
    silences=[{"start":float(a),"end":float(b),"duration":float(c)} for a,b,c in
              re.findall(r"silence_start: ([\d.]+).*?silence_end: ([\d.]+) \| silence_duration: ([\d.]+)",text,re.S)]
    blacks=[{"start":float(a),"end":float(b),"duration":float(c)} for a,b,c in
            re.findall(r"black_start:([\d.]+) black_end:([\d.]+) black_duration:([\d.]+)",text)]
    streams=meta.get("streams",[]); has_video=any(x.get("codec_type")=="video" for x in streams)
    has_audio=any(x.get("codec_type")=="audio" for x in streams)
    li=num("input_i"); tp=num("input_tp")
    checks={"probe_ok":probe.returncode==0,"decode_ok":decode.returncode==0 and not decode.stderr.strip(),
            "video_stream_present":has_video,"audio_stream_present":has_audio,
            "loudness_near_target":li is not None and abs(li-args.target_lufs)<=args.loudness_tolerance,
            "true_peak_ok":tp is not None and tp<=args.true_peak+0.15,"black_sequence_free":not blacks}
    report={"video":str(video),"passed":all(checks.values()),"checks":checks,"probe":meta,
            "loudness":loud,"silence_events":silences,"black_events":blacks,"decode_errors":decode.stderr.strip()}
    if args.json_out:
        args.json_out.parent.mkdir(parents=True,exist_ok=True)
        args.json_out.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(report,ensure_ascii=False,indent=2))
    raise SystemExit(0 if report["passed"] else 1)

if __name__=="__main__": main()
