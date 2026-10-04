"""Throwaway renderer corpus: each scanner rule against markdown-it-py (CommonMark preset)."""
import markdown_it
md = markdown_it.MarkdownIt("commonmark")
cases = [
 ("opener at 3 spaces IS a fence",            "   ```bash\nX\n```\n",                      "code",   "<code"),
 ("opener at 4 spaces is NOT a fence",        "    ```bash\nX\n",                          "indented-code", "<pre><code>```bash"),
 ("closer shorter than opener does not close","````\nX\n```\nY\n````\n",                   "one-block-with-``` inside", "```\nY"),
 ("closer with trailing text does not close", "```\nX\n``` trailing\nY\n```\n",            "one-block", "``` trailing"),
 ("closer at 4 spaces does not close",        "```\nX\n    ```\nY\n```\n",                 "one-block", "    ```"),
 ("tilde does not close a backtick fence",    "```\nX\n~~~\nY\n```\n",                     "one-block", "~~~\nY"),
 ("body de-indented by opener indent (2)",    "  ```\n  a\n b\n   c\n  ```\n",             "code-body", "a\nb\n c"),
 ("#hashtag is not a heading",                "#hashtag\n",                                "para",   "<p>#hashtag"),
 ("seven hashes is not a heading",            "####### x\n",                               "para",   "<p>####### x"),
 ("4-space-indented ## is not a heading",     "    ## x\n",                                "indented-code", "<pre><code>## x"),
 ("3-space-indented ## IS a heading",         "   ## x\n",                                 "h2",     "<h2>x</h2>"),
 ("closing hashes are stripped",              "## x ##\n",                                 "h2",     "<h2>x</h2>"),
 ("tab after hashes IS a heading",            "##\tx\n",                                   "h2",     "<h2>x</h2>"),
 ("heading inside a fence is not a heading",  "```\n## x\n```\n",                          "code",   "<code>## x"),
]
for name, src, expect_kind, needle in cases:
    html = md.render(src)
    print(f"{'OK ' if needle in html else 'NO '} {name:44s} | {html.strip()[:70]!r}")
