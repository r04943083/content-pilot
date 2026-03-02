"""QR code display utilities for terminal login."""

from __future__ import annotations

import io

from rich.console import Console

console = Console()


def display_qr_in_terminal(data: str) -> None:
    """Render a QR code in the terminal using qrcode library."""
    import qrcode

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=1,
        border=1,
    )
    qr.add_data(data)
    qr.make(fit=True)

    f = io.StringIO()
    qr.print_ascii(out=f, invert=True)
    console.print(f.getvalue())


def display_qr_image_in_terminal(image_bytes: bytes) -> None:
    """Display a QR code image (from screenshot) in terminal."""
    try:
        from PIL import Image

        img = Image.open(io.BytesIO(image_bytes))
        # Convert to ASCII art for terminal display
        img = img.convert("L").resize((60, 30))
        chars = " .:-=+*#%@"
        pixels = img.getdata()
        ascii_str = ""
        width = img.width
        for i, pixel in enumerate(pixels):
            ascii_str += chars[pixel * (len(chars) - 1) // 255]
            if (i + 1) % width == 0:
                ascii_str += "\n"
        console.print(ascii_str)
    except Exception:
        console.print("[yellow]Could not render QR image in terminal.[/yellow]")
        console.print("[yellow]Please scan the QR code in the browser window.[/yellow]")
