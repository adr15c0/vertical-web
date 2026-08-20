"""
hero_card.py — Divi asset generator for the pipeline POC (issue #8).

Pure functions (no side effects): given brand tokens, produce
  * a Divi Library layout (hero + 3 cards) as Divi shortcodes,
  * a Divi Library **portability JSON** (the format Divi's Import/Export uses),
  * a module **preset** for et_pb_button,
using MUI (clean hero + card grid) purely as a *design reference* — the output
is 100% Divi-native and uses only CORE et_pb_* modules (no add-on dependency).

Grounded on the live site's real formats: sections carry fb_built="1", every
module carries _builder_version / _module_preset / global_colors_info.
"""
from __future__ import annotations

import json
import uuid
from typing import Any

BUILDER_VERSION = "4.27.7"

# Brand Global Colors (gcid -> hex), grounded from et_divi.et_global_colors.
GLOBAL_COLORS: dict[str, str] = {
    "gcid-2ebbc52c-9ee6-4712-a077-fcaec9b98540": "#15c586",  # brand green
    "gcid-2bb820f4-8993-4899-8850-c73e9c1e988e": "rgba(0,0,0,0.2)",
    "gcid-b70c6ec4-3d09-43b5-80df-154e6e990bf3": "#2b79ee",  # brand blue
    "gcid-b6c4f12c-f25d-4f61-9fb1-6e96404634cd": "#f4f4f4",  # light gray
    "gcid-53054839-b83d-4ef0-8659-8a010e6148fd": "#333333",  # dark gray
}
GC_GREEN = "gcid-2ebbc52c-9ee6-4712-a077-fcaec9b98540"
GC_LIGHT = "gcid-b6c4f12c-f25d-4f61-9fb1-6e96404634cd"

# Three MUI-inspired feature cards.
CARDS = [
    {"title": "Plan a Visit", "body": "New here? Find service times and what to expect on your first Sunday."},
    {"title": "Watch Online", "body": "Can't make it in person? Join the live stream in English and Español."},
    {"title": "Get Connected", "body": "Join a group, serve on a team, and grow together in community."},
]


def _attrs(d: dict[str, str]) -> str:
    """Render shortcode attributes (values already Divi-encoded where needed)."""
    return "".join(f' {k}="{v}"' for k, v in d.items())


def _gc_info(mapping: dict[str, list[str]] | None = None) -> str:
    """Divi encodes global_colors_info as HTML-entity-quoted JSON."""
    payload = json.dumps(mapping or {}, separators=(",", ":"))
    return payload.replace('"', "&quot;")


def build_button_preset() -> tuple[str, dict[str, Any]]:
    """A selectable et_pb_button preset styled in brand colors."""
    preset_id = f"gid-poc-{uuid.uuid4().hex[:12]}"
    preset = {
        "name": "Brand Primary Button (POC)",
        "created": 0,
        "updated": 0,
        "version": BUILDER_VERSION,
        "is_temp": False,
        "settings": {
            "custom_button": "on",
            "button_text_color": "#ffffff",
            "button_bg_color": "#15c586",
            "button_border_width": "0px",
            "button_border_radius": "6px",
            "button_font": "|700|||||||",
            "button_use_icon": "off",
            "custom_padding": "14px|32px|14px|32px|true|true",
        },
    }
    return preset_id, preset


