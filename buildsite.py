import markdown
import os
import shutil
import sys
from datetime import datetime
import time

def read_config(config_file_path):
    config = {}
    with open(config_file_path, 'r', encoding='utf-8') as config_file:
        for line in config_file:
            if line.strip() and not line.startswith('#'):
                key, value = line.split('=', 1)
                config[key.strip()] = value.strip()
        print(f'Config  : {config}')
    return config

def calculate_relative_path(html_file_path, public_dir):
    depth = os.path.relpath(html_file_path, public_dir).count(os.sep)
    return '../' * depth # Return relative path based on depth

def convert_md_to_html(md_file_path, html_file_path, config):
    with open(md_file_path, 'r', encoding='utf-8') as md_file:
        md_content = md_file.read()
        html_content = markdown.markdown(md_content)
        print(f'Reading : {md_file_path}')
        # Read .md then Convert it to .html
    
    with open('template/head.html', 'r', encoding='utf-8') as head_file:
        head_content = head_file.read()
        head_content = head_content.replace('{{ Title }}', config.get('Title', ''))

        # This is important, !! CSS MUST BE IN THE ROOT OF ./src !! 
        # Otherwise, it won't work. As relative_path is calculated from ./public and
        # since ./src is copied to ./public, the CSS file is expected to be in the root of ./public

        relative_path = calculate_relative_path(html_file_path, 'public')
        head_content = head_content.replace('{{ style }}', f'<link href="{relative_path}style.css" rel="stylesheet">')
        
    with open('template/header.html', 'r', encoding='utf-8') as header_file:
        header_content = header_file.read()

        relative_path = calculate_relative_path(html_file_path, './public')
        header_content = header_content.replace('{{ header }}', f'<ul class="topnav"> \n <li><a href="{relative_path}index.html">Home</a></li> \n <li><a href="{relative_path}content/news.html">News</a></li> \n <li><a href="{relative_path}content/gallery.html">Gallery</a></li> \n <li><a href="{relative_path}content/about.html">About</a></li> \n </ul>')
        # I put the header content here because i need to calculate the relative path first
        # IT EXPECTED INDEX.HTML TO BE IN THE ROOT OF ./src !
        # (github-pages require you to do so anyway..)
        # You may change the link for other pages to its respective path

    with open('template/body.html', 'r', encoding='utf-8') as body_file:
        body_content = body_file.read()
        body_content = body_content.replace('{{ content }}', html_content)
        # Insert the converted HTML content into the body template

    with open('template/script.html', 'r', encoding='utf-8') as script_file:
        script_content = script_file.read()
        script_content = script_content.replace('{{ script_src }}', f'<script src="{relative_path}script.js"></script>')
        # !! JAVASCRIPT MUST BE IN THE ROOT OF ./src !!
    
    with open('template/base.html', 'r', encoding='utf-8') as base_file:
        base_content = base_file.read()
    
    final_content = (base_content.replace('{{ head }}', head_content)
                                  .replace('{{ header }}', header_content)
                                  .replace('{{ body }}', body_content)
                                  .replace('{{ footer }}', f'<footer id="footer">\n<p>IT Club MAN 1 Metro<br>\n<a href="mailto:itclubmanmet@gmail.com">Email IT Club MAN 1 Metro</a><br>\n<a href="https://www.instagram.com/itclub_mansametro/">Instagram IT Club</a></p></footer>')
                                  .replace('{{ script }}', script_content)
                    )
    
    os.makedirs(os.path.dirname(html_file_path), exist_ok=True)
    with open(html_file_path, 'w', encoding='utf-8') as final_html_file:
        final_html_file.write(final_content)
        print(f'Writing : {html_file_path}')

        def generate_news_html(news_dir, news_template_path, output_path):
            news_items = []
            for root, _, files in os.walk(news_dir):
                for file in files:
                    if file.endswith('.html'):
                        # Extract title from HTML file
                        def extract_title_from_html(html_file_path):
                            with open(html_file_path, 'r', encoding='utf-8') as html_file:
                                for line in html_file:
                                    if '<h1>' in line:
                                        start = line.find('<h1>') + 4
                                        end = line.find('</h1>')
                                        return line[start:end].strip()
                                    
                        def extract_timestamp_from_html(html_file_path):
                            with open(html_file_path, 'r', encoding='utf-8') as html_file:
                                for line in html_file:
                                    if '<h3>' in line:
                                        start = line.find('<h3>') + 4
                                        end = line.find('</h3>')
                                        return line[start:end].strip()

                        news_file_path = os.path.join(root, file)
                        relative_path = os.path.relpath(news_file_path, news_dir)
                        title_path = './public/content/news/' + relative_path
                        news_items.append(f'<li><a href="news/{relative_path}"><b>{extract_title_from_html(title_path)}</b><br>{extract_timestamp_from_html(title_path)}</a></li>')
                        
            with open(news_template_path, 'r', encoding='utf-8') as news_template_file:
                news_template_content = news_template_file.read()
                news_items = [item for item in news_items if 'zzzzz-dummy.html' not in item] # Remove dummy news items
                news_items.sort(key=lambda x: x.split('news/')[1].split('.html')[0], reverse=True)
                news_list = '\n'.join(news_items)
                news_html_content = news_template_content.replace('{{ news_list }}', news_list)

            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as news_html_file:
                news_html_file.write(news_html_content)

        news_dir = './public/content/news'
        news_template_path = 'template/news.html'
        output_path = './public/content/news.html'
        generate_news_html(news_dir, news_template_path, output_path)
    
