<objective>
Using the specification from prompt 001-codebase-cartographer-skill.md, generate the actual Claude skill file that can be placed in `.claude/skills/codebase-cartographer/SKILL.md` or `src/skills/codebase-cartographer/SKILL.md`.

The skill file must be a complete, executable skill definition following the established pattern in this repository.

**CRITICAL**: The skill MUST include full CDC (Change Data Capture) functionality:
- Snapshot versioning and storage
- Differential analysis between snapshots
- Change categorization and impact scoring
- History management with retention policies
</objective>

<context>
This prompt generates the SKILL.md file that Claude Code will read when the skill is triggered.

Reference existing skills in the repository for patterns:
- `src/skills/repository-analyzer/SKILL.md`
- `src/skills/sdd/skill.md`
- `src/skills/exec-briefing/SKILL.md`

The skill should be immediately usable after creation.

**Two commands will be registered:**
1. `/cartograph` - Full repository index with snapshot creation
2. `/cartograph-diff` - Differential analysis between snapshots
</context>

<requirements>
## Skill File Structure

Create a SKILL.md file with these sections:

### 1. YAML Frontmatter
```yaml
---
name: codebase-cartographer
description: [Full description with CDC mention]
version: 1.0.0
priority: HIGH
triggers:
  # Full index triggers
  - index repository
  - map codebase
  - cartograph
  - /cartograph
  # CDC/Differential triggers
  - what changed
  - codebase diff
  - /cartograph-diff
use_when: [...]
avoid_when: [...]
conflicts_with: []
---
```

### 2. Purpose Section
- Clear explanation of what the skill does
- Target audience and use cases
- **CDC capabilities and benefits**
- Differentiation from similar skills (e.g., repository-analyzer)

### 3. Activation Triggers
- List of phrases for FULL INDEX
- List of phrases for DIFFERENTIAL ANALYSIS
- Example user requests

### 4. CDC System Documentation
- Snapshot storage structure
- Manifest file format
- Change categories tracked
- Retention policy

### 5. Core Workflow (/cartograph)
- Step-by-step execution process
- File scanning strategy
- Snapshot creation
- Output generation logic

### 6. Differential Workflow (/cartograph-diff)
- Trigger detection
- Snapshot comparison logic
- Change categorization
- Report generation

### 7. Output Templates
- Complete CODEBASE_INDEX.md template
- Complete CODEBASE_INDEX.json schema
- Complete CODEBASE_CHANGELOG.md template
- Complete CODEBASE_CHANGELOG.json schema

### 8. Quality Checklist
- Verification steps before delivery
- Success criteria
- CDC-specific checks

### 9. Output Delivery
- Where files are saved
- Snapshot archival location
- User notification format (for both full index and diff)

### 10. Integration Notes
- How it works with other skills
- Companion tools and agents
</requirements>

<output>
Generate the complete SKILL.md file content.

Save to: `./src/skills/codebase-cartographer/SKILL.md`

Also create a minimal `.skilz-manifest.yaml`:
Save to: `./src/skills/codebase-cartographer/.skilz-manifest.yaml`

```yaml
name: codebase-cartographer
version: 1.0.0
description: Repository indexer with CDC (Change Data Capture) for tracking codebase evolution
author: [Your organization]
license: MIT
commands:
  - name: cartograph
    description: Generate full codebase index with snapshot
    triggers:
      - /cartograph
      - index repository
      - map codebase
  - name: cartograph-diff
    description: Show changes since last index
    triggers:
      - /cartograph-diff
      - what changed
      - codebase diff
outputs:
  - CODEBASE_INDEX.md
  - CODEBASE_INDEX.json
  - CODEBASE_CHANGELOG.md
  - CODEBASE_CHANGELOG.json
storage:
  history: .claude/codebase-cartography/history/
  current: .claude/codebase-cartography/current/
  diffs: .claude/codebase-cartography/diffs/
  manifest: .claude/codebase-cartography/manifest.json
```
</output>

<verification>
After generating:
1. Verify YAML frontmatter is valid
2. Confirm all sections are complete
3. Check that bash commands are cross-platform compatible
4. Ensure output templates match the specification
5. Verify CDC system is fully documented
6. Confirm both /cartograph and /cartograph-diff are defined
</verification>

<key_cdc_features_to_include>
## Must Document These CDC Features

### Snapshot System
- Unique snapshot IDs: `{ISO-timestamp}_{short-git-hash}`
- Storage in `.claude/codebase-cartography/history/{snapshot-id}/`
- snapshot.json and meta.json per snapshot
- manifest.json for index of all snapshots

### Change Categories
1. **File Changes**: ADDED, DELETED, MODIFIED, RENAMED
2. **Dependency Changes**: DEP_ADDED, DEP_REMOVED, DEP_UPGRADED, DEP_MAJOR_BUMP
3. **Architecture Changes**: DIR_ADDED, DIR_REMOVED, PATTERN_SHIFT, ENTRY_POINT_ADDED
4. **Code Quality Changes**: DEBT_ADDED, DEBT_RESOLVED, LARGE_FILE_ADDED, COMPLEXITY_INCREASED
5. **API Changes**: ENDPOINT_ADDED, ENDPOINT_REMOVED, ENDPOINT_MODIFIED

### Impact Scoring
- CRITICAL: Breaking changes, security fixes, major refactors
- HIGH: New features, API changes, dependency major bumps
- MEDIUM: Bug fixes, minor features, dependency minor bumps
- LOW: Documentation, config, minor tweaks

### Differential Commands
- `/cartograph-diff` - Compare to last snapshot
- `/cartograph-diff <id1> <id2>` - Compare specific snapshots
- `/cartograph-diff --since=7d` - Compare to snapshot from 7 days ago

### Retention Policy
- maxSnapshots: 30 (default)
- maxAgeDays: 90 (default)
- minSnapshots: 5 (always keep at least 5)
</key_cdc_features_to_include>
