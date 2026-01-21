#!/usr/bin/env python3
import json
import logging
from pathlib import Path

import fitz  # PyMuPDF
from PIL import Image
import pytesseract

logger = logging.getLogger("dionysus.utils.pdf_extractor")

def ensure_dir(path: Path):
    path.mkdir(parents=True, exist_ok=True)

def extract_block_and_lines(page):
    """Return blocks and lines (with coordinates) for academic PDFs."""
    page_dict = page.get_text("dict")  # structured layout
    blocks_out = []

    for b in page_dict.get("blocks", []):
        if "lines" not in b:
            continue
        block_bbox = [float(x) for x in b["bbox"]]
        lines_out = []
        for line in b["lines"]:
            spans_text = "".join(s["text"] for s in line["spans"]).strip()
            if not spans_text:
                continue
            lines_out.append({
                "bbox": [float(x) for x in line["bbox"]],
                "text": spans_text,
            })
        if not lines_out:
            continue
        blocks_out.append({
            "bbox": block_bbox,
            "lines": lines_out,
        })
    return blocks_out

def extract_images_from_page(doc, page, page_index, out_dir: Path):
    image_meta = []
    for img_index, img in enumerate(page.get_images(full=True), start=1):
        xref = img[0]
        try:
            base = fitz.Pixmap(doc, xref)
            if base.n > 4:  # e.g. CMYK -> RGB
                pix = fitz.Pixmap(fitz.csRGB, base)
                base = None
            else:
                pix = base
            img_name = f"page{page_index+1}_fig{img_index}.png"
            img_path = out_dir / img_name
            pix.save(img_path.as_posix())
            pix = None

            image_meta.append({
                "file": img_name,
                "page": page_index + 1,
                "xref": int(xref),
            })
        except Exception as e:
            logger.warning(f"Failed to extract image {img_index} on page {page_index+1}: {e}")
    return image_meta

def ocr_page(page):
    try:
        pix = page.get_pixmap(dpi=300)
        img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
        text = pytesseract.image_to_string(img)
        return text.strip()
    except Exception as e:
        logger.error(f"OCR failed: {e}")
        return ""

def process_paper(pdf_path: str, out_dir: str = "paper_output", ocr_if_empty: bool = True):
    pdf_path = Path(pdf_path)
    out_dir = Path(out_dir)
    text_dir = out_dir / "text"
    img_dir = out_dir / "figures"

    ensure_dir(text_dir)
    ensure_dir(img_dir)

    try:
        doc = fitz.open(pdf_path.as_posix())
    except Exception as e:
        logger.error(f"Failed to open PDF {pdf_path}: {e}")
        return

    meta = {"file": pdf_path.name, "pages": []}

    for page_index in range(len(doc)):
        page = doc[page_index]

        # 1. structured text
        blocks = extract_block_and_lines(page)

        ocr_text = None
        if not blocks and ocr_if_empty:
            ocr_text = ocr_page(page)
            if ocr_text:
                blocks = [{
                    "bbox": [0.0, 0.0, float(page.rect.width), float(page.rect.height)],
                    "lines": [{"bbox": [0.0, 0.0, float(page.rect.width), float(page.rect.height)],
                               "text": ocr_text}],
                    "source": "ocr"
                }]

        text_json_path = text_dir / f"page{page_index+1}.json"
        with open(text_json_path, "w", encoding="utf-8") as f:
            json.dump(blocks, f, ensure_ascii=False, indent=2)

        # 2. figures / diagrams
        images = extract_images_from_page(doc, page, page_index, img_dir)

        meta["pages"].append({
            "page": page_index + 1,
            "text_blocks_file": text_json_path.name,
            "num_blocks": len(blocks),
            "images": images,
            "used_ocr": bool(ocr_text),
        })

    meta_path = out_dir / "summary.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)

    print(f"Done. Output in: {out_dir}")
    print(f"Metadata: {meta_path}")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Extract text + figures from academic PDF.")
    parser.add_argument("pdf", help="Path to academic paper PDF")
    parser.add_argument("--out", default="paper_output", help="Output directory")
    parser.add_argument("--no-ocr", action="store_true", help="Disable OCR fallback")
    args = parser.parse_args()

    process_paper(args.pdf, out_dir=args.out, ocr_if_empty=not args.no_ocr)
