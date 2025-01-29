# Static Site Builder

Static site builder tailored for IT Club MAN's Website

## Dependencies :

markdown

## Usage:

To generate markdown file inside *content* folder 

`$ python buildsite.py <folder>/<filename>.md`

example:

`$ python buildsite.py foo/bar.md`

To generate the HTML file 

`$ python buildsite.py generate`

This will convert all markdown file under *content* folder, copy CSS, JS or whatever in *src* and put them inside *public* folder<br>
Note: ALL files under *src* will be put in the root folder of *public*

## Configuration

Inside `config.txt`, you can set `Title`. That's it as of right now<br>
I mean, you could just modify the template html inside *template* and `buildsite.py` to add more config

## File structure

```
.
├── buildsite.py
├── config.txt
├── content
├── public
├── src
└── template
    ├── base.html
    ├── body.html
    ├── footer.html
    ├── header.html
    ├── head.html
    ├── news.html
    └── script.html
```