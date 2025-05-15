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

def read_config(config_file_path):
    with open(config_file_path, 'r', encoding='utf-8') as config_file:
        config = toml.load(config_file)
    return config

def calculate_relative_path(html_file_path, public_dir):
    depth = os.path.relpath(html_file_path, public_dir).count(os.sep)
    return '../' * depth

def convert_md_to_html(md_file_path, html_file_path, config):
    with open(md_file_path, 'r', encoding='utf-8') as md_file:
        md_content = md_file.read()
        html_content = markdown.markdown(md_content)
        #print(f'{color.GREEN}[ R ]{color.RESET} : {md_file_path}')
    
    with open('template/head.html', 'r', encoding='utf-8') as head_file:
        head_content = head_file.read()
        head_content = head_content.replace('{{ Title }}', config.get('metadata').get('Title'))
        relative_path = calculate_relative_path(html_file_path, 'public')
        head_content = head_content.replace('{{ style }}', f'<link href="{relative_path}style.css" rel="stylesheet">')
        
    with open('template/header.html', 'r', encoding='utf-8') as header_file:
        header_content = header_file.read()

        relative_path = calculate_relative_path(html_file_path, './public')
        header_content = header_content.replace('{{ header }}', f'<ul class="topnav"> \n <li><a href="{relative_path}index.html">Home</a></li> \n <li><a href="{relative_path}content/news.html">News</a></li> \n <li><a href="{relative_path}content/gallery.html">Gallery</a></li> \n <li><a href="{relative_path}content/about.html">About</a></li> \n </ul>')

    with open('template/body.html', 'r', encoding='utf-8') as body_file:
        body_content = body_file.read()
        body_content = body_content.replace('{{ content }}', html_content)

    with open('template/script.html', 'r', encoding='utf-8') as script_file:
        script_content = script_file.read()
        script_content = script_content.replace('{{ script_src }}', f'<script src="{relative_path}script.js"></script>')
    
    with open('template/footer.html', 'r', encoding='utf-8') as footer_file:
        footer_content = footer_file.read()

    with open('template/base.html', 'r', encoding='utf-8') as base_file:
        base_content = base_file.read()
    
    final_content = (base_content.replace('{{ head }}', head_content)
                                  .replace('{{ header }}', header_content)
                                  .replace('{{ body }}', body_content)
                                  .replace('{{ footer }}', footer_content)
                                  .replace('{{ script }}', script_content)
                    )
    
    os.makedirs(os.path.dirname(html_file_path), exist_ok=True)
    with open(html_file_path, 'w', encoding='utf-8') as final_html_file:
        final_html_file.write(final_content)
        print(f'{color.GREEN}[ OK ]{color.RESET} : Generated {html_file_path}')

def extract_from_html(news_file_path):
    with open(news_file_path, 'r', encoding='utf-8') as html_file:
        judul = []
        timestamp = []
        gambar = []
        for line in html_file:
            if '<h1>' in line:
                start = line.find('<h1>') + 4
                end = line.find('</h1>')
                judul_berita = line[start:end].strip()
                judul.append(judul_berita)

            if '<h3>' in line:
                start = line.find('<h3>') + 4
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

        if not gambar:
            gambar.append('../img/default.png')
        if not timestamp:
            timestamp.append('No Timestamp')
        return judul, timestamp, gambar
                            
def generate_news_html(news_dir, news_template_path, output_path):
    # brace for if for else chain !!!!1!111!!
    news_items = []
            
    with os.scandir(news_dir) as entries:
        for entry in entries:
            if entry.is_file():
                item = entry.name
                if item.endswith('.html'):
                    news_file_path = os.path.join(news_dir, item)
                    relative_path = os.path.relpath(news_file_path, news_dir)
                    metadata = extract_from_html(news_file_path)
                    news_items.append(f'<div class="news" style="background-image: linear-gradient(rgba(0, 0, 0, 0.25), rgba(0, 0, 0, 0.5)), url({metadata[2][0]}); background-size: cover;"><a href="./news/{relative_path}"><b>{metadata[0][0]}</b><br>{metadata[1][0]}</a></div>')
        
            with open(news_template_path, 'r', encoding='utf-8') as news_template_file:
                news_template_content = news_template_file.read()
                news_items.sort(key=lambda x: x.split('news/')[1].split('.html')[0], reverse=True)
                news_list = '\n'.join(news_items)
                news_html_content = news_template_content.replace('{{ news_list }}', news_list)

            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as news_html_file:
                news_html_file.write(news_html_content)
    
def process_directory(content_dir, public_dir, config):
    for root, _, files in os.walk(content_dir):
        for file in files:
            if file.endswith('.md'):
                md_file_path = os.path.join(root, file)
                relative_path = os.path.relpath(md_file_path, content_dir)
                html_file_path = os.path.join(public_dir, os.path.splitext(relative_path)[0] + '.html')
                convert_md_to_html(md_file_path, html_file_path, config)

