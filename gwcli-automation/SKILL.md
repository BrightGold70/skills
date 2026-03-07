---
name: gwcli-automation
description: Automate Google Workspace tasks (Calendar, Drive, Docs, Sheets, Presentations, Gmail) natively via the gwcli command line tool using terminal commands. This skill is a lightweight alternative to the MCP server.
---

# gwcli-automation

This skill provides comprehensive instructions on how to use the `gwcli` system tool to interact with Google Workspace natively through the standard `run_command` tool.

`gwcli` (Google Workspace CLI) allows you to read/write emails, manage Calendar events, and interact with Google Drive without the heavy overhead of an MCP server.

## General Guidelines

- All commands must be run via the `run_command` tool.
- For most simple read/list commands, you can set `SafeToAutoRun: true`. 
- Be aware that `gwcli` handles Drive reading very well, but does not natively "write" or "edit" text inside Docs or Sheets. You can only upload local files.

## Command Reference

### Gmail
- **List emails:** `gwcli mail list --limit <N> [--label <LABEL>] [--unread]`
- **Search emails:** `gwcli mail search "<query>"` (Standard Gmail search queries apply, e.g., `from:someone@example.com is:unread`)
- **Read an email:** `gwcli mail read <message_id>`
- **Send an email:** `gwcli mail send --to <email> --subject "<subject>" --body "<body>"`

### Google Calendar
- **List events:** `gwcli calendar list --limit <N> [--time-min <ISO-8601>] [--time-max <ISO-8601>]`
- **Search events:** `gwcli calendar search "<query>"`
- **Create an event:** `gwcli calendar create --summary "<title>" --start "<ISO-8601>" --end "<ISO-8601>"`

### Google Drive
- **List files:** `gwcli drive list --limit <N>`
- **Search files:** `gwcli drive search "<query>"`
- **Upload file to Drive:** `gwcli drive upload <local_file_path> [--name <custom_name>]`
- **Download a standard file:** `gwcli drive download <file_id> --output <local_file_path>`
- **Export a Google Doc/Sheet/Presentation:**
  - Google Docs (to Markdown): `gwcli drive export <file_id> --mime-type text/plain > doc.md`
  - Google Sheets (to CSV): `gwcli drive export <file_id> --mime-type text/csv > sheet.csv`
  - Google Presentations (to Text): `gwcli drive export <file_id> --mime-type text/plain > deck.txt`
  - (Note: You can use `application/pdf` as a mime-type as well)

## Workflow Example: Reading a Doc
To read a file called "Project Plan":
1. `gwcli drive search "name contains 'Project Plan'"`
2. Identify the `<file_id>` of the document.
3. `gwcli drive export <file_id> --mime-type text/plain > /tmp/plan.md`
4. Use `view_file` tool to read the contents of `/tmp/plan.md`.
5. `rm /tmp/plan.md`

## Workflow Example: Creating a Document
To "create" a new document and write text to it:
1. Use `write_to_file` to create a markdown/text file (e.g., `/tmp/new_doc.txt`) with the desired contents.
2. Upload to Drive: `gwcli drive upload /tmp/new_doc.txt --name "New Google Doc"`

*(Note: Before uploading via gwcli on a new machine for the first time, you must authorize write permissions).*
