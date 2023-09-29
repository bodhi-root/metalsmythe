# File: jinja_test.py
# Helper script for testing your markdown pages and ensuring they
# transform correctly with jinja templates.

from jinja2 import Environment, FileSystemLoader
import frontmatter
import markdown
import datetime as dt
import re
from metalsmythe.builder import load_json, prep_template_params
from metalsmythe.utils import format_date


jinja_env = Environment(
    loader=FileSystemLoader("layouts"),
    autoescape=True
)


jinja_env.filters["format"] = format
jinja_env.filters["format_date"] = format_date
jinja_env.filters["spaceToDash"] = lambda x: re.sub("\\s+", "-", x)
jinja_env.filters["condenseTitle"] = lambda x: re.sub("\\s+", "", x.lower())
jinja_env.filters["trimSlashes"] = lambda x: x.strip("/")
jinja_env.filters["UTCDate"] = lambda x: format_date(x, "%b %d, %Y")   # date.toUTCString("M d, yyyy");
jinja_env.filters["blogDate"] = lambda x: format_date(x, "%B %d, %Y")  # new Date(string).toLocaleString("en-US", { year: "numeric", month: "long", day: "numeric" });
# NOTE: demo site shows UTCDate as: Fri, 02 Jun 2023 23:10:36 GMT


metadata = {
    "site": load_json("src/content/data/site.json"),
    "nav": load_json("src/content/data/navigation.json"),
    "stats": {
        "build_time": dt.datetime.now()
    }
}

file = "src/content/index.md"
#file = "src/content/code.md"
#file = "src/content/other-page.md"
#file = "src/content/blog.md"
#file = "src/content/blog/cras-mattis-consectetur-purus.md"

post = frontmatter.load(file)
template_name = post["layout"]
post.content = markdown.markdown(post.content, extensions=["extra"])
page_data = prep_template_params(post, metadata)

template = jinja_env.get_template(template_name)
result = template.render(**page_data)
print(result)
