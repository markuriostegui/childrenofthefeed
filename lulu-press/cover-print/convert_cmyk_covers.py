#!/usr/bin/env python3
"""Create Photoshop-managed CMYK front-cover assets for the Lulu templates."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import tempfile
from datetime import UTC, datetime
from pathlib import Path

from PIL import Image


PROFILE_NAME = "U.S. Web Coated (SWOP) v2"
PROFILE_PATH = Path("lulu-press/cover-print/profiles/USWebCoatedSWOPv2.icc")
COVERS = {
    "eng": (
        Path("lulu-press/cover-print/eng/children-of-the-feed-front-cover-en-gpt-image-2.png"),
        Path("lulu-press/cover-print/eng/children-of-the-feed-front-cover-en-swopv2.tif"),
    ),
    "esp": (
        Path("lulu-press/cover-print/esp/children-of-the-feed-front-cover-es-gpt-image-2.png"),
        Path("lulu-press/cover-print/esp/children-of-the-feed-front-cover-es-swopv2.tif"),
    ),
}
PIXELS = (2160, 3240)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_photoshop(source: Path, output: Path, app_name: str) -> None:
    javascript = (
        "app.displayDialogs=DialogModes.NO;"
        f"var d=app.open(File({json.dumps(str(source))}));"
        f"d.convertProfile({json.dumps(PROFILE_NAME)},Intent.RELATIVECOLORIMETRIC,true,false);"
        "d.resizeImage(undefined,undefined,300,ResampleMethod.NONE);"
        "var o=new TiffSaveOptions();"
        "o.imageCompression=TIFFEncoding.TIFFLZW;"
        "o.embedColorProfile=true;"
        f"d.saveAs(File({json.dumps(str(output))}),o,true,Extension.LOWERCASE);"
        "d.close(SaveOptions.DONOTSAVECHANGES);"
    )
    applescript = f'tell application {json.dumps(app_name)} to do javascript {json.dumps(javascript)}'
    subprocess.run(["osascript", "-e", applescript], check=True)


def embedded_profile_sha256(tiff: Path) -> str:
    with tempfile.TemporaryDirectory() as temporary:
        profile = Path(temporary) / "embedded.icc"
        scratch = Path(temporary) / "scratch.tif"
        subprocess.run(["tificc", f"-s{profile}", str(tiff), str(scratch)], check=True)
        return sha256(profile)


def validate(output: Path, profile_sha256: str) -> None:
    with Image.open(output) as image:
        if image.size != PIXELS:
            raise RuntimeError(f"{output} must be {PIXELS}, got {image.size}")
        if image.mode != "CMYK":
            raise RuntimeError(f"{output} must be CMYK, got {image.mode}")
        if "transparency" in image.info:
            raise RuntimeError(f"{output} must not contain transparency")
        dpi = image.info.get("dpi")
        if not dpi or any(abs(value - 300) > 0.1 for value in dpi):
            raise RuntimeError(f"{output} must be 300 ppi, got {dpi}")
    if embedded_profile_sha256(output) != profile_sha256:
        raise RuntimeError(f"{output} does not embed the pinned {PROFILE_NAME} ICC profile")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--photoshop-app", default="Adobe Photoshop 2026")
    parser.add_argument("--edition", choices=(*COVERS, "all"), default="all")
    args = parser.parse_args()
    root = args.root.resolve()
    profile = root / PROFILE_PATH
    if not profile.exists():
        raise RuntimeError(f"Missing pinned ICC profile: {profile}")
    profile_hash = sha256(profile)
    editions = COVERS if args.edition == "all" else {args.edition: COVERS[args.edition]}

    for edition, (source_relative, output_relative) in editions.items():
        source, output = root / source_relative, root / output_relative
        if not source.exists():
            raise RuntimeError(f"Missing approved source image: {source}")
        output.parent.mkdir(parents=True, exist_ok=True)
        run_photoshop(source, output, args.photoshop_app)
        validate(output, profile_hash)
        provenance = {
            "source": {"path": str(source_relative), "sha256": sha256(source)},
            "output": {"path": str(output_relative), "sha256": sha256(output), "pixels": list(PIXELS), "mode": "CMYK"},
            "icc_profile": {"name": PROFILE_NAME, "path": str(PROFILE_PATH), "sha256": profile_hash},
            "conversion": {
                "engine": args.photoshop_app,
                "rendering_intent": "relative colorimetric",
                "black_point_compensation": True,
                "alpha": False,
            },
            "created_at": datetime.now(UTC).replace(microsecond=0).isoformat(),
        }
        output.with_suffix(".provenance.json").write_text(json.dumps(provenance, indent=2) + "\n", encoding="utf-8")
        print(f"created {edition}: {output_relative}")


if __name__ == "__main__":
    main()