def build_layout_shortcodes(button_preset_id: str) -> str:
    """Hero (brand-green background + preset button) + a 3-card feature row."""
    gc_empty = _gc_info()

    # Note: modules keep global_colors_info="{}" (the proven-safe pattern used by
    # the site's own content). We do NOT embed a gcid->[attr] map in the shortcode:
    # its inner `]` breaks WordPress's shortcode parser at render. The brand palette
    # is still generated and pushed to et_global_colors so it's selectable in the VB.
    # --- Hero section: brand-green background, hex value ---
    hero = (
        f'[et_pb_section fb_built="1" _builder_version="{BUILDER_VERSION}" '
        f'_module_preset="default" background_color="{GLOBAL_COLORS[GC_GREEN]}" '
        f'custom_padding="120px||120px||true|false" global_colors_info="{gc_empty}"]'
        f'[et_pb_row _builder_version="{BUILDER_VERSION}" _module_preset="default" '
        f'global_colors_info="{gc_empty}"]'
        f'[et_pb_column type="4_4" _builder_version="{BUILDER_VERSION}" '
        f'_module_preset="default" global_colors_info="{gc_empty}"]'
        f'[et_pb_text _builder_version="{BUILDER_VERSION}" _module_preset="default" '
        f'header_font="|700|||||||" header_text_color="#ffffff" header_font_size="52px" '
        f'text_orientation="center" global_colors_info="{gc_empty}"]'
        f"<h1>One Church. Two Languages.</h1>"
        f"[/et_pb_text]"
        f'[et_pb_text _builder_version="{BUILDER_VERSION}" _module_preset="default" '
        f'text_text_color="#ffffff" text_font_size="20px" text_orientation="center" '
        f'custom_margin="10px||30px||false|false" global_colors_info="{gc_empty}"]'
        f"<p>Worship with us in English and Español — in person and online.</p>"
        f"[/et_pb_text]"
        f'[et_pb_button button_text="Plan Your Visit" button_url="/plan-a-visit" '
        f'button_alignment="center" _builder_version="{BUILDER_VERSION}" '
        f'_module_preset="{button_preset_id}" global_colors_info="{gc_empty}"]'
        f"[/et_pb_button]"
        f"[/et_pb_column][/et_pb_row][/et_pb_section]"
    )

    # --- Card section: 3 feature cards on a light background ---
    cols = []
    for c in CARDS:
        cols.append(
            f'[et_pb_column type="1_3" _builder_version="{BUILDER_VERSION}" '
            f'_module_preset="default" background_color="#ffffff" '
            f'custom_padding="30px|30px|30px|30px|true|true" '
            f'border_radii="on|8px|8px|8px|8px" '
            f'box_shadow_style="preset2" global_colors_info="{gc_empty}"]'
            f'[et_pb_text _builder_version="{BUILDER_VERSION}" _module_preset="default" '
            f'header_font="|700|||||||" header_text_color="#333333" '
            f'global_colors_info="{gc_empty}"]'
            f"<h3>{c['title']}</h3>"
            f"[/et_pb_text]"
            f'[et_pb_text _builder_version="{BUILDER_VERSION}" _module_preset="default" '
            f'text_text_color="#333333" global_colors_info="{gc_empty}"]'
            f"<p>{c['body']}</p>"
            f"[/et_pb_text]"
            f"[/et_pb_column]"
        )
    cards = (
        f'[et_pb_section fb_built="1" _builder_version="{BUILDER_VERSION}" '
        f'_module_preset="default" background_color="#f4f4f4" '
        f'custom_padding="80px||80px||true|false" global_colors_info="{gc_empty}"]'
        f'[et_pb_row column_structure="1_3,1_3,1_3" _builder_version="{BUILDER_VERSION}" '
        f'_module_preset="default" global_colors_info="{gc_empty}"]'
        + "".join(cols)
        + "[/et_pb_row][/et_pb_section]"
    )
    return hero + cards


def build_portability_json(shortcodes: str, preset_id: str,
                           preset: dict[str, Any]) -> dict[str, Any]:
    """The Divi Library export format (context et_builder)."""
    return {
        "context": "et_builder",
        "data": {"1": shortcodes},
        "presets": {
            "et_pb_button": {
                "default": "_initial",
                "presets": {preset_id: preset},
            }
        },
        "global_colors": [[gcid, {"color": hexv, "active": "yes"}]
                          for gcid, hexv in GLOBAL_COLORS.items()],
        "images": {},
        "thumbnails": [],
    }


def generate() -> dict[str, Any]:
    """Produce the full asset bundle."""
    preset_id, preset = build_button_preset()
    shortcodes = build_layout_shortcodes(preset_id)
    return {
        "asset_key": "poc-hero-card",
        "title": "POC — Hero + Card (generated)",
        "shortcodes": shortcodes,
        "preset_id": preset_id,
        "preset": preset,
        "global_colors": GLOBAL_COLORS,
        "portability_json": build_portability_json(shortcodes, preset_id, preset),
    }


if __name__ == "__main__":
    print(json.dumps(generate()["portability_json"], indent=2))
