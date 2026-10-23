import asyncio
import os
import subprocess
import edge_tts
from PIL import Image, ImageDraw, ImageFont

VIDEO_INPUT_PATH = "/Users/ritesh/Downloads/arcmarket.mp4"
OUTPUT_CAPTIONED_VIDEO_PATH = "/Users/ritesh/Downloads/ApexMarkets_Demo_Captioned.mp4"
OUTPUT_CLEAN_VIDEO_PATH = "/Users/ritesh/Downloads/ApexMarkets_Demo_Clean.mp4"

REPO_DEMO_DIR = "/Users/ritesh/Downloads/ArcMarkets/demo"
REPO_AUDIO_PATH = os.path.join(REPO_DEMO_DIR, "apexmarkets_demo_voiceover.mp3")
REPO_NARRATION_PATH = os.path.join(REPO_DEMO_DIR, "narration.txt")
REPO_SRT_PATH = os.path.join(REPO_DEMO_DIR, "apexmarkets_demo_subtitles.srt")
REPO_VTT_PATH = os.path.join(REPO_DEMO_DIR, "apexmarkets_demo_subtitles.vtt")

TOTAL_DURATION_SEC = 68.533

# 9 micro-timed narration cues mapped to the visual actions in the 68.5s demo
RAW_CUES = [
    {
        "id": "1",
        "fixed_start": 0.80,
        "tts_text": "Welcome to ApexMarkets — the premier decentralized prediction platform built natively on Arc Network and settled in USDC.",
        "card_text": "Welcome to ApexMarkets — the premier decentralized prediction platform\nbuilt natively on Arc Network and settled in USDC."
    },
    {
        "id": "2",
        "fixed_start": 9.00,
        "tts_text": "Explore live sports and crypto markets with real-time oracle feeds, dynamic odds multipliers, and instant on-chain settlement.",
        "card_text": "Explore live sports and crypto markets with real-time oracle feeds,\ndynamic odds multipliers, and instant on-chain settlement."
    },
    {
        "id": "3",
        "fixed_start": 16.50,
        "tts_text": "Every market is transparently backed by automated liquidity pools with sub-second finality on Arc.",
        "card_text": "Every market is transparently backed by automated liquidity pools\nwith sub-second finality on Arc."
    },
    {
        "id": "4",
        "fixed_start": 22.80,
        "tts_text": "Seamless network switching enables instant connection to Arc Mainnet with near-zero gas fees.",
        "card_text": "Seamless network switching enables instant connection to Arc Mainnet\nwith near-zero gas fees."
    },
    {
        "id": "5",
        "fixed_start": 29.00,
        "tts_text": "Meet our autonomous AI Betting Agent. It monitors markets 24/7 and executes disciplined Kelly Criterion sizing.",
        "card_text": "Meet our autonomous AI Betting Agent — monitoring markets 24/7\nand executing disciplined Kelly Criterion sizing."
    },
    {
        "id": "6",
        "fixed_start": 37.00,
        "tts_text": "Traders can configure custom risk profiles, allocate non-custodial escrow budgets, and stream live execution logs.",
        "card_text": "Traders can configure custom risk profiles,\nallocate non-custodial escrow budgets, and stream live execution logs."
    },
    {
        "id": "7",
        "fixed_start": 46.50,
        "tts_text": "Every prediction is verified on the Arc Explorer — calling smart contracts and minting verifiable receipt tokens.",
        "card_text": "Every prediction is verified on the Arc Explorer —\ncalling smart contracts and minting verifiable receipt tokens."
    },
    {
        "id": "8",
        "fixed_start": 54.50,
        "tts_text": "Track active prediction slips, live PnL, and claim winnings directly from your unified trader portfolio.",
        "card_text": "Track active prediction slips, live PnL,\nand claim winnings directly from your unified trader portfolio."
    },
    {
        "id": "9",
        "fixed_start": 61.20,
        "tts_text": "Compete on the global on-chain leaderboard. Experience the future of intelligent predictions with ApexMarkets on Arc.",
        "card_text": "Compete on the global on-chain leaderboard.\nExperience the future of intelligent predictions with ApexMarkets on Arc."
    }
]

def format_timestamp_srt(seconds):
    millis = int(round((seconds - int(seconds)) * 1000))
    if millis >= 1000:
        millis = 999
    hours = int(seconds) // 3600
    minutes = (int(seconds) % 3600) // 60
    secs = int(seconds) % 60
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

