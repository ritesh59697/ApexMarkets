import asyncio
import os
import subprocess
import edge_tts
from PIL import Image, ImageDraw, ImageFont

VIDEO_INPUT_PATH = "/Users/ritesh/Downloads/apex2.mp4"
OUTPUT_CAPTIONED_VIDEO_PATH = "/Users/ritesh/Downloads/ApexMarkets_Demo_Captioned.mp4"
OUTPUT_CLEAN_VIDEO_PATH = "/Users/ritesh/Downloads/ApexMarkets_Demo_Clean.mp4"

REPO_DEMO_DIR = "/Users/ritesh/Downloads/ArcMarkets/demo"
REPO_AUDIO_PATH = os.path.join(REPO_DEMO_DIR, "apexmarkets_demo_voiceover.mp3")
REPO_NARRATION_PATH = os.path.join(REPO_DEMO_DIR, "narration.txt")
REPO_SRT_PATH = os.path.join(REPO_DEMO_DIR, "apexmarkets_demo_subtitles.srt")
REPO_VTT_PATH = os.path.join(REPO_DEMO_DIR, "apexmarkets_demo_subtitles.vtt")

TOTAL_DURATION_SEC = 77.183

# 8 micro-timed narration cues mapped to the visual actions in the 77.2s demo
RAW_CUES = [
    {
        "id": "1",
        "fixed_start": 1.00,
        "tts_text": "ApexMarkets is a decentralized prediction protocol built on Arc Network using Arc Studio. Here is our project workspace running the live dev preview.",
        "card_text": "ApexMarkets: Decentralized prediction protocol built on Arc Network using Arc Studio.\nHere is our project workspace running the live dev preview."
    },
    {
        "id": "2",
        "fixed_start": 13.00,
        "tts_text": "Using Arc Studio's onchain AI agent, we scaffolded and tested PredictionMarket.sol and BetReceiptNFT.sol, optimized for native USDC gas.",
        "card_text": "Using Arc Studio's onchain AI agent, we scaffolded and tested\nPredictionMarket.sol & BetReceiptNFT.sol, optimized for native USDC gas."
    },
    {
        "id": "3",
        "fixed_start": 22.50,
        "tts_text": "Arc Studio executed unit tests and launched our Next.js frontend right inside the container sandbox.",
        "card_text": "Arc Studio executed unit tests and launched our Next.js frontend\nright inside the container sandbox."
    },
    {
        "id": "4",
        "fixed_start": 29.50,
        "tts_text": "Switching to our live app on Vercel, users access real-time sports and crypto fixtures with dynamic parimutuel pools.",
        "card_text": "Switching to our live app on Vercel, users access real-time\nsports & crypto fixtures with dynamic parimutuel pools."
    },
    {
        "id": "5",
        "fixed_start": 38.50,
        "tts_text": "Participants wager natively in USDC, minting an on-chain SVG NFT receipt for every prediction.",
        "card_text": "Participants wager natively in USDC,\nminting an on-chain SVG NFT receipt for every prediction."
    },
    {
        "id": "6",
        "fixed_start": 48.50,
        "tts_text": "Here is our confirmed transaction on Arc Mainnet Explorer, moving real USDC with instant finality.",
        "card_text": "Here is our confirmed transaction on Arc Mainnet Explorer,\nmoving real USDC with instant finality."
    },
    {
        "id": "7",
        "fixed_start": 56.50,
        "tts_text": "In the AI Agent tab, users can escrow USDC to an autonomous agent sizing bets via the Kelly Criterion, with instant revocation rights.",
        "card_text": "In the AI Agent tab, users can escrow USDC to an autonomous agent\nsizing bets via the Kelly Criterion, with instant revocation rights."
    },
    {
        "id": "8",
        "fixed_start": 67.50,
        "tts_text": "The on-chain leaderboard tracks realized profits transparently. ApexMarkets built on Arc Network. Thanks for watching!",
        "card_text": "The on-chain leaderboard tracks realized profits transparently.\nApexMarkets built on Arc Network. Thanks for watching!"
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
    temp_dir = "/tmp/apexmarkets_demo_pipeline_v2"
    os.makedirs(temp_dir, exist_ok=True)
    os.makedirs(REPO_DEMO_DIR, exist_ok=True)
    
    print("=== Step 1: Synthesizing Audio Cues with Edge TTS ===")
    voice = "en-US-AndrewNeural"
    scheduled_cues = []
    
    for cue in RAW_CUES:
        cue_file = os.path.join(temp_dir, f"cue_{cue['id']}.mp3")
        communicate = edge_tts.Communicate(cue["tts_text"], voice, rate="+12%")
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
        f.write("# ApexMarkets Arc Network & Arc Studio Demo Narration (77.2s)\n\n" + "\n\n".join(narration_entries) + "\n")
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
    print(f"Mixed voice track: {voice_track_wav}")
    
    # Save MP3 version for repo demo folder
    subprocess.run([
        "ffmpeg", "-y", "-i", voice_track_wav,
        "-c:a", "libmp3lame", "-b:a", "192k",
        REPO_AUDIO_PATH
    ], check=True)
    print(f"Saved demo audio: {REPO_AUDIO_PATH}")
    
    print("\n=== Step 4: Generating PNG Subtitle Cards with Pillow ===")
    cards_info = []
    for c in scheduled_cues:
        card_png = os.path.join(temp_dir, f"card_{c['id']}.png")
        generate_caption_card(c["card_text"], card_png)
        cards_info.append({
            "id": c["id"],
            "path": card_png,
            "start": c["start"],
            "end": c["end"]
        })
    print(f"Generated {len(cards_info)} caption cards.")
    
    print("\n=== Step 5: Rendering Master Clean Video ===")
    clean_cmd = [
        "ffmpeg", "-y",
        "-i", VIDEO_INPUT_PATH,
        "-i", voice_track_wav,
        "-map", "0:v:0",
        "-map", "1:a:0",
        "-c:v", "h264_videotoolbox",
        "-b:v", "14M",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        OUTPUT_CLEAN_VIDEO_PATH
    ]
    subprocess.run(clean_cmd, check=True)
    print(f"Clean Video Rendered: {OUTPUT_CLEAN_VIDEO_PATH}")
    
    print("\n=== Step 6: Rendering Master Captioned Video with Burned-In Cards ===")
    cap_inputs = [
        "-i", VIDEO_INPUT_PATH,
        "-i", voice_track_wav
    ]
    for card in cards_info:
        cap_inputs.extend(["-i", card["path"]])
        
    overlay_filters = ["[0:v]null[v0]"]
    for i, card in enumerate(cards_info):
        card_input_idx = i + 2
        prev_v = f"v{i}"
        next_v = f"v{i+1}"
        # Position card centered horizontally, 100px from the bottom
        overlay_filters.append(
            f"[{prev_v}][{card_input_idx}:v]overlay="
            f"(W-w)/2:H-h-100:"
            f"enable='between(t,{card['start']:.2f},{card['end']:.2f})'"
            f"[{next_v}]"
        )
        
    last_v = f"v{len(cards_info)}"
    cap_filter_str = ";".join(overlay_filters)
    
    captioned_cmd = [
        "ffmpeg", "-y",
        *cap_inputs,
        "-filter_complex", cap_filter_str,
        "-map", f"[{last_v}]",
        "-map", "1:a:0",
        "-c:v", "h264_videotoolbox",
        "-b:v", "14M",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        OUTPUT_CAPTIONED_VIDEO_PATH
    ]
    subprocess.run(captioned_cmd, check=True)
    print(f"Master Captioned Video Rendered: {OUTPUT_CAPTIONED_VIDEO_PATH}")
    print("\n🎉 PRODUCTION PIPELINE COMPLETE!")

if __name__ == "__main__":
    asyncio.run(main())
