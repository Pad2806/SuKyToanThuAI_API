"""
services/google_slides_service.py
Tạo Google Slides presentation trong Drive của USER bằng OAuth2 access token.
FE lấy token qua Google Sign-In → gửi cho backend → backend dùng token tạo slides.
"""
import logging
import uuid

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)

# Colors (RGB 0-1 float)
CREAM = {"red": 0.96, "green": 0.94, "blue": 0.91}
BROWN = {"red": 0.36, "green": 0.23, "blue": 0.10}
ACCENT = {"red": 0.55, "green": 0.37, "blue": 0.20}
WHITE = {"red": 1, "green": 1, "blue": 1}
DARK_BROWN = {"red": 0.24, "green": 0.13, "blue": 0.06}
GOLD = {"red": 0.83, "green": 0.66, "blue": 0.26}


def create_presentation_with_user_token(
    access_token: str, title: str, slides_data: list[dict]
) -> dict:
    """
    Tạo Google Slides trong Drive của user bằng OAuth2 access token.

    Returns: { presentation_id, presentation_url }
    """
    creds = Credentials(token=access_token)
    slides_svc = build("slides", "v1", credentials=creds)

    # 1. Tạo presentation
    pres = slides_svc.presentations().create(body={"title": title}).execute()
    pres_id = pres["presentationId"]
    logger.info("Created presentation: %s", pres_id)

    # 2. Xóa slide mặc định
    default_slide_id = pres["slides"][0]["objectId"]
    slides_svc.presentations().batchUpdate(
        presentationId=pres_id,
        body={"requests": [{"deleteObject": {"objectId": default_slide_id}}]},
    ).execute()

    # 3. Thêm slides
    requests = []
    for sd in sorted(slides_data, key=lambda s: s.get("slide_order", 0)):
        layout = sd.get("layout_type", "content")
        reqs = _build_slide_requests(sd, layout)
        requests.extend(reqs)

    if requests:
        slides_svc.presentations().batchUpdate(
            presentationId=pres_id, body={"requests": requests}
        ).execute()

    url = f"https://docs.google.com/presentation/d/{pres_id}/edit"
    logger.info("Presentation URL: %s", url)

    return {"presentation_id": pres_id, "presentation_url": url}


def _emu(inches):
    return int(inches * 914400)


def _uid():
    return uuid.uuid4().hex[:10]


def _create_textbox(slide_id, obj_id, left, top, width, height, text,
                     font_size=14, bold=False, italic=False, color=BROWN,
                     font="Calibri", alignment="START"):
    return [
        {
            "createShape": {
                "objectId": obj_id,
                "shapeType": "TEXT_BOX",
                "elementProperties": {
                    "pageObjectId": slide_id,
                    "size": {"width": {"magnitude": _emu(width), "unit": "EMU"},
                             "height": {"magnitude": _emu(height), "unit": "EMU"}},
                    "transform": {"scaleX": 1, "scaleY": 1,
                                  "translateX": _emu(left), "translateY": _emu(top), "unit": "EMU"},
                },
            }
        },
        {"insertText": {"objectId": obj_id, "text": text, "insertionIndex": 0}},
        {
            "updateTextStyle": {
                "objectId": obj_id,
                "style": {
                    "fontSize": {"magnitude": font_size, "unit": "PT"},
                    "fontFamily": font, "bold": bold, "italic": italic,
                    "foregroundColor": {"opaqueColor": {"rgbColor": color}},
                },
                "textRange": {"type": "ALL"},
                "fields": "fontSize,fontFamily,bold,italic,foregroundColor",
            }
        },
        {
            "updateParagraphStyle": {
                "objectId": obj_id,
                "style": {"alignment": alignment},
                "textRange": {"type": "ALL"},
                "fields": "alignment",
            }
        },
    ]


def _create_rect(slide_id, obj_id, left, top, width, height, fill_color):
    return [
        {
            "createShape": {
                "objectId": obj_id,
                "shapeType": "RECTANGLE",
                "elementProperties": {
                    "pageObjectId": slide_id,
                    "size": {"width": {"magnitude": _emu(width), "unit": "EMU"},
                             "height": {"magnitude": _emu(height), "unit": "EMU"}},
                    "transform": {"scaleX": 1, "scaleY": 1,
                                  "translateX": _emu(left), "translateY": _emu(top), "unit": "EMU"},
                },
            }
        },
        {
            "updateShapeProperties": {
                "objectId": obj_id,
                "shapeProperties": {
                    "shapeBackgroundFill": {"solidFill": {"color": {"rgbColor": fill_color}}},
                    "outline": {"outlineFill": {"solidFill": {"color": {"rgbColor": fill_color}}}},
                },
                "fields": "shapeBackgroundFill,outline",
            }
        },
    ]


