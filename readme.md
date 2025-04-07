# IT Club's Static Site Generator
Static Site Generator tailored for IT Club MAN's Website<br>

## Requirement :
- Python 3
- UNIX or UNIX-like Operating System (not tested on Windows yet)

## Dependencies :
markdown

(yes, it only need single dependencies from pip)

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
To generate markdown file inside `content` folder <br>

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

There's 3 configuration you can change it `config.txt`
- `Title` (string), Change the title on the website tab
- `file-with-date` (boolean), generate new markdown file with date at the front
- `generate-news` (boolean), choose to generate `news.html` or not

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

- `public` folder is where all converted markdown in `content`, assets in `src`, and images in `img` will 
reside after running the `buildsite.py generate`
- `img` folder is where the images are stored, when running the script it will be copied to `./public/img/`. 
- `template` folder is where the templates are located like the base, head, body, and also if `src` don't have `index.html`, it will copy `index.html`, stylesheet, and script from `template` instead
- `src` folder is where the index HTMl, script, and stylesheet are, this folder will be copied to `./public/`, if there's no `index.html` in it then the program will copy from `template` instead
- `content` folder is where the markdowns are stored.

