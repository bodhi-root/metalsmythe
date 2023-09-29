import os
import shutil
import frontmatter as _frontmatter
import markdown
import glob
import json
from dotmap import DotMap
from .utils import GlobPattern


def load_file(path, base_dir=None, frontmatter=True):
    """Loads a single file from the given 'path'.  The path will be evaluated relative
    to base_dir.  A dict will be returned containing 'path' and 'contents'.  It will
    also contain properties for the front-matter if frontmatter is True.
    """
    path = path.replace('\\', '/')

    full_path = path
    if base_dir is not None:
        full_path = os.path.join(base_dir, path)

    file = {}
    if frontmatter:
        with open(full_path) as fp:
            post = _frontmatter.load(fp)
            file.update({key: post[key] for key in post.keys()})
            file["contents"] = post.content
    else:
        with open(full_path) as fp:
            file["contents"] = fp.read()

    file["path"] = path
    return file


def remove_directory(directory):
    """Deletes the given directory (so we can cleanly create a new one with
    the same name)"""
    if os.path.exists(directory):
        shutil.rmtree(directory)


def copy_directory(src_dir, dst_dir):
    """Copies the directory and all of its children to the destination.  This is
    useful for doing a simple copy of asset files (images, style sheets, etc.)"""
    shutil.copytree(src_dir, dst_dir, dirs_exist_ok=True)


def load_json(path):
    """Loads JSON data from a file."""
    with open(path) as fp:
        return json.load(fp)


def prep_template_params(file: dict, metadata :dict, dotmap=True):
    """Prepares a parameter dict for calling render(**params) on a Jinja template.
    This will begin with any global metadata (supplied as a dict) and add the keys
    from the frontmatter.Post object as well.  Another value named "contents" is
    added for the contents of the Post.  By default, we convert any dicts we
    encounter to DotMap objects so that we can access their members with "value.member"
    instead of "value['member']".  This can be disabled, if desired.
    """
    params = dict(metadata)
    params.update(file)

    if dotmap:
        def convert(x):
            if isinstance(x, dict):
                return DotMap(x)
            elif isinstance(x, list):
                return [convert(x) for x in x]
            return x
        params = {key: convert(item) for key, item in params.items()}

    return params


