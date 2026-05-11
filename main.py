#   MAN IT Club's SSG by Programming Division
#   zvlfahmi, slvr.12
#   IT Club 2024-2025
#   Rewritten by zvlfahmi

import os
import re
import shutil
import sys
import tempfile
import time
from datetime import datetime
from html import escape
from pathlib import Path

import markdown
import tomllib
from PIL import Image

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def buildTopnavHtml(config: dict[str, str | int | bool], relative_path: str):
    default_topnav = (
        '<ul class="topnav">\n'
        f'    <li><a href="{relative_path}">{escape(str(config.get("Title", "Home")))}</a></li>\n'
        f'    <li><a href="{relative_path}content/about">About</a></li>\n'
        "</ul>"
    )

    navbar_template_path = config.get(
        "navbar_template_path", "template/design/navbar.html"
    )
    if isinstance(navbar_template_path, str) and os.path.isfile(navbar_template_path):
        with open(navbar_template_path, "r", encoding="utf-8") as navbar_file:
            return navbar_file.read().replace("{{ relpath }}", relative_path)

    return str(config.get("topnav_html", default_topnav)).replace(
        "{{ relpath }}", relative_path
    )


def stripHtmlTags(value: str):
    return re.sub(r"<[^>]+>", "", value)


def extractFirstImageSrc(html_content: str):
    match = re.search(r'<img[^>]*\ssrc="([^"]+)"', html_content, re.IGNORECASE)
    return match.group(1) if match else None


def extractFirstH1Title(html_content: str):
    heading_match = re.search(
        r"<h1\b[^>]*>(.*?)</h1>", html_content, re.IGNORECASE | re.DOTALL
    )
    if not heading_match:
        return ""
    return stripHtmlTags(heading_match.group(1)).strip()


def wrapTitleAndDateHero(html_content: str, image_src: str):
    h1_match = re.search(
        r"<h1\b[^>]*>.*?</h1>", html_content, re.IGNORECASE | re.DOTALL
    )
    if not h1_match:
        return html_content

    h3_match = re.search(
        r"<h3\b[^>]*>.*?</h3>", html_content, re.IGNORECASE | re.DOTALL
    )

    wrapper_start = h1_match.start()
    wrapper_end = h1_match.end()
    wrapper_inner = h1_match.group(0)

    if h3_match and h3_match.start() >= h1_match.end():
        wrapper_end = h3_match.end()
        wrapper_inner = f"{wrapper_inner}\n{h3_match.group(0)}"

    categories_match = re.search(
        r'<p\b[^>]*class="[^"]*post-categories[^"]*"[^>]*>.*?</p>',
        html_content,
        re.IGNORECASE | re.DOTALL,
    )
    if categories_match and categories_match.start() >= wrapper_end:
        between = html_content[wrapper_end : categories_match.start()]
        if not between.strip():
            wrapper_end = categories_match.end()
            wrapper_inner = f"{wrapper_inner}\n{categories_match.group(0)}"

    wrapper_html = (
        f'<div class="post-hero" style="--hero-bg-image: url(\'{escape(image_src, quote=True)}\');">'
        f"{wrapper_inner}</div>"
    )

    return html_content[:wrapper_start] + wrapper_html + html_content[wrapper_end:]


def makeMetaDescription(html_content: str, config: dict[str, str | int | bool]) -> str:
    raw_description = ""
    for paragraph in re.finditer(
        r"<p[^>]*>(.*?)</p>", html_content, re.IGNORECASE | re.DOTALL
    ):
        candidate = stripHtmlTags(paragraph.group(1)).strip()
        if candidate:
            raw_description = candidate
            break

    if not raw_description:
        raw_description = stripHtmlTags(html_content)

    normalized = " ".join(raw_description.split())
    default_description = config.get("Description")
    if not isinstance(default_description, str):
        default_description = config.get("Title", "")
    if not isinstance(default_description, str):
        default_description = ""
    description = normalized[:157] + "..." if len(normalized) > 160 else normalized
    return description if description else default_description


def parseCategoryList(raw_value: str):
    categories: list[str] = []
    for part in raw_value.split(","):
        category = part.strip()
        if category and category not in categories:
            categories.append(category)
    return categories


def extractCategoriesFromMarkdownMeta(md: markdown.Markdown):
    meta = getattr(md, "Meta", {})
    if not isinstance(meta, dict):
        return []

    values: list[str] = []
    for key in ("category", "categories"):
        raw = meta.get(key)
        if isinstance(raw, list):
            values.extend(raw)

    categories: list[str] = []
    for value in values:
        if not isinstance(value, str):
            continue
        for category in parseCategoryList(value):
            if category not in categories:
                categories.append(category)
    return categories