def _build_slide_requests(sd, layout):
    slide_id = f"s_{_uid()}"
    reqs = [{"createSlide": {"objectId": slide_id, "insertionIndex": sd.get("slide_order", 1) - 1}}]

    bg = DARK_BROWN if layout == "section_divider" else CREAM
    reqs.append({
        "updatePageProperties": {
            "objectId": slide_id,
            "pageProperties": {"pageBackgroundFill": {"solidFill": {"color": {"rgbColor": bg}}}},
            "fields": "pageBackgroundFill",
        }
    })

    builders = {
        "title": _title_slide,
        "section_divider": _section_divider,
        "two_column": _two_column_slide,
        "timeline": _timeline_slide,
        "summary": _summary_slide,
        "quote": _quote_slide,
        "table": _table_slide,
    }
    builder = builders.get(layout, _content_slide)
    reqs.extend(builder(slide_id, sd))
    return reqs


def _title_slide(sid, sd):
    r = []
    r.extend(_create_textbox(sid, f"t_{_uid()}", 1, 2, 11, 1.5,
                              sd.get("title", ""), 44, True, font="Georgia", alignment="CENTER"))
    if sd.get("subtitle"):
        r.extend(_create_textbox(sid, f"t_{_uid()}", 2, 3.8, 9, 0.6,
                                  sd["subtitle"], 16, color=ACCENT, alignment="CENTER"))
    r.extend(_create_rect(sid, f"r_{_uid()}", 5.5, 4.6, 2, 0.03, ACCENT))
    if sd.get("content"):
        r.extend(_create_textbox(sid, f"t_{_uid()}", 3, 4.9, 7, 0.4,
                                  sd["content"], 13, color=ACCENT, alignment="CENTER"))
    return r


def _content_slide(sid, sd):
    r = []
    r.extend(_create_rect(sid, f"r_{_uid()}", 0.5, 0.4, 0.06, 0.5, ACCENT))
    r.extend(_create_textbox(sid, f"t_{_uid()}", 0.75, 0.35, 8, 0.6,
                              sd.get("title", ""), 26, True, font="Georgia"))
    y = 1.2
    if sd.get("content"):
        r.extend(_create_textbox(sid, f"t_{_uid()}", 0.75, y, 7, 0.6,
                                  sd["content"], 12, italic=True, color=ACCENT))
        y += 0.7
    bullets = sd.get("bullets", [])
    if bullets:
        r.extend(_create_textbox(sid, f"t_{_uid()}", 0.75, y, 7, 3,
                                  "\n".join(f"●  {b}" for b in bullets[:5]), 12))
    return r


def _two_column_slide(sid, sd):
    r = []
    r.extend(_create_rect(sid, f"r_{_uid()}", 0.5, 0.4, 0.06, 0.5, ACCENT))
    r.extend(_create_textbox(sid, f"t_{_uid()}", 0.75, 0.35, 8, 0.6,
                              sd.get("title", ""), 26, True, font="Georgia"))
    for i, col in enumerate(sd.get("columns", [])[:3]):
        left = 0.6 + i * 5.8
        r.extend(_create_rect(sid, f"r_{_uid()}", left, 1.5, 5.2, 4.5, WHITE))
        r.extend(_create_rect(sid, f"r_{_uid()}", left, 5.95, 5.2, 0.05, ACCENT))
        r.extend(_create_textbox(sid, f"t_{_uid()}", left + 0.3, 2, 4.6, 0.5,
                                  col.get("heading", ""), 16, True, font="Georgia", alignment="CENTER"))
        r.extend(_create_textbox(sid, f"t_{_uid()}", left + 0.3, 2.7, 4.6, 2.5,
                                  col.get("text", ""), 11, color=ACCENT, alignment="CENTER"))
    return r


def _timeline_slide(sid, sd):
    r = []
    r.extend(_create_rect(sid, f"r_{_uid()}", 0.5, 0.4, 0.06, 0.5, ACCENT))
    r.extend(_create_textbox(sid, f"t_{_uid()}", 0.75, 0.35, 8, 0.6,
                              sd.get("title", ""), 26, True, font="Georgia"))
    events = sd.get("events", [])
    n = min(len(events), 4)
    cw = 11.5 / max(n, 1)
    for i, ev in enumerate(events[:4]):
        left = 0.5 + i * (cw + 0.15)
        r.extend(_create_rect(sid, f"r_{_uid()}", left, 1.5, cw - 0.15, 4.5, WHITE))
        r.extend(_create_rect(sid, f"r_{_uid()}", left, 5.95, cw - 0.15, 0.05, ACCENT))
        place = ev.get("place", ev.get("year", ""))
        r.extend(_create_textbox(sid, f"t_{_uid()}", left + 0.2, 1.8, cw - 0.5, 0.4,
                                  place, 14, True, font="Georgia", alignment="CENTER"))
        if ev.get("year") and ev.get("place"):
            r.extend(_create_textbox(sid, f"t_{_uid()}", left + 0.2, 2.3, cw - 0.5, 0.3,
                                      ev["year"], 10, color=ACCENT, alignment="CENTER"))
        r.extend(_create_textbox(sid, f"t_{_uid()}", left + 0.2, 2.8, cw - 0.5, 2.5,
                                  ev.get("text", ""), 10, color=ACCENT, alignment="CENTER"))
    return r


