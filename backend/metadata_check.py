"""
Pre-model metadata check for AI-generation tells.

Looks at three signal sources, in order of trustworthiness:
  1. C2PA "AI-generated" claims (JUMBF box in JPEG/PNG).
  2. XMP CreatorTool / DigitalSourceType / Generator fields.
  3. EXIF Software / Make / Model fields containing known AI tool names.

Returns a single MetadataFinding or None. The caller decides whether to
short-circuit (we recommend yes — false-positive rate from these signals
is very low; the failure mode is silent strip-on-upload).
"""
from __future__ import annotations

import io
import re
from dataclasses import dataclass
from typing import Optional

from PIL import Image, ExifTags

# Known AI-generation tool names that may appear in Software / CreatorTool /
# Generator fields. Match case-insensitively as a substring.
# Organized by category so future additions stay scoped.
#
# IMPORTANT: this only catches files that haven't had metadata stripped.
# Most images shared on social platforms lose EXIF on upload — that's why
# this check is a *positive-only* signal (high precision, low recall) and
# the model still runs whenever it doesn't fire.
_AI_TOOL_PATTERNS = [
    # ── Stable Diffusion ecosystem ───────────────────────────────────────
    r"stable\s*diffusion",
    r"\bsdxl\b",
    r"\bsd[-_ ]?(3|3\.5|cascade|next)\b",
    r"\bsd[-_ ]?webui\b",
    r"automatic\s*1111",
    r"comfy\s*ui",
    r"invoke\s*ai",
    r"sd\s*next",
    r"vladmandic",
    r"\bfooocus\b",
    r"diffusion\s*bee",
    r"draw\s*things",
    r"easy\s*diffusion",
    r"webui\s*forge",

    # ── Major commercial / consumer generators ───────────────────────────
    r"midjourney",
    r"dall[-·\s]?e\b",
    r"\bdalle\b",
    r"openai\s*(image|gpt[-\s]?image)?",
    r"\bgpt[-\s]?image(?:-?\d)?\b",
    r"\bchat\s*gpt\s+image\b",
    r"adobe\s+firefly",
    r"\bfirefly\b",
    r"generative\s+(fill|expand|remove|replace)",
    r"\bphotoshop\s+(ai|generative)",
    r"\bgoogle\s+imagen\b",
    r"\bimagen\s*\d*\b",
    r"\bgemini\s+(image|imagen|nano\s+banana)",
    r"bing\s+image\s+creator",
    r"microsoft\s+designer",
    r"meta\s+ai(\s+image)?",
    r"imagine\s+with\s+meta",
    r"image\s+playground",            # Apple Intelligence
    r"\bgenmoji\b",                   # Apple
    r"galaxy\s+ai",                   # Samsung
    r"sketch[-\s]?to[-\s]?image",     # Samsung
    r"drawing\s+assist",              # Samsung
    r"generative\s+edit",             # Samsung / Pixel
    r"magic\s+editor",                # Google Pixel
    r"\bpixel\s+studio\b",            # Google Pixel

    # ── Video / multimodal generators ────────────────────────────────────
    r"\bsora\b",
    r"\bveo\s*\d*\b",
    r"runway(\s*ml)?",
    r"kling\s*ai",
    r"pika\s*labs?",
    r"luma\s+(labs|dream\s+machine|ai)",
    r"\bhailuo\b",
    r"hunyuan\s*video",
    r"\bmochi\b",
    r"cog\s*video",

    # ── Other major image models / services ──────────────────────────────
    r"\bflux\.?\s*\d*\b",
    r"flux[-\s]?(dev|schnell|pro|kontext)",
    r"\bideogram\b",
    r"leonardo\.?\s*ai",
    r"playground\s*ai",
    r"novel\s*ai",
    r"recraft\.?\s*ai",
    r"krea\.?\s*ai",
    r"\bmagnific\b",
    r"reve\.\s*art",
    r"canva\s+(magic\s+media|ai|dream\s+lab)",
    r"picsart\s+ai",
    r"photoroom\s+ai",
    r"deep\s*ai",
    r"craiyon",
    r"night\s*cafe",
    r"blue\s*willow",
    r"mage\.\s*space",
    r"tensor\.?\s*art",
    r"\bcivitai\b",
    r"starry\s*ai",
    r"wombo(\s+dream)?",
    r"\blensa\b",
    r"freepik\s+ai",
    r"shutterstock\s+ai",
    r"getty\s+(generative|ai)",
    r"\bglif\b",
    r"\bfal\.\s*ai\b",
    r"replicate\.\s*com",
    r"stability\s*ai",
    r"\bdream\s*studio\b",

    # ── Open-source / research models ────────────────────────────────────
    r"hunyuan(?:dit|image|gen)?",
    r"pixart[-_ ]?(alpha|sigma|α|σ)",
    r"kandinsky",
    r"w[üu]rstchen",
    r"stable\s+cascade",
    r"lumina[-\s]?next",
    r"aura\s*flow",
    r"\bsana\b",
    r"hi\s*dream",
    r"qwen[-\s]?image",
    r"omni\s*gen",
    r"janus[-\s]?pro",
    r"deep\s*floyd",
    r"latent\s+diffusion",
    r"\bdit\b\s+(model|generated)",
    r"control\s*net",                 # often tags AI-edited images
    r"\bcogview\b",
    r"hi\s*resolve",

    # ── Mobile / niche apps ──────────────────────────────────────────────
    r"\bdream\s+by\s+wombo\b",
    r"\bremini\s+ai\b",
    r"face\s*app\s+ai",
    r"prequel\s+ai",
    r"motionleap\s+ai",
    r"mirage\s+ai",
    r"artbreeder",
    r"playground\s+v\d",

    # ── Generic / fallback synthetic-media markers ───────────────────────
    r"\bai[-_ ]?generated\b",
    r"\bai[-_ ]?image\b",
    r"\bgenerative\s+ai\b",
    r"\btext[-\s]?to[-\s]?image\b",
    r"\bimage[-\s]?to[-\s]?image\b",
    r"synthetic\s+media",
    r"machine[-\s]?generated",
]
_AI_TOOL_RE = re.compile("|".join(_AI_TOOL_PATTERNS), re.IGNORECASE)

