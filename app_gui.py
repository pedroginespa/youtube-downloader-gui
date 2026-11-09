import os
import re
import sys
import threading
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
from PIL import Image, ImageTk

# Identificador de aplicación para Windows (asegura que el icono aparezca en la barra de tareas)
if sys.platform == "win32":
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            "com.pedro.youtubedownloader.gui"
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

# Configuración inicial de CustomTkinter
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DOWNLOAD_DIR = BASE_DIR / "descargas"


def get_resource_path(relative_path: str) -> Path:
    """Obtiene la ruta absoluta a un recurso, funcionando en modo desarrollo y en ejecutable empaquetado (PyInstaller)."""
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS) / relative_path
    return BASE_DIR / relative_path


class DownloaderApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Descargador de YouTube - Música y Video")
        self.geometry("720x680")
        self.minsize(650, 620)

        # Configurar icono de la ventana
        self._setup_icons()

        # Directorio de descarga
        self.download_path = tk.StringVar(value=str(DEFAULT_DOWNLOAD_DIR))

        # Modos y Calidades
        self.download_type = tk.StringVar(value="video")  # "video" o "audio"
        self.selected_format = tk.StringVar(value="mp4")
        self.selected_quality = tk.StringVar(value="Máxima resolución")
        self.embed_metadata = tk.BooleanVar(value=True)

        self.is_downloading = False

        self._build_ui()
        self._on_type_changed("Video")

    def _setup_icons(self):
        """Aplica el logotipo como icono de la ventana y barra de tareas."""
        self._apply_delayed_icon()
        # Reforzar tras el mapeo de la ventana en CustomTkinter
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
        # Cabecera con logotipo y título
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=25, pady=(20, 10))

        # Logo en la cabecera
        logo_path = get_resource_path("assets/logo.png")
        if logo_path.exists():
            try:
                logo_pil = Image.open(logo_path)
                self.logo_ctk = ctk.CTkImage(
                    light_image=logo_pil,
                    dark_image=logo_pil,
                    size=(54, 54),
                )
                logo_label = ctk.CTkLabel(header_frame, image=self.logo_ctk, text="")
                logo_label.pack(side="left", padx=(0, 14))
            except Exception:
                pass

        # Textos de título y subtítulo
        title_box = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_box.pack(side="left", fill="both", expand=True)

        title = ctk.CTkLabel(
            title_box,
            text="Descargador de YouTube",
            font=ctk.CTkFont(size=24, weight="bold"),
        )
        title.pack(anchor="w")

        subtitle = ctk.CTkLabel(
            title_box,
            text="Descarga música en alta calidad o videos en máxima resolución con yt-dlp",
            font=ctk.CTkFont(size=13),
            text_color="gray",
        )
        subtitle.pack(anchor="w")

        # Botón Acerca de / Info
        about_btn = ctk.CTkButton(
            header_frame,
            text="ℹ Acerca de",
            width=90,
            height=32,
            fg_color="#333333",
            hover_color="#444444",
            command=self._show_about_dialog,
        )
        about_btn.pack(side="right", padx=(10, 0))

        # Contenedor principal del formulario
        form_frame = ctk.CTkFrame(self, corner_radius=12)
        form_frame.pack(fill="both", expand=True, padx=25, pady=10)

        # 1. Campo de URL
        url_label = ctk.CTkLabel(
            form_frame,
            text="Enlace del Video o Canción:",
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        url_label.pack(anchor="w", padx=20, pady=(15, 5))

        url_input_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        url_input_frame.pack(fill="x", padx=20, pady=(0, 15))

        self.url_entry = ctk.CTkEntry(
            url_input_frame,
            placeholder_text="https://www.youtube.com/watch?v=...",
            font=ctk.CTkFont(size=13),
            height=38,
        )
        self.url_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        paste_btn = ctk.CTkButton(
            url_input_frame,
            text="Pegar",
            width=70,
            height=38,
            command=self._paste_clipboard,
        )
        paste_btn.pack(side="left", padx=(0, 5))

        clear_btn = ctk.CTkButton(
            url_input_frame,
            text="Borrar",
            width=70,
            height=38,
            fg_color="#444444",
            hover_color="#555555",
            command=self._clear_url,
        )
        clear_btn.pack(side="left")

        # 2. Selector de Tipo (Audio / Video)
        type_label = ctk.CTkLabel(
            form_frame,
            text="Tipo de Descarga:",
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        type_label.pack(anchor="w", padx=20, pady=(5, 5))

        self.type_selector = ctk.CTkSegmentedButton(
            form_frame,
            values=["🎬 Video", "🎵 Música (Audio)"],
            command=self._on_type_changed,
            font=ctk.CTkFont(size=14, weight="bold"),
            height=36,
        )
        # Asegurar que ambos segmentos tengan exactamente el mismo tamaño (50% / 50%)
        self.type_selector.grid_columnconfigure(0, weight=1, uniform="type_selector")
        self.type_selector.grid_columnconfigure(1, weight=1, uniform="type_selector")
        self.type_selector.set("🎬 Video")
        self.type_selector.pack(fill="x", padx=20, pady=(0, 15))

        # 3. Opciones de Formato y Calidad en dos columnas
        options_row = ctk.CTkFrame(form_frame, fg_color="transparent")
        options_row.pack(fill="x", padx=20, pady=(0, 15))

        # Columna Formato
        format_col = ctk.CTkFrame(options_row, fg_color="transparent")
        format_col.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.format_label = ctk.CTkLabel(
            format_col,
            text="Formato de salida:",
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        self.format_label.pack(anchor="w", pady=(0, 5))

        self.format_menu = ctk.CTkOptionMenu(
            format_col,
            values=["MP4", "MKV"],
            variable=self.selected_format,
            height=34,
        )
        self.format_menu.pack(fill="x")

        # Columna Calidad
        quality_col = ctk.CTkFrame(options_row, fg_color="transparent")
        quality_col.pack(side="left", fill="x", expand=True, padx=(10, 0))

        self.quality_label = ctk.CTkLabel(
            quality_col,
            text="Calidad:",
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        self.quality_label.pack(anchor="w", pady=(0, 5))

        self.quality_menu = ctk.CTkOptionMenu(
            quality_col,
            values=[
                "Máxima resolución",
                "1080p (Full HD)",
                "720p (HD)",
                "480p (SD)",
            ],
            variable=self.selected_quality,
            height=34,
        )
        self.quality_menu.pack(fill="x")

        # 4. Carpeta de destino
        folder_label = ctk.CTkLabel(
            form_frame,
            text="Carpeta de Destino:",
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        folder_label.pack(anchor="w", padx=20, pady=(5, 5))

        folder_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        folder_frame.pack(fill="x", padx=20, pady=(0, 15))

        folder_entry = ctk.CTkEntry(
            folder_frame,
            textvariable=self.download_path,
            state="readonly",
            height=36,
        )
        folder_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        browse_btn = ctk.CTkButton(
            folder_frame,
            text="Examinar...",
            width=100,
            height=36,
            command=self._select_folder,
        )
        browse_btn.pack(side="left", padx=(0, 5))

        open_folder_btn = ctk.CTkButton(
            folder_frame,
            text="Abrir",
            width=65,
            height=36,
            fg_color="#333333",
            hover_color="#444444",
            command=self._open_folder,
        )
        open_folder_btn.pack(side="left")

        # 5. Opciones avanzadas (Metadatos y carátula)
        self.metadata_checkbox = ctk.CTkCheckBox(
            form_frame,
            text="Incrustar carátula y metadatos (artista, álbum, título)",
            variable=self.embed_metadata,
            font=ctk.CTkFont(size=13),
        )
        self.metadata_checkbox.pack(anchor="w", padx=20, pady=(0, 15))

        # Panel inferior de Progreso y Acción
        bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
        bottom_frame.pack(fill="x", padx=25, pady=(5, 20))

        # Barra de progreso
        self.progress_bar = ctk.CTkProgressBar(bottom_frame, height=12)
        self.progress_bar.set(0)
        self.progress_bar.pack(fill="x", pady=(0, 8))

        # Etiqueta de estado
        self.status_label = ctk.CTkLabel(
            bottom_frame,
            text="Listo para descargar.",
            font=ctk.CTkFont(size=12),
            text_color="gray",
        )
        self.status_label.pack(anchor="w", pady=(0, 12))

        # Botón de Descargar
        self.download_button = ctk.CTkButton(
            bottom_frame,
            text="Descargar Ahora",
            font=ctk.CTkFont(size=15, weight="bold"),
            height=44,
            command=self._start_download,
        )
        self.download_button.pack(fill="x")

    def _show_about_dialog(self):
        about_window = ctk.CTkToplevel(self)
        about_window.title("Acerca del Descargador")
        about_window.geometry("420x460")
        about_window.resizable(False, False)
        about_window.transient(self)
        about_window.grab_set()

        # Configurar icono en la ventana modal
        ico_path = get_resource_path("assets/icon.ico")
        if ico_path.exists():
            try:
                about_window.iconbitmap(str(ico_path))
            except Exception:
                pass

        # Centrar ventana modal respecto a la principal
        x = self.winfo_x() + (self.winfo_width() // 2) - 210
        y = self.winfo_y() + (self.winfo_height() // 2) - 230
        about_window.geometry(f"420x460+{max(x, 0)}+{max(y, 0)}")

        content_frame = ctk.CTkFrame(about_window, corner_radius=12)
        content_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Logo en grande
        logo_path = get_resource_path("assets/logo.png")
        if logo_path.exists():
            try:
                logo_pil = Image.open(logo_path)
                modal_logo = ctk.CTkImage(
                    light_image=logo_pil,
                    dark_image=logo_pil,
                    size=(84, 84),
                )
                logo_label = ctk.CTkLabel(content_frame, image=modal_logo, text="")
                logo_label.image = modal_logo  # Mantener referencia
                logo_label.pack(pady=(20, 10))
            except Exception:
                pass

        # Título y versión
        app_title = ctk.CTkLabel(
            content_frame,
            text="Descargador de YouTube",
            font=ctk.CTkFont(size=20, weight="bold"),
        )
        app_title.pack(pady=(0, 2))

        version_label = ctk.CTkLabel(
            content_frame,
            text="Música & Video • Versión 1.2",
            font=ctk.CTkFont(size=12),
            text_color="#FF334B",
        )
        version_label.pack(pady=(0, 15))

        # Descripción
        desc_text = (
            "Aplicación de escritorio moderna para descargar\n"
            "música con carátula y metadatos incrustados,\n"
            "o videos en máxima calidad (1080p, HD, 4K).\n\n"
            "Desarrollado con Python, CustomTkinter y yt-dlp."
        )
        desc_label = ctk.CTkLabel(
            content_frame,
            text=desc_text,
            font=ctk.CTkFont(size=12),
            text_color="gray80",
            justify="center",
        )
        desc_label.pack(pady=(0, 20), padx=20)

        close_btn = ctk.CTkButton(
            content_frame,
            text="Cerrar",
            width=120,
            height=34,
            command=about_window.destroy,
        )
        close_btn.pack(pady=(0, 15))

    def _paste_clipboard(self):
        try:
            clipboard_content = self.clipboard_get().strip()
            self.url_entry.delete(0, "end")
            self.url_entry.insert(0, clipboard_content)
        except Exception:
            pass

    def _clear_url(self):
        self.url_entry.delete(0, "end")

    def _on_type_changed(self, value):
        if "Música" in value or "Audio" in value:
            self.download_type.set("audio")
            # Actualizar formatos disponibles
            self.format_menu.configure(values=["MP3", "M4A", "WAV", "FLAC"])
            self.selected_format.set("MP3")
            # Actualizar calidades de audio
            self.quality_menu.configure(
                values=[
                    "320 kbps (Máxima calidad)",
                    "256 kbps (Muy alta)",
                    "192 kbps (Recomendada)",
                    "128 kbps (Estándar)",
                ]
            )
            self.selected_quality.set("320 kbps (Máxima calidad)")
            self.metadata_checkbox.configure(state="normal")
        else:
            self.download_type.set("video")
            # Actualizar formatos de video
            self.format_menu.configure(values=["MP4", "MKV"])
            self.selected_format.set("MP4")
            # Actualizar resoluciones
            self.quality_menu.configure(
                values=[
                    "Máxima resolución",
                    "1080p (Full HD)",
                    "720p (HD)",
                    "480p (SD)",
                ]
            )
            self.selected_quality.set("Máxima resolución")

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
                "URL Inválida", "La URL introducida no es válida. Debe comenzar por http o https."
            )
            return

        # Preparar UI para descarga
        self.is_downloading = True
        self.download_button.configure(state="disabled", text="Descargando...")
        self.progress_bar.set(0)
        self.status_label.configure(
            text="Obteniendo información del video...", text_color="#3B8ED0"
        )

        # Iniciar en hilo secundario para evitar congelar la interfaz
        thread = threading.Thread(target=self._run_download, args=(url,), daemon=True)
        thread.start()

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
                status_text = (
                    f"Descargando: {percent * 100:.1f}%  |  {speed_str}  |  Restante: {eta_str}"
                )
                self.after(
                    0,
                    self.status_label.configure,
                    {"text": status_text, "text_color": "#3B8ED0"},
                )
            else:
                downloaded_mb = downloaded / (1024 * 1024)
                self.after(
                    0,
                    self.status_label.configure,
                    {
                        "text": f"Descargando: {downloaded_mb:.1f} MB...",
                        "text_color": "#3B8ED0",
                    },
                )
        elif d["status"] == "finished":
            self.after(0, self.progress_bar.set, 1.0)
            self.after(
                0,
                self.status_label.configure,
                {"text": "Procesando audio/video con FFmpeg...", "text_color": "#FFA500"},
            )

    def _build_yt_options(self, target_folder: Path) -> dict:
        mode = self.download_type.get()
        chosen_format = self.selected_format.get().lower()
        quality_str = self.selected_quality.get()
        embed_meta = self.embed_metadata.get()

        out_template = str(target_folder / "%(title)s.%(ext)s")

        postprocessors = []

        if mode == "audio":
            # Extraer bitrate numérico
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
            # Modo Video
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
        # Subcarpeta opcional por tipo para mantener orden
        subfolder = target_folder / ("musica" if mode == "audio" else "videos")
        subfolder.mkdir(parents=True, exist_ok=True)

        try:
            ydl_opts = self._build_yt_options(subfolder)
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                title = info.get("title", "Archivo")

            self.after(
                0,
                self._on_download_success,
                title,
                subfolder,
            )
        except Exception as e:
            error_message = str(e)
            self.after(0, self._on_download_error, error_message)

    def _on_download_success(self, title: str, folder: Path):
        self.is_downloading = False
        self.progress_bar.set(1.0)
        self.download_button.configure(state="normal", text="Descargar Ahora")
        self.status_label.configure(
            text="✓ Descarga completada exitosamente.", text_color="#2FA572"
        )

        resp = messagebox.askyesno(
            "Descarga completada",
            f"Se ha descargado:\n'{title}'\n\n¿Deseas abrir la carpeta contenedora?",
        )
        if resp:
            try:
                if sys.platform == "win32":
                    os.startfile(str(folder))
            except Exception:
                pass

    def _on_download_error(self, err_msg: str):
        self.is_downloading = False
        self.progress_bar.set(0)
        self.download_button.configure(state="normal", text="Descargar Ahora")
        self.status_label.configure(
            text="✗ Ocurrió un error en la descarga.", text_color="#FF4D4D"
        )
        messagebox.showerror(
            "Error de Descarga",
            f"No se pudo completar la descarga.\n\nDetalles:\n{err_msg}",
        )


if __name__ == "__main__":
    app = DownloaderApp()
    app.mainloop()

