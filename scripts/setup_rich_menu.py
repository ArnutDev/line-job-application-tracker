"""Script to generate, upload, and set default LINE Rich Menu for JobTrack.

Usage:
    # 1. Generate image only (preview)
    python scripts/setup_rich_menu.py --action generate-only

    # 2. Full setup: generate image, create rich menu, upload, and set as default
    python scripts/setup_rich_menu.py --action create

    # 3. List all current rich menus
    python scripts/setup_rich_menu.py --action list

    # 4. Delete all existing rich menus
    python scripts/setup_rich_menu.py --action delete-all
"""

import argparse
from io import BytesIO
import json
import os
from pathlib import Path
import sys
import urllib.error
import urllib.request

from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont

# Set UTF-8 encoding for console output on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Load backend/.env if present
env_path = Path(__file__).resolve().parent.parent / "backend" / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)

LINE_API_BASE = "https://api.line.me/v2/bot"
LINE_DATA_API_BASE = "https://api-data.line.me/v2/bot"

WIDTH = 2500
HEIGHT = 1686


def get_font(size: int, bold: bool = False) -> ImageFont.ImageFont:
    """Find and return an appropriate TrueType font with Thai support."""
    font_candidates = [
        "C:\\Windows\\Fonts\\tahomabd.ttf" if bold else "C:\\Windows\\Fonts\\tahoma.ttf",
        "C:\\Windows\\Fonts\\segoeuib.ttf" if bold else "C:\\Windows\\Fonts\\segoeui.ttf",
        "C:\\Windows\\Fonts\\arialbd.ttf" if bold else "C:\\Windows\\Fonts\\arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
        if bold
        else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/System/Library/Fonts/Thonburi.ttc",
    ]
    for path in font_candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                pass
    return ImageFont.load_default()