# IPTC/XMP DigitalSourceType controlled vocabulary entries indicating AI.
# See https://cv.iptc.org/newscodes/digitalsourcetype/ — Adobe, Microsoft,
# Google, OpenAI all use these codes when they emit Content Credentials.
_IPTC_AI_DST = re.compile(
    r"trainedAlgorithmicMedia"
    r"|compositeWithTrainedAlgorithmicMedia"
    r"|algorithmicMedia"
    r"|algorithmicallyEnhanced",
    re.IGNORECASE,
)

# C2PA AI-generation hints inside JUMBF metadata. C2PA-signed AI images
# (Firefly, Photoshop Generative Fill, Bing Image Creator, ChatGPT/DALL·E,
# Google's SynthID-tagged images, Leica/Sony AI cameras) emit these tokens.
# We also scan for software-agent identifiers and the legacy CAI namespace.
_C2PA_AI_HINTS = re.compile(
    rb"trainedAlgorithmicMedia"
    rb"|compositeWithTrainedAlgorithmicMedia"
    rb"|algorithmicMedia"
    rb"|algorithmicallyEnhanced"
    rb"|c2pa\.created.{0,400}(generative|ai|trainedAlgorithmic)"
    rb"|c2pa\.ai_generative"
    rb"|c2pa\.ai_training_mining_prohibited"
    rb"|com\.adobe\.firefly"
    rb"|com\.openai"
    rb"|com\.openai\.image"
    rb"|gpt-image-\d"
    rb"|chat\s*gpt"
    rb"|com\.midjourney"
    rb"|com\.microsoft\.designer"
    rb"|com\.microsoft\.bing"
    rb"|stability\.ai"
    rb"|stable[\s_-]?diffusion"
    rb"|google\.ai\.generative"
    rb"|com\.google\.gemini"
    rb"|com\.google\.imagen"
    rb"|google\.com/models/imagen"
    rb"|org\.contentauthenticity"
    rb"|claim_generator.{0,200}(openai|midjourney|stability|firefly|imagen|gemini|designer)"
    rb"|softwareAgent.{0,200}(openai|midjourney|stability|firefly|imagen|gemini|gpt-image|dall.?e|comfy|automatic)",
    re.IGNORECASE | re.DOTALL,
)


