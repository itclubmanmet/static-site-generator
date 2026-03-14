#   MAN IT Club's SSG by Programming Division
#   zvlfahmi, slvr.12
#   IT Club 2024-2025

import os
import re
import subprocess
import sys
import tempfile
import time
from datetime import datetime
from html import escape

import markdown
import tomllib

try:
    from PIL import Image  # pyright: ignore[reportMissingImports]
except ImportError:
    Image = None  # type: ignore[assignment]


IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def readConfig(configPath: str):
    with open(configPath, "rb") as config_file:
        parsed = tomllib.load(config_file)

    config: dict[str, str | int | bool] = {}

    metadata = parsed.get("metadata", {})
    tool_setting = parsed.get("tool-setting", {})

    if isinstance(metadata, dict):
        for key, value in metadata.items():
            config[key] = value

    if isinstance(tool_setting, dict):
        for key, value in tool_setting.items():
            config[key] = value

    return config


def searchFile(directory: str, filename: str):
    list_files: list[str] = []
    for root, dirs, files in os.walk(directory):  # pyright: ignore[reportUnusedVariable]
        if filename in files:
            list_files.append(os.path.join(root, filename))
    return list_files if list_files else None


def calculateRelPath(contentHtmlPath: str, publicDir: str):
    depth = os.path.relpath(contentHtmlPath, publicDir).count(os.sep)
    return "../" * depth


def parseBool(value: str | int | bool | None, default: bool = False):
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value != 0
    return value.strip().lower() in {"1", "true", "yes", "on", "enabled"}


def parseInt(
    value: str | int | bool | None,
    default: int,
    min_value: int | None = None,
    max_value: int | None = None,
):
    if value is None:
        return default

    try:
        if isinstance(value, bool):
            parsed = int(value)
        elif isinstance(value, int):
            parsed = value
        else:
            parsed = int(value.strip())
    except (TypeError, ValueError):
        return default

    if min_value is not None:
        parsed = max(min_value, parsed)
    if max_value is not None:
        parsed = min(max_value, parsed)

    return parsed


def getConfigStr(config: dict[str, str | int | bool], key: str, default: str = ""):
    value = config.get(key)
    return value if isinstance(value, str) else default


