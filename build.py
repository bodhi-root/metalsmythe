import datetime as dt
from jinja2 import Environment, FileSystemLoader
import re
from metalsmythe.builder import Builder, load_json, copy_directory
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


builder = Builder(metadata)
builder.load_files("**/*.md", base_dir="src/content")
builder.create_collection("blog", "blog/*.md", limit=10, sort_key=lambda x: x["date"], reverse=True)
#builder.remove("blog.md")
#print([file["path"] for file in builder.files])
#builder.remove_spaces()
builder.markdown_to_html()
builder.apply_layouts(jinja_env, default_layout="simple.html")

builder.write("build", clean=True)
copy_directory("src/assets", "build/assets")
