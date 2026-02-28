import qrcode
import os

ip = "192.168.18.16"  # Local IP found earlier
url = f"http://{ip}:3000"

print(f"Generating QR code for: {url}")

qr = qrcode.QRCode(version=1, box_size=10, border=4)
qr.add_data(url)
qr.make(fit=True)

img = qr.make_image(fill_color="#0D9488", back_color="white")
img.save("sehatbook_qr.png")

print(f"QR Code saved as sehatbook_qr.png!")
print("Scan this QR code with your phone to open SehatBook")