def buildTopnavHtml(
    config: dict[str, str | int | bool],
    relative_path: str,
):
    default_topnav = (
        '<ul class="topnav">\n'
        f'    <li><a href="{relative_path}">{escape(getConfigStr(config, "Title", "Home"))}</a></li>\n'
        f'    <li><a href="{relative_path}content/about">About</a></li>\n'
        "</ul>"
    )

    navbar_template_path = getConfigStr(
        config, "navbar_template_path", "template/design/navbar.html"
    )

    if navbar_template_path and os.path.isfile(navbar_template_path):
        with open(navbar_template_path, "r", encoding="utf-8") as navbar_file:
            return navbar_file.read().replace("{{ relpath }}", relative_path)

    # Backward compatibility: allow inline HTML from config if a navbar template is not set.
    return getConfigStr(config, "topnav_html", default_topnav).replace(
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

    # Keep title + timestamp together inside one hero block when both are present.
    if h3_match and h3_match.start() >= h1_match.end():
        wrapper_end = h3_match.end()
        wrapper_inner = f"{wrapper_inner}\n{h3_match.group(0)}"

    wrapper_html = (
        f'<div class="post-hero" style="--hero-bg-image: url(\'{escape(image_src, quote=True)}\');">'
        f"{wrapper_inner}</div>"
    )

    return html_content[:wrapper_start] + wrapper_html + html_content[wrapper_end:]


def makeMetaDescription(html_content: str, config: dict[str, str | int | bool]):
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

    # Normalize whitespace and keep snippets concise for search results.
    normalized = " ".join(raw_description.split())
    default_description = getConfigStr(
        config, "Description", getConfigStr(config, "Title", "")
    )
    description = normalized[:157] + "..." if len(normalized) > 160 else normalized
    return description if description else default_description


def isSelinuxEnabled(config: dict[str, str | int | bool]):
    return parseBool(config.get("SELinux") or config.get("selinux"), False)


def installDir(path: str, selinux_enabled: bool = False):
    try:
        cmd = ["install", "-d", "-m", "0755"]
        if selinux_enabled:
            cmd.append("-Z")
        cmd.append(path)
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError:
        if not selinux_enabled:
            raise
        subprocess.run(["install", "-d", "-m", "0755", path], check=True)


def installFile(src: str, dst: str, mode: str = "0644", selinux_enabled: bool = False):
    dst_dir = os.path.dirname(dst)
    if dst_dir:
        os.makedirs(dst_dir, exist_ok=True)

    if dst_dir and not os.access(dst_dir, os.W_OK | os.X_OK):
        print(
            f"{color.YELLOW}[ !! ]{color.RESET} : skip write (directory permission denied): {dst_dir}"
        )
        return False

    # install may fail overwriting root-owned files in /var/www; do not abort full build.
    if os.path.exists(dst) and not os.access(dst, os.W_OK):
        print(
            f"{color.YELLOW}[ !! ]{color.RESET} : skip overwrite (permission denied): {dst}"
        )
        return False

    try:
        cmd = ["install", "-m", mode]
        if selinux_enabled:
            cmd.append("-Z")
        cmd.extend([src, dst])
        subprocess.run(cmd, check=True)
        return True
    except subprocess.CalledProcessError:
        if selinux_enabled:
            try:
                subprocess.run(["install", "-m", mode, src, dst], check=True)
                return True
            except subprocess.CalledProcessError:
                pass

        print(f"{color.YELLOW}[ !! ]{color.RESET} : skip write (install failed): {dst}")
        return False


def installTree(src: str, dst: str, selinux_enabled: bool = False):
    installDir(dst, selinux_enabled)

    for root, _, files in os.walk(src):
        rel_root = os.path.relpath(root, src)
        target_root = dst if rel_root == "." else os.path.join(dst, rel_root)
        installDir(target_root, selinux_enabled)

        for filename in files:
            src_file = os.path.join(root, filename)
            dst_file = os.path.join(target_root, filename)
            installFile(src_file, dst_file, selinux_enabled=selinux_enabled)


def writeTextFile(path: str, content: str, selinux_enabled: bool = False):
    dir_path = os.path.dirname(path)
    try:
        os.makedirs(dir_path, exist_ok=True)
    except PermissionError:
        print(
            f"{color.YELLOW}[ !! ]{color.RESET} : skip write (directory permission denied): {dir_path}"
        )
        return False

    if not os.access(dir_path, os.W_OK | os.X_OK):
        print(
            f"{color.YELLOW}[ !! ]{color.RESET} : skip write (directory permission denied): {dir_path}"
        )
        return False

    with tempfile.NamedTemporaryFile("w", delete=False, encoding="utf-8") as temp_file:
        temp_file.write(content)
        temp_path = temp_file.name

    try:
        return installFile(temp_path, path, selinux_enabled=selinux_enabled)
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def thumbnailWebpPath(image_path: str):
    root, _ = os.path.splitext(image_path)
    return f"{root}.thumb.webp"


def buildThumbnailFromImage(
    src: str,
    dst: str,
    selinux_enabled: bool = False,
    webp_quality: int = 45,
):
    ext = os.path.splitext(src)[1].lower()
    if ext not in IMAGE_EXTENSIONS:
        return False

    if Image is None:
        print(
            f"{color.YELLOW}[ !! ]{color.RESET} : Pillow not installed, skipping thumbnail: {src}"
        )
        return False

    temp_path = ""
    try:
        with Image.open(src) as image:
            if image.mode not in {"RGB", "L"}:
                image = image.convert("RGB")

            with tempfile.NamedTemporaryFile(delete=False, suffix=".webp") as temp_file:
                temp_path = temp_file.name

            image.save(
                temp_path,
                format="WEBP",
                quality=webp_quality,
                method=6,
            )
            return installFile(temp_path, dst, selinux_enabled=selinux_enabled)
    except Exception as exc:
        print(
            f"{color.YELLOW}[ !! ]{color.RESET} : thumbnail generation failed ({src}): {exc}"
        )
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


def writeApacheCacheHeaders(
    public_dir: str,
    selinux_enabled: bool = False,
    cache_max_age_days: int = 365,
):
    cache_seconds = max(1, cache_max_age_days) * 86400
    htaccess_path = os.path.join(public_dir, ".htaccess")
    htaccess_content = f"""# Generated by buildsite.py for static asset caching
<IfModule mod_expires.c>
    ExpiresActive On
    ExpiresByType text/css \"access plus {cache_seconds} seconds\"
    ExpiresByType application/javascript \"access plus {cache_seconds} seconds\"
    ExpiresByType image/jpeg \"access plus {cache_seconds} seconds\"
    ExpiresByType image/png \"access plus {cache_seconds} seconds\"
    ExpiresByType image/webp \"access plus {cache_seconds} seconds\"
    ExpiresByType image/svg+xml \"access plus {cache_seconds} seconds\"
    ExpiresByType font/woff2 \"access plus {cache_seconds} seconds\"
    ExpiresByType font/woff \"access plus {cache_seconds} seconds\"
    ExpiresByType text/html \"access plus 0 seconds\"
</IfModule>

<IfModule mod_headers.c>
    <FilesMatch \"\\.(css|js|jpg|jpeg|png|webp|svg|woff|woff2)$\">
        Header set Cache-Control \"public, max-age={cache_seconds}, immutable\"
    </FilesMatch>
    <FilesMatch \"\\.(html)$\">
        Header set Cache-Control \"no-cache\"
    </FilesMatch>
</IfModule>
"""
    writeTextFile(htaccess_path, htaccess_content, selinux_enabled)


def processMarkdown(
    markdownPath: str, contentHtmlPath: str, config: dict[str, str | int | bool]
):
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

    relative_path = calculateRelPath(
        contentHtmlPath, getConfigStr(config, "public_dir", "public")
    )
    topnav_html = buildTopnavHtml(config, relative_path)
    with open(markdownPath, "r", encoding="utf-8") as md_file:
        markdownContent = md_file.read()
        htmlContent = md.convert(markdownContent)

    with open("template/head.html", "r", encoding="utf-8") as head_file:
        head_content = head_file.read()
        title = getConfigStr(config, "Title", extractFirstH1Title(htmlContent))
        # Use the first image source for metadata and h1 hero if available.
        first_image_src = extractFirstImageSrc(htmlContent)
        meta_image = first_image_src or getConfigStr(
            config, "meta_image", "img/default.png"
        )
        og_base_url = getConfigStr(config, "site_url", "").rstrip("/")
        og_image_path = meta_image.lstrip("/")
        while og_image_path.startswith("../"):
            og_image_path = og_image_path[3:]
        og_image = f"{og_base_url}/{og_image_path}" if og_base_url else meta_image
        meta_description = makeMetaDescription(htmlContent, config)
        font_stylesheet_url = getConfigStr(
            config,
            "font_stylesheet_url",
            "https://fonts.googleapis.com/css2?family=Roboto+Mono:ital,wght@0,100..700;1,100..700&display=optional",
        )
        head_content = head_content.replace("{{ meta_image }}", meta_image)
        head_content = head_content.replace("{{ og_image }}", og_image)
        head_content = head_content.replace(
            "{{ meta_description }}", escape(meta_description)
        )
        head_content = head_content.replace(
            "{{ font_stylesheet_url }}", font_stylesheet_url
        )
        head_content = head_content.replace("{{ Title }}", title)
        head_content = head_content.replace("{{ relpath }}", f"{relative_path}")
        head_content = head_content.replace("{{ topnav }}", topnav_html)

    if first_image_src:
        htmlContent = wrapTitleAndDateHero(htmlContent, first_image_src)

    with open("template/body.html", "r", encoding="utf-8") as body_file:
        body_content = body_file.read()
        body_content = body_content.replace("{{ content }}", htmlContent)

    with open("template/script.html", "r", encoding="utf-8") as script_file:
        script_content = script_file.read()

    with open("template/footer.html", "r", encoding="utf-8") as footer_file:
        footer_content = footer_file.read()

    with open("template/base.html", "r", encoding="utf-8") as base_file:
        base_content = base_file.read()

    final_content = (
        base_content.replace("{{ head }}", head_content)
        .replace("{{ body }}", body_content)
        .replace("{{ footer }}", footer_content)
        .replace("{{ script }}", script_content)
    )

    if writeTextFile(contentHtmlPath, final_content, isSelinuxEnabled(config)):
        print(f"{color.GREEN}[ >> ]{color.RESET} : {contentHtmlPath}")


def extract_from_html(news_file_path: str):
    with open(news_file_path, "r", encoding="utf-8") as html_file:
        html_content = html_file.read()

    judul: list[str] = []
    timestamp: list[str] = []
    gambar: list[str] = []

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

    if not judul:
        judul.append("No Title")
    if not gambar:
        gambar.append("../img/default.png")
    if not timestamp:
        timestamp.append("No Timestamp")

    return judul, timestamp, gambar


def generateNewsList(
    news_dir: str,
    news_template_path: str,
    output_path: str,
    public_dir: str,
    selinux_enabled: bool = False,
):
    records: list[dict[str, str]] = []
    output_dir = os.path.dirname(output_path)

    if not os.path.isdir(news_dir):
        print(
            f"{color.YELLOW}[ !! ]{color.RESET} : news directory not found, skipping scan: {news_dir}"
        )
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
                f'<div class="news" style="background-image: linear-gradient(rgba(0, 0, 0, 0.25), rgba(0, 0, 0, 0.5)), url({thumbnail_href}); background-size: cover; background-position: center;"><a href="{news_href}"><b>{escape(record["title"])}</b><br>{escape(record["timestamp"])}</a></div>'
            )

        news_list = "\n".join(news_items)
        news_htmlContent = news_template_content.replace("{{ news_list }}", news_list)

    writeTextFile(output_path, news_htmlContent, selinux_enabled)


