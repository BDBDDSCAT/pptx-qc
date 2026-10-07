"""Helpers for building throwaway decks in tests."""

from __future__ import annotations

from PIL import Image
from pptx import Presentation
from pptx.opc.constants import CONTENT_TYPE as CT
from pptx.opc.constants import RELATIONSHIP_TYPE as RT
from pptx.opc.package import Part
from pptx.opc.packuri import PackURI
from pptx.oxml import parse_xml
from pptx.oxml.ns import nsdecls
from pptx.util import Inches, Pt


def new_deck():
    """A deck with one title+body slide; returns (prs, slide)."""
    prs = Presentation()
    slide = prs.slides.add_slide(prs.slide_layouts[1])
    return prs, slide


def set_text(shape, text: str, font: str | None = None, size: float | None = None):
    tf = shape.text_frame
    tf.text = ""
    run = tf.paragraphs[0].add_run()
    run.text = text
    if font:
        run.font.name = font
    if size:
        run.font.size = Pt(size)
    return run


def tiny_png(path, size=(48, 48)):
    Image.new("RGB", size, (120, 160, 200)).save(path)
    return path


def save(prs, path):
    prs.save(path)
    return path


def embed_font(prs, typeface: str):
    """Add embedded-font metadata and its related part for a saved-deck fixture.

    The font payload is a stub: the checks inspect the declaration, not glyph data.
    """
    part = Part(PackURI("/ppt/fonts/font1.fntdata"), CT.X_FONTDATA, prs.part.package, b"test-font")
    rid = prs.part.relate_to(part, RT.FONT)
    font_list = parse_xml(f'<p:embeddedFontLst {nsdecls("p", "r")}/>')
    font = parse_xml(f'<p:embeddedFont {nsdecls("p", "r")}/>')
    declaration = parse_xml(f'<p:font {nsdecls("p")}/>')
    declaration.set("typeface", typeface)
    font.append(declaration)
    regular = parse_xml(f'<p:regular {nsdecls("p", "r")} r:id="{rid}"/>')
    font.append(regular)
    font_list.append(font)
    prs.element.insert_element_before(font_list, "p:defaultTextStyle", "p:modifyVerifier", "p:extLst")


INCH = Inches
