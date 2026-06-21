# Report History Center Documentation

The **Report History Center** manages compiled PDF executive digests and Excel spreadsheets.

## Architecture & Features

- **Storage Folder**: All compiled PDF reports are written to the `reports/` folder.
- **Spreadsheets**: Excel files are saved to `output/`.
- **User Interface Actions**:
  - *Download*: Serves files from disk.
  - *Regenerate*: Reruns PDF compile scripts on current active data.
  - *Delete*: Safely deletes logs from disk.
