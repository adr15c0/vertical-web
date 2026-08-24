"""
rooted_page.py — generator for the "Rooted" page (based on the "You Said Yes"
design language). Pure functions; output is Divi-native shortcodes.

Design tokens grounded from the live "You Said Yes" page (post 3177):
  fonts  : Neue Hass Display Medium v2 (headings) / Roman v2 (body)
  palette: sage #7d8871, green #27925C, cream #faf7e9, dark #2D2F33
  motifs : sage hero, FAQ toggles (green icon/text, FA f13a), white-border buttons

Content from docs/reference/rooted_page.md (banner, session details, video,
seven rhythms, FAQ, CTA). MUI used only as a layout reference (info row + card grid).
"""
from __future__ import annotations

BV = "4.27.4"
FONT_HEAD = "Neue Hass Display Medium v2|500|||||||"
FONT_HEAD_PLAIN = "Neue Hass Display Medium v2||||||||"
FONT_BODY = "Neue Hass Display Roman v2||||||||"

SAGE = "#7d8871"
GREEN = "#27925C"
CREAM = "#faf7e9"
DARK = "#2D2F33"
WHITE = "#FFFFFF"
BLACK = "#000000"


# --------------------------------------------------------------------------- #
# Shortcode helpers (mirror the site's real attribute shape)
# --------------------------------------------------------------------------- #
def _a(d: dict[str, str]) -> str:
    return "".join(f' {k}="{v}"' for k, v in d.items())


def sect(bg: str, inner: str, padding: str = "80px||80px||true|false",
         extra: dict | None = None) -> str:
    d = {"fb_built": "1", "_builder_version": BV, "_module_preset": "default",
         "background_color": bg, "custom_padding": padding, "global_colors_info": "{}"}
    if extra:
        d.update(extra)
    return f"[et_pb_section{_a(d)}]{inner}[/et_pb_section]"


def row(inner: str, struct: str | None = None, extra: dict | None = None) -> str:
    d: dict[str, str] = {}
    if struct:
        d["column_structure"] = struct
    d.update({"_builder_version": BV, "_module_preset": "default", "global_colors_info": "{}"})
    if extra:
        d.update(extra)
    return f"[et_pb_row{_a(d)}]{inner}[/et_pb_row]"


def col(inner: str, ctype: str = "4_4", extra: dict | None = None) -> str:
    d = {"type": ctype, "_builder_version": BV, "_module_preset": "default",
         "global_colors_info": "{}"}
    if extra:
        d.update(extra)
    return f"[et_pb_column{_a(d)}]{inner}[/et_pb_column]"


def text(content: str, extra: dict | None = None) -> str:
    d = {"_builder_version": BV, "_module_preset": "default", "global_colors_info": "{}"}
    if extra:
        d.update(extra)
    return f"[et_pb_text{_a(d)}]{content}[/et_pb_text]"


def toggle(title: str, body: str, is_open: bool) -> str:
    d = {
        "title": title, "open": "on" if is_open else "off",
        "open_toggle_text_color": GREEN, "open_toggle_background_color": WHITE,
        "closed_toggle_background_color": WHITE, "icon_color": GREEN,
        "toggle_icon": "&#xf13a;||fa||900", "open_icon_color": GREEN,
        "_builder_version": BV, "_module_preset": "default", "title_text_color": BLACK,
        "title_font": FONT_HEAD, "title_font_size": "22px",
        "closed_title_font": FONT_HEAD_PLAIN, "body_font": FONT_BODY,
        "custom_margin": "0px||0px||false|false", "global_colors_info": "{}",
    }
    return f"[et_pb_toggle{_a(d)}]{body}[/et_pb_toggle]"


def button(txt: str, url: str, bg: str = WHITE, fg: str = BLACK,
           extra: dict | None = None) -> str:
    d = {
        "button_url": url, "button_text": txt, "_builder_version": BV,
        "_module_preset": "default", "custom_button": "on",
        "button_text_color": fg, "button_bg_color": bg, "button_border_width": "3px",
        "button_border_color": bg, "button_font": FONT_HEAD,
        "custom_margin": "20px||||false|false", "global_colors_info": "{}",
    }
    if extra:
        d.update(extra)
    return f"[et_pb_button{_a(d)}][/et_pb_button]"