def copy_src_to_public(src_dir, public_dir, template_dir):
    if not os.path.exists(public_dir):
        os.makedirs(public_dir)
    
    if 'index.html' in os.listdir(src_dir):
        for item in os.listdir(src_dir):
            print(f'{color.GREEN}[ -> ]{color.RESET} : Copying {item} to {public_dir}')
            s = os.path.join(src_dir, item)
            d = os.path.join(public_dir, item)
            if os.path.isdir(s):
                shutil.copytree(s, d, dirs_exist_ok=True)
            else:
                shutil.copy2(s, d)
    else:
        print(f'{color.YELLOW}[ !! ]{color.RESET} : ./src did not contain index.html, using template design instead')
        for item in os.listdir(template_dir):
            print(f'[ -> ] : {template_dir}/{item} -> {public_dir}')
            s = os.path.join(template_dir, item)
            d = os.path.join(public_dir, item)
            if os.path.isdir(s):
                shutil.copytree(s, d, dirs_exist_ok=True)
            else:
                shutil.copy2(s, d)
    
def copy_img_to_public(img_dir, public_dir):
    public_img_dir = os.path.join(public_dir, 'img')
    
    if not os.path.exists(public_img_dir):
        os.makedirs(public_img_dir)
    
    list_public_img = os.listdir(public_img_dir)
    for item in os.listdir(img_dir):
        if item in list_public_img:
            # print(f'{color.YELLOW}[ W ]{color.RESET} : {item} already exists in ./public/img, skipping')
            continue
        else:
            print(f'Copying : {item}')
            s = os.path.join(img_dir, item)
            d = os.path.join(public_img_dir, item)
            if os.path.isdir(s):
                shutil.copytree(s, d, dirs_exist_ok=True)
            else:
                shutil.copy2(s, d)

if __name__ == "__main__":

    config = read_config('./config.toml')

    class color:
        GREEN = '\033[92m'
        YELLOW = '\033[93m'
        RED = '\033[91m'
        BLUE = '\033[94m'
        MAGENTA = '\033[95m'
        CYAN = '\033[96m'
        WHITE = '\033[97m'
        RESET = '\033[0m'

    def create_md_file(md_file_path, title):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        md_file_path = os.path.join('./content', md_file_path)
        os.makedirs(os.path.dirname(md_file_path), exist_ok=True)
        with open(md_file_path, 'w', encoding='utf-8') as md_file:
            md_file.write(f'# {title}\n### {timestamp}\n\nContent goes here.')
        print(f"{color.CYAN}[ // ] :{color.RESET} Created {md_file_path}")

    def generate():
        start_time = time.time()
        # print(f'[ ++ ]: {config}')
        copy_src_to_public(config.get('tool-setting').get('src_dir'), config.get('tool-setting').get('public_dir'), config.get('tool-setting').get('template_dir'))
        copy_img_to_public(config.get('tool-setting').get('img_dir'), config.get('tool-setting').get('public_dir'))
        process_directory(config.get('tool-setting').get('content_dir'), config.get('tool-setting').get('public_dir'), config)
        generate_news_html(config.get('tool-setting').get('news_dir'), config.get('tool-setting').get('news_template_path'), config.get('tool-setting').get('news_output_path'))
        end_time = time.time()
        print(f"Time taken: {(end_time - start_time) * 1000:.2f} ms")

    args = []
    args_gen = ['--g', 'generate', 'gen']
    args_new = ['--n', 'new']
    date = ''

    for i in range(len(sys.argv)):
        args.append(sys.argv[i])
    
    if len(args) < 2 or args[1] not in args_gen and args[1] not in args_new and not "rconf":
        print(f"IT Club SSG by zvlfahmi, slvr.12\n\nUsage:\n  python buildsite.py generate\n  python buildsite.py new [folder] [filename]\n\nOptions:\n  generate, : Generate the static site from markdown files. \n  --g, gen\n  new, --n  : Create a new markdown file with the specified filename.")
        sys.exit()
        
    if args[1] in args_gen:
        generate()
    
    if args[1] == 'rconf' :
        print(config)
        # debugging purposes

    elif args[1] in args_new:
        folder = ''
        title = args[2]
        
        if len(args) > 3:
            folder = args[2]
            title = args[3]
            if folder.endswith('/'):
                folder = folder[:-1]
        
        if config.get('file-with-date') == '1':
            date = datetime.now().strftime('%Y%m%d') + '-'
        
        md_file_path = os.path.join(folder, date + title)
        
        if md_file_path.endswith('.md'):
            create_md_file(f'{md_file_path}', title[:-3])
        else:
            create_md_file(f'{md_file_path}.md', title)
