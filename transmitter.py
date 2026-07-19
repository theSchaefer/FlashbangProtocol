import pygame
import qrcode
import io
from qrcode.constants import ERROR_CORRECT_L
from PIL import Image
from pathlib import Path
import numpy as np
import ctypes
import sys

# Windows-only: opt into per-monitor DPI awareness so the fullscreen surface
# matches the physical resolution. ctypes.windll does not exist on other platforms.
if sys.platform == "win32":
    ctypes.windll.shcore.SetProcessDpiAwareness(1)

import struct, base64

VERSION, CHUNK, BOX_SIZE, BORDER = 10, 150, 6, 4



error_correction = ERROR_CORRECT_L
pygame.init()

clock = pygame.time.Clock()

file_path = str(input("Enter file path:"))
with open(file_path, 'rb') as file:
    data = file.read()

WIDTH, HEIGHT = 2560, 1440
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN, vsync=1)
canvas = pygame.Surface((WIDTH, HEIGHT))
canvas.fill((30, 30, 30))

data_array = []

chunks = [data[i:i+CHUNK] for i in range(0, len(data), CHUNK)]
total = len(chunks)

for idx, chunk in enumerate(chunks):
    payload = base64.b64encode(struct.pack(">II", idx, total) + chunk)
    # payload in qr.add_data(), version=10

sprites = []
for idx, chunk in enumerate(chunks):
    payload = base64.b64encode(struct.pack(">II", idx, total) + chunk)
    qr = qrcode.QRCode(
        version=VERSION,
        error_correction=error_correction,
        box_size=1,
        border=BORDER,
        mask_pattern=0,
    )
    qr.add_data(payload)
    qr.make(fit=False)
    grid = np.array(qr.get_matrix(), dtype=bool)
    gray = np.where(grid, 0, 255).astype(np.uint8)
    gray = np.repeat(np.repeat(gray, BOX_SIZE, axis=0), BOX_SIZE, axis=1)
    gray = gray.T
    rgb = np.stack([gray, gray, gray], axis=-1)
    sprite = pygame.surfarray.make_surface(rgb).convert()
    sprites.append((sprite.get_size(), sprite))
   
x = 0 
y = 0
row_height = 0
count = 0
frames = []
qr_side = sprites[0][1].get_width()
cols = WIDTH // qr_side
rows = HEIGHT // qr_side
per_frame = cols * rows

for i, (dimensions, sprite) in enumerate(sprites):
    slot = i % per_frame
    if slot == 0 and i > 0:
        frames.append(canvas.copy())
        canvas.fill((30, 30, 30))
    x = (slot % cols) * qr_side
    y = (slot // cols) * qr_side
    canvas.blit(sprite, (x, y))


FRAME_MS = 500
last_switch = pygame.time.get_ticks()   
running = True
frame_index = 0
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            running = False
    
    now = pygame.time.get_ticks()
    if now - last_switch >= FRAME_MS:
        last_switch = now
        frame_index = (frame_index + 1) 
        if frame_index >= len(frames):
            running = False


    screen.blit(frames[frame_index], (0,0))
    pygame.display.flip()
    clock.tick(60)

pygame.quit()



