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

This will convert all markdown file under `content` folder and also copy CSS, JS or whatever in `src` then put them inside `public` folder

Note: *ALL files* under `src` will be put in the root folder of `public` and oh ANY FILE WITH EXTENSION OTHER THAN .md WILL BE IGNORED AND NOT COPIED OVER TO `public`

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
│   ├── design
│   │   ├── index.html
│   │   ├── style.css
│   │   └── script.js
│   ├── base.html
│   ├── body.html
│   ├── footer.html
│   ├── header.html
│   ├── head.html
│   ├── news.html
│   └── script.html
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

### e. Template

These are the base of the website that was generated, it will be used when generating the markdown into html.
