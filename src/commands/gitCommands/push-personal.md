---
allowed-tools: Bash(git:*), Read, Edit
description: stage, commit, and finally push the current branch to the relative remote one
---

# Git stage and commit for final push

Complete the staging and commit and finally push of the current branch

## Task

Use the credentials below to simply stage all the edited/added/deleted files. Commit using the rules below and then push to remote branch.

### 1. Stage files
Stage all files which have been edited, added or deleted. Even large files.

### 2. Commit changes
Commit all changes adding a message to the commit like:
`bash
git commit -m "YYYYMMDD_backup#"

The format for the commit messgae should be based on date:
YYYYMMDD_backupNumber
The date pull it from the system dattime. Add an underscore "_" and the a string stating backup+seq commit number for the day.
If the repo does not have any commits for the current day, the seq number qould be: 1.
After that, add a sequential number like: backup2, backup3 etc.
Below some examples:

20260103_backup1
20260103_backup2
20260103_backup3

### 3. Push to remote
Push the commit to remote repo using the ssh "C:\Users\DAVI\.ssh\personalAccount"
It will require a pwd.
`bash
git push origin main

use the pwd in the .md file in the same repo: git_agent.md
The variable is called: SSH_KEYVALUE

### 4. Provide a brief summary of the successfull (or not) commands. The list of the files pushed to the remote and the commit message.