def inferCategoriesFromPath(markdown_path: str, content_dir: str):
    relative_path = os.path.relpath(markdown_path, content_dir)
    parent_dir = os.path.dirname(relative_path)
    if not parent_dir or parent_dir == ".":
        return []

    categories: list[str] = []
    for part in parent_dir.split(os.sep):
        normalized = part.strip()
        if normalized and normalized not in categories:
            categories.append(normalized)
    return categories


def parseMarkdownMetadataTable(markdown_content: str):
    block_pattern = re.compile(
        r"^\s*\[metastart\]\s*\n"
        r"(?P<block>.*?)"
        r"\n\s*\[metaend\]\s*\n?",
        re.IGNORECASE | re.DOTALL,
    )
    block_match = block_pattern.match(markdown_content)
    if block_match:
        title = ""
        timestamp = ""
        categories: list[str] = []

        for line in block_match.group("block").splitlines():
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            key_normalized = key.strip().lower()
            value_normalized = value.strip()

            if key_normalized == "title":
                title = value_normalized
            elif key_normalized == "timestamp":
                timestamp = value_normalized
            elif key_normalized in {"category", "categories"}:
                categories = parseCategoryList(value_normalized)

        markdown_body = markdown_content[block_match.end() :].lstrip("\n")
        return title, timestamp, categories, markdown_body

    metadata_table_pattern = re.compile(
        r"^\s*\|\s*title\s*\|\s*timestamp\s*\|\s*categories?\s*\|\s*\n"
        r"\s*\|\s*:?-{3,}:?\s*\|\s*:?-{3,}:?\s*\|\s*:?-{3,}:?\s*\|\s*\n"
        r"\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|\s*(?:\n+)?",
        re.IGNORECASE,
    )

    table_match = metadata_table_pattern.match(markdown_content)
    if not table_match:
        return "", "", [], markdown_content

    table_title = table_match.group(1).strip()
    table_timestamp = table_match.group(2).strip()
    table_categories = parseCategoryList(table_match.group(3).strip())
    markdown_body = markdown_content[table_match.end() :].lstrip("\n")
    return table_title, table_timestamp, table_categories, markdown_body


def injectTitleAndTimestamp(html_content: str, title: str, timestamp: str):
    if not title and not timestamp:
        return html_content

    leading_h1 = re.search(
        r"^\s*<h1\b[^>]*>(.*?)</h1>", html_content, re.IGNORECASE | re.DOTALL
    )
    leading_h3 = re.search(
        r"^\s*(?:<h1\b[^>]*>.*?</h1>)?\s*<h3\b[^>]*>(.*?)</h3>",
        html_content,
        re.IGNORECASE | re.DOTALL,
    )

    has_matching_leading_h1 = False
    if leading_h1 and title:
        leading_h1_text = stripHtmlTags(leading_h1.group(1)).strip()
        has_matching_leading_h1 = leading_h1_text == title.strip()

    has_matching_leading_h3 = False
    if leading_h3 and timestamp:
        leading_h3_text = stripHtmlTags(leading_h3.group(1)).strip()
        has_matching_leading_h3 = leading_h3_text == timestamp.strip()

    blocks: list[str] = []
    if title and not has_matching_leading_h1:
        blocks.append(f"<h1>{escape(title)}</h1>")
    if timestamp and not has_matching_leading_h3:
        blocks.append(f"<h3>{escape(timestamp)}</h3>")

    if not blocks:
        return html_content

    return "".join(blocks) + html_content


def renderArticleCategories(categories: list[str]):
    if not categories:
        return ""

    category_badges = "".join(
        f'<span class="post-category">{escape(category)}</span>'
        for category in categories
    )
    return f'<p class="post-categories">{category_badges}</p>'


def injectArticleCategories(html_content: str, categories: list[str]):
    categories_html = renderArticleCategories(categories)
    if not categories_html:
        return html_content

    h3_match = re.search(
        r"<h3\b[^>]*>.*?</h3>", html_content, re.IGNORECASE | re.DOTALL
    )
    if h3_match:
        insert_at = h3_match.end()
        return html_content[:insert_at] + categories_html + html_content[insert_at:]

    h1_match = re.search(
        r"<h1\b[^>]*>.*?</h1>", html_content, re.IGNORECASE | re.DOTALL
    )
    if h1_match:
        insert_at = h1_match.end()
        return html_content[:insert_at] + categories_html + html_content[insert_at:]

    return categories_html + html_content


