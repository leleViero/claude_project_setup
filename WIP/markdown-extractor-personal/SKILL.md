---
name: markdown-extractor-personal
description: Converts a URL or local file into a self-contained, offline-capable markdown note using the markitdown MCP server. Downloads all images locally, rewrites links, and formats output using the personal note template.
triggers:
  - "extract markdown"
  - "convert to note"
  - "save page as note"
  - "markdown extractor"
---

# markdown-extractor-personal

You are executing the **markdown-extractor-personal** skill. Your job is to convert a URL or local file path into a fully self-contained markdown note, formatted with the personal knowledge base template, with all images saved locally.

## Input

The user provides either:
- A URL: `https://example.com/article`
- A local file path: `/path/to/file.pdf` or `C:\path\to\file.docx`

If no input was provided with the skill invocation, ask the user:
> "Please provide a URL or local file path to convert."

## Execution Steps

### Step 1 — Resolve the URI

- If the input starts with `http://` or `https://`, use it as-is.
- If the input is a local file path, convert it to a `file://` URI:
  - Unix: `/home/user/file.pdf` → `file:///home/user/file.pdf`
  - Windows: `C:\path\file.pdf` → `file:///C:/path/file.pdf` (replace backslashes with forward slashes)

### Step 2 — Convert to Markdown and Read Template (in parallel)

Run both of these simultaneously — they are independent:

**A) Call the MCP tool:**

The `markitdown` MCP server is registered as an SSE server at `http://172.21.0.105:3001/sse`. Use its tool via:
```
mcp__markitdown__convert_to_markdown(uri="<resolved URI>")
```

**B) Read the template file:**
Read `template/{{01 Knowledge base}}.md` located in the same directory as this skill file.

If the MCP tool returns an error or empty content, stop and report the error to the user. Do not proceed with empty content.

### Step 3 — Extract Metadata from Converted Markdown

From the raw converted markdown:

1. **Title**: Extract the first `# Heading` found. If none, derive from the URL path or filename (strip extension, replace hyphens/underscores with spaces, title-case).
2. **Description**: Extract the first non-heading paragraph (max 200 characters). This becomes `descriptionValue`.
3. **Source**: The original URL or file path provided by the user.
4. **Date**: Today's date in ISO format (`YYYY-MM-DD`).
5. **Content body**: Everything after the first `# Heading` (or all content if no heading found).
6. **Tags**: Scan the content for recurring domain keywords (tech stack names, proper nouns, topic words with 3+ occurrences). Propose up to 5 tags as a YAML list. Leave `clusterTags` as `[]`.

### Step 4 — Build the Output Slug and Folder

1. Slug = title → lowercase → replace spaces and special chars with `-` → truncate to 60 chars → strip leading/trailing `-`
2. Output folder: `./notes/<slug>/`
3. Output markdown file: `./notes/<slug>/<slug>.md`
4. Create the output folder (and `./notes/<slug>/_ref/`) before writing.

### Step 5 — Apply the Template

Take the template content and produce the final note by substituting the following:

| Template field | Value |
|---|---|
| `strategicValue: 0` | Keep as `0` (user fills later) |
| `innovationValue: 0` | Keep as `0` |
| `digitalTransformationValue: 0` | Keep as `0` |
| `leadershipValue: 0` | Keep as `0` |
| `technologyValue: 0` | Keep as `0` |
| `tags: []` | Replace with extracted tags list, e.g. `tags: [python, llm, api]` |
| `clusterTags: []` | Keep as `[]` |
| `descriptionValue: string` | Replace `string` with the extracted description |
| `[[]]` (Graph connections) | Keep as `[[]]` — user fills Obsidian links manually |
| `###### Links` section | Add a line below: `- [Source](<source URL or path>)` |
| `# Main description` | Replace with `# <extracted title>` |
| `Main content` | Replace with the full extracted content body |
| `## Header section` / `Content` blocks | Remove these placeholder blocks — the extracted content replaces them |
| `### Header section` / `Content` | Remove |
| `#### Checkbox if necessary` block | Remove |
| `###### File Attachments` block | Keep the section header, remove the placeholder line; images will be listed here after download |

Write the assembled note to `./notes/<slug>/<slug>.md`.

### Step 6 — Download Images

Determine the absolute path to this skill file's directory, then run:

```bash
python "<absolute-path-to-skill-dir>/scripts/image_downloader.py" "./notes/<slug>/<slug>.md"
```

The skill directory is `markdown-extractor-personal/` — resolve its absolute path at runtime using the project root or the path from which the skill was invoked.

Wait for the script to complete and capture its output summary (images found / downloaded / failed).

If the script is not yet available (file doesn't exist at `scripts/image_downloader.py`), skip this step and inform the user:
> "Image downloader script not found at scripts/image_downloader.py. Images remain as remote links."

### Step 7 — Report to User

Output a clean summary:

```
✓ Note created: ./notes/<slug>/<slug>.md
  Title    : <title>
  Source   : <original input>
  Images   : <N downloaded> / <M found> (saved to _ref/)
  Tags     : <extracted tags>

Open the file or copy to your knowledge base.
```

## Error Handling

| Situation | Action |
|---|---|
| MCP tool unavailable | Stop. Tell user: "The markitdown MCP server is not running. Start it and retry." |
| MCP returns empty markdown | Stop. Ask user to verify the URL/file is accessible. |
| Image download fails | Keep original URL, append `<!-- download-failed -->` inline. Continue with remaining images. |
| Template file missing | Create a minimal default template (see below) at the template path, then continue. |
| Output folder already exists | Proceed — overwrite the `.md` file but do not delete existing assets. |

**Minimal fallback template** (create at `template/{{01 Knowledge base}}.md` if missing):
```markdown
---
strategicValue: 0
innovationValue: 0
digitalTransformationValue: 0
leadershipValue: 0
technologyValue: 0
tags: []
clusterTags: []
descriptionValue: string
---
###### Graph connections
[[]]

###### Links

# Main description
Main content
```

## Notes

- Always resolve output paths relative to the current working directory (`./notes/`), not relative to the skill file location.
- The skill directory path (`scripts/image_downloader.py`) must be resolved to an absolute path before calling via Bash.
- The Python script handles all image downloading and in-place link rewriting. Do not attempt to download images yourself.
- Do not modify the template file itself — only use it as a read-only scaffold.
- The output note should be valid Obsidian-compatible markdown (frontmatter + wikilinks preserved).
