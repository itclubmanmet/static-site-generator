# IT Club's Static Site Generator
Static Site Generator tailored for IT Club MAN's Website<br>


## Requirement :
- Python 3

## Dependencies :
markdown

## Installation : 
Install Python, check Python website for installation guide on your Operating System.

Then, clone this repository to your desired path and change directory to the cloned repository folder

```
~ $ git clone https://github.com/itclubmanmet/static-site-generator.git
~ $ cd static-site-builder
```

NOTE: If you need to, you can create virtual environment for Python

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
$ python buildsite.py new <folder>/<filename>.md
```

This will create file named `<filename>.md` inside folder `<folder>`

```
.
└── content
    └── <folder>
        └── <filename>.md
```

To generate the HTML file 

```
$ python buildsite.py generate
```

This will convert all markdown file under `content` folder and also copy CSS, JS or whatever in `src` then put them inside `public` folder

Note: *ALL files* under `src` will be put in the root folder of `public`

## Configuration

Inside `config.txt`, you can set `Title` and `file-with-date`.<br>
`file-with-date` will add date to the newly made markdown file<br>
I mean, you could just modify the template html inside *template* and `buildsite.py` to add more config

## File structure

Though not uploaded to this repository, you should add these folder:

```
.
├── buildsite.py
├── config.txt
├── content
├── public
├── src
├── img
├── template
│   ├── base.html
│   ├── body.html
│   ├── footer.html
│   ├── header.html
│   ├── head.html
│   ├── news.html
│   └── script.html
└── readme.md
```

- `public` folder is where all converted markdown in `content`, assets in `src`, images in `img` will 
reside after running the `buildsite.py generate`
- `img` folder is where the images are stored, when running the script it will be copied to `./public/img/`
- `template` folder is where the templates are located like the base, head, body, etc.
- `src` folder is where the script and stylesheet are, this folder will be copied to `./public/`
- `content` folder is where the markdowns are stored.

Though i just explained that `src` is for storing script and styesheet, i use it to store the base of my website such as
`index.html`, `news.html`, `about.html` because it has different layout than the template. 