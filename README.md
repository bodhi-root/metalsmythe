# Metalsmythe

## Overview

Metalsmythe is a simple Python package that can be used to build static websites from Markdown files.  It is based on the ["Metalsmith" package](https://metalsmith.io) for Node.js.  If you like Metalsmith and don't mind working with Node.js, npm, and JavaScript, you should probably just stick with that.  On the other hand, if you hate working with JavaScript, get frustrated looking up documentation for all the Metalsmith plugins, and would rather have a few Python scripts that are easier to read and modify for your own purposes, you just might find this useful.  I developed this package for a website I had built using Metalsmith that published my guitar tabs collection on GitHub Pages.  Even though it doesn't have near as much functionality or support as Metalsmith, I think I like it better for this simple purpose.  It also lets me test the site without having to install Node.js, npm, and all that weird JavaScript stuff on my computer.

## Project Setup and Usage

The Python code for the project is contained in the "metalsmythe" subdirectory as well as the following files:

- build.py - Build script for website
- serve.py - Simple web server for local testing
- jinja_test.py - A test script for rendering a single page

If you want to use this with your own project, you will need to:

1. Copy the ```metalsmythe``` directory along with ```requirements.txt```, ```build.py```, and ```serve.py```, to your project
2. Install Python requirements with ```pip install -r requirements.txt```
3. Modify the ```build.py``` script for your purposes
4. Run ```python build.py``` to build your site
5. Run ```python serve.py``` to run the local test server and view your site on http://localhost:8000

The content for the website is located in the ```src``` and ```layouts``` directories, but this is customizable.  The demo website content is copied (with only slight modifications) from [this awesome Metalsmith demo site](https://github.com/wernerglinka/metalsmith-blog-starter).  Thank you to the creator of that project for making such a simple and beautiful template!

## Build Script

The example ```build.py``` script basically looks like this:

```python
from metalsmythe.builder import Builder, copy_directory
from jinja2 import Environment, FileSystemLoader

metadata = {...}

jinja_env = Environment(
    loader=FileSystemLoader("layouts"),
    autoescape=True
)

builder = Builder(metadata)
builder.load_files("**/*.md", base_dir="src/content")
builder.create_collection("blog", "blog/*.md", 
                          sort_key=lambda x: x["date"], 
                          reverse=True, limit=10)
builder.markdown_to_html()
builder.apply_layouts(jinja_env, default_layout="simple.html")

builder.write("build", clean=True)
copy_directory("src/assets", "build/assets")
```

This will:

1. Define some metadata (a dictionary of values that we want to make available to all pages)
2. Create a Jinja2 environment for HTML templating.  (This will use templates located in the "layouts" directory.)
3. Load every ".md" file under "src/content".  These are loaded with path names relative to the base directory ("src/content").  YAML frontmatter is parsed into a dictionary and special properties are added for page content ("contents") and path ("path").
4. Convert all ".md" files we've loaded to HTML content
5. Use Jinja2 templates to convert the HTML fragments into full web pages
6. Writes the output to the "build" directory (after deleting it first so we can build cleanly).
7. Copy static assets (image and style sheets) from "src/assets" to "build/assets".

While the Builder object has some common, pre-defined functions for reading, transforming, and writing our content, we can also add any custom logic we want to this process.  All file content is stored in ```builder.files``` as a list of dict objects.  Metadata is also available as ```builder.metadata```.  If we were to follow the Metalsmith paradigm of creating a pipeline of transformations to apply, these might look like:

```python
def transform(builder:Builder):
    # transform logic here
```

We could easily chain these tranfsormations together if we'd like as well to look even more like Metalsmith.  We have decided not to do that since it's easier for developers to write and debug their transformations one-at-a-time on data that is already loaded rather than having to re-run the pipeline and then hunt through the stack trace to see where errors occur.  Loading everything into memory might be problematic for massive websites, but we're going for simplicity here, not production-level performance.

## Jinja Templates

[Jinja](https://jinja.palletsprojects.com/en/3.1.x/) is used for HTML templating.  These are nearly identical to the JavaScript "Nunjucks" templating language used by the original project.  Jinja lets you templates reference each other, so you can break up your website design into smaller parts.  You might have a high-level layout that looks like this:

__File: layout.html__

```html
<html>
  <head>
  
    {% include "partials/head.html" %}
  
  </head>
  <body class="{{ bodyClass }}">

    {% include "partials/header.html" %}
    
    <main>
    {% block body %}
    {# will be replaced by page content #}
    {% endblock %}
    </main>

    {% include "partials/footer.html" %}
    
  </body>
  
</html>
```

The ```include``` directive lets this template reference other template fragments, as shown for the content of ```<head>``` as well as the page header and footer.  Variables can be inserted into the template as shown for ```{{ bodyClass }}```.  This value will be obtained from the environment when the template is rendered.  The ```{% block body %}``` is a placeholder that will be replaced with content from a child template that extends this one.

A child template could then be defined as:

__File: simple.layout__

```html
{% extends "layout.html" %}

{% block body %}
  <div class="container">
    {{ contents | safe }}
  </div>
{% endblock %}
```

This indicates that it extends ```layout.html```.  We now define the ```{% block body %}``` content that will be rendered in the placeholder of the parent template.  (We can also define multiple named blocks if the parent template has placeholders for those.)

The ```simple.layout``` template only renders a ```<div>``` with a single variable referencing the ```contents``` of the page.  The ```| safe``` filter is used to indicate that this content is HTML and can be rendered safely without having to escape all the HTML tags.

If we wanted to manually render this template, we could do that with code such as:

```python
from jinja2 import Environment, FileSystemLoader

jinja_env = Environment(
    loader=FileSystemLoader("layouts"),
    autoescape=True
)

template = jinja_env.get_template("simple.html")
html = template.render(contents=..., bodyClass=...)
```

Of course, Metalsmythe will do this for you automatically, preparing all the variables to pass to ```template.render()``` so that they include:

1. Global ```metadata``` dict defined on the ```Builder``` object
2. Any frontmatter from the page being rendered (loaded into a dict)
3. The page "contents" and "path"

These are all stored as dicts internally, but when we pass them to the template we convert them to ```DotMap``` objects so you can access their properties with dict notation or dot notation (i.e. ```site.title``` or ```site["title"]```).  The DotMap objects are setup so that if a property is accessed that doesn't exist, it returns an empty DotMap object without causing an error.

An example of a Markdown file that can be converted to HTML with this approach is shown below:

__File: other-page.md__

```
---
layout: simple.html
bodyClass: "other-page"

seo:
  title: Metalsmith Bare-bones Starter
  description: "This starter should get you up and running with your new favorite static site genrator Metalsmith"
  socialImage: "/assets/images/metalsmith-starter-social.png"
  canonicalOverwrite: ""
---
# Just another page

Nothing here... fill in the blanks
```

This page uses YAML frontmatter to define some variables that we can access from our Jinja templates.  This provides access to variables such as ```layout``` and ```seo.title```.  When we call ```builder.apply_layouts()```, Metalsmythe will examine the ```layout``` property to see what template should be applied.  A default template can also be indicated when this function is called.  The page content will at first be loaded as plain text into the ```contents``` variable of the file dict.  When we call ```builder.markdown_to_html()``` it will be converted to HTML and the file's path will be changed from ```other-page.md``` to ```other-page.html```.  This content is then ready to be rendered using Jinja.

## Local Test Server

Once you build your site, you can run a local test server with:

```bash
python serve.py [port]
```

By default this will run the server on port 8000.

The script runs a modified version of Python's built-in 'http.server' with the same syntax as running ```python -m http.server```.  The only modification is to default the directory for the server to 'build' and to look for files with '.html' and '.htm' extensions when given an extension-less URL.  The [Python documentation](https://docs.python.org/3/library/http.server.html) emphasizes that this server is only to be used for testing and not for any kind of production work, so please don't use it for that purpose.

## Vivian Smith-Smythe-Smith

Lastly, if you're wondering how to pronounce "Metalsmythe", it's "smythe" with a long "I" sound, as in:

> Vivian Smith-Smythe-Smith, [Upper Class Twit of the Year](https://en.wikipedia.org/wiki/Upper_Class_Twit_of_the_Year) (second place)
> - Has an O-level in chemo-hygiene
> - Can count up to 4
> - Is in the Grenadier Guards 

This was the best Monty Python reference I could find at the time.
