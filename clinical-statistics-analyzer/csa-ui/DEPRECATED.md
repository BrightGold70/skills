# DEPRECATED — csa-ui/

This directory has been retired as of 2026-03-06.

All CSA functionality is now integrated into the HPW unified app:

```
hematology-paper-writer/ui/components/csa/
  documents_tab.py    ← moved here
  pipeline_tab.py     ← moved here
  analysis_tab.py     ← moved here

hematology-paper-writer/ui/script_registry.json  ← moved here
```

**Launch (single command):**
```bash
streamlit run hematology-paper-writer/ui/app.py --server.port 8501
```

The "Statistical Analysis" tab contains all previous CSA App functionality.
Port 8502 is no longer used.
