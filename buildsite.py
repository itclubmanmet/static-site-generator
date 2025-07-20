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

time_total = []

def read_config(config_file_path):
    with open(config_file_path, 'r', encoding='utf-8') as config_file:
        config = toml.load(config_file)
    return config

def calculate_relative_path(html_file_path, public_dir):
    depth = os.path.relpath(html_file_path, public_dir).count(os.sep)
    return '../' * depth

def convert_md_to_html(md_file_path, html_file_path, config):
    md = markdown.Markdown(extensions=[
        'markdown.extensions.extra',
        'markdown.extensions.codehilite',
        'markdown.extensions.tables',
        'markdown.extensions.toc',
        'markdown.extensions.meta',
        'markdown.extensions.admonition',
        'markdown_del_ins',
    ])

    relative_path = calculate_relative_path(html_file_path, 'public')
    with open(md_file_path, 'r', encoding='utf-8') as md_file:
        md_content = md_file.read()
        html_content = md.convert(md_content)
        #print(f'{color.GREEN}[ R ]{color.RESET} : {md_file_path}')
    
    with open('template/head.html', 'r', encoding='utf-8') as head_file:
        head_content = head_file.read()
        meta_image = []
        title = html_content.split('<h1 id="')[1].split('</h1>')[0].split('">')[1] if '<h1' in html_content else config.get('Title', '')
        head_content = head_content.replace('{{ meta_image }}', f'{html_content.split("<img alt=\"\" src=\""+relative_path)[1].split("\"")[0]}' if '<img alt="" src="' in html_content else config.get('meta_image', 'img/default.png'))        
        head_content = head_content.replace('{{ Title }}', title)
        head_content = head_content.replace('{{ relpath }}', f'{relative_path}')

    with open('template/body.html', 'r', encoding='utf-8') as body_file:
        body_content = body_file.read()
        body_content = body_content.replace('{{ content }}', html_content)

    with open('template/script.html', 'r', encoding='utf-8') as script_file:
        script_content = script_file.read()

    with open('template/footer.html', 'r', encoding='utf-8') as footer_file:
        footer_content = footer_file.read()

    with open('template/base.html', 'r', encoding='utf-8') as base_file:
        base_content = base_file.read()
    
    final_content = (base_content.replace('{{ head }}', head_content)
                                  .replace('{{ body }}', body_content)
                                  .replace('{{ footer }}', footer_content)
                                  .replace('{{ script }}', script_content)
                    )
    
    os.makedirs(os.path.dirname(html_file_path), exist_ok=True)
    with open(html_file_path, 'w', encoding='utf-8') as final_html_file:
        final_html_file.write(final_content)
        print(f'{color.GREEN}[ >> ]{color.RESET} : {html_file_path}')

def extract_from_html(news_file_path):
    with open(news_file_path, 'r', encoding='utf-8') as html_file:

        judul = []
        timestamp = []
        gambar = []
        
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
                            
def generate_news_html(news_dir, news_template_path, output_path):
    start_time = time.time()

    news_items = []
    
    with os.scandir(news_dir) as entries:
        for entry in entries:
            
            if entry.is_file():
                item = entry.name
                
                if item.endswith('.html'):
                    if item.startswith('index'):
                        continue

                    news_file_path = os.path.join(news_dir, item)
                    metadata = extract_from_html(news_file_path)
                    relative_path = os.path.splitext(os.path.relpath(news_file_path, news_dir))[0]
                    news_items.append(f'<div class="news" style="background-image: linear-gradient(rgba(0, 0, 0, 0.25), rgba(0, 0, 0, 0.5)), url({metadata[2][0]}); background-size: cover;"><a href="content/news/{relative_path}"><b>{metadata[0][0]}</b><br>{metadata[1][0]}</a></div>')
            
    with open(news_template_path, 'r', encoding='utf-8') as news_template_file:
        news_template_content = news_template_file.read()
        news_items.sort(key=lambda x: x.split('news/')[1].split('.html')[0], reverse=True)
        news_list = '\n'.join(news_items)
        news_html_content = news_template_content.replace('{{ news_list }}', news_list)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as news_html_file:
        news_html_file.write(news_html_content)

    end_time = time.time()
    time_total.append(f"generate_news_to_html took {(end_time - start_time) * 1000:.2f} ms")
    
