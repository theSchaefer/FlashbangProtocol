import base64
import struct
import sys

import cv2
from pyzbar.pyzbar import ZBarSymbol, decode

HEADER = struct.calcsize(">II")


def parse(text):
    """Base64-String -> (index, total, payload) oder None bei Schrott."""
    try:
        record = base64.b64decode(text, validate=True)
    except Exception:
        return None
    if len(record) < HEADER:
        return None
    idx, total = struct.unpack(">II", record[:HEADER])
    if total == 0 or idx >= total:
        return None
    return idx, total, record[HEADER:]


def main(out_path):
    cam = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    cam.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
    cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
    if not cam.isOpened():
        sys.exit("Keine Kamera gefunden.")

    chunks = {}
    total = None

    while True:
        ok, frame = cam.read()
        if not ok:
            continue

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        for result in decode(gray, symbols=[ZBarSymbol.QRCODE]):
            parsed = parse(result.data.decode("ascii", errors="ignore"))
            if parsed is None:
                continue
            idx, tot, payload = parsed
            total = tot
            chunks[idx] = payload

            r = result.rect
            cv2.rectangle(frame, (r.left, r.top),
                          (r.left + r.width, r.top + r.height), (0, 255, 0), 2)

        if total and len(chunks) == total:
            break

        status = f"{len(chunks)}/{total}" if total else f"{len(chunks)}/?"
        cv2.putText(frame, status, (20, 50),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.5, (0, 255, 0), 3)
        cv2.imshow("receiver (q = quit)", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cam.release()
    cv2.destroyAllWindows()

    if total and len(chunks) == total:
        with open(out_path, "wb") as f:
            for i in range(total):
                f.write(chunks[i])
        print(f"Fertig: {out_path} ({sum(len(c) for c in chunks.values())} Bytes)")
    else:
        missing = sorted(set(range(total)) - set(chunks)) if total else []
        print(f"Abgebrochen. Fehlend: {missing[:20]}{' ...' if len(missing) > 20 else ''}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "output.bin")