def writeTextFile(path: str, content: str):
    dir_path = os.path.dirname(path) or "."
    try:
        os.makedirs(dir_path, exist_ok=True)
    except PermissionError:
        print(f"[ WARN ] : skip write (directory permission denied): {dir_path}")
        return False

    if not os.access(dir_path, os.W_OK | os.X_OK):
        print(f"[ WARN ] : skip write (directory permission denied): {dir_path}")
        return False

    temp_path = ""
    try:
        with tempfile.NamedTemporaryFile(
            "w", delete=False, encoding="utf-8", dir=dir_path
        ) as temp_file:
            temp_file.write(content)
            temp_path = temp_file.name

        os.replace(temp_path, path)
        return True
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)


def thumbnailWebpPath(image_path: str):
    root, _ = os.path.splitext(image_path)
    return f"{root}.thumb.webp"


def buildThumbnailFromImage(src: str, dst: str, webp_quality: int = 45):
    ext = os.path.splitext(src)[1].lower()
    if ext not in IMAGE_EXTENSIONS:
        return False

    dst_dir = os.path.dirname(dst) or "."
    os.makedirs(dst_dir, exist_ok=True)

    temp_path = ""
    try:
        with Image.open(src) as image:
            if image.mode not in {"RGB", "L"}:
                image = image.convert("RGB")

            with tempfile.NamedTemporaryFile(
                delete=False,
                suffix=".webp",
                dir=dst_dir,
            ) as temp_file:
                temp_path = temp_file.name

            image.save(
                temp_path,
                format="WEBP",
                quality=webp_quality,
                method=6,
            )
            os.replace(temp_path, dst)
            return True
    except Exception as exc:
        print(f"[ WARN ] : thumbnail generation failed ({src}): {exc}")
        return False
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)


def selectThumbnailOrOriginal(image_path: str, public_dir: str):
    normalized = image_path.strip()
    if normalized.startswith("../"):
        normalized = normalized[3:]
    normalized = normalized.lstrip("/")

    thumb_rel = thumbnailWebpPath(normalized)
    thumb_abs = os.path.join(public_dir, thumb_rel)
    if os.path.exists(thumb_abs):
        return thumb_rel
    return normalized


def readConfig(configPath: str):
    with open(configPath, "rb") as f:
        parsed = tomllib.load(f)
    config = {}
    for section in ["metadata", "tool-setting"]:
        data = parsed.get(section, {})
        if isinstance(data, dict):
            config.update(data)
    return config


def createMarkdown(markdown_path: str, title: str, date: bool):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    full_path = (
        markdown_path + "/" + datetime.now().strftime("%Y%m%d") + "-" + title + ".md"
        if date
        else markdown_path + "/" + title + ".md"
    )
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as md_file:
        md_file.write(
            "[metastart]\n"
            f"title: {title}\n"
            f"timestamp: {timestamp}\n"
            "categories: Uncategorized\n"
            "[metaend]\n\n"
            "Content goes here."
        )  # pyright: ignore[reportUnusedCallResult]
    print(f"[ // ] : Created {full_path}")


def copySrcDir(public_dir: str, src_dir: str):
    try:
        if not os.path.exists(public_dir):
            os.makedirs(public_dir)

        if not os.path.exists(src_dir):
            print(f"[ WARN ] {src_dir} doesn't exist")
            return

        if not os.listdir(src_dir):
            print(f"[ WARN ] : {src_dir} did not contain files, ignoring src")
            return

        shutil.copytree(
            src_dir, public_dir, dirs_exist_ok=True, copy_function=shutil.copy2
        )
        for item in os.listdir(src_dir):
            print(f"[  OK  ]\t: Copying {item}")

    except PermissionError:
        print(" [ ERROR ] Unable to create Public Directory: No Permission")
    except Exception as e:
        print(f"[ ERROR ] {e}")


