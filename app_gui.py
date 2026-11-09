"""
YouTube Downloader Pro - Interfaz Gráfica Moderna y Limpia
Desarrollada con CustomTkinter, yt-dlp, FFmpeg y Pillow.
"""
import io
import os
import re
import sys
import threading
import urllib.request
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
from PIL import Image, ImageDraw, ImageTk

# Identificador de aplicación para Windows (asegura que el icono aparezca en la barra de tareas)
if sys.platform == "win32":
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            "com.pedro.youtubedownloader.gui.v2"
        )
    except Exception:
        pass

try:
    import yt_dlp
except ImportError:
    messagebox.showerror(
        "Error", "yt-dlp no está instalado.\nEjecuta: pip install yt-dlp"
    )
    sys.exit(1)

# Configuración de diseño y paleta de colores moderna (Obsidian & YouTube Red)
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

THEME = {
    "bg": "#111215",
    "card_bg": "#181A20",
    "card_border": "#262933",
    "input_bg": "#20232B",
    "accent": "#FF2A44",
    "accent_hover": "#E01E38",
    "secondary": "#2A2D37",
    "secondary_hover": "#353945",
    "text_primary": "#FFFFFF",
    "text_secondary": "#9CA3AF",
    "success": "#10B981",
    "info": "#3B82F6",
}

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DOWNLOAD_DIR = BASE_DIR / "descargas"


def get_resource_path(relative_path: str) -> Path:
    """Obtiene la ruta absoluta a un recurso, funcionando en modo desarrollo y en ejecutable PyInstaller."""
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS) / relative_path
    return BASE_DIR / relative_path


def make_rounded_image(img: Image.Image, size: tuple, radius: int = 10) -> Image.Image:
    """Redimensiona una imagen y le aplica esquinas redondeadas."""
    img = img.resize(size, Image.Resampling.LANCZOS).convert("RGBA")
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle([0, 0, size[0], size[1]], radius=radius, fill=255)
    rounded = Image.new("RGBA", size, (0, 0, 0, 0))
    rounded.paste(img, (0, 0), mask)
    return rounded


class DownloaderApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("YouTube Downloader Pro - Música y Video")
        self.geometry("760x820")
        self.minsize(700, 750)
        self.configure(fg_color=THEME["bg"])

        # Iconos nativos
        self._setup_icons()

        # Variables de estado
        self.download_path = tk.StringVar(value=str(DEFAULT_DOWNLOAD_DIR))
        self.download_type = tk.StringVar(value="video")  # "video" o "audio"
        self.selected_format = tk.StringVar(value="MP4")
        self.selected_quality = tk.StringVar(value="Máxima resolución")
        self.embed_metadata = tk.BooleanVar(value=True)

        self.is_downloading = False
        self.is_fetching_info = False
        self.last_fetched_url = ""
        self.current_video_info = None
        self.last_downloaded_file = None

        self._build_ui()
        self._on_type_changed("🎬 Video (MP4 / MKV)")

    def _setup_icons(self):
        """Aplica el logotipo como icono de la ventana."""
        self._apply_delayed_icon()
        self.after(150, self._apply_delayed_icon)

    def _apply_delayed_icon(self):
        ico_path = get_resource_path("assets/icon.ico")
        png_path = get_resource_path("assets/logo_64.png")

        if sys.platform == "win32" and ico_path.exists():
            try:
                self.iconbitmap(str(ico_path))
                return
            except Exception:
                pass

        if png_path.exists():
            try:
                self._app_icon_tk = ImageTk.PhotoImage(file=str(png_path))
                self.iconphoto(False, self._app_icon_tk)
            except Exception:
                pass

    def _build_ui(self):
        # 1. Cabecera principal moderna
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=30, pady=(24, 16))

        # Logotipo de la app
        logo_path = get_resource_path("assets/logo.png")
        if logo_path.exists():
            try:
                logo_pil = Image.open(logo_path)
                self.logo_ctk = ctk.CTkImage(
                    light_image=logo_pil,
                    dark_image=logo_pil,
                    size=(52, 52),
                )
                logo_label = ctk.CTkLabel(header_frame, image=self.logo_ctk, text="")
                logo_label.pack(side="left", padx=(0, 14))
            except Exception:
                pass

        title_box = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_box.pack(side="left", fill="both", expand=True)

        app_title = ctk.CTkLabel(
            title_box,
            text="YouTube Downloader",
            font=ctk.CTkFont(family="Segoe UI", size=22, weight="bold"),
            text_color=THEME["text_primary"],
        )
        app_title.pack(anchor="w")

        app_subtitle = ctk.CTkLabel(
            title_box,
            text="Descarga música en alta calidad o videos en máxima resolución con yt-dlp",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=THEME["text_secondary"],
        )
        app_subtitle.pack(anchor="w")

        # Botón Acerca de estilo píldora
        about_btn = ctk.CTkButton(
            header_frame,
            text="ℹ Acerca de",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            width=96,
            height=34,
            corner_radius=17,
            fg_color=THEME["secondary"],
            hover_color=THEME["secondary_hover"],
            text_color=THEME["text_primary"],
            command=self._show_about_dialog,
        )
        about_btn.pack(side="right")

        # Contenedor desplazable para adaptarse a cualquier resolución de pantalla
        scroll_container = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            corner_radius=0,
        )
        scroll_container.pack(fill="both", expand=True, padx=20, pady=(0, 15))

        # --- TARJETA 1: Entrada de URL y Vista Previa ---
        url_card = ctk.CTkFrame(
            scroll_container,
            fg_color=THEME["card_bg"],
            border_color=THEME["card_border"],
            border_width=1,
            corner_radius=14,
        )
        url_card.pack(fill="x", padx=10, pady=(0, 14))

        url_card_header = ctk.CTkFrame(url_card, fg_color="transparent")
        url_card_header.pack(fill="x", padx=20, pady=(16, 8))

        url_title = ctk.CTkLabel(
            url_card_header,
            text="Enlace de YouTube",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color=THEME["text_primary"],
        )
        url_title.pack(side="left")

        # Caja de entrada de texto
        input_box = ctk.CTkFrame(url_card, fg_color=THEME["input_bg"], corner_radius=10)
        input_box.pack(fill="x", padx=20, pady=(0, 12))

        self.url_entry = ctk.CTkEntry(
            input_box,
            placeholder_text="https://www.youtube.com/watch?v=...",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            fg_color="transparent",
            border_width=0,
            height=42,
        )
        self.url_entry.pack(side="left", fill="x", expand=True, padx=(12, 8))
        self.url_entry.bind("<KeyRelease>", self._on_url_keyrelease)

        paste_btn = ctk.CTkButton(
            input_box,
            text="Pegar",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            width=70,
            height=32,
            corner_radius=8,
            fg_color=THEME["accent"],
            hover_color=THEME["accent_hover"],
            command=self._paste_clipboard,
        )
        paste_btn.pack(side="left", padx=(0, 6))

        clear_btn = ctk.CTkButton(
            input_box,
            text="✕",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            width=36,
            height=32,
            corner_radius=8,
            fg_color=THEME["secondary"],
            hover_color=THEME["secondary_hover"],
            command=self._clear_url,
        )
        clear_btn.pack(side="left", padx=(0, 6))

        # Panel de Vista Previa del Video
        self.preview_frame = ctk.CTkFrame(
            url_card,
            fg_color=THEME["input_bg"],
            corner_radius=10,
        )
        self.preview_frame.pack(fill="x", padx=20, pady=(0, 16))

        # Contenido por defecto de la vista previa
        self.preview_thumb_label = ctk.CTkLabel(
            self.preview_frame,
            text="🎬",
            font=ctk.CTkFont(size=28),
            width=130,
            height=74,
            fg_color="#14161C",
            corner_radius=8,
        )
        self.preview_thumb_label.pack(side="left", padx=12, pady=12)

        preview_info = ctk.CTkFrame(self.preview_frame, fg_color="transparent")
        preview_info.pack(side="left", fill="both", expand=True, padx=(0, 12), pady=12)

        self.preview_title_label = ctk.CTkLabel(
            preview_info,
            text="Pega o introduce una URL para ver los detalles del video",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            text_color=THEME["text_primary"],
            anchor="w",
            wraplength=480,
            justify="left",
        )
        self.preview_title_label.pack(fill="x")

        self.preview_meta_label = ctk.CTkLabel(
            preview_info,
            text="Compatible con videos, canciones individuales y directos de YouTube",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=THEME["text_secondary"],
            anchor="w",
        )
        self.preview_meta_label.pack(fill="x", pady=(4, 0))

        # --- TARJETA 2: Tipo de Descarga y Formatos ---
        options_card = ctk.CTkFrame(
            scroll_container,
            fg_color=THEME["card_bg"],
            border_color=THEME["card_border"],
            border_width=1,
            corner_radius=14,
        )
        options_card.pack(fill="x", padx=10, pady=(0, 14))

        opt_title = ctk.CTkLabel(
            options_card,
            text="Modo y Calidad de Descarga",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color=THEME["text_primary"],
        )
        opt_title.pack(anchor="w", padx=20, pady=(16, 10))

        # Selector de Tipo (Segmented Button con columnas 50% / 50% simétricas)
        self.type_selector = ctk.CTkSegmentedButton(
            options_card,
            values=["🎬 Video (MP4 / MKV)", "🎵 Música (MP3 / FLAC / M4A)"],
            command=self._on_type_changed,
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            height=38,
            corner_radius=10,
            selected_color=THEME["accent"],
            selected_hover_color=THEME["accent_hover"],
            unselected_color=THEME["input_bg"],
            unselected_hover_color=THEME["secondary_hover"],
        )
        # Garantizar 50% uniforme exacto a ambos lados
        self.type_selector.grid_columnconfigure(0, weight=1, uniform="type_selector")
        self.type_selector.grid_columnconfigure(1, weight=1, uniform="type_selector")
        self.type_selector.set("🎬 Video (MP4 / MKV)")
        self.type_selector.pack(fill="x", padx=20, pady=(0, 16))

        # Cuadrícula de Formato y Calidad
        selectors_row = ctk.CTkFrame(options_card, fg_color="transparent")
        selectors_row.pack(fill="x", padx=20, pady=(0, 16))

        # Columna Formato
        fmt_col = ctk.CTkFrame(selectors_row, fg_color="transparent")
        fmt_col.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.fmt_label = ctk.CTkLabel(
            fmt_col,
            text="Formato de salida:",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=THEME["text_secondary"],
        )
        self.fmt_label.pack(anchor="w", pady=(0, 6))

        self.format_menu = ctk.CTkOptionMenu(
            fmt_col,
            values=["MP4", "MKV"],
            variable=self.selected_format,
            height=38,
            corner_radius=8,
            fg_color=THEME["input_bg"],
            button_color=THEME["secondary"],
            button_hover_color=THEME["secondary_hover"],
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
        )
        self.format_menu.pack(fill="x")

        # Columna Calidad
        qual_col = ctk.CTkFrame(selectors_row, fg_color="transparent")
        qual_col.pack(side="left", fill="x", expand=True, padx=(10, 0))

        self.qual_label = ctk.CTkLabel(
            qual_col,
            text="Calidad:",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=THEME["text_secondary"],
        )
        self.qual_label.pack(anchor="w", pady=(0, 6))

        self.quality_menu = ctk.CTkOptionMenu(
            qual_col,
            values=[
                "Máxima resolución",
                "1080p (Full HD)",
                "720p (HD)",
                "480p (SD)",
            ],
            variable=self.selected_quality,
            height=38,
            corner_radius=8,
            fg_color=THEME["input_bg"],
            button_color=THEME["secondary"],
            button_hover_color=THEME["secondary_hover"],
            font=ctk.CTkFont(family="Segoe UI", size=13),
        )
        self.quality_menu.pack(fill="x")

        # Switch elegante para metadatos
        self.metadata_switch = ctk.CTkSwitch(
            options_card,
            text="Incrustar carátula original y metadatos (artista, título, portada)",
            variable=self.embed_metadata,
            font=ctk.CTkFont(family="Segoe UI", size=13),
            progress_color=THEME["accent"],
        )
        self.metadata_switch.pack(anchor="w", padx=20, pady=(0, 16))

        # --- TARJETA 3: Carpeta de Destino ---
        folder_card = ctk.CTkFrame(
            scroll_container,
            fg_color=THEME["card_bg"],
            border_color=THEME["card_border"],
            border_width=1,
            corner_radius=14,
        )
        folder_card.pack(fill="x", padx=10, pady=(0, 14))

        folder_header = ctk.CTkFrame(folder_card, fg_color="transparent")
        folder_header.pack(fill="x", padx=20, pady=(14, 8))

        folder_title = ctk.CTkLabel(
            folder_header,
            text="Carpeta de Destino",
            font=ctk.CTkFont(family="Segoe UI", size=14, weight="bold"),
            text_color=THEME["text_primary"],
        )
        folder_title.pack(side="left")

        folder_row = ctk.CTkFrame(folder_card, fg_color="transparent")
        folder_row.pack(fill="x", padx=20, pady=(0, 16))

        folder_entry = ctk.CTkEntry(
            folder_row,
            textvariable=self.download_path,
            state="readonly",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            fg_color=THEME["input_bg"],
            border_width=0,
            height=38,
            corner_radius=8,
        )
        folder_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        browse_btn = ctk.CTkButton(
            folder_row,
            text="Examinar...",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            width=95,
            height=38,
            corner_radius=8,
            fg_color=THEME["secondary"],
            hover_color=THEME["secondary_hover"],
            command=self._select_folder,
        )
        browse_btn.pack(side="left", padx=(0, 6))

        open_folder_btn = ctk.CTkButton(
            folder_row,
            text="📁 Abrir",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            width=75,
            height=38,
            corner_radius=8,
            fg_color=THEME["secondary"],
            hover_color=THEME["secondary_hover"],
            command=self._open_folder,
        )
        open_folder_btn.pack(side="left")

        # --- PANEL INFERIOR FIJO: Botón Principal y Progreso ---
        bottom_panel = ctk.CTkFrame(
            self,
            fg_color=THEME["card_bg"],
            border_color=THEME["card_border"],
            border_width=1,
            corner_radius=16,
        )
        bottom_panel.pack(fill="x", padx=30, pady=(0, 20))

        bottom_inner = ctk.CTkFrame(bottom_panel, fg_color="transparent")
        bottom_inner.pack(fill="x", padx=20, pady=16)

        # Barra de progreso estilizada
        self.progress_bar = ctk.CTkProgressBar(
            bottom_inner,
            height=10,
            corner_radius=5,
            fg_color=THEME["input_bg"],
            progress_color=THEME["accent"],
        )
        self.progress_bar.set(0)
        self.progress_bar.pack(fill="x", pady=(0, 10))

        # Fila de Estado y Estadísticas
        stats_row = ctk.CTkFrame(bottom_inner, fg_color="transparent")
        stats_row.pack(fill="x", pady=(0, 12))

        self.status_label = ctk.CTkLabel(
            stats_row,
            text="Listo para descargar.",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=THEME["text_secondary"],
        )
        self.status_label.pack(side="left")

        self.speed_label = ctk.CTkLabel(
            stats_row,
            text="",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            text_color=THEME["text_primary"],
        )
        self.speed_label.pack(side="right")

        # Fila del Botón de Acción Principal y Acciones Post-descarga
        action_row = ctk.CTkFrame(bottom_inner, fg_color="transparent")
        action_row.pack(fill="x")

        self.download_button = ctk.CTkButton(
            action_row,
            text="Descargar Ahora",
            font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
            height=46,
            corner_radius=10,
            fg_color=THEME["accent"],
            hover_color=THEME["accent_hover"],
            command=self._start_download,
        )
        self.download_button.pack(side="left", fill="x", expand=True)

        self.open_file_btn = ctk.CTkButton(
            action_row,
            text="Reproducir Archivo",
            font=ctk.CTkFont(family="Segoe UI", size=13, weight="bold"),
            width=150,
            height=46,
            corner_radius=10,
            fg_color=THEME["success"],
            hover_color="#0D9468",
            command=self._open_downloaded_file,
        )
        # Oculto por defecto, visible cuando termina con éxito

    # --- LÓGICA DE INTERFAZ Y DETECCIÓN AUTOMÁTICA ---

    def _paste_clipboard(self):
        try:
            clipboard_content = self.clipboard_get().strip()
            self.url_entry.delete(0, "end")
            self.url_entry.insert(0, clipboard_content)
            self._trigger_fetch_info(clipboard_content)
        except Exception:
            pass

    def _clear_url(self):
        self.url_entry.delete(0, "end")
        self._reset_preview()

    def _on_url_keyrelease(self, event=None):
        url = self.url_entry.get().strip()
        if len(url) > 15 and ("youtube.com" in url or "youtu.be" in url):
            self._trigger_fetch_info(url)

    def _reset_preview(self):
        self.current_video_info = None
        self.preview_thumb_label.configure(image="", text="🎬")
        self.preview_title_label.configure(
            text="Pega o introduce una URL para ver los detalles del video",
            text_color=THEME["text_primary"],
        )
        self.preview_meta_label.configure(
            text="Compatible con videos, canciones individuales y directos de YouTube"
        )

    def _trigger_fetch_info(self, url: str):
        if url == self.last_fetched_url or self.is_fetching_info:
            return
        if not (url.startswith("http://") or url.startswith("https://")):
            return

        self.last_fetched_url = url
        self.is_fetching_info = True

        self.preview_title_label.configure(
            text="Obteniendo información del video...",
            text_color=THEME["info"],
        )
        self.preview_meta_label.configure(text="Conectando con YouTube...")

        threading.Thread(target=self._async_fetch_info, args=(url,), daemon=True).start()

    def _async_fetch_info(self, url: str):
        try:
            ydl_opts = {
                "quiet": True,
                "skip_download": True,
                "no_warnings": True,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                title = info.get("title", "Video sin título")
                uploader = info.get("uploader", "Canal desconocido")
                duration = info.get("duration_string", "")
                thumb_url = info.get("thumbnail")

                thumb_image = None
                if thumb_url:
                    try:
                        req = urllib.request.Request(
                            thumb_url,
                            headers={"User-Agent": "Mozilla/5.0"},
                        )
                        with urllib.request.urlopen(req, timeout=4) as resp:
                            raw_data = resp.read()
                        pil_img = Image.open(io.BytesIO(raw_data))
                        thumb_image = make_rounded_image(pil_img, (136, 76), radius=8)
                    except Exception:
                        thumb_image = None

            self.after(
                0,
                self._update_preview_ui,
                title,
                uploader,
                duration,
                thumb_image,
                info,
            )
        except Exception:
            self.after(0, self._on_fetch_info_error)
        finally:
            self.is_fetching_info = False

    def _update_preview_ui(self, title, uploader, duration, thumb_image, info):
        self.current_video_info = info
        self.preview_title_label.configure(
            text=title,
            text_color=THEME["text_primary"],
        )
        dur_text = f" • Duración: {duration}" if duration else ""
        self.preview_meta_label.configure(
            text=f"👤 {uploader}{dur_text}  •  Listo para descargar"
        )

        if thumb_image:
            self._thumb_ctk = ctk.CTkImage(
                light_image=thumb_image,
                dark_image=thumb_image,
                size=(136, 76),
            )
            self.preview_thumb_label.configure(image=self._thumb_ctk, text="")

    def _on_fetch_info_error(self):
        self.preview_title_label.configure(
            text="No se pudo obtener la vista previa del enlace",
            text_color=THEME["text_secondary"],
        )
        self.preview_meta_label.configure(
            text="Puedes intentar descargar directamente con el botón inferior"
        )

    def _on_type_changed(self, value):
        if "Música" in value or "Audio" in value:
            self.download_type.set("audio")
            self.format_menu.configure(values=["MP3", "M4A", "WAV", "FLAC"])
            self.selected_format.set("MP3")
            self.quality_menu.configure(
                values=[
                    "320 kbps (Máxima calidad)",
                    "256 kbps (Muy alta)",
                    "192 kbps (Recomendada)",
                    "128 kbps (Estándar)",
                ]
            )
            self.selected_quality.set("320 kbps (Máxima calidad)")
            self.metadata_switch.configure(state="normal")
            self.download_button.configure(text="Descargar Música (MP3)")
        else:
            self.download_type.set("video")
            self.format_menu.configure(values=["MP4", "MKV"])
            self.selected_format.set("MP4")
            self.quality_menu.configure(
                values=[
                    "Máxima resolución",
                    "1080p (Full HD)",
                    "720p (HD)",
                    "480p (SD)",
                ]
            )
            self.selected_quality.set("Máxima resolución")
            self.download_button.configure(text="Descargar Video (MP4)")

    def _select_folder(self):
        folder = filedialog.askdirectory(initialdir=self.download_path.get())
        if folder:
            self.download_path.set(folder)

    def _open_folder(self):
        path = Path(self.download_path.get())
        path.mkdir(parents=True, exist_ok=True)
        try:
            if sys.platform == "win32":
                os.startfile(str(path))
            elif sys.platform == "darwin":
                os.system(f'open "{path}"')
            else:
                os.system(f'xdg-open "{path}"')
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir la carpeta: {e}")

    def _open_downloaded_file(self):
        if self.last_downloaded_file and self.last_downloaded_file.exists():
            try:
                if sys.platform == "win32":
                    os.startfile(str(self.last_downloaded_file))
                elif sys.platform == "darwin":
                    os.system(f'open "{self.last_downloaded_file}"')
                else:
                    os.system(f'xdg-open "{self.last_downloaded_file}"')
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo abrir el archivo: {e}")

    # --- DESCARGA CON YT-DLP ---

    def _start_download(self):
        if self.is_downloading:
            return

        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("Atención", "Por favor, introduce una URL de YouTube.")
            self.url_entry.focus()
            return

        if not (url.startswith("http://") or url.startswith("https://")):
            messagebox.showwarning(
                "URL Inválida", "La URL debe comenzar por http:// o https://"
            )
            return

        self.is_downloading = True
        self.download_button.configure(state="disabled", text="Descargando...")
        self.open_file_btn.pack_forget()
        self.progress_bar.set(0)
        self.status_label.configure(
            text="Iniciando descarga...", text_color=THEME["info"]
        )
        self.speed_label.configure(text="")

        threading.Thread(target=self._run_download, args=(url,), daemon=True).start()

    def _progress_hook(self, d):
        if d["status"] == "downloading":
            total_bytes = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            downloaded = d.get("downloaded_bytes", 0)
            speed = d.get("speed")
            eta = d.get("eta")

            if total_bytes > 0:
                percent = downloaded / total_bytes
                self.after(0, self.progress_bar.set, percent)

                speed_str = (
                    f"{speed / (1024 * 1024):.1f} MB/s" if speed else "-- MB/s"
                )
                eta_str = f"{int(eta)}s" if eta is not None else "--"
                mb_curr = downloaded / (1024 * 1024)
                mb_tot = total_bytes / (1024 * 1024)

                self.after(
                    0,
                    self.status_label.configure,
                    {
                        "text": f"Descargando: {percent * 100:.1f}% ({mb_curr:.1f} / {mb_tot:.1f} MB)",
                        "text_color": THEME["info"],
                    },
                )
                self.after(
                    0,
                    self.speed_label.configure,
                    {"text": f"⚡ {speed_str}  •  ⏱ Restante: {eta_str}"},
                )
            else:
                downloaded_mb = downloaded / (1024 * 1024)
                self.after(
                    0,
                    self.status_label.configure,
                    {
                        "text": f"Descargando: {downloaded_mb:.1f} MB...",
                        "text_color": THEME["info"],
                    },
                )
        elif d["status"] == "finished":
            self.after(0, self.progress_bar.set, 1.0)
            self.after(
                0,
                self.status_label.configure,
                {
                    "text": "Procesando audio/video con FFmpeg...",
                    "text_color": "#F59E0B",
                },
            )
            self.after(0, self.speed_label.configure, {"text": "Finalizando archivo..."})

    def _build_yt_options(self, target_folder: Path) -> dict:
        mode = self.download_type.get()
        chosen_format = self.selected_format.get().lower()
        quality_str = self.selected_quality.get()
        embed_meta = self.embed_metadata.get()

        out_template = str(target_folder / "%(title)s.%(ext)s")
        postprocessors = []

        if mode == "audio":
            match = re.search(r"(\d+)", quality_str)
            bitrate = match.group(1) if match else "320"

            ydl_opts = {
                "format": "bestaudio/best",
                "outtmpl": out_template,
                "progress_hooks": [self._progress_hook],
                "quiet": True,
                "no_warnings": True,
            }

            postprocessors.append(
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": chosen_format,
                    "preferredquality": bitrate,
                }
            )

            if embed_meta:
                postprocessors.append(
                    {
                        "key": "FFmpegMetadata",
                        "add_metadata": True,
                    }
                )
                if chosen_format in ("mp3", "m4a"):
                    postprocessors.append({"key": "EmbedThumbnail"})
                    ydl_opts["writethumbnail"] = True

            ydl_opts["postprocessors"] = postprocessors
            return ydl_opts

        else:
            if "1080p" in quality_str:
                fmt = "bestvideo[height<=1080]+bestaudio/best[height<=1080]"
            elif "720p" in quality_str:
                fmt = "bestvideo[height<=720]+bestaudio/best[height<=720]"
            elif "480p" in quality_str:
                fmt = "bestvideo[height<=480]+bestaudio/best[height<=480]"
            else:
                fmt = "bestvideo+bestaudio/best"

            ydl_opts = {
                "format": fmt,
                "outtmpl": out_template,
                "merge_output_format": chosen_format,
                "progress_hooks": [self._progress_hook],
                "quiet": True,
                "no_warnings": True,
            }

            if embed_meta:
                postprocessors.append(
                    {
                        "key": "FFmpegMetadata",
                        "add_metadata": True,
                    }
                )
                if chosen_format == "mp4":
                    postprocessors.append({"key": "EmbedThumbnail"})
                    ydl_opts["writethumbnail"] = True

            if postprocessors:
                ydl_opts["postprocessors"] = postprocessors

            return ydl_opts

    def _run_download(self, url: str):
        target_folder = Path(self.download_path.get())
        mode = self.download_type.get()
        subfolder = target_folder / ("musica" if mode == "audio" else "videos")
        subfolder.mkdir(parents=True, exist_ok=True)

        try:
            ydl_opts = self._build_yt_options(subfolder)
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                title = info.get("title", "Archivo")
                ext = self.selected_format.get().lower()
                downloaded_file = subfolder / f"{title}.{ext}"

            self.after(
                0,
                self._on_download_success,
                title,
                subfolder,
                downloaded_file,
            )
        except Exception as e:
            error_message = str(e)
            self.after(0, self._on_download_error, error_message)

    def _on_download_success(self, title: str, folder: Path, file_path: Path):
        self.is_downloading = False
        self.last_downloaded_file = file_path if file_path.exists() else None
        self.progress_bar.set(1.0)

        # Restaurar botón de descarga
        current_type = self.download_type.get()
        btn_text = (
            "Descargar Música (MP3)" if current_type == "audio" else "Descargar Video (MP4)"
        )
        self.download_button.configure(state="normal", text=btn_text)

        self.status_label.configure(
            text="✓ Descarga completada exitosamente.",
            text_color=THEME["success"],
        )
        self.speed_label.configure(text="Completado al 100%")

        # Mostrar botón de reproducir archivo directamente
        if self.last_downloaded_file:
            self.open_file_btn.pack(side="left", padx=(10, 0))

    def _on_download_error(self, err_msg: str):
        self.is_downloading = False
        self.progress_bar.set(0)
        current_type = self.download_type.get()
        btn_text = (
            "Descargar Música (MP3)" if current_type == "audio" else "Descargar Video (MP4)"
        )
        self.download_button.configure(state="normal", text=btn_text)

        self.status_label.configure(
            text="✗ Ocurrió un error en la descarga.",
            text_color="#EF4444",
        )
        self.speed_label.configure(text="")
        messagebox.showerror(
            "Error de Descarga",
            f"No se pudo completar la descarga.\n\nDetalles:\n{err_msg}",
        )

    # --- VENTANA ACERCA DE ---

    def _show_about_dialog(self):
        about_window = ctk.CTkToplevel(self)
        about_window.title("Acerca del Descargador")
        about_window.geometry("420x460")
        about_window.resizable(False, False)
        about_window.configure(fg_color=THEME["bg"])
        about_window.transient(self)
        about_window.grab_set()

        ico_path = get_resource_path("assets/icon.ico")
        if ico_path.exists():
            try:
                about_window.iconbitmap(str(ico_path))
            except Exception:
                pass

        x = self.winfo_x() + (self.winfo_width() // 2) - 210
        y = self.winfo_y() + (self.winfo_height() // 2) - 230
        about_window.geometry(f"420x460+{max(x, 0)}+{max(y, 0)}")

        card = ctk.CTkFrame(
            about_window,
            fg_color=THEME["card_bg"],
            border_color=THEME["card_border"],
            border_width=1,
            corner_radius=14,
        )
        card.pack(fill="both", expand=True, padx=20, pady=20)

        logo_path = get_resource_path("assets/logo.png")
        if logo_path.exists():
            try:
                logo_pil = Image.open(logo_path)
                modal_logo = ctk.CTkImage(
                    light_image=logo_pil,
                    dark_image=logo_pil,
                    size=(80, 80),
                )
                logo_label = ctk.CTkLabel(card, image=modal_logo, text="")
                logo_label.image = modal_logo
                logo_label.pack(pady=(22, 10))
            except Exception:
                pass

        app_title = ctk.CTkLabel(
            card,
            text="YouTube Downloader Pro",
            font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"),
            text_color=THEME["text_primary"],
        )
        app_title.pack(pady=(0, 2))

        version_label = ctk.CTkLabel(
            card,
            text="Versión 2.0 • Edición Moderna",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=THEME["accent"],
        )
        version_label.pack(pady=(0, 14))

        desc_text = (
            "Aplicación de escritorio moderna para descargar\n"
            "música con carátula y metadatos incrustados,\n"
            "o videos en máxima calidad (1080p, HD, 4K).\n\n"
            "Potenciado por Python, CustomTkinter y yt-dlp."
        )
        desc_label = ctk.CTkLabel(
            card,
            text=desc_text,
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color=THEME["text_secondary"],
            justify="center",
        )
        desc_label.pack(pady=(0, 20), padx=20)

        close_btn = ctk.CTkButton(
            card,
            text="Cerrar",
            font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
            width=120,
            height=34,
            corner_radius=8,
            fg_color=THEME["secondary"],
            hover_color=THEME["secondary_hover"],
            command=about_window.destroy,
        )
        close_btn.pack(pady=(0, 15))


if __name__ == "__main__":
    app = DownloaderApp()
    app.mainloop()