def process_directory(content_dir, public_dir, config):
    start_time = time.time()
    for root, _, files in os.walk(content_dir):
        for file in files:
            if file.endswith('.md'):
                md_file_path = os.path.join(root, file)
                relative_path = os.path.relpath(md_file_path, content_dir)
                html_file_path = os.path.join(public_dir, os.path.splitext(relative_path)[0] + '.html')
                convert_md_to_html(md_file_path, html_file_path, config)
    
    end_time = time.time()
    time_total.append(f"process_directory took {(end_time - start_time) * 1000:.2f} ms")

def copy_src_to_public(src_dir, public_dir, template_dir):
    start_time = time.time()
    if not os.path.exists(public_dir):
        os.makedirs(public_dir)
    
    if 'index.html' in os.listdir(src_dir):
        for item in os.listdir(src_dir):
            print(f'{color.GREEN}[ -> ]{color.RESET}	: {item}')
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
    end_time = time.time()
    time_total.append(f"copy_src_to_public took {(end_time - start_time) * 1000:.2f} ms")
    
    
def copy_img_to_public(img_dir, public_dir):
    start_time = time.time()
    public_img_dir = os.path.join(public_dir, 'img')
    
    if not os.path.exists(public_img_dir):
        os.makedirs(public_img_dir)
    
    list_public_img = os.listdir(public_img_dir)
    exist = []
    for item in os.listdir(img_dir):
        if item in list_public_img:
            exist.append(item)
            continue

        else:
            print(f'[ ~> ] : {item}')
            s = os.path.join(img_dir, item)
            d = os.path.join(public_img_dir, item)
            if os.path.isdir(s):
                shutil.copytree(s, d, dirs_exist_ok=True)
            else:
                shutil.copy2(s, d)
    
    print(f'{color.YELLOW}[ !! ]{color.RESET} : {len(exist)} images already exist in public/img, skipping copy')
    end_time = time.time()
    time_total.append(f"copy_img_to_public took {(end_time - start_time) * 1000:.2f} ms")

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
        
        md_file_path = os.path.join('./content', md_file_path + '.md')
        os.makedirs(os.path.dirname(md_file_path), exist_ok=True)
        with open(md_file_path, 'w', encoding='utf-8') as md_file:
            md_file.write(f'# {title}\n### {timestamp}\n\nContent goes here.')
        print(f"{color.CYAN}[ // ] :{color.RESET} Created {md_file_path}")

    def generate():
        start_time = time.time()
        copy_src_to_public(config.get('tool-setting').get('src_dir'), config.get('tool-setting').get('public_dir'), config.get('tool-setting').get('template_dir'))
        copy_img_to_public(config.get('tool-setting').get('img_dir'), config.get('tool-setting').get('public_dir'))
        process_directory(config.get('tool-setting').get('content_dir'), config.get('tool-setting').get('public_dir'), config)
        generate_news_html(config.get('tool-setting').get('news_dir'), config.get('tool-setting').get('news_template_path'), config.get('tool-setting').get('news_output_path'))
        end_time = time.time()
        print(f"[ T* ] : Total time taken {(end_time - start_time) * 1000:.2f} ms")
        print("[ T* ] : " + ", ".join(time_total))

    args = []
    date = ''
    args_gen = ['--g', 'generate', 'gen']
    args_new = ['--n', 'new']

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
        
        folder = args[2]

        if len(args) > 3:
            title = args[3]
            date = ""

            config = read_config('./config.txt')

            if config.get('file-with-date'):
                date = datetime.now().strftime('%Y%m%d') + '-'
            
            if folder.endswith('/'):
                folder = folder[:-1]

            if title.endswith('.md'):
                title = title[:-3]

            md_file_path = os.path.join(folder, date + title)

            create_md_file(md_file_path, title)

        else:
            title = folder.split('/')[-1]
            create_md_file(folder, title)