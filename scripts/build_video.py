import random
import subprocess
from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parent.parent

MEMES_DIR = BASE_DIR / "videos" / "memes"
FRONTDESK_DIR = BASE_DIR / "videos" / "frontdesk"
CONTENT_DIR = BASE_DIR / "videos" / "content"

OUTPUT_FILE = BASE_DIR / "output.mp4"
VIDEO_TYPE_FILE = BASE_DIR / "video_type.txt"
SELECTED_FILES_FILE = BASE_DIR / "selected_files.txt"

VIDEO_EXTS = {".mp4", ".mov", ".m4v", ".webm", ".mkv", ".avi"}

TARGET_WIDTH = 1080
TARGET_HEIGHT = 1920
TARGET_FPS = 30
TARGET_AUDIO_RATE = 48000


def get_videos(folder: Path) -> list[Path]:
    if not folder.exists():
        raise FileNotFoundError(f"Folder does not exist: {folder}")

    files = [
        p for p in folder.iterdir()
        if p.is_file() and p.suffix.lower() in VIDEO_EXTS
    ]

    if not files:
        raise FileNotFoundError(f"No video files found in: {folder}")

    return sorted(files)


def choose_video_type() -> str:
    return random.choice(["frontdesk"])
    # If you want more frontdesk videos later:
    # return random.choices(["frontdesk", "content"], weights=[70, 30], k=1)[0]


def get_video_folder(video_type: str) -> Path:
    if video_type == "frontdesk":
        return FRONTDESK_DIR
    if video_type == "content":
        return CONTENT_DIR
    raise ValueError(f"Unsupported video type: {video_type}")


def run_ffmpeg(meme_path: Path, main_video_path: Path, output_path: Path) -> None:
    video_norm = (
        f"scale={TARGET_WIDTH}:{TARGET_HEIGHT}:force_original_aspect_ratio=decrease,"
        f"pad={TARGET_WIDTH}:{TARGET_HEIGHT}:(ow-iw)/2:(oh-ih)/2,"
        f"fps={TARGET_FPS},setsar=1,format=yuv420p"
    )

    filter_complex = (
        f"[0:v]{video_norm}[v0];"
        f"[1:v]{video_norm}[v1];"
        f"[0:a]aresample={TARGET_AUDIO_RATE},aformat=sample_rates={TARGET_AUDIO_RATE}:"
        f"channel_layouts=stereo[a0];"
        f"[1:a]aresample={TARGET_AUDIO_RATE},aformat=sample_rates={TARGET_AUDIO_RATE}:"
        f"channel_layouts=stereo[a1];"
        f"[v0][a0][v1][a1]concat=n=2:v=1:a=1[outv][outa]"
    )

    cmd = [
        "ffmpeg",
        "-y",
        "-i", str(meme_path),
        "-i", str(main_video_path),
        "-filter_complex", filter_complex,
        "-map", "[outv]",
        "-map", "[outa]",
        "-c:v", "libx264",
        "-profile:v", "high",
        "-level", "4.1",
        "-pix_fmt", "yuv420p",
        "-r", str(TARGET_FPS),
        "-movflags", "+faststart",
        "-c:a", "aac",
        "-ar", str(TARGET_AUDIO_RATE),
        "-ac", "2",
        "-b:a", "128k",
        "-preset", "veryfast",
        "-crf", "23",
        str(output_path),
    ]

    subprocess.run(cmd, check=True)


def write_video_type(video_type: str) -> None:
    VIDEO_TYPE_FILE.write_text(video_type, encoding="utf-8")


def write_selected_files(meme_path: Path, main_video_path: Path, video_type: str) -> None:
    contents = (
        f"video_type={video_type}\n"
        f"meme_file={meme_path.name}\n"
        f"main_video_file={main_video_path.name}\n"
    )
    SELECTED_FILES_FILE.write_text(contents, encoding="utf-8")


def main() -> None:
    try:
        memes = get_videos(MEMES_DIR)

        video_type = choose_video_type()
        main_video_folder = get_video_folder(video_type)
        main_videos = get_videos(main_video_folder)

        chosen_meme = random.choice(memes)
        chosen_main_video = random.choice(main_videos)

        print(f"Selected video type: {video_type}")
        print(f"Selected meme: {chosen_meme.name}")
        print(f"Selected main video: {chosen_main_video.name}")

        run_ffmpeg(chosen_meme, chosen_main_video, OUTPUT_FILE)

        if not OUTPUT_FILE.exists():
            print("output.mp4 was not created.", file=sys.stderr)
            sys.exit(1)

        write_video_type(video_type)
        write_selected_files(chosen_meme, chosen_main_video, video_type)

        print(f"Created: {OUTPUT_FILE}")
        print(f"Created: {VIDEO_TYPE_FILE}")
        print(f"Created: {SELECTED_FILES_FILE}")

    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()