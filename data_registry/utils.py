from markdown_it import MarkdownIt


# https://markdown-it-py.readthedocs.io/en/latest/using.html#renderers
def render_blank_link(self, tokens, idx, options, env):
    tokens[idx].attrSet("target", "_blank")
    # pass token to default renderer.
    return self.renderToken(tokens, idx, options, env)


def markdownify(content):
    md = MarkdownIt("commonmark", {"typographer": True})
    md.enable(["smartquotes"])
    md.add_render_rule("link_open", render_blank_link)
    return md.render(content)
