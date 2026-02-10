---
description: Workflow for making changes using feature branches
---

1. Identify the specific, atomic change to be made.
2. Create a new branch with a descriptive name: `git checkout -b <branch-name>`
3. Implement the change.
4. Verify the change (build, lint, test).
5. Review all changes: `git diff` (review unstaged changes to write accurate commit messages)
6. Stage changes: `git add .`
7. Commit with an accurate message based on the diff: `git commit -m "<type>: <description>"`
   - For multiline messages, use multiple `-m` flags:
     `git commit -m "<type>: <summary>" -m "<detailed body>"`
8. Switch to main: `git checkout main`
9. Review what will be merged: `git diff main..<branch-name>`
10. Merge with an accurate message describing the changes: `git merge --no-ff <branch-name> -m "Merge branch '<branch-name>': <what-changed>"`
   - For multiline merge messages, chain `-m` flags: `-m "<summary>" -m "<details>"`
11. Delete the feature branch: `git branch -d <branch-name>`
12. Proceed to the next change.
