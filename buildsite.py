#   MAN IT Club's SSG by Programming Division
#   zvlfahmi, slvr.12
#   IT Club 2024-2025

import markdown
import os
import shutil
import sys
from datetime import datetime
import time
import toml
from typing import List, Tuple, Dict

time_total: List[str] = []

def readConfig(configPath: str) -> Dict[str, str]:
    config: Dict[str, str] = {}
    with open(configPath, 'r', encoding='utf-8') as configFile:
        config = toml.load(configFile)
    return config

def calculateFolderRelPath(contentHtmlPath: str, publicDirPath: str) -> str:
    depth = os.path.relpath(contentHtmlPath, publicDirPath).count(os.sep)
    return '../' * depth

def processMarkdown(markdownPath: str, contentHtmlPath: str, config: Dict[str, str]) -> None:
    md = markdown.Markdown(extensions=[
        'markdown.extensions.extra',
        'markdown.extensions.codehilite',
        'markdown.extensions.tables',
        'markdown.extensions.toc',
        'markdown.extensions.meta',
        'markdown.extensions.admonition',
        'markdown_del_ins',
    ])

    relPath = calculateFolderRelPath(contentHtmlPath, 'public')
    with open(markdownPath, 'r', encoding='utf-8') as mdFile:
        mdFileContent = mdFile.read()
        htmlContent = md.convert(mdFileContent)
    
    with open('template/head.html', 'r', encoding='utf-8') as head_file:
        htmlContentHead = head_file.read()
        title = htmlContent.split('<h1 id="')[1].split('</h1>')[0].split('">')[1] if '<h1' in htmlContent else config.get('Title', '')
        htmlContentHead = htmlContentHead.replace('{{ meta_image }}', f'{htmlContent.split("<img alt=\"\" src=\""+relPath)[1].split("\"")[0]}' if '<img alt="" src="' in htmlContent else config.get('meta_image', 'img/default.png'))        
        htmlContentHead = htmlContentHead.replace('{{ Title }}', title)
        htmlContentHead = htmlContentHead.replace('{{ relpath }}', f'{relPath}')

    with open('template/body.html', 'r', encoding='utf-8') as templateFileBody:
        htmlContentBody = templateFileBody.read()
        htmlContentBody = htmlContentBody.replace('{{ content }}', htmlContent)

    with open('template/script.html', 'r', encoding='utf-8') as templateFileScript:
        htmlContentScript = templateFileScript.read()

    with open('template/footer.html', 'r', encoding='utf-8') as templateFileFooter:
        htmlContentFooter = templateFileFooter.read()

    with open('template/base.html', 'r', encoding='utf-8') as base_file:
        htmlContentBase = base_file.read()
    
    htmlContentProcessed = (htmlContentBase.replace('{{ head }}', htmlContentHead)
                                  .replace('{{ body }}', htmlContentBody)
                                  .replace('{{ footer }}', htmlContentFooter)
                                  .replace('{{ script }}', htmlContentScript)
                    )
    
    os.makedirs(os.path.dirname(contentHtmlPath), exist_ok=True)
    with open(contentHtmlPath, 'w', encoding='utf-8') as htmlContentProcessedFile:
        htmlContentProcessedFile.write(htmlContentProcessed)

def extractHtmlMetadata(newsFilePath: str) -> Tuple[List[str], List[str], List[str]]:
    with open(newsFilePath, 'r', encoding='utf-8') as html_file:

        judul: List[str] = []
        timestamp: List[str] = []
        gambar: List[str] = []
        
        for line in html_file:
            if '<h1 id="' in line:
                start = line.find('">') + 2
                end = line.find('</h1>')
                judul_berita = line[start:end].strip()
                judul.append(judul_berita)

            if '<h3 id="' in line:
                start = line.find('">') + 2
                end = line.find('</h3>')
                timestamp_berita = line[start:end].strip()
                timestamp.append(timestamp_berita)

            if '<img alt="" src="' in line:
                start = line.find('<img alt="" src="') + 17
                end = line.find('"', start)
                image_path = line[start:end].strip()
                if image_path.startswith('../'):
                    image_path = image_path[3:]
                gambar.append(image_path)

        if not judul:
            judul.append('No Title')
        if not gambar:
            gambar.append('../img/default.png')
        if not timestamp:
            timestamp.append('No Timestamp')
            
        return judul, timestamp, gambar
                            
def generateNewsFile(news_dir: str, templateNewsFile: str, outputPath: str) -> None:
    start_time = time.time()

    news_items: List[str] = []
    
    with os.scandir(news_dir) as entries:
        for entry in entries:
            
            if entry.is_file():
                item = entry.name
                
                if item.endswith('.html'):
                    if item.startswith('index'):
                        continue

                    newsFilePath = os.path.join(news_dir, item)
                    metadata = extractHtmlMetadata(newsFilePath)
                    relPath = os.path.splitext(os.path.relpath(newsFilePath, news_dir))[0]
                    news_items.append(f'<div class="news" style="background-image: linear-gradient(rgba(0, 0, 0, 0.25), rgba(0, 0, 0, 0.5)), url({metadata[2][0]}); background-size: cover;"><a href="news/{relPath}"><b>{metadata[0][0]}</b><br>{metadata[1][0]}</a></div>')
            
    with open(templateNewsFile, 'r', encoding='utf-8') as news_template_file:
        news_template_content = news_template_file.read()
        news_items.sort(key=lambda x: x.split('news/')[1].split('.html')[0], reverse=True)
        news_list = '\n'.join(news_items)
        news_htmlContent = news_template_content.replace('{{ news_list }}', news_list)

    os.makedirs(os.path.dirname(outputPath), exist_ok=True)
    with open(outputPath, 'w', encoding='utf-8') as news_html_file:
        news_html_file.write(news_htmlContent)

    end_time = time.time()
    time_total.append(f"generate_news_to_html took {(end_time - start_time) * 1000:.2f} ms")
    