def copyImgDir(
    public_dir: str,
    img_dir: str,
    img_quality: int,
    thumbnail_quality: int | None = None,
):
    dest_dir = os.path.join(public_dir, "img")
    if not os.path.isdir(img_dir):
        print(f"[ WARN ] {img_dir} doesn't exist")
        return

    os.makedirs(dest_dir, exist_ok=True)

    for root, _, files in os.walk(img_dir):
        rel_root = os.path.relpath(root, img_dir)
        dest_root = dest_dir if rel_root == "." else os.path.join(dest_dir, rel_root)
        os.makedirs(dest_root, exist_ok=True)

        for item in files:
            s_path = os.path.join(root, item)
            rel_path = os.path.relpath(s_path, img_dir)
            _, ext = os.path.splitext(item)
            ext_lower = ext.lower()

            if ext_lower in IMAGE_EXTENSIONS:
                filename, _ = os.path.splitext(item)
                d_path = os.path.join(dest_root, f"{filename}.webp")
                should_write = True
                if os.path.exists(d_path):
                    should_write = os.path.getmtime(s_path) > os.path.getmtime(d_path)

                if should_write:
                    try:
                        with Image.open(s_path) as img:
                            if img.mode in ("RGBA", "P"):
                                img = img.convert("RGB")
                            img.save(d_path, "WEBP", quality=img_quality)
                            print(f"[  OK  ] Compressing {rel_path}")
                    except Exception as e:
                        print(f"[ ERROR ] {rel_path}: {e}")

                if thumbnail_quality is not None and os.path.exists(d_path):
                    thumb_path = thumbnailWebpPath(d_path)
                    if not os.path.exists(thumb_path) or os.path.getmtime(
                        d_path
                    ) > os.path.getmtime(thumb_path):
                        buildThumbnailFromImage(
                            d_path,
                            thumb_path,
                            webp_quality=thumbnail_quality,
                        )
            else:
                d_path = os.path.join(dest_root, item)
                should_copy = True
                if os.path.exists(d_path):
                    should_copy = os.path.getmtime(s_path) > os.path.getmtime(d_path)

                if should_copy:
                    try:
                        shutil.copy2(s_path, d_path)
                        print(f"[  OK  ] Copying {rel_path}")
                    except Exception as e:
                        print(f"[ ERROR ] {rel_path}: {e}")


def extract_from_html(news_file_path: str):
    with open(news_file_path, "r", encoding="utf-8") as html_file:
        html_content = html_file.read()

    judul: list[str] = []
    timestamp: list[str] = []
    gambar: list[str] = []
    categories: list[str] = []

    title_match = re.search(
        r"<h1\b[^>]*>(.*?)</h1>", html_content, re.IGNORECASE | re.DOTALL
    )
    if title_match:
        judul.append(stripHtmlTags(title_match.group(1)).strip())

    timestamp_match = re.search(
        r"<h3\b[^>]*>(.*?)</h3>", html_content, re.IGNORECASE | re.DOTALL
    )
    if timestamp_match:
        timestamp.append(stripHtmlTags(timestamp_match.group(1)).strip())

    image_match = re.search(r'<img[^>]*\ssrc="([^"]+)"', html_content, re.IGNORECASE)
    if image_match:
        image_path = image_match.group(1).strip()
        if image_path.startswith("../"):
            image_path = image_path[3:]
        gambar.append(image_path)

    for category_match in re.finditer(
        r'<span\s+class="post-category"\s*>(.*?)</span>',
        html_content,
        re.IGNORECASE | re.DOTALL,
    ):
        category_text = stripHtmlTags(category_match.group(1)).strip()
        if category_text and category_text not in categories:
            categories.append(category_text)

    if not judul:
        judul.append("No Title")
    if not gambar:
        gambar.append("../img/default.webp")
    if not timestamp:
        timestamp.append("No Timestamp")
    if not categories:
        categories.append("Uncategorized")

    return judul, timestamp, gambar, categories


