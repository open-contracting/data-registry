from markdown_it import MarkdownIt


def markdownify(content):
    md = MarkdownIt("commonmark", {"typographer": True})
    md.enable(["smartquotes"])
    return md.render(content)
