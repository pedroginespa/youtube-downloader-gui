"""
Generador del logotipo oficial refinado y de alta fidelidad
Descargador de YouTube (Música y Video)
"""
import math
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

def create_super_logo(size=512):
    scale = 4
    canvas_size = size * scale
    
    base = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
    
    pad = int(canvas_size * 0.08)
    w = canvas_size - 2 * pad
    h = canvas_size - 2 * pad
    radius = int(canvas_size * 0.22)
    rect = [pad, pad, pad + w, pad + h]
    
    # 1. Sombra suave para dar volumen
    shadow_offset_y = int(canvas_size * 0.04)
    shadow_layer = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
    s_draw = ImageDraw.Draw(shadow_layer)
    s_draw.rounded_rectangle(
        [pad, pad + shadow_offset_y, pad + w, pad + h + shadow_offset_y],
        radius=radius,
        fill=(0, 0, 0, 135)
    )
    shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(canvas_size * 0.035))
    base = Image.alpha_composite(base, shadow_layer)
    
    # 2. Degradado de fondo rojo rubí YouTube moderno (#FF1E42 a #880018)
    grad_layer = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
    for y_idx in range(pad, pad + h):
        t = (y_idx - pad) / h
        r = int(255 - t * (255 - 136))
        g = int(32 - t * 32)
        b = int(62 - t * (62 - 24))
        line_draw = ImageDraw.Draw(grad_layer)
        line_draw.line([(pad, y_idx), (pad + w, y_idx)], fill=(r, g, b, 255))
    
    mask = Image.new("L", (canvas_size, canvas_size), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle(rect, radius=radius, fill=255)
    
    squircle_layer = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
    squircle_layer.paste(grad_layer, (0, 0), mask)
    
    # 3. Brillo de iluminación superior (Glassmorphism / Fluent)
    highlight_layer = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
    hl_draw = ImageDraw.Draw(highlight_layer)
    hl_draw.ellipse(
        [pad - int(w * 0.1), pad - int(h * 0.3), pad + int(w * 1.1), pad + int(h * 0.45)],
        fill=(255, 255, 255, 48)
    )
    highlight_layer = highlight_layer.filter(ImageFilter.GaussianBlur(canvas_size * 0.04))
    
    hl_masked = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
    hl_masked.paste(highlight_layer, (0, 0), mask)
    squircle_layer = Image.alpha_composite(squircle_layer, hl_masked)
    
    # Borde fino translúcido para definición
    border_draw = ImageDraw.Draw(squircle_layer)
    border_draw.rounded_rectangle(
        rect,
        radius=radius,
        outline=(255, 255, 255, 80),
        width=int(canvas_size * 0.007)
    )
    
    base = Image.alpha_composite(base, squircle_layer)
    
    # 4. Disco interior oscuro translúcido para alto contraste y profundidad
    cx = canvas_size // 2
    cy = int(canvas_size * 0.505)
    disc_radius = int(canvas_size * 0.285)
    disc_layer = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
    disc_draw = ImageDraw.Draw(disc_layer)
    disc_draw.ellipse(
        [cx - disc_radius, cy - disc_radius, cx + disc_radius, cy + disc_radius],
        fill=(0, 0, 0, 70),
        outline=(255, 255, 255, 35),
        width=int(canvas_size * 0.006)
    )
    base = Image.alpha_composite(base, disc_layer)
    
    # 5. Capa gráfica de elementos frontales
    fg_layer = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
    fg_draw = ImageDraw.Draw(fg_layer)
    
    # A) AURICULARES PREMIUM (Representa Música)
    hp_radius = int(canvas_size * 0.235)
    hp_center_y = cy - int(canvas_size * 0.045)
    hp_arc_box = [cx - hp_radius, hp_center_y - hp_radius, cx + hp_radius, hp_center_y + hp_radius]
    
    arc_width = int(canvas_size * 0.034)
    fg_draw.arc(hp_arc_box, start=185, end=355, fill=(255, 255, 255, 245), width=arc_width)
    
    # Almohadillas / Auriculares laterales
    ear_w = int(canvas_size * 0.052)
    ear_h = int(canvas_size * 0.125)
    ear_rad = ear_w // 2
    
    left_x = cx - hp_radius - ear_w // 2 + int(canvas_size * 0.006)
    right_x = cx + hp_radius - ear_w // 2 - int(canvas_size * 0.006)
    ear_y = hp_center_y - int(canvas_size * 0.005)
    
    fg_draw.rounded_rectangle([left_x, ear_y, left_x + ear_w, ear_y + ear_h], radius=ear_rad, fill=(255, 255, 255, 255))
    fg_draw.rounded_rectangle([right_x, ear_y, right_x + ear_w, ear_y + ear_h], radius=ear_rad, fill=(255, 255, 255, 255))
    
    # Detalle interior almohadillas
    fg_draw.rounded_rectangle(
        [left_x + int(ear_w * 0.28), ear_y + int(ear_h * 0.22), left_x + int(ear_w * 0.72), ear_y + int(ear_h * 0.78)],
        radius=int(ear_rad * 0.5),
        fill=(220, 220, 225, 255)
    )
    fg_draw.rounded_rectangle(
        [right_x + int(ear_w * 0.28), ear_y + int(ear_h * 0.22), right_x + int(ear_w * 0.72), ear_y + int(ear_h * 0.78)],
        radius=int(ear_rad * 0.5),
        fill=(220, 220, 225, 255)
    )
    
    # B) ECUALIZADOR LATERAL (Ondas musicales que flanquean la flecha)
    eq_heights = [0.038, 0.075, 0.050]
    eq_bar_w = int(canvas_size * 0.016)
    eq_bar_rad = eq_bar_w // 2
    eq_spacing = int(canvas_size * 0.026)
    eq_center_y = cy - int(canvas_size * 0.01)
    
    for i, h_pct in enumerate(eq_heights):
        b_len = int(canvas_size * h_pct)
        # Izquierda
        bx_l = cx - int(canvas_size * 0.125) - ((2 - i) * eq_spacing)
        fg_draw.rounded_rectangle(
            [bx_l - eq_bar_w//2, eq_center_y - b_len//2, bx_l + eq_bar_w//2, eq_center_y + b_len//2],
            radius=eq_bar_rad,
            fill=(255, 255, 255, 185)
        )
        # Derecha
        bx_r = cx + int(canvas_size * 0.125) + (i * eq_spacing)
        fg_draw.rounded_rectangle(
            [bx_r - eq_bar_w//2, eq_center_y - b_len//2, bx_r + eq_bar_w//2, eq_center_y + b_len//2],
            radius=eq_bar_rad,
            fill=(255, 255, 255, 185)
        )

    # C) FLECHA DE DESCARGA CENTRAL (Unificada y nítida al 100%)
    stem_w = int(canvas_size * 0.068)
    stem_top = cy - int(canvas_size * 0.14)
    stem_bottom = cy + int(canvas_size * 0.01)
    stem_r = stem_w // 2
    
    arrow_w = int(canvas_size * 0.122)
    arrow_top = cy - int(canvas_size * 0.005)
    arrow_tip = cy + int(canvas_size * 0.115)
    
    # Vástago redondeado arriba
    fg_draw.rounded_rectangle(
        [cx - stem_w // 2, stem_top, cx + stem_w // 2, stem_bottom],
        radius=stem_r,
        fill=(255, 255, 255, 255)
    )
    
    # Cabeza poligonal limpia (el supersampling 4x le da antialiasing perfecto)
    arrow_points = [
        (cx - arrow_w, arrow_top),
        (cx + arrow_w, arrow_top),
        (cx, arrow_tip)
    ]
    fg_draw.polygon(arrow_points, fill=(255, 255, 255, 255))

    # D) BANDEJA DE DESCARGA (Base elegante)
    tray_w = int(canvas_size * 0.20)
    tray_h = int(canvas_size * 0.024)
    tray_y = arrow_tip + int(canvas_size * 0.038)
    fg_draw.rounded_rectangle(
        [cx - tray_w // 2, tray_y, cx + tray_w // 2, tray_y + tray_h],
        radius=tray_h // 2,
        fill=(255, 255, 255, 245)
    )

    # 6. Sombra suave de los elementos frontales para relieve 3D
    fg_shadow = fg_layer.copy()
    fg_shadow = fg_shadow.filter(ImageFilter.GaussianBlur(canvas_size * 0.014))
    shadow_colored = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 80))
    final_fg_shadow = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
    final_fg_shadow.paste(shadow_colored, (0, int(canvas_size * 0.009)), fg_shadow.split()[3])
    
    base = Image.alpha_composite(base, final_fg_shadow)
    base = Image.alpha_composite(base, fg_layer)
    
    return base.resize((size, size), Image.Resampling.LANCZOS)

def generate_svg():
    """Genera versión SVG vectorial limpia del logotipo."""
    svg_content = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="100%" height="100%">
  <defs>
    <!-- Gradiente de fondo YouTube -->
    <linearGradient id="bgGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#FF2A42"/>
      <stop offset="45%" stop-color="#E60026"/>
      <stop offset="100%" stop-color="#880018"/>
    </linearGradient>
    
    <!-- Sombra principal -->
    <filter id="shadow" x="-10%" y="-10%" width="130%" height="130%">
      <feDropShadow dx="0" dy="16" stdDeviation="16" flood-color="#000000" flood-opacity="0.45"/>
    </filter>

    <!-- Reflejo superior de cristal -->
    <radialGradient id="highlight" cx="50%" cy="15%" r="60%">
      <stop offset="0%" stop-color="#FFFFFF" stop-opacity="0.25"/>
      <stop offset="100%" stop-color="#FFFFFF" stop-opacity="0"/>
    </radialGradient>
  </defs>

  <!-- Contenedor squircle con sombra -->
  <rect x="40" y="40" width="432" height="432" rx="95" fill="url(#bgGrad)" filter="url(#shadow)" stroke="rgba(255,255,255,0.3)" stroke-width="3"/>
  <rect x="40" y="40" width="432" height="432" rx="95" fill="url(#highlight)"/>

  <!-- Disco central de contraste -->
  <circle cx="256" cy="258" r="146" fill="rgba(0,0,0,0.25)" stroke="rgba(255,255,255,0.14)" stroke-width="3"/>

  <!-- Auriculares (Música) -->
  <path d="M 136 235 A 120 120 0 0 1 376 235" fill="none" stroke="#FFFFFF" stroke-width="17" stroke-linecap="round"/>
  <!-- Almohadillas -->
  <rect x="122" y="228" width="26" height="64" rx="13" fill="#FFFFFF"/>
  <rect x="128" y="240" width="14" height="40" rx="7" fill="#DCDCE0"/>
  <rect x="364" y="228" width="26" height="64" rx="13" fill="#FFFFFF"/>
  <rect x="370" y="240" width="14" height="40" rx="7" fill="#DCDCE0"/>

  <!-- Ecualizador de ondas musicales laterales -->
  <!-- Izquierda -->
  <rect x="160" y="243" width="8" height="20" rx="4" fill="rgba(255,255,255,0.75)"/>
  <rect x="173" y="233" width="8" height="38" rx="4" fill="rgba(255,255,255,0.75)"/>
  <rect x="186" y="240" width="8" height="26" rx="4" fill="rgba(255,255,255,0.75)"/>
  <!-- Derecha -->
  <rect x="318" y="240" width="8" height="26" rx="4" fill="rgba(255,255,255,0.75)"/>
  <rect x="331" y="233" width="8" height="38" rx="4" fill="rgba(255,255,255,0.75)"/>
  <rect x="344" y="243" width="8" height="20" rx="4" fill="rgba(255,255,255,0.75)"/>

  <!-- Flecha de Descarga central (Video / Downloader) -->
  <rect x="238" y="186" width="36" height="76" rx="18" fill="#FFFFFF"/>
  <polygon points="193,252 319,252 256,316" fill="#FFFFFF"/>

  <!-- Bandeja de Descarga -->
  <rect x="205" y="334" width="102" height="12" rx="6" fill="#FFFFFF"/>
</svg>
'''
    with open("assets/logo.svg", "w", encoding="utf-8") as f:
        f.write(svg_content)

def main():
    assets_dir = Path("assets")
    assets_dir.mkdir(exist_ok=True)
    
    print("Generando logo maestro 512x512...")
    logo_512 = create_super_logo(512)
    logo_512.save(assets_dir / "logo.png", "PNG")
    
    sizes = [256, 128, 64, 48, 32, 24, 16]
    images = []
    
    for s in sizes:
        resized = logo_512.resize((s, s), Image.Resampling.LANCZOS)
        resized.save(assets_dir / f"logo_{s}.png", "PNG")
        images.append(resized)
    
    print("Generando assets/icon.ico con múltiples resoluciones...")
    images[0].save(
        assets_dir / "icon.ico",
        format="ICO",
        sizes=[(s, s) for s in [256, 128, 64, 48, 32, 24, 16]]
    )
    
    generate_svg()
    print("¡Assets generados con éxito!")

if __name__ == "__main__":
    main()