def generateNewsList(
    news_dir: str,
    news_template_path: str,
    output_path: str,
    public_dir: str,
):
    if not news_template_path or not output_path:
        print("[ WARN ] : news template/output path not set, skipping news list")
        return

    if not os.path.isfile(news_template_path):
        print(
            f"[ WARN ] : news template not found, skipping news list: {news_template_path}"
        )
        return

    records: list[dict[str, str]] = []
    output_dir = os.path.dirname(output_path) or "."

    if not os.path.isdir(news_dir):
        print(f"[ WARN ] : news directory not found, skipping scan: {news_dir}")
    else:
        with os.scandir(news_dir) as entries:
            for entry in entries:
                if entry.is_file():
                    item = entry.name

                    if item.endswith(".html"):
                        if item.startswith("index"):
                            continue

                        news_file_path = os.path.join(news_dir, item)
                        metadata = extract_from_html(news_file_path)
                        relative_path = os.path.splitext(
                            os.path.relpath(news_file_path, news_dir)
                        )[0]
                        records.append(
                            {
                                "relative_path": relative_path,
                                "news_file_path": news_file_path,
                                "title": metadata[0][0],
                                "timestamp": metadata[1][0],
                                "thumbnail_path": selectThumbnailOrOriginal(
                                    metadata[2][0], public_dir
                                ),
                                "categories": ", ".join(metadata[3]),
                            }
                        )

    with open(news_template_path, "r", encoding="utf-8") as news_template_file:
        news_template_content = news_template_file.read()

        records.sort(key=lambda x: x["relative_path"], reverse=True)
        news_items: list[str] = []
        for record in records:
            news_href = os.path.relpath(record["news_file_path"], output_dir).replace(
                os.sep, "/"
            )
            thumbnail_href = os.path.relpath(
                os.path.join(public_dir, record["thumbnail_path"]),
                output_dir,
            ).replace(os.sep, "/")
            news_items.append(
                f'<div class="news" style="background-image: linear-gradient(rgba(0, 0, 0, 0.25), rgba(0, 0, 0, 0.5)), url({thumbnail_href}); background-size: cover; background-position: center;"><a href="{news_href}"><b>{escape(record["title"])}</b><br>{escape(record["timestamp"])}<br><small>{escape(record["categories"])}</small></a></div>'
            )

        news_list = "\n".join(news_items)
        news_htmlContent = news_template_content.replace("{{ news_list }}", news_list)

    writeTextFile(output_path, news_htmlContent)


def processMarkdown(
    content_dir: str, public_dir: str, config: dict[str, str | int | bool]
):
    content_path = Path(content_dir)
    public_path = Path(public_dir)

    md = markdown.Markdown(
        extensions=[
            "markdown.extensions.extra",
            "markdown.extensions.codehilite",
            "markdown.extensions.tables",
            "markdown.extensions.toc",
            "markdown.extensions.meta",
            "markdown.extensions.admonition",
            "markdown_del_ins",
        ]
    )

    templates = {}
    for t in ["head", "body", "script", "footer", "base"]:
        try:
            with open(f"template/{t}.html", "r", encoding="utf-8") as f:
                templates[t] = f.read()
        except FileNotFoundError:
            templates[t] = ""

    for md_file in content_path.rglob("*.md"):
        rel_path = md_file.relative_to(content_path)
        html_file = public_path / rel_path.with_suffix(".html")

        if html_file.exists() and md_file.stat().st_mtime <= html_file.stat().st_mtime:
            continue

        with open(md_file, "r", encoding="utf-8") as f:
            raw_text = f.read()

        meta_title, meta_timestamp, table_categories, markdown_body = (
            parseMarkdownMetadataTable(raw_text)
        )

        md.reset()
        raw_html = md.convert(markdown_body)
        categories = extractCategoriesFromMarkdownMeta(md)

        raw_html = injectTitleAndTimestamp(raw_html, meta_title, meta_timestamp)

        if not categories and table_categories:
            categories = table_categories

        if not categories:
            categories = inferCategoriesFromPath(str(md_file), str(content_path))
        if not categories:
            categories = ["Uncategorized"]

        raw_html = injectArticleCategories(raw_html, categories)

        depth = len(rel_path.parts) - 1
        rel_prefix = "../" * depth if depth > 0 else ""

        first_img = extractFirstImageSrc(raw_html)
        page_title = meta_title or extractFirstH1Title(raw_html)
        title = page_title if page_title else str(config.get("Title", rel_path.stem))

        meta_desc = makeMetaDescription(raw_html, config)

        current_nav = buildTopnavHtml(config, rel_prefix)
        meta_image = first_img or str(config.get("meta_image", "img/default.webp"))
        site_url = str(config.get("site_url", "")).rstrip("/")
        og_image_path = meta_image.lstrip("/")
        while og_image_path.startswith("../"):
            og_image_path = og_image_path[3:]
        og_image = f"{site_url}/{og_image_path}" if site_url else meta_image

        head_filled = (
            templates["head"]
            .replace("{{ Title }}", title)
            .replace("{{ relpath }}", rel_prefix)
            .replace("{{ meta_image }}", meta_image)
            .replace("{{ og_image }}", og_image)
            .replace("{{ meta_description }}", escape(meta_desc))
            .replace("{{ topnav }}", current_nav)
            .replace(
                "{{ font_stylesheet_url }}", str(config.get("font_stylesheet_url", ""))
            )
        )

        final_body_content = (
            wrapTitleAndDateHero(raw_html, first_img) if first_img else raw_html
        )
        body_filled = templates["body"].replace("{{ content }}", final_body_content)

        final_html = (
            templates["base"]
            .replace("{{ head }}", head_filled)
            .replace("{{ body }}", body_filled)
            .replace("{{ footer }}", templates["footer"])
            .replace("{{ script }}", templates["script"])
        )

        html_file.parent.mkdir(parents=True, exist_ok=True)
        if writeTextFile(str(html_file), final_html):
            print(f"[ BUILD ] {rel_path} -> {html_file.name}")