class Builder(object):
    """Object that can read input files, apply common transformations, and write the
    results to a directory.  All files are loaded into memory and can then be manipulated
    either by methods of this class or by custom, external logic.
    """

    def __init__(self, metadata={}):
        self.metadata = dict(metadata)
        self.files = []

    def load_file(self, path, base_dir=None, frontmatter=True):
        """Loads a single file from the given 'path'.  The path will be evaluated relative
        to self.directory.  The 'path' will also be used as the file key."""
        file = load_file(path, base_dir, frontmatter)
        self.files.append(file)

    def load_files(self, pattern="**/*.md", base_dir=None, recursive=True, frontmatter=True):
        """Loads all files that match the given glob pattern.  This essentially runs
        glob.glob(pattern, recursive=recursive) from either the working directory or
        the directory specified by 'base_path'.  All matching files will be loaded using
        their paths as keys.  Paths are standardized so that forward slashes are used
        instead of backslashes.
        """
        # NOTE: glob.glob(..., root_dir=) is only available in Python 3.10.  We hack
        #       around this by joining the glob_pattern to the base_path and then stripping
        #       the base_path off of the results.
        glob_pattern = pattern
        if base_dir is not None:
            glob_pattern = os.path.join(base_dir, glob_pattern)

        paths = glob.glob(glob_pattern, recursive=recursive)
        for path in paths:
            rel_path = path
            if base_dir is not None:
                rel_path = path[len(base_dir):]
                rel_path = rel_path.replace('\\', '/')
                if rel_path[0] == '/':
                    rel_path = rel_path[1:]

            self.load_file(rel_path, base_dir, frontmatter=frontmatter)

    #TODO: metalsmith-type loader (load everything but allow an ignore list)
    #def load_directory(self, directory, ignore=[]):

    def remove(self, path):
        """Removes the file with the given path (if it exists)"""
        self.files = [file for file in self.files if file["path"] != path]

    def write(self, output_dir, clean=False):
        """Writes all files to the specified directory.  The current set of keys will be
        used as the file names.  Each item's 'content' value will be used as the content
        of the file."""
        if clean:
            remove_directory(output_dir)

        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        for file in self.files:
            path = file["path"]
            rel_dir, file_name = os.path.split(path)
            full_dir = os.path.join(output_dir, rel_dir)
            if not os.path.exists(full_dir):
                os.makedirs(full_dir)

            full_path = os.path.join(full_dir, file_name)
            with open(full_path, "w") as fp:
                fp.write(file["contents"])

    def remove_spaces(self, replace_with='-'):
        """Removes all spaces from path names, replacing them with the specified character"""
        for file in self.files:
            file["path"] = file["path"].replace(' ', replace_with)

    def markdown_to_html(self, file_extensions=[".md", ".markdown"], markdown_extensions=["extra"]):
        """Converts markdown content to HTML.  This will apply to any file keys ending with the
        given extensions (default=".md" and ".markdown").  The file extension will be replaced
        with ".html".  We call markdown.markdown(content, extensions=markdown_extensions) to perform
        the conversion.  The list of extensions lets us extend the capabilities of the markdown
        process as specified here: https://python-markdown.github.io/extensions/.
        """

        for file in self.files:
            path = file["path"]
            for file_ext in file_extensions:
                if path.endswith(file_ext):
                    end_index = len(path) - len(file_ext)
                    file["path"] = path[0:end_index] + ".html"
                    file["contents"] = markdown.markdown(file["contents"], extensions=markdown_extensions)
                    break

    def apply_layouts(self, jinja_env, default_layout=None, dotmap=True):
        """Applies Jinja2 templates to our content.  A Jinja2.Environment provides the
        context for loading templates by name.  Each file object specifies the template
        it wants to use via the 'layout' property.  A default_layout can be specified
        for when this is missing.  Without a default, the file will be left alone.  The
        template is loaded, and then we call render().  The variables passed to render()
        include the current metadata, properties defined in the post's front-matter, as
        well as the special properties:

          contents - The file contents
          path - The path (key) associated with this file
        """

        for file in self.files:
            template_name = file.get("layout", default_layout)
            if template_name is None:
                continue

            template = jinja_env.get_template(template_name)
            params = prep_template_params(file, self.metadata, dotmap=dotmap)
            file["contents"] = template.render(**params)

    def get_files(self, pattern):
        """Returns a list of files whose 'path' matches the given glob pattern.  Example:

           get_files("blog/*.md")

        """
        glob_pattern = GlobPattern(pattern)
        return [file for file in self.files if glob_pattern.is_match(file["path"])]

    def create_collection(self, name, pattern, sort_key=None, reverse=False, limit=0, refer=True):
        """Creates a collection of file objects in a manner similar to Metalsmith's 'collection'
        plugin.  (see: https://github.com/metalsmith/collections).  Example:

           create_collection("blog", "blog/*.md",
                             sort_key=lamdba file: file["date"], reverse=True, limit=10)

        The code above will create a collection named "blog" including files that match the pattern
        "blog/*.md".  The files will be sorted in reverse order based on their 'date' property.  No more
        than 10 files will be included.  The collection will be created as a list of file objects and stored
        in self.metadata.collections["blog"].  Since 'refer' is True by default, they will have links to
        othe files in the collection via properties named 'previous' and 'next'.  The files are stored in
        the collection by reference so that changes to the file object in one place (either their main entry
        or the collection reference) will be visible in all places.

        @param name The name of the collection (will be used as a key in self.metadata.collections[name])
        @param pattern Glob pattern for files to include in this collection (example: blogs/*.md)
        @param sort_key Function to return a value used in sorting the files
        @param reverse True if you want to sort in reverse order
        @param limit The maximum number of files to put into the collection (applied after sorting)
        @param refer If true, add 'previous' and 'next' elements to the files in the collection
        """
        files = self.get_files(pattern)

        if sort_key is not None:
            files.sort(key=sort_key, reverse=reverse)

        if limit > 0:
            files = files[0:limit]

        if refer:
            for i in range(1, len(files)):
                files[i]["previous"] = files[i - 1]
                files[i - 1]["next"] = files[i]

        if "collections" not in self.metadata:
            self.metadata["collections"] = {}

        self.metadata["collections"][name] = files
