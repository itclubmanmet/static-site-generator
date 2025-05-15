# IT Club's Static Site Generator
Static Site Generator tailored for IT Club MAN's Website<br>

## Requirement :
- Python 3
- Any OS that is supported by Python

## Dependencies :
- markdown
- toml

## Installation : 
Install Python, check Python website for installation guide on your Operating System.

Then, clone this repository to your desired path and change directory to the cloned repository folder

```
$ git clone https://github.com/itclubmanmet/static-site-generator.git
$ cd static-site-generator
```

To install the dependency, run this command.
NOTE: If you need to, you can create virtual environment for your Python installation.

```
$ pip install -r requirements.txt
```

## Usage:
To generate markdown file inside `content` folder

```
$ python buildsite.py new <filename>.md
```

This will create a file under `content` folder

```
.
└── content
    └── <filename>.md
```

You can also make a file inside a folder by adding path to that file

```
$ python buildsite.py new <folder> <filename>.md
```

This will create file named `<filename>.md` inside folder `<folder>`

```
.
└── content
    └── <folder>
        └── <filename>.md
```

By default, newly made markdown file will contain the following

```
# { filename }
### { Timestamp } 
```

To generate the HTML file 

```
$ python buildsite.py generate
```

## Configuration

```
[metadata]
    Title = "IT Club"
    description = "" 
    # as of right now, description does nothing

[tool-setting]
    file-with-date = 1
    content_dir = "./content"
    public_dir = "./public"
    src_dir = "./src"
    img_dir = "./img"
    template_dir = "./template/design"
    news_dir = "./public/content/news"
    news_template_path = "./template/news.html"
    news_output_path = "./public/content/news.html"
```

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

- `public` folder is where all the converted markdown in `content`, assets in `src`, and images in `img` will go after running the `buildsite.py generate`
- `img` contains image
- `template` contains template to generate the site, it also contains the theme. 
stylesheet, and script from `template` instead
- `src` contains source if you're writing the index.html, script or stylesheet yourself.
- `content` folder is where the markdowns are stored.

