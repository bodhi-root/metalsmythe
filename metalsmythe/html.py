from bs4 import BeautifulSoup


def prefix_links(html, prefix, selectors=["a", "link", "script", "img", "video", "audio", "source"]):
    """Rewrites links in the given HTML text, prefixing any link that begins with '/' with the given
    prefix.  This is intended to work similarly to the Metalsmith prefix plugin:

      https://github.com/rosszurowski/metalsmith-prefix

    """
    # ensure prefix starts with '/' but does not end with one:
    if not prefix.startswith('/'):
        prefix = '/' + prefix
    if prefix.endswith('/'):
        prefix = prefix[0:-1]

    def _prefix(url):
        return prefix + url if url.startswith('/') else url

    def _prefix_attrs(elem_name, attr_name):
        for elem in soup.findAll(elem_name):
            if elem.has_attr(attr_name):
                elem[attr_name] = _prefix(elem[attr_name])

    soup = BeautifulSoup(html, features="html.parser")

    if "a" in selectors:
        _prefix_attrs("a", "href")
    if "link" in selectors:
        _prefix_attrs("link", "href")
    if "script" in selectors:
        _prefix_attrs("script", "src")
    if "img" in selectors:
        _prefix_attrs("img", "src")
    if "video" in selectors:
        _prefix_attrs("video", "src")
    if "audio" in selectors:
        _prefix_attrs("audio", "")
    if "source" in selectors:
        _prefix_attrs("source", "")

    return str(soup)
