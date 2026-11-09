import argparse
import sys
from pathlib import Path

try:
    import yt_dlp
except ImportError:
    print("Error: 'yt-dlp' no está instalado. Ejecuta: pip install yt-dlp")
    sys.exit(1)

# Carpetas de destino
BASE_DIR = Path(__file__).resolve().parent
DOWNLOADS_DIR = BASE_DIR / "descargas"
MUSIC_DIR = DOWNLOADS_DIR / "musica"
VIDEO_DIR = DOWNLOADS_DIR / "videos"


def get_audio_options() -> dict:
    """Configuración para descargar audio en formato MP3 con carátula y metadatos."""
    MUSIC_DIR.mkdir(parents=True, exist_ok=True)
    return {
        "format": "bestaudio/best",
        "outtmpl": str(MUSIC_DIR / "%(title)s.%(ext)s"),
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "320",
            },
            {
                "key": "FFmpegMetadata",
                "add_metadata": True,
            },
            {
                "key": "EmbedThumbnail",
            },
        ],
        "writethumbnail": True,
        "quiet": False,
        "no_warnings": False,
    }


def get_video_options() -> dict:
    """Configuración para descargar video en la mejor calidad combinando video + audio en MP4."""
    VIDEO_DIR.mkdir(parents=True, exist_ok=True)
    return {
        "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best",
        "outtmpl": str(VIDEO_DIR / "%(title)s.%(ext)s"),
        "merge_output_format": "mp4",
        "postprocessors": [
            {
                "key": "FFmpegMetadata",
                "add_metadata": True,
            }
        ],
        "quiet": False,
        "no_warnings": False,
    }


def download(url: str, mode: str) -> bool:
    """Descarga el contenido según el modo seleccionado ('audio' o 'video')."""
    if mode == "audio":
        print("\n🎵 Iniciando descarga de Audio (MP3 a 320kbps)...")
        options = get_audio_options()
        dest_folder = MUSIC_DIR
    elif mode == "video":
        print("\n🎬 Iniciando descarga de Video (MP4 en máxima resolución)...")
        options = get_video_options()
        dest_folder = VIDEO_DIR
    else:
        print("[!] Modo de descarga no reconocido.")
        return False

    try:
        with yt_dlp.YoutubeDL(options) as ydl:
            ydl.download([url])
        print(f"\n[✓] Descarga completada con éxito.")
        print(f"[📂] Archivo guardado en: {dest_folder}\n")
        return True
    except yt_dlp.utils.DownloadError as e:
        print(f"\n[✗] Error en la descarga: {e}\n")
        return False
    except Exception as e:
        print(f"\n[✗] Ocurrió un error inesperado: {e}\n")
        return False


def interactive_menu():
    """Menú interactivo por consola."""
    print("=" * 55)
    print("      DESCARGADOR DE YOUTUBE CON YT-DLP")
    print("=" * 55)

    while True:
        url = input("Ingresa la URL del video o canción (o 'q' para salir): ").strip()
        if not url:
            continue
        if url.lower() in ("q", "quit", "salir", "exit"):
            print("¡Hasta luego!")
            break

        print("\n¿Qué deseas descargar?")
        print("1) Solo Audio (MP3 320kbps)")
        print("2) Video Completo (MP4 Mejor Calidad)")
        print("3) Cancelar")

        choice = input("Selecciona una opción (1-3): ").strip()

        if choice == "1":
            download(url, "audio")
        elif choice == "2":
            download(url, "video")
        elif choice == "3":
            print("Operación cancelada.\n")
        else:
            print("Opción no válida. Inténtalo de nuevo.\n")


def main():
    parser = argparse.ArgumentParser(
        description="Descarga música (MP3) o video (MP4) desde YouTube usando yt-dlp."
    )
    parser.add_argument("url", nargs="?", help="URL del video de YouTube")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-a", "--audio", action="store_true", help="Descargar únicamente el audio en formato MP3")
    group.add_argument("-v", "--video", action="store_true", help="Descargar el video en formato MP4")

    args = parser.parse_args()

    if args.url:
        if args.audio:
            download(args.url, "audio")
        elif args.video:
            download(args.url, "video")
        else:
            # Si se pasa la URL pero no la opción, preguntar
            print("\nURL recibida. ¿Qué formato prefieres?")
            print("1) Audio MP3")
            print("2) Video MP4")
            c = input("Opción (1 o 2): ").strip()
            if c == "1":
                download(args.url, "audio")
            elif c == "2":
                download(args.url, "video")
            else:
                print("Opción cancelada.")
    else:
        # Modo interactivo
        interactive_menu()


if __name__ == "__main__":
    main()

