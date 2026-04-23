"""Generate a PNG QR code image from a token string."""
import io
import qrcode
from qrcode.constants import ERROR_CORRECT_M


def make_qr_png(token: str) -> bytes:
    """Return PNG bytes for a QR code encoding the given token."""
    qr = qrcode.QRCode(
        version=None,
        error_correction=ERROR_CORRECT_M,
        box_size=10,
        border=2,
    )
    qr.add_data(token)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()