def initDir(content_dir: str, public_dir: str, config: dict[str, str | int | bool]):
    for root, _, files in os.walk(content_dir):
        for file in files:
            if file.endswith(".md"):
                markdownPath = os.path.join(root, file)
                relative_path = os.path.relpath(markdownPath, content_dir)
                contentHtmlPath = os.path.join(
                    public_dir, os.path.splitext(relative_path)[0] + ".html"
                )
                processMarkdown(markdownPath, contentHtmlPath, config)


def copySrcToPublic(
    src_dir: str, public_dir: str, template_dir: str, selinux_enabled: bool = False
):
    try:
        if not os.path.exists(public_dir):
            os.makedirs(public_dir)
    except PermissionError:
        print(
            f"{color.YELLOW}[ !! ]{color.RESET} : skip deploy (directory permission denied): {public_dir}"
        )
        return

    if not os.access(public_dir, os.W_OK | os.X_OK):
        print(
            f"{color.YELLOW}[ !! ]{color.RESET} : skip deploy (directory permission denied): {public_dir}"
        )
        return

    if len(os.listdir(src_dir)):
        for item in os.listdir(src_dir):
            print(f"{color.GREEN}[ -> ]{color.RESET}\t: {item}")
            s = os.path.join(src_dir, item)
            d = os.path.join(public_dir, item)
            if os.path.isdir(s):
                installTree(s, d, selinux_enabled)
            else:
                installFile(s, d, selinux_enabled=selinux_enabled)
    else:
        print(
            f"{color.YELLOW}[ !! ]{color.RESET} : ./src did not contain index.html, using template design instead"
        )