@dataclass
class MetadataFinding:
    source: str           # "c2pa" | "xmp" | "exif"
    field: str            # which field triggered (e.g. "Software")
    evidence: str         # the matched value (truncated)
    probability: float    # confidence to surface as ai_probability


def _exif_check(img: Image.Image) -> Optional[MetadataFinding]:
    try:
        exif = img.getexif()
    except Exception:
        return None
    if not exif:
        return None

    tag_lookup = {v: k for k, v in ExifTags.TAGS.items()}
    for field in ("Software", "Make", "Model", "ImageDescription", "Artist"):
        tag_id = tag_lookup.get(field)
        if tag_id is None:
            continue
        value = exif.get(tag_id)
        if not value:
            continue
        text = str(value)
        if _AI_TOOL_RE.search(text):
            return MetadataFinding(
                source="exif",
                field=field,
                evidence=text[:200],
                probability=0.95,
            )
    return None


def _xmp_check(img: Image.Image) -> Optional[MetadataFinding]:
    # PIL exposes raw XMP bytes via .info["XML:com.adobe.xmp"] or .getxmp() (PIL>=9).
    xmp_text: Optional[str] = None
    try:
        raw = img.info.get("XML:com.adobe.xmp") or img.info.get("xmp")
        if isinstance(raw, bytes):
            xmp_text = raw.decode("utf-8", errors="ignore")
        elif isinstance(raw, str):
            xmp_text = raw
    except Exception:
        pass

    if xmp_text is None:
        try:
            xmp_dict = img.getxmp()  # type: ignore[attr-defined]
            if xmp_dict:
                xmp_text = repr(xmp_dict)
        except Exception:
            xmp_text = None

    if not xmp_text:
        return None

    if _IPTC_AI_DST.search(xmp_text):
        m = _IPTC_AI_DST.search(xmp_text)
        return MetadataFinding(
            source="xmp",
            field="Iptc4xmpExt:DigitalSourceType",
            evidence=(m.group(0) if m else "")[:200],
            probability=0.97,
        )
    if _AI_TOOL_RE.search(xmp_text):
        m = _AI_TOOL_RE.search(xmp_text)
        return MetadataFinding(
            source="xmp",
            field="CreatorTool",
            evidence=(m.group(0) if m else "")[:200],
            probability=0.95,
        )
    return None


def _c2pa_check(raw: bytes) -> Optional[MetadataFinding]:
    # JUMBF / C2PA boxes live in the file binary. Scan first ~1MB for
    # cheap textual hints. Real C2PA verification needs the c2pa SDK; this
    # is a fast positive-only signal.
    head = raw[: 1024 * 1024]
    head_lower = head.lower()
    has_c2pa_box = (
        b"jumbf" in head_lower
        or b"c2pa" in head_lower
        or b"contentauthenticity" in head_lower
    )
    # Even if we don't see a C2PA box marker, ChatGPT/DALL-E sometimes
    # embed software identifiers as plain XMP/EXIF strings, so still scan.
    m = _C2PA_AI_HINTS.search(head)
    if not m:
        return None
    return MetadataFinding(
        source="c2pa" if has_c2pa_box else "embedded",
        field="actions" if has_c2pa_box else "softwareAgent",
        evidence=m.group(0).decode("utf-8", errors="ignore")[:200],
        probability=0.97,
    )


def check(raw: bytes) -> Optional[MetadataFinding]:
    """Run all metadata signals. Returns the strongest hit, or None."""
    # C2PA first — strongest signal.
    try:
        finding = _c2pa_check(raw)
        if finding:
            return finding
    except Exception:
        pass

    try:
        with Image.open(io.BytesIO(raw)) as img:
            img.load()
            finding = _xmp_check(img)
            if finding:
                return finding
            finding = _exif_check(img)
            if finding:
                return finding
    except Exception:
        return None

    return None