def generate_rich_menu_image(output_path: str | None = None) -> bytes:
    """Generate high-resolution 2500x1686 2x2 grid Rich Menu image."""
    img = Image.new("RGB", (WIDTH, HEIGHT), "#0F172A")  # Dark slate background
    draw = ImageDraw.Draw(img)

    half_w = WIDTH // 2  # 1250
    half_h = HEIGHT // 2  # 843
    pad = 20
    radius = 36

    # 4 Quadrants specification
    quadrants = [
        {
            "rect": (pad, pad, half_w - pad, half_h - pad),
            "bg": "#2563EB",  # Royal Blue
            "badge_color": "#1D4ED8",
            "icon_type": "plus",
            "title": "บันทึกงานใหม่",
            "sub": "เพิ่มงานที่สมัครลงระบบ",
        },
        {
            "rect": (half_w + pad, pad, WIDTH - pad, half_h - pad),
            "bg": "#0D9488",  # Teal
            "badge_color": "#0F766E",
            "icon_type": "list",
            "title": "รายการสมัครงาน",
            "sub": "ดูประวัติและสถานะงานทั้งหมด",
        },
        {
            "rect": (pad, half_h + pad, half_w - pad, HEIGHT - pad),
            "bg": "#D97706",  # Amber / Warm Orange
            "badge_color": "#B45309",
            "icon_type": "chart",
            "title": "สรุปสถิติ",
            "sub": "ดูจำนวนงานแยกตามสถานะ",
        },
        {
            "rect": (half_w + pad, half_h + pad, WIDTH - pad, HEIGHT - pad),
            "bg": "#16A34A",  # Emerald Green (Excel)
            "badge_color": "#15803D",
            "icon_type": "download",
            "title": "ส่งออก Excel",
            "sub": "ดาวน์โหลดไฟล์ .xlsx พร้อมใช้",
        },
    ]

    title_font = get_font(84, bold=True)
    sub_font = get_font(44, bold=False)

    for q in quadrants:
        x0, y0, x1, y1 = q["rect"]
        cx = (x0 + x1) // 2
        cy = (y0 + y1) // 2

        # Draw card rounded rectangle
        draw.rounded_rectangle([x0, y0, x1, y1], radius=radius, fill=q["bg"])

        # Draw icon badge circle
        badge_r = 105
        badge_cy = y0 + 260
        draw.ellipse(
            [cx - badge_r, badge_cy - badge_r, cx + badge_r, badge_cy + badge_r],
            fill="#FFFFFF",
        )

        # Draw vector icon inside badge
        c_fill = q["bg"]
        icon = q["icon_type"]

        if icon == "plus":
            # Clean plus symbol
            bar_w = 18
            bar_len = 52
            draw.rectangle(
                [cx - bar_len, badge_cy - bar_w // 2, cx + bar_len, badge_cy + bar_w // 2],
                fill=c_fill,
            )
            draw.rectangle(
                [cx - bar_w // 2, badge_cy - bar_len, cx + bar_w // 2, badge_cy + bar_len],
                fill=c_fill,
            )
        elif icon == "list":
            # Clipboard / Checklist
            cw = 50
            ch = 64
            draw.rounded_rectangle(
                [cx - cw, badge_cy - ch, cx + cw, badge_cy + ch],
                radius=10,
                outline=c_fill,
                width=10,
            )
            # Clip top
            draw.rectangle([cx - 22, badge_cy - ch - 10, cx + 22, badge_cy - ch + 6], fill=c_fill)
            # 3 lines
            draw.line([(cx - 30, badge_cy - 20), (cx + 30, badge_cy - 20)], fill=c_fill, width=8)
            draw.line([(cx - 30, badge_cy + 10), (cx + 30, badge_cy + 10)], fill=c_fill, width=8)
            draw.line([(cx - 30, badge_cy + 40), (cx + 15, badge_cy + 40)], fill=c_fill, width=8)
        elif icon == "chart":
            # 3 vertical bar charts
            draw.rounded_rectangle([cx - 52, badge_cy + 5, cx - 22, badge_cy + 60], radius=6, fill=c_fill)
            draw.rounded_rectangle([cx - 15, badge_cy - 30, cx + 15, badge_cy + 60], radius=6, fill=c_fill)
            draw.rounded_rectangle([cx + 22, badge_cy - 60, cx + 52, badge_cy + 60], radius=6, fill=c_fill)
        elif icon == "download":
            # Download arrow + tray
            aw = 16
            draw.rectangle([cx - aw // 2, badge_cy - 60, cx + aw // 2, badge_cy + 10], fill=c_fill)
            # Arrow head
            draw.polygon(
                [(cx - 46, badge_cy + 5), (cx + 46, badge_cy + 5), (cx, badge_cy + 48)],
                fill=c_fill,
            )
            # Tray line
            draw.line([(cx - 54, badge_cy + 62), (cx + 54, badge_cy + 62)], fill=c_fill, width=12)

        # Draw Title
        title_bbox = draw.textbbox((0, 0), q["title"], font=title_font)
        title_w = title_bbox[2] - title_bbox[0]
        title_x = cx - title_w // 2
        title_y = y0 + 440
        draw.text((title_x, title_y), q["title"], font=title_font, fill="#FFFFFF")

        # Draw Subtitle
        sub_bbox = draw.textbbox((0, 0), q["sub"], font=sub_font)
        sub_w = sub_bbox[2] - sub_bbox[0]
        sub_x = cx - sub_w // 2
        sub_y = y0 + 560
        draw.text((sub_x, sub_y), q["sub"], font=sub_font, fill="#E2E8F0")

    # Save to file if output path provided
    buf = BytesIO()
    img.save(buf, format="PNG")
    png_bytes = buf.getvalue()

    if output_path:
        out_file = Path(output_path)
        out_file.parent.mkdir(parents=True, exist_ok=True)
        with open(out_file, "wb") as f:
            f.write(png_bytes)
        print(f"Rich Menu image saved successfully to: {out_file.resolve()}")

    return png_bytes


def create_rich_menu_object(access_token: str) -> str:
    """Create Rich Menu definition via LINE Messaging API and return richMenuId."""
    half_w = WIDTH // 2  # 1250
    half_h = HEIGHT // 2  # 843

    payload = {
        "size": {"width": WIDTH, "height": HEIGHT},
        "selected": True,
        "name": "JobTrack Main Menu",
        "chatBarText": "📌 เมนูหลัก",
        "areas": [
            {
                "bounds": {"x": 0, "y": 0, "width": half_w, "height": half_h},
                "action": {
                    "type": "message",
                    "label": "บันทึกงานใหม่",
                    "text": "ต้องการบันทึกการสมัครงานใหม่",
                },
            },
            {
                "bounds": {"x": half_w, "y": 0, "width": half_w, "height": half_h},
                "action": {
                    "type": "message",
                    "label": "รายการสมัครงาน",
                    "text": "ดูรายการสมัครงานทั้งหมด",
                },
            },
            {
                "bounds": {"x": 0, "y": half_h, "width": half_w, "height": half_h},
                "action": {
                    "type": "message",
                    "label": "สรุปสถิติ",
                    "text": "สรุปข้อมูลการสมัครงาน",
                },
            },
            {
                "bounds": {"x": half_w, "y": half_h, "width": half_w, "height": half_h},
                "action": {
                    "type": "message",
                    "label": "ส่งออก Excel",
                    "text": "ขอ export ไฟล์ excel",
                },
            },
        ],
    }

    req = urllib.request.Request(
        f"{LINE_API_BASE}/richmenu",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {access_token}",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as res:
            data = json.loads(res.read().decode("utf-8"))
            rich_menu_id = data["richMenuId"]
            print(f"Created Rich Menu ID: {rich_menu_id}")
            return rich_menu_id
    except urllib.error.HTTPError as e:
        err = e.read().decode("utf-8", errors="replace")
        print(f"Error creating Rich Menu: {e.code} - {err}", file=sys.stderr)
        raise


def upload_rich_menu_image(access_token: str, rich_menu_id: str, image_bytes: bytes) -> bool:
    """Upload PNG image to the created Rich Menu."""
    url = f"{LINE_DATA_API_BASE}/richmenu/{rich_menu_id}/content"
    req = urllib.request.Request(
        url,
        data=image_bytes,
        headers={
            "Content-Type": "image/png",
            "Authorization": f"Bearer {access_token}",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as res:
            if res.status in (200, 201):
                print(f"Uploaded Rich Menu image successfully for {rich_menu_id}")
                return True
            print(f"Upload returned status {res.status}", file=sys.stderr)
            return False
    except urllib.error.HTTPError as e:
        err = e.read().decode("utf-8", errors="replace")
        print(f"Error uploading Rich Menu image: {e.code} - {err}", file=sys.stderr)
        raise


def set_default_rich_menu(access_token: str, rich_menu_id: str) -> bool:
    """Set the Rich Menu as default for all users."""
    url = f"{LINE_API_BASE}/user/all/richmenu/{rich_menu_id}"
    req = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {access_token}"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as res:
            if res.status == 200:
                print(f"Set Rich Menu {rich_menu_id} as default for ALL users! 🎉")
                return True
            return False
    except urllib.error.HTTPError as e:
        err = e.read().decode("utf-8", errors="replace")
        print(f"Error setting default Rich Menu: {e.code} - {err}", file=sys.stderr)
        raise


def list_rich_menus(access_token: str) -> list[dict]:
    """Fetch and list all existing Rich Menus."""
    url = f"{LINE_API_BASE}/richmenu/list"
    req = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {access_token}"},
        method="GET",
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as res:
            data = json.loads(res.read().decode("utf-8"))
            menus = data.get("richmenus", [])
            print(f"Found {len(menus)} Rich Menus:")
            for m in menus:
                print(f" - ID: {m.get('richMenuId')} | Name: '{m.get('name')}' | Bar: '{m.get('chatBarText')}'")
            return menus
    except urllib.error.HTTPError as e:
        err = e.read().decode("utf-8", errors="replace")
        print(f"Error listing Rich Menus: {e.code} - {err}", file=sys.stderr)
        return []


def delete_all_rich_menus(access_token: str) -> int:
    """Delete all existing Rich Menus from the LINE channel."""
    menus = list_rich_menus(access_token)
    deleted_count = 0
    for m in menus:
        menu_id = m.get("richMenuId")
        url = f"{LINE_API_BASE}/richmenu/{menu_id}"
        req = urllib.request.Request(
            url,
            headers={"Authorization": f"Bearer {access_token}"},
            method="DELETE",
        )
        try:
            with urllib.request.urlopen(req, timeout=15):
                print(f"Deleted Rich Menu {menu_id}")
                deleted_count += 1
        except Exception as e:
            print(f"Failed to delete {menu_id}: {e}", file=sys.stderr)

    print(f"Deleted {deleted_count} Rich Menu(s).")
    return deleted_count


def main():
    parser = argparse.ArgumentParser(description="LINE Rich Menu Setup for JobTrack")
    parser.add_argument(
        "--action",
        choices=["create", "generate-only", "list", "delete-all"],
        default="create",
        help="Action to perform (default: create)",
    )
    parser.add_argument(
        "--token",
        default=os.getenv("LINE_CHANNEL_ACCESS_TOKEN"),
        help="LINE Channel Access Token (defaults to LINE_CHANNEL_ACCESS_TOKEN env var)",
    )
    parser.add_argument(
        "--output",
        default="scripts/rich_menu.png",
        help="Output file path for generated Rich Menu PNG",
    )

    args = parser.parse_args()

    if args.action == "generate-only":
        print("Generating Rich Menu image...")
        generate_rich_menu_image(args.output)
        return

    if not args.token:
        print(
            "Error: LINE_CHANNEL_ACCESS_TOKEN is not set. "
            "Please configure it in backend/.env or pass via --token.",
            file=sys.stderr,
        )
        sys.exit(1)

    if args.action == "list":
        list_rich_menus(args.token)
    elif args.action == "delete-all":
        delete_all_rich_menus(args.token)
    elif args.action == "create":
        print("1. Generating Rich Menu image (2500x1686)...")
        img_bytes = generate_rich_menu_image(args.output)

        print("2. Creating Rich Menu object on LINE...")
        rich_menu_id = create_rich_menu_object(args.token)

        print("3. Uploading Rich Menu image...")
        upload_rich_menu_image(args.token, rich_menu_id, img_bytes)

        print("4. Setting Rich Menu as default for all users...")
        set_default_rich_menu(args.token, rich_menu_id)

        print("\n✅ Rich Menu setup complete! Users opening the LINE chat will see the new menu immediately.")


if __name__ == "__main__":
    main()