def copyImageToPublic(
    img_dir: str,
    public_dir: str,
    selinux_enabled: bool = False,
    config: dict[str, str | int | bool] | None = None,
):
    public_img_dir = os.path.join(public_dir, "img")

    if not os.path.isdir(img_dir):
        print(
            f"{color.YELLOW}[ !! ]{color.RESET} : image directory not found, skipping copy: {img_dir}"
        )
        return

    thumbnail_webp_quality = parseInt(
        (config or {}).get("thumbnail_webp_quality"),
        default=45,
        min_value=1,
        max_value=100,
    )

    try:
        if not os.path.exists(public_img_dir):
            os.makedirs(public_img_dir)
    except PermissionError:
        print(
            f"{color.YELLOW}[ !! ]{color.RESET} : skip images (directory permission denied): {public_img_dir}"
        )
        return

    if not os.access(public_img_dir, os.W_OK | os.X_OK):
        print(
            f"{color.YELLOW}[ !! ]{color.RESET} : skip images (directory permission denied): {public_img_dir}"
        )
        return

    exist_count = 0
    for root, _, files in os.walk(img_dir):
        rel_root = os.path.relpath(root, img_dir)
        target_root = (
            public_img_dir
            if rel_root == "."
            else os.path.join(public_img_dir, rel_root)
        )
        installDir(target_root, selinux_enabled)

        for filename in files:
            src_file = os.path.join(root, filename)
            dst_file = os.path.join(target_root, filename)

            if os.path.exists(dst_file):
                exist_count += 1
            else:
                print(f"[ ~> ] : {os.path.relpath(src_file, img_dir)}")
                installFile(src_file, dst_file, selinux_enabled=selinux_enabled)

            if os.path.splitext(filename)[1].lower() in IMAGE_EXTENSIONS:
                thumb_dst = thumbnailWebpPath(dst_file)
                buildThumbnailFromImage(
                    src_file,
                    thumb_dst,
                    selinux_enabled,
                    thumbnail_webp_quality,
                )

    print(
        f"{color.YELLOW}[ !! ]{color.RESET} : {exist_count} images already exist in public/img, skipped original copy"
    )