def initDir(contentDirPath: str, publicDirPath: str, config: Dict[str, str]) -> None:
    start_time = time.time()
    for root, _, files in os.walk(contentDirPath):
        for file in files:
            if file.endswith('.md'):
                markdownPath = os.path.join(root, file)
                relPath = os.path.relpath(markdownPath, contentDirPath)
                contentHtmlPath = os.path.join(publicDirPath, os.path.splitext(relPath)[0] + '.html')
                processMarkdown(markdownPath, contentHtmlPath, config)
    
    end_time = time.time()
    time_total.append(f"initDir took {(end_time - start_time) * 1000:.2f} ms")

def copySourceToPublic(sourceDirPath: str, publicDirPath: str, template_dir: str) -> None:
    start_time = time.time()
    if not os.path.exists(publicDirPath):
        os.makedirs(publicDirPath)
    
    if 'index.html' in os.listdir(sourceDirPath):
        for item in os.listdir(sourceDirPath):
            s = os.path.join(sourceDirPath, item)
            d = os.path.join(publicDirPath, item)
            if os.path.isdir(s):
                shutil.copytree(s, d, dirs_exist_ok=True)
            else:
                shutil.copy2(s, d)
    else:
        for item in os.listdir(template_dir):
            s = os.path.join(template_dir, item)
            d = os.path.join(publicDirPath, item)
            if os.path.isdir(s):
                shutil.copytree(s, d, dirs_exist_ok=True)
            else:
                shutil.copy2(s, d)
    end_time = time.time()
    time_total.append(f"copySourceToPublic took {(end_time - start_time) * 1000:.2f} ms")
    
    
def copyImageToPublic(img_dir: str, publicDirPath: str) -> None:
    start_time = time.time()
    public_img_dir = os.path.join(publicDirPath, 'img')
    
    if not os.path.exists(public_img_dir):
        os.makedirs(public_img_dir)
    
    list_public_img = os.listdir(public_img_dir)
    exist: List[str] = []
    for item in os.listdir(img_dir):
        if item in list_public_img:
            exist.append(item)
            continue

        else:
            s = os.path.join(img_dir, item)
            d = os.path.join(public_img_dir, item)
            if os.path.isdir(s):
                shutil.copytree(s, d, dirs_exist_ok=True)
            else:
                shutil.copy2(s, d)
    
    end_time = time.time()
    time_total.append(f"copyImageToPublic took {(end_time - start_time) * 1000:.2f} ms")

if __name__ == "__main__":

    config = readConfig('./config.toml')

    class color:
        GREEN = '\033[92m'
        YELLOW = '\033[93m'
        RED = '\033[91m'
        BLUE = '\033[94m'
        MAGENTA = '\033[95m'
        CYAN = '\033[96m'
        WHITE = '\033[97m'
        RESET = '\033[0m'

    def createMarkdown(markdownPath: str, title: str) -> None:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        markdownPath = os.path.join('./content', markdownPath + '.md')
        os.makedirs(os.path.dirname(markdownPath), exist_ok=True)
        with open(markdownPath, 'w', encoding='utf-8') as mdFile:
            mdFile.write(f'# {title}\n### {timestamp}\n\nContent goes here.')

    def generateSite() -> None:
        start_time = time.time()
        tool_setting = config.get('tool-setting', {})
        if isinstance(tool_setting, dict):
            required_keys = ['sourceDirPath', 'publicDirPath', 'template_dir', 'img_dir', 'contentDirPath', 'news_dir', 'templateNewsFile', 'news_outputPath']
            missing_keys = [key for key in required_keys if not tool_setting.get(key)]
            if missing_keys:
                sys.exit(1)

            copySourceToPublic(tool_setting['sourceDirPath'], tool_setting['publicDirPath'], tool_setting['template_dir'])
            copyImageToPublic(tool_setting['img_dir'], tool_setting['publicDirPath'])
            initDir(tool_setting['contentDirPath'], tool_setting['publicDirPath'], config)
            generateNewsFile(tool_setting['news_dir'], tool_setting['templateNewsFile'], tool_setting['news_outputPath'])
        else:
            sys.exit(1)
        end_time = time.time()
        print(f"[ T* ] : Total time taken {(end_time - start_time) * 1000:.2f} ms")
        print("[ T* ] : " + ", ".join(time_total))
    
    args: List[str] = []
    date = ""
    args_gen = ["--g", "generate", "gen"]
    args_new = ["--n", "new"]

    for i in range(len(sys.argv)):
        args.append(sys.argv[i])

    if (
        len(args) < 2
        or args[1] not in args_gen
        and args[1] not in args_new
        and not "rconf"
    ):
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

            config = readConfig("./config.txt")

            if config.get("file-with-date"):
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