def format_timestamp_vtt(seconds):
    millis = int(round((seconds - int(seconds)) * 1000))
    if millis >= 1000:
        millis = 999
    hours = int(seconds) // 3600
    minutes = (int(seconds) % 3600) // 60
    secs = int(seconds) % 60
    return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millis:03d}"

def generate_caption_card(text, out_path):
    font_path = "/System/Library/Fonts/SFNS.ttf"
    font = ImageFont.truetype(font_path, 52)
    lines = text.split("\n")
    
    dummy = Image.new("RGBA", (1, 1))
    draw = ImageDraw.Draw(dummy)
    boxes = [draw.textbbox((0, 0), l, font=font) for l in lines]
    widths = [b[2] - b[0] for b in boxes]
    heights = [b[3] - b[1] for b in boxes]
    max_w = max(widths)
    line_sp = 14
    total_h = sum(heights) + (len(lines) - 1) * line_sp
    pad_x, pad_y = 52, 22
    bw = max_w + pad_x * 2
    bh = total_h + pad_y * 2
    
    card = Image.new("RGBA", (bw, bh), (0, 0, 0, 0))
    cd = ImageDraw.Draw(card)
    cd.rounded_rectangle(
        [(0, 0), (bw - 1, bh - 1)],
        radius=24,
        fill=(8, 14, 28, 235),
        outline=(255, 255, 255, 45),
        width=2
    )
    cy = pad_y
    for i, l in enumerate(lines):
        lx = (bw - widths[i]) // 2
        # Drop shadow for readability
        cd.text((lx + 2, cy + 2), l, font=font, fill=(0, 0, 0, 200))
        # Crisp white text
        cd.text((lx, cy), l, font=font, fill=(255, 255, 255, 255))
        cy += heights[i] + line_sp
        
    card.save(out_path)