if __name__ == "__main__":
    config_path = "./config.toml"
    args: list[str] = list(sys.argv)

    if "--config" in args:
        config_index = args.index("--config")
        if config_index + 1 >= len(args):
            print("Error: --config requires a path")
            sys.exit(1)
        config_path = args[config_index + 1]
    elif "-c" in args:
        config_index = args.index("-c")
        if config_index + 1 >= len(args):
            print("Error: -c requires a path")
            sys.exit(1)
        config_path = args[config_index + 1]

    config: dict[str, str | int | bool] = readConfig(config_path)

    class color:
        GREEN = "\033[92m"
        YELLOW = "\033[93m"
        RED = "\033[91m"
        BLUE = "\033[94m"
        MAGENTA = "\033[95m"
        CYAN = "\033[96m"
        WHITE = "\033[97m"
        RESET = "\033[0m"

    def createMarkdown(markdownPath: str, title: str):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        markdownPath = os.path.join("./content", markdownPath + ".md")
        os.makedirs(os.path.dirname(markdownPath), exist_ok=True)
        with open(markdownPath, "w", encoding="utf-8") as md_file:
            md_file.write(f"# {title}\n### {timestamp}\n\nContent goes here.")  # pyright: ignore[reportUnusedCallResult]
        print(f"{color.CYAN}[ // ] :{color.RESET} Created {markdownPath}")

    def generateSite():
        start_time = time.time()
        selinux_enabled = isSelinuxEnabled(config)
        src_dir = getConfigStr(config, "src_dir")
        public_dir = getConfigStr(config, "public_dir")
        template_dir = getConfigStr(config, "template_dir")
        img_dir = getConfigStr(config, "img_dir")
        content_dir = getConfigStr(config, "content_dir")
        news_dir = getConfigStr(config, "news_dir")
        news_template_path = getConfigStr(config, "news_template_path")
        output_path = getConfigStr(config, "output_path")
        cache_max_age_days = parseInt(
            config.get("cache_max_age_days"), default=365, min_value=1, max_value=3650
        )
        copySrcToPublic(
            src_dir,
            public_dir,
            template_dir,
            selinux_enabled,
        )
        copyImageToPublic(
            img_dir,
            public_dir,
            selinux_enabled,
            config,
        )
        initDir(content_dir, public_dir, config)
        generateNewsList(
            news_dir,
            news_template_path,
            output_path,
            public_dir,
            selinux_enabled,
        )
        if parseBool(config.get("write_apache_cache_headers"), False):
            writeApacheCacheHeaders(
                public_dir,
                selinux_enabled,
                cache_max_age_days,
            )
        print(searchFile("./", "head.html"))
        end_time = time.time()
        print(f"[ T* ] : Total time taken {(end_time - start_time) * 1000:.2f} ms")

    date = ""
    args_gen = ["--g", "generate", "gen"]
    args_new = ["--n", "new"]

    if (
        len(args) < 2
        or args[1] not in args_gen
        and args[1] not in args_new
        and not "rconf"
    ):
        print(
            "IT Club SSG by zvlfahmi, slvr.12\n\nUsage:\n  python buildsite.py generate [--config path | -c path]\n  python buildsite.py new [folder] [filename] [--config path | -c path]\n\nOptions:\n  generate, : Generate the static site from markdown files.\n  --g, gen\n  new, --n  : Create a new markdown file with the specified filename.\n  --config, -c : Use a custom TOML config file."
        )
        sys.exit()

    if args[1] in args_gen:
        generateSite()

    if args[1] == "rconf":
        print(config)

    elif args[1] in args_new:
        folder = args[2]

        if len(args) > 3:
            title = args[3]
            date = ""

            config = readConfig(config_path)

            if parseBool(config.get("file-with-date"), False):
                date = datetime.now().strftime("%Y%m%d") + "-"

            if folder.endswith("/"):
                folder = folder[:-1]

            if title.endswith(".md"):
                title = title[:-3]

            markdownPath = os.path.join(folder, date + title)

            createMarkdown(markdownPath, title)

        else:
            title = folder.split("/")[-1]
            createMarkdown(folder, title)