def process_directory(content_dir, public_dir, config):
    for root, _, files in os.walk(content_dir):
        for file in files:
            if file.endswith('.md'):
                md_file_path = os.path.join(root, file)
                relative_path = os.path.relpath(md_file_path, content_dir)
                html_file_path = os.path.join(public_dir, os.path.splitext(relative_path)[0] + '.html')
                convert_md_to_html(md_file_path, html_file_path, config)

def copy_src_to_public(src_dir, public_dir):
    if not os.path.exists(public_dir):
        os.makedirs(public_dir)
    for item in os.listdir(src_dir):
        print(f'Copying : {item}')
        s = os.path.join(src_dir, item)
        d = os.path.join(public_dir, item)
        if os.path.isdir(s):
            shutil.copytree(s, d, dirs_exist_ok=True)
        else:
            shutil.copy2(s, d)

def copy_img_to_public(img_dir, public_dir):
    public_img_dir = os.path.join(public_dir, 'img')
    if not os.path.exists(public_img_dir):
        os.makedirs(public_img_dir)
    for item in os.listdir(img_dir):
        print(f'Copying : {item}')
        s = os.path.join(img_dir, item)
        d = os.path.join(public_img_dir, item)
        if os.path.isdir(s):
            shutil.copytree(s, d, dirs_exist_ok=True)
        else:
            shutil.copy2(s, d)

if __name__ == "__main__":
    

    def create_md_file(md_file_path):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        md_file_path = os.path.join('./content', md_file_path)
        os.makedirs(os.path.dirname(md_file_path), exist_ok=True)
        with open(md_file_path, 'w', encoding='utf-8') as md_file:
            md_file.write(f'# New Markdown File\n### {timestamp}\n\nContent goes here.')

    if len(sys.argv) > 1:
        if sys.argv[1] == 'generate':
            start_time = time.time()
            content_dir = './content'
            public_dir = './public'
            src_dir = './src'
            img_dir = './img'
            config_file_path = './config.txt'
            config = read_config(config_file_path)
            copy_src_to_public(src_dir, public_dir)
            copy_img_to_public(img_dir, public_dir)
            process_directory(content_dir, public_dir, config)
            end_time = time.time()
            print(f"Time taken: {end_time - start_time:.2f} seconds")

        elif sys.argv[1] == 'new':
                if len(sys.argv) > 2:
                    md_file_path = sys.argv[2]
                    if md_file_path.endswith('.md'):
                        config = read_config('./config.txt')
                        date = ''
                        if config.get('file-with-date') == '1':
                            date = datetime.now().strftime('%Y%m%d') + '-'
                        create_md_file(f'{date + md_file_path}')
                    else:
                        print("Error: The specified file must have a .md extension.")
                else:
                    print("Error: No file path specified.")
        else: 
            print("Error: Invalid arguments. Use 'generate' to build the site or 'new' to create a new markdown file.")

    else:
        print("Error: Invalid arguments. Use 'generate' to build the site or 'new' to create a new markdown file.")