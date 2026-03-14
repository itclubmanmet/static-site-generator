# IT Club's Static Site Generator
Static Site Generator tailored for IT Club MAN's Website<br>
Created by IT Club (2024-2025) Programming Division [Zulfahmi Azka](https://github.com/zvlfahmi) and Hasan Ibnu (slvr.12)

## Requirement :
- Python 3
- AmogOS not tested yet, but it theoretically work on modern operating system.

## Dependencies :

markdown, markdown_del_ins, Pillow, toml

## Installation : 

Install Python, check Python website for installation guide on your Operating System.

Then, clone this repository to your desired path and change directory to the cloned repository folder

```sh
git clone https://github.com/itclubmanmet/static-site-generator.git
cd static-site-generator
```

To install the dependency, run this command.

> Best Practice: generate virtual environment with `python -m venv env` to seperate the system python package with this project package. Arch Linux doesn't like when you use `pip` without virtual environment

```sh
pip install -r requirements.txt
```

## Usage:

To generate markdown file inside `content` folder

```sh
python buildsite.py new <filename>.md
```

This will create a file under `content` folder

```term
.
└── content
    └── <filename>.md
```

You can also make a file inside a folder by adding path to that file

```sh
python buildsite.py new <folder> <filename>.md
```

This will create file named `<filename>.md` inside folder `<folder>`

```term
.
└── content
    └── <folder>
        └── <filename>.md
```

By default, newly made markdown file will contain the following

```md
# { filename }
### { Timestamp } 
```

To generate the HTML file 

```sh
python buildsite.py generate
```

## Configuration

```toml
[metadata]
    Title = "IT Club"
    description = ""
    site_url = "https://itclubmanmet.github.io"
    font_stylesheet_url = "https://fonts.googleapis.com/css2?family=Red+Hat+Display:ital,wght@0,300..900;1,300..900&display=swap"
    navbar_template_path = "template/design/navbar.html"

[tool-setting]
    file-with-date = 1
    content_dir = "./content"
    public_dir = "./public"
    src_dir = "./src"
    img_dir = "./img"
    template_dir = "./template/design"
    news_dir = "./public/content/news"
    news_template_path = "./template/design/newsitc.html"
    output_path = "./public/content/index.html"
    debugMode = 1
    SELinux = true
    image_jpeg_quality = 70
    image_png_compress_level = 8
    image_webp_quality = 70
    thumbnail_webp_quality = 45
    write_apache_cache_headers = 0

````
### [metadata]

1. `Title`, as the name suggest this is the Title of the website. This will show up in the Tab Title.
2. `description`, fallback description if the content description not available.
3. `site_url`, site root URL
4. `font_stylesheet_url`, global font used for the website
5. `navbar_template_path`, navbar template location

### [tool-setting]

1. `file-with-date` (boolean): when making new markdown content it will put the creation date (not published date) on the filename 
2. `content_dir` (string): markdown files folder location
3. `public_dir` (string): output folder path, can be anything 
4. `src_dir` (string): source file folder path [deprecated]
5. `img_dir` (string): image folder path
6. `template_dir` (string): website template folder path 
7. `news_dir` (string): news/content folder output path (usually under `public_dir`)
8. `news_template_path` (string): news/content template path 
9. `output_path` (string): news/content HTML file output path (usually under `public_dir`)
10. `debugMode` (boolean): enable verbose info [deprecated]
11. `SELinux` (boolean): add proper SELinux tag for SELinux enabled (or perhaps AppArmor too) distro
12. `image_jpeg_quality` (integer): JPEG Quality
13. `image_png_compress_level` (integer): PNG Compress level
14. `image_webp_quality` (integer): WebP Quality
15. `thumbnail_webp_quality` (integer): WebP Quality for Thumbnail
16. `write_apache_cache_headers` (boolean): Set longer caching for Apache webserver

## File structure

Though not uploaded to this repository, you should add these folder:

```
.
├── buildsite.py
├── main.py
├── config.txt
├── content
├── public
├── src
├── img
├── template
│  ├── design
│  │   ├── index.html
│  │   ├── style.css
│  │   └── script.js
│  ├── base.html
│  ├── body.html
│  ├── footer.html
│  ├── header.html
│  ├── head.html
│  ├── news.html
│  └── script.html
├── requirements.txt
└── readme.md
```

### a. Markdown

This Static Site Generator utilize Markdown as it was easy to use, the markdown file(s) will reside in `content`. The markdown file(s) will be generated into `public_dir` when running the script with `generate` 

> WARNING: `content` acts like the root of the website, so if you only had `content/file.md` it will be put into `public_dir/file.html`!

### b. Output Folder

By default configuration, the script will generate its output into `public` directory. In `config.toml` this is defined by `public_dir`, this can be changed to any directory.

Example usecase: Changing the `public_dir` to `/var/www/blog` if you hosted Apache or nginx webserver

### c. Theme

Theme can be done in `template/design` directory, you can put custom `index.html` if you want different front page or `style.css`.

This used to be done in `src` but it was deprecated in favor of `template/design`

### d. Image

Images can be put into `img` directory, and it will be copied to `public_dir` as `public_dir/img`. While trying to embed the image, you can do `![comment](/img/file.jpg)` but this do some weird stuff with VS Code Live Server Extension

> Adding comment might break things, let me know if it broke something

### e. Template

These are the base of the website that was generated, it will be used when generating the markdown into html.