def _summary_slide(sid, sd):
    r = []
    r.extend(_create_textbox(sid, f"t_{_uid()}", 1, 0.5, 11, 0.8,
                              sd.get("title", ""), 32, True, font="Georgia", alignment="CENTER"))
    if sd.get("subtitle"):
        r.extend(_create_textbox(sid, f"t_{_uid()}", 2, 1.3, 9, 0.4,
                                  sd["subtitle"], 13, italic=True, color=ACCENT, alignment="CENTER"))
    bullets = sd.get("bullets", [])
    n = min(len(bullets), 3)
    cw = 3.5
    sx = (13.333 - n * cw - (n - 1) * 0.3) / 2
    for i, b in enumerate(bullets[:3]):
        left = sx + i * (cw + 0.3)
        r.extend(_create_rect(sid, f"r_{_uid()}", left, 2.2, cw, 3, WHITE))
        r.extend(_create_rect(sid, f"r_{_uid()}", left, 5.15, cw, 0.05, ACCENT))
        r.extend(_create_textbox(sid, f"t_{_uid()}", left + 0.2, 2.8, cw - 0.4, 2,
                                  b, 12, color=ACCENT, alignment="CENTER"))
    if sd.get("footer_text"):
        r.extend(_create_textbox(sid, f"t_{_uid()}", 1, 5.8, 11, 0.4,
                                  sd["footer_text"], 12, italic=True, color=ACCENT, alignment="CENTER"))
    return r


def _quote_slide(sid, sd):
    r = []
    r.extend(_create_rect(sid, f"r_{_uid()}", 0.5, 0.4, 0.06, 0.5, ACCENT))
    r.extend(_create_textbox(sid, f"t_{_uid()}", 0.75, 0.35, 8, 0.6,
                              sd.get("title", ""), 26, True, font="Georgia"))
    quote = sd.get("quote_text", sd.get("content", ""))
    r.extend(_create_textbox(sid, f"t_{_uid()}", 1.5, 1.8, 10, 2.5,
                              f'"{quote}"', 18, italic=True, font="Georgia", alignment="CENTER"))
    if sd.get("quote_author"):
        r.extend(_create_textbox(sid, f"t_{_uid()}", 2, 4.5, 9, 0.4,
                                  f"— {sd['quote_author']}", 13, italic=True, color=ACCENT, alignment="CENTER"))
    return r


def _table_slide(sid, sd):
    r = []
    r.extend(_create_rect(sid, f"r_{_uid()}", 0.5, 0.4, 0.06, 0.5, ACCENT))
    r.extend(_create_textbox(sid, f"t_{_uid()}", 0.75, 0.35, 8, 0.6,
                              sd.get("title", ""), 26, True, font="Georgia"))
    headers = sd.get("table_headers", [])
    rows = sd.get("table_rows", [])
    if headers and rows:
        tid = f"tbl_{_uid()}"
        nr, nc = len(rows) + 1, len(headers)
        r.append({
            "createTable": {
                "objectId": tid,
                "elementProperties": {
                    "pageObjectId": sid,
                    "size": {"width": {"magnitude": _emu(11), "unit": "EMU"},
                             "height": {"magnitude": _emu(0.4 * nr), "unit": "EMU"}},
                    "transform": {"scaleX": 1, "scaleY": 1,
                                  "translateX": _emu(1), "translateY": _emu(1.4), "unit": "EMU"},
                },
                "rows": nr, "columns": nc,
            }
        })
        for j, h in enumerate(headers):
            r.append({"insertText": {"objectId": tid, "cellLocation": {"rowIndex": 0, "columnIndex": j},
                                      "text": h, "insertionIndex": 0}})
        for i, row in enumerate(rows):
            for j, val in enumerate(row):
                r.append({"insertText": {"objectId": tid, "cellLocation": {"rowIndex": i + 1, "columnIndex": j},
                                          "text": str(val), "insertionIndex": 0}})
    if sd.get("footer_text"):
        r.extend(_create_textbox(sid, f"t_{_uid()}", 1, 5.8, 11, 0.4,
                                  sd["footer_text"], 12, italic=True, color=ACCENT, alignment="CENTER"))
    return r


def _section_divider(sid, sd):
    r = []
    r.extend(_create_rect(sid, f"r_{_uid()}", 5.5, 2.5, 2, 0.02, GOLD))
    r.extend(_create_textbox(sid, f"t_{_uid()}", 1, 2.8, 11, 1,
                              sd.get("title", ""), 36, True, color=CREAM, font="Georgia", alignment="CENTER"))
    if sd.get("subtitle"):
        r.extend(_create_textbox(sid, f"t_{_uid()}", 2, 3.9, 9, 0.5,
                                  sd["subtitle"], 15, italic=True, color=GOLD, alignment="CENTER"))
    r.extend(_create_rect(sid, f"r_{_uid()}", 5.5, 4.6, 2, 0.02, GOLD))
    return r
