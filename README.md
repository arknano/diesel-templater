# Diesel Templater

![License](https://img.shields.io/github/license/arknano/diesel-templater)
![Python](https://img.shields.io/badge/python-3.9%2B-blue)

Diesel-kun is a helpful html website templater for creating simple static sites.

Using a configurable template marker like `%template_name%`, you can easily insert reused html elements like navbars and footers without relying on any complex templating tools. It also has Markdown support i guess!

## Quick Start

Build the included example:

```bash
python diesel.py --config example/diesel.config
```

The default output folder is `export/` next to `diesel.py`.
The export folder is deleted and rebuilt on every run.

## Arguments
- `--config`: Specify the config file. If not provided, uses `diesel.config` in the current directory.
- `--export_dir`: Specify the export directory. If not provided, exports to `export/` in the current directory.
- `--md`: Enable Markdown parsing.
  

## Configuration

Config files are JSON. Relative paths are resolved from the config file's directory.

```json
{
  "template_dir": "site/templates",
  "source_dir": "site",
  "template_pattern": "%(\\w+)%",
  "markdown_template": "site/templates/markdown.html",
  "markdown_content_marker": "{{markdown}}",
  "exclude_dirs": ["templates"],
  "exclude_files": []
}
```

Options:

- `template_dir`: folder containing template snippets.
- `source_dir`: folder containing the site files to copy and process.
- `template_pattern`: regex used to find template markers. The first capture group is used as the template name.
- `markdown_template`: optional HTML page template used when converting Markdown with `--md`.
- `markdown_content_marker`: marker in `markdown_template` that receives the rendered Markdown HTML. Defaults to `{{markdown}}`.
- `exclude_dirs`: directory names to skip while copying.
- `exclude_files`: filenames, source-relative paths, or glob patterns to skip, such as `README.md`, `pages/draft.html`, or `*.tmp`.

## Templates

Any HTML file copied to the export folder can include template markers:

```html
<body>
  %header%
  <main>Hello</main>
</body>
```

Diesel-kun looks for a matching file in `template_dir`:

```html
<!-- site/templates/header.html -->
<header>My Site</header>
```

After building, the exported page contains the expanded template content.

## Markdown Pages

When building with `--md`, Markdown files are rendered to HTML. If `markdown_template` is configured, Diesel-kun inserts the rendered Markdown into that template before the normal template pass runs:

```html
<!DOCTYPE html>
<html>
<head>
  %style%
  %github_markdown%
  <title>Markdown Page</title>
</head>
<body>
  %header%
  <main class="markdown-body">
    {{markdown}}
  </main>
</body>
</html>
```

The `{{markdown}}` marker is replaced with the rendered Markdown content. Other template markers, such as `%style%` and `%header%`, are then expanded from `template_dir` like any other HTML page.

Exported HTML pages are located in the same relative location as the original Markdown file. When linking to these files, just pretend it's already a html file :) (link to `page.html` instead of `page.md`)

## Nested Pages

Template links are adjusted for nested output pages. If `site/templates/header.html` contains:

```html
<a href="index.html">Home</a>
```

then `site/pages/nested.html` receives:

```html
<a href="../index.html">Home</a>
```

Absolute URLs, root-relative paths, anchors, `mailto:`, and paths that already start with `../` are left unchanged.

## Credits

The example GitHub Markdown stylesheet is based on [`sindresorhus/github-markdown-css`](https://github.com/sindresorhus/github-markdown-css), an MIT-licensed stylesheet that replicates GitHub's Markdown style.