def video(src: str, thumb: str | None = None) -> str:
    d = {"src": src, "_builder_version": BV, "_module_preset": "default",
         "custom_margin": "30px||||false|false", "global_colors_info": "{}"}
    if thumb:
        d["image_src"] = thumb
    return f"[et_pb_video{_a(d)}][/et_pb_video]"


# --------------------------------------------------------------------------- #
# Content
# --------------------------------------------------------------------------- #
RHYTHMS = [
    ("Daily Devotion", "Acts 2:42, 46"),
    ("Prayer", "Acts 2:42"),
    ("Repentance", "Acts 2:37-39"),
    ("Sacrificial Generosity", "Acts 2:44-45"),
    ("Serve the Community", "Acts 2:44-45"),
    ("Share Your Story", "Acts 2:24-36"),
    ("Worship", "Acts 2:26-28, 46-47"),
]

FAQ = [
    ("Do You Offer Rooted Online?",
     "<p>At Vertical, Rooted is intentionally designed as an in-person experience. "
     "We believe spiritual growth happens best when people gather together—building "
     "authentic relationships, engaging in meaningful conversation, and walking "
     "alongside one another in biblical community. Because of this vision, we do not "
     "offer an online option.</p><p>If you're unable to participate in person, we "
     "encourage you to connect with a local church in your area. For any questions, "
     "please reach out to groups@goverticalchurch.com.</p>"),
    ("How Are Rooted Groups Formed?",
     "<p>Rooted groups are based on age and stage of life, with groups for men, women, "
     "or married couples. Groups typically include 10–12 people. While we do our best "
     "to honor friend or leader requests, placements may vary based on availability.</p>"),
    ("What If I Can't Make It Every Week?",
     "<p>Rooted is a 10-week experience, with groups meeting for two hours each week. "
     "For the best experience for you and your group, we ask participants to plan to "
     "miss no more than two weeks. If you already know you'll miss more than that, we "
     "recommend joining a future Rooted session.</p>"),
    ("What Happens After Rooted Ends?",
     "<p>After Rooted, groups are encouraged to continue meeting as an ongoing Group, "
     "growing in discipleship to Jesus in community.</p>"),
]

SIGNUP_URL = "https://vertical-web.ddev.site/rooted"
# Placeholder testimony video (creative swaps this in the Visual Builder).
VIDEO_SRC = "https://youtu.be/x6uJji_ZOLs"
VIDEO_THUMB = "https://vertical-web.ddev.site/wp-content/uploads/2025/04/thumb-eng.jpg"


def _hero() -> str:
    inner = col(
        text("Rooted", {"text_font": FONT_HEAD, "text_text_color": WHITE,
                        "text_font_size": "64px", "text_line_height": "1.1em",
                        "text_orientation": "center"})
        + text("A 10-week discipleship experience",
               {"text_font": FONT_HEAD, "text_text_color": WHITE,
                "text_font_size": "24px", "text_orientation": "center",
                "custom_margin": "||6px|||"})
        + text("Rooted helps you grow closer to God and find community through a group. "
               "Whether you're exploring what it means to follow Jesus, ready to grow "
               "deeper in your faith, or looking for people to do life with, Rooted is "
               "for you.",
               {"text_font": FONT_BODY, "text_text_color": WHITE,
                "text_font_size": "18px", "text_orientation": "center",
                "max_width": "760px", "module_alignment": "center"})
        + button("Sign Up for Rooted", SIGNUP_URL,
                 extra={"button_alignment": "center"})
    )
    return sect(SAGE, row(inner), padding="90px||80px||false|false")


