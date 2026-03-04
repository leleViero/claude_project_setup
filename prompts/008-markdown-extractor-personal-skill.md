<objective>
Create a Claude Code skill named "markdown-extractor-personal" that converts any URL or local file into a self-contained, offline-capable markdown note. The skill leverages the running MCP server "markitdown" for initial conversion, applies a personal note template, downloads all referenced images locally, and rewrites links to use local relative paths — producing a robust, portable entry for a personal knowledge dataset.
</objective>

<context>
This skill lives inside the Claude Code skills system. The user maintains a personal knowledge base and wants every captured note to be:
- Fully offline-capable (no broken images if source URL goes down)
- Consistently formatted via a personal template
- Self-contained in a single output folder (markdown + assets together)

MCP server available: `markitdown` — exposes the tool `mcp__markitdown__convert_to_markdown(uri)` which accepts `http:`, `https:`, `file:`, or `data:` URIs and returns markdown text.

Skill directory structure to create:
```
src/skills/markdown-extractor-personal/
├── markdown-extractor-personal.md   ← skill definition (the main skill file)
├── image_downloader.py              ← Python helper script
└── template/
    └── noteTemplate.md              ← placeholder template (user will populate)
```

The skill file itself is the Claude Code skill definition. It must be self-contained and usable via the Skill tool.
</context>

<requirements>
**Skill behavior (markdown-extractor-personal.md)**:
1. Accept a single input: a URL (`http://` / `https://`) or a local file path
2. Normalize local file paths to `file://` URI format before passing to the MCP tool
3. Call `mcp__markitdown__convert_to_markdown` with the URI to get raw markdown
4. Read `template/noteTemplate.md` (relative to the skill file) and use it as the structural scaffold for the output note — inject the converted content into the appropriate template section
5. Determine an output slug from the page title or filename (snake_case, max 60 chars)
6. Create an output folder: `./notes/<slug>/`
7. Write the initial markdown to `./notes/<slug>/<slug>.md`
8. Call the Python helper `image_downloader.py` passing the output markdown file path — this script handles image downloading and link rewriting in-place
9. Report the final output path and image count to the user

**Python helper script (image_downloader.py)**:
- Accepts one argument: path to the markdown file to process
- Parses all image references using regex: both `![alt](url)` and HTML `<img src="url">` patterns
- Skips images that are already local paths or `data:` URIs
- Creates `./notes/<slug>/assets/images/` directory alongside the markdown file
- Downloads each remote image using `urllib` (stdlib only — no pip installs required)
- Preserves original filename from URL; if collision, appends a counter suffix
- Rewrites the markdown file in-place: replaces remote URLs with relative paths like `assets/images/<filename>`
- Prints a summary: total images found, downloaded successfully, skipped, failed
- Handles errors gracefully: if an image download fails, logs the failure but keeps the original URL with a `<!-- download-failed -->` comment appended
- Must work on Python 3.8+

**Template application**:
- Read `template/noteTemplate.md`
- The template may contain placeholder tokens like `{{title}}`, `{{date}}`, `{{source}}`, `{{content}}`, `{{tags}}`
- Replace tokens with extracted metadata: title from converted markdown's first H1, date as today's ISO date, source as the original input URL/path, content as the converted markdown body (everything after the first H1), tags left empty for user to fill
- If the template file doesn't exist yet, create a sensible default template and save it before proceeding

**Default noteTemplate.md content** (create this if missing):
```markdown
---
title: {{title}}
date: {{date}}
source: {{source}}
tags: {{tags}}
---

# {{title}}

> Source: {{source}}

{{content}}
```
</requirements>

<implementation>
**Skill file structure** — the `.md` skill file must follow Claude Code skill conventions:
- Start with a YAML-style header block defining: name, description, trigger conditions
- Include clear step-by-step instructions Claude must follow when the skill is invoked
- Reference the Python script with an explicit `!python` bash call
- Include error handling guidance for each step

**Python script constraints**:
- Use only Python stdlib: `urllib.request`, `urllib.parse`, `os`, `re`, `sys`, `pathlib`, `datetime`, `hashlib` — no external dependencies, so it works in any environment without setup
- Keep under 200 lines; if logic grows, split into clearly named functions
- Use `pathlib.Path` throughout for cross-platform path handling
- Validate that the input markdown file exists before processing

**Claude behavior during skill execution**:
- For maximum efficiency, read the template file and call the MCP tool in parallel (both are independent operations)
- After receiving the MCP tool result, reflect on whether the content looks complete before proceeding
- If the MCP tool returns an error, surface a clear message to the user and stop — do not proceed with empty content
- When calling the Python script, use the Bash tool with the full absolute path to the output markdown file

**Avoid**:
- Do not use `requests`, `beautifulsoup4`, or any non-stdlib library in the Python script
- Do not create nested notes folders (output is always `./notes/<slug>/`)
- Do not alter the template file after initial creation
- Do not hard-code paths — always resolve relative to the current working directory at execution time
</implementation>

<output>
Create the following files with these exact relative paths:

1. `./src/skills/markdown-extractor-personal/markdown-extractor-personal.md`
   - The full Claude Code skill definition
   - Must be invokable via the Skill tool as "markdown-extractor-personal"

2. `./src/skills/markdown-extractor-personal/image_downloader.py`
   - The Python image downloading and link-rewriting script
   - Executable standalone: `python image_downloader.py <path-to-markdown-file>`

3. `./src/skills/markdown-extractor-personal/template/noteTemplate.md`
   - The default note template with all placeholder tokens
   - User will customize this file to their preference

After creating all files, display a summary tree of what was created and a usage example showing both URL and local file inputs.
</output>

<verification>
Before declaring complete, verify:
- [ ] The skill `.md` file references `mcp__markitdown__convert_to_markdown` correctly
- [ ] The Python script handles both `![alt](url)` and `<img src="url">` patterns
- [ ] Template token replacement covers: `{{title}}`, `{{date}}`, `{{source}}`, `{{content}}`, `{{tags}}`
- [ ] The Python script uses only stdlib imports (check every `import` statement)
- [ ] Output path resolves to `./notes/<slug>/<slug>.md` relative to CWD
- [ ] The skill instructs Claude to call MCP tool and read template in parallel
- [ ] Error handling is present for: MCP failure, image download failure, missing template, invalid input
- [ ] All three files exist at the specified paths
</verification>

<success_criteria>
- A user can invoke the skill with a URL like `https://example.com/article` and receive a complete `./notes/article_title/article_title.md` with all images saved to `./notes/article_title/assets/images/`
- The output markdown opens correctly offline with no broken image links
- The note follows the structure defined in `template/noteTemplate.md`
- The Python script runs without installing any packages
- The skill is discoverable and invocable via the Claude Code Skill tool as "markdown-extractor-personal"
</success_criteria>