async def main():
    temp_dir = "/tmp/apexmarkets_demo_pipeline"
    os.makedirs(temp_dir, exist_ok=True)
    os.makedirs(REPO_DEMO_DIR, exist_ok=True)
    
    print("=== Step 1: Synthesizing Audio Cues with Edge TTS ===")
    voice = "en-US-AndrewNeural"
    scheduled_cues = []
    
    for cue in RAW_CUES:
        cue_file = os.path.join(temp_dir, f"cue_{cue['id']}.mp3")
        communicate = edge_tts.Communicate(cue["tts_text"], voice, rate="+10%")
        await communicate.save(cue_file)
        
        res = subprocess.run([
            "ffprobe", "-v", "error", "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1", cue_file
        ], capture_output=True, text=True)
        dur = float(res.stdout.strip())
        start = cue["fixed_start"]
        end = min(start + dur, TOTAL_DURATION_SEC)
        
        scheduled_cues.append({
            "id": cue["id"],
            "file": cue_file,
            "start": start,
            "end": end,
            "dur": dur,
            "card_text": cue["card_text"],
            "tts_text": cue["tts_text"]
        })
        print(f"Cue {cue['id']:2s}: {start:5.2f}s -> {end:5.2f}s (dur: {dur:4.2f}s) | {cue['tts_text']}")
        
    print("\n=== Step 2: Generating Subtitles (SRT & VTT) & Narration Doc ===")
    srt_lines = []
    vtt_lines = ["WEBVTT\n"]
    narration_entries = []
    
    for i, c in enumerate(scheduled_cues):
        clean_text = c["card_text"].replace("\n", " ")
        narration_entries.append(f"[{format_timestamp_srt(c['start'])} --> {format_timestamp_srt(c['end'])}]\n{clean_text}")
        
        srt_lines.append(f"{i+1}")
        srt_lines.append(f"{format_timestamp_srt(c['start'])} --> {format_timestamp_srt(c['end'])}")
        srt_lines.append(clean_text + "\n")
        
        vtt_lines.append(f"{i+1}")
        vtt_lines.append(f"{format_timestamp_vtt(c['start'])} --> {format_timestamp_vtt(c['end'])}")
        vtt_lines.append(clean_text + "\n")
        
    with open(REPO_SRT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(srt_lines))
    print(f"Saved: {REPO_SRT_PATH}")
    
    with open(REPO_VTT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(vtt_lines))
    print(f"Saved: {REPO_VTT_PATH}")
    
    with open(REPO_NARRATION_PATH, "w", encoding="utf-8") as f:
        f.write("# ApexMarkets Arc Network Demo Narration (68.5s)\n\n" + "\n\n".join(narration_entries) + "\n")
    print(f"Saved: {REPO_NARRATION_PATH}")
    
    print("\n=== Step 3: Mixing Master Audio Track with FFmpeg ===")
    ffmpeg_inputs = [
        "-f", "lavfi",
        "-i", f"anullsrc=r=48000:cl=stereo:d={TOTAL_DURATION_SEC}"
    ]
    filter_parts = []
    mix_inputs = ["[0:a]"]
    
    for i, s in enumerate(scheduled_cues):
        ffmpeg_inputs.extend(["-i", s["file"]])
        input_idx = i + 1
        delay_ms = int(round(s["start"] * 1000))
        filter_parts.append(f"[{input_idx}:a]aresample=48000,adelay=delays={delay_ms}:all=1[a{input_idx}]")
        mix_inputs.append(f"[a{input_idx}]")
        
    num_inputs = len(mix_inputs)
    filter_parts.append(f"{''.join(mix_inputs)}amix=inputs={num_inputs}:duration=first:dropout_transition=0:normalize=0[voice_out]")
    filter_complex_str = ";".join(filter_parts)
    
    voice_track_wav = os.path.join(temp_dir, "master_voice.wav")
    mix_cmd = [
        "ffmpeg", "-y",
        *ffmpeg_inputs,
        "-filter_complex", filter_complex_str,
        "-map", "[voice_out]",
        "-c:a", "pcm_s16le",
        voice_track_wav
    ]
    subprocess.run(mix_cmd, check=True)
    print(f"Exported master voice WAV: {voice_track_wav}")
    
    # Save MP3 version in repo
    subprocess.run([
        "ffmpeg", "-y",
        "-i", voice_track_wav,
        "-c:a", "libmp3lame",
        "-b:a", "192k",
        REPO_AUDIO_PATH
    ], check=True)
    print(f"Exported repo MP3: {REPO_AUDIO_PATH}")
    
    print("\n=== Step 4: Rendering Glassmorphic Subtitle Cards ===")
    caption_images = []
    for i, c in enumerate(scheduled_cues):
        card_file = os.path.join(temp_dir, f"caption_{i:02d}.png")
        generate_caption_card(c["card_text"], card_file)
        caption_images.append((card_file, c["start"], c["end"]))
    print(f"Rendered {len(caption_images)} high-resolution caption cards.")
    
    print("\n=== Step 5: Building Clean Synced Video (AAC Audio + Embedded CC Track) ===")
    clean_cmd = [
        "ffmpeg", "-y",
        "-i", VIDEO_INPUT_PATH,
        "-i", voice_track_wav,
        "-i", REPO_SRT_PATH,
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "192k",
        "-c:s", "mov_text",
        "-metadata:s:s:0", "language=eng",
        "-metadata:s:s:0", "handler_name=English",
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-map", "2:s:0",
        "-t", str(TOTAL_DURATION_SEC),
        OUTPUT_CLEAN_VIDEO_PATH
    ]
    subprocess.run(clean_cmd, check=True)
    print(f"Clean Video saved: {OUTPUT_CLEAN_VIDEO_PATH}")
    
    print("\n=== Step 6: Burning in Subtitles with Apple Silicon Videotoolbox ===")
    overlay_inputs = ["-i", VIDEO_INPUT_PATH]
    overlay_filter_parts = []
    
    for i, (card_file, start, end) in enumerate(caption_images):
        overlay_inputs.extend(["-i", card_file])
        input_idx = i + 1
        prev_node = f"[v{i}]" if i > 0 else "[0:v]"
        out_node = f"[v{i+1}]" if i < len(caption_images) - 1 else "[vcaptioned]"
        # Center horizontally, place 60px above bottom edge
        overlay_filter_parts.append(
            f"{prev_node}[{input_idx}:v]overlay=x=(W-w)/2:y=H-h-60:enable='between(t,{start:.2f},{end:.2f})'{out_node}"
        )
        
    overlay_filter_str = ";".join(overlay_filter_parts)
    
    caption_cmd = [
        "ffmpeg", "-y",
        *overlay_inputs,
        "-i", voice_track_wav,
        "-filter_complex", overlay_filter_str,
        "-map", "[vcaptioned]",
        "-map", f"{len(caption_images) + 1}:a",
        "-c:v", "h264_videotoolbox",
        "-b:v", "16M",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-t", str(TOTAL_DURATION_SEC),
        OUTPUT_CAPTIONED_VIDEO_PATH
    ]
    subprocess.run(caption_cmd, check=True)
    print(f"Captioned Video saved: {OUTPUT_CAPTIONED_VIDEO_PATH}")
    print("\n=== Pipeline Complete! Both Demo Videos Ready in Downloads! ===")

if __name__ == "__main__":
    asyncio.run(main())