def _details() -> str:
    def card(big: str, small: str) -> str:
        return col(
            text(big, {"text_font": FONT_HEAD, "text_text_color": GREEN,
                       "text_font_size": "30px", "text_orientation": "center"})
            + text(small, {"text_font": FONT_BODY, "text_text_color": DARK,
                           "text_font_size": "16px", "text_orientation": "center"}),
            "1_3",
            {"background_color": WHITE, "custom_padding": "28px|24px|28px|24px|true|true",
             "border_radii": "on|10px|10px|10px|10px", "box_shadow_style": "preset1"},
        )
    heading = row(col(text("Next Session",
                           {"text_font": FONT_HEAD, "text_text_color": DARK,
                            "text_font_size": "32px", "text_orientation": "center"})))
    cards = row(
        card("September 8", "Next session begins")
        + card("Weekly", "Times vary per campus & date")
        + card("$20", "Covers materials & your Rooted workbook"),
        "1_3,1_3,1_3",
    )
    return sect(CREAM, heading + cards)


def _video() -> str:
    inner = col(
        text("Hear from the Rooted Community",
             {"text_font": FONT_HEAD, "text_text_color": WHITE,
              "text_font_size": "32px", "text_orientation": "center"})
        + video(VIDEO_SRC, VIDEO_THUMB)
    )
    return sect(DARK, row(inner))


def _rhythms() -> str:
    def rcard(name: str, ref: str, ctype: str) -> str:
        return col(
            text(name, {"text_font": FONT_HEAD, "text_text_color": GREEN,
                        "text_font_size": "20px", "text_orientation": "center"})
            + text(ref, {"text_font": FONT_BODY, "text_text_color": DARK,
                         "text_font_size": "15px", "text_orientation": "center"}),
            ctype,
            {"background_color": CREAM, "custom_padding": "24px|18px|24px|18px|true|true",
             "border_radii": "on|10px|10px|10px|10px"},
        )
    intro = row(col(
        text("The Seven Rhythms",
             {"text_font": FONT_HEAD, "text_text_color": DARK,
              "text_font_size": "32px", "text_orientation": "center"})
        + text("Grounded in God's word, the seven rhythms are the foundation of the "
               "Rooted experience — each one practiced by the early church in Acts 2.",
               {"text_font": FONT_BODY, "text_text_color": DARK, "text_font_size": "18px",
                "text_orientation": "center", "max_width": "760px",
                "module_alignment": "center"})
    ))
    row1 = row("".join(rcard(n, r, "1_4") for n, r in RHYTHMS[:4]),
               "1_4,1_4,1_4,1_4")
    row2 = row("".join(rcard(n, r, "1_3") for n, r in RHYTHMS[4:]),
               "1_3,1_3,1_3")
    return sect(WHITE, intro + row1 + row2)


def _faq() -> str:
    heading = row(col(text("Frequently Asked Questions",
                           {"text_font": FONT_HEAD, "text_text_color": DARK,
                            "text_font_size": "32px", "text_orientation": "center"})))
    toggles = "".join(toggle(t, b, i == 0) for i, (t, b) in enumerate(FAQ))
    return sect(CREAM, heading + row(col(toggles)))


def _cta() -> str:
    inner = col(
        text("Ready to Put Down Roots?",
             {"text_font": FONT_HEAD, "text_text_color": WHITE,
              "text_font_size": "34px", "text_orientation": "center"})
        + text("Next session begins September 8. Spots fill up — sign up today.",
               {"text_font": FONT_BODY, "text_text_color": WHITE,
                "text_font_size": "18px", "text_orientation": "center"})
        + button("Sign Up for Rooted", SIGNUP_URL, bg=WHITE, fg=GREEN,
                 extra={"button_alignment": "center"})
        + text("Questions? groups@goverticalchurch.com",
               {"text_font": FONT_BODY, "text_text_color": WHITE, "text_font_size": "15px",
                "text_orientation": "center", "custom_margin": "16px||||false|false"})
    )
    return sect(GREEN, row(inner), padding="70px||70px||true|false")


def build_shortcodes() -> str:
    return _hero() + _details() + _video() + _rhythms() + _faq() + _cta()


def generate() -> dict:
    return {
        "title": "Rooted",
        "slug": "rooted",
        "based_on": {"page_id": 3177, "title": "You Said Yes"},
        "shortcodes": build_shortcodes(),
    }


if __name__ == "__main__":
    print(build_shortcodes())