if __name__ == "__main__":
    config_path: str = ""
    args: list[str] = sys.argv

    if "--config" in args or "-c" in args:
        cfg_idx: int = (
            args.index("--config") if "--config" in args else args.index("-c")
        )
        if cfg_idx + 1 < len(args):
            if ".toml" in args[cfg_idx + 1]:
                config_path = args[cfg_idx + 1]
            else:
                print(
                    "Invalid value for config or the provided value is not a TOML config file"
                )

    config: dict[str, str | int | bool] = (
        readConfig(config_path) if config_path != "" else {}
    )

    if "--new" in args or "-n" in args or "new" in args:
        if "--new" in args:
            val_idx: int = args.index("--new") + 1
        elif "-n" in args:
            val_idx = args.index("-n") + 1
        else:
            val_idx = args.index("new") + 1

        folder: str = ""
        file: str = ""

        if val_idx < len(args):
            first_arg = args[val_idx]
            second_arg = ""
            if val_idx + 1 < len(args) and not args[val_idx + 1].startswith("-"):
                second_arg = args[val_idx + 1]

            if second_arg:
                folder = first_arg
                filename = second_arg
            else:
                parts = first_arg.rsplit("/", 1)
                if len(parts) > 1:
                    folder = parts[0]
                    filename = parts[1]
                else:
                    folder = ""
                    filename = parts[0]

            file = filename[:-3] if filename.endswith(".md") else filename

        else:
            print("Invalid folder/filename")
            file = ""

        if not file:
            sys.exit(1)

        if folder:
            if os.path.isabs(folder):
                createMarkdown(folder, file, bool(config.get("file-with-date", 1)))
            else:
                content_root_norm = os.path.normpath(
                    str(config.get("content_dir", "content"))
                ).lstrip("./")
                folder_norm = os.path.normpath(folder).lstrip("./")
                if folder_norm == "content" or folder_norm.startswith(
                    "content" + os.sep
                ):
                    remainder = folder_norm[len("content") :].lstrip(os.sep)
                    if remainder:
                        createMarkdown(
                            os.path.join(
                                str(config.get("content_dir", "content")), remainder
                            ),
                            file,
                            bool(config.get("file-with-date", 1)),
                        )
                    else:
                        createMarkdown(
                            str(config.get("content_dir", "content")),
                            file,
                            bool(config.get("file-with-date", 1)),
                        )
                elif folder_norm == content_root_norm or folder_norm.startswith(
                    content_root_norm + os.sep
                ):
                    createMarkdown(folder, file, bool(config.get("file-with-date", 1)))
                else:
                    createMarkdown(
                        os.path.join(str(config.get("content_dir", "content")), folder),
                        file,
                        bool(config.get("file-with-date", 1)),
                    )
        else:
            createMarkdown(
                str(config.get("content_dir", "content")),
                file,
                bool(config.get("file-with-date", 1)),
            )

    if "--generate" in args or "-g" in args or "generate" in args:
        start_time = time.perf_counter()
        public_dir = str(config.get("public_dir", "public"))
        copySrcDir(public_dir, str(config.get("src_dir", "src")))

        image_quality = config.get("image_webp_quality", 80)
        try:
            image_quality = int(image_quality)
        except (TypeError, ValueError):
            image_quality = 80

        thumbnail_quality = config.get("thumbnail_webp_quality", 45)
        try:
            thumbnail_quality = int(thumbnail_quality)
        except (TypeError, ValueError):
            thumbnail_quality = 45

        copyImgDir(
            public_dir,
            str(config.get("img_dir", "img")),
            image_quality,
            thumbnail_quality=thumbnail_quality,
        )

        processMarkdown(
            str(config.get("content_dir", "content")),
            public_dir,
            config,
        )

        generateNewsList(
            str(config.get("news_dir", "")),
            str(config.get("news_template_path", "")),
            str(config.get("output_path", "")),
            public_dir,
        )
        end_time = time.perf_counter()
        print(f"[ TIME ] : {(end_time - start_time) * 1000:.2f} ms")
