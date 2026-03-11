---
description: Run the YOLO FULL autonomous workflow (Antigravity Ops Version)
---

# YOLO FULL Workflow

> [!CAUTION]
> **YOLO MODE ENABLED**: This workflow grants the agent autonomous write access and shell execution. Ensure you have committed your current work before proceeding.

This workflow enables full autonomy for the agent by allowing it to execute commands without user confirmation. It integrates environment validation, project path display, and project startup context.

// turbo-all
1.  **Validate Environment**: Run the health check and validation script.
    `bash ~/Agents/antigravity-ops/scripts/run-workflow.sh validate-autonomous-mode --json`

2.  **Display Project Paths**: show the current project development and resources folder mappings.
    `bash ~/Agents/antigravity-ops/scripts/run-workflow.sh display-project-paths`

3.  **Show Project Startup**: Display the `AGENT-STARTUP.md` file if it exists in the resources folder.
    `bash ~/Agents/antigravity-ops/scripts/run-workflow.sh show-project-startup`

4.  **Launch start-project**: The macOS folder picker will appear to confirm/designate project paths.
    `bash ~/Agents/antigravity-ops/scripts/run-workflow.sh start-project`

5.  **Refresh Setup**: Display the project startup context again after paths are updated.
    `bash ~/Agents/antigravity-ops/scripts/run-workflow.sh show-project-startup`

**Note**: This workflow uses the `// turbo-all` annotation to bypass command confirmations. It is the primary entry point for deep autonomous work in the Antigravity IDE.
