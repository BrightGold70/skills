"""
FileManager Component
Drag-and-drop file upload for reference PDFs and PPTs.
"""

import streamlit as st
from pathlib import Path
from typing import List, Optional
import shutil


class FileManager:
    """Manages file upload and reference library organization."""

    ALLOWED_TYPES = ["pdf", "ppt", "pptx", "doc", "docx", "txt"]
    MAX_FILE_SIZE_MB = 50

    def __init__(self, upload_dir: Optional[str] = None):
        """Initialize file manager."""
        self.upload_dir = (
            Path(upload_dir) if upload_dir else Path.home() / ".hpw_uploads"
        )
        self.upload_dir.mkdir(exist_ok=True)

    def render(self):
        """Render file manager UI."""
        # Drag and drop file uploader
        uploaded_files = st.file_uploader(
            "Drop reference files here",
            type=self.ALLOWED_TYPES,
            accept_multiple_files=True,
            help="Upload PDF, PPT, or Word documents containing references",
        )

        if uploaded_files:
            self._process_uploads(uploaded_files)

        # Show uploaded files
        self._render_file_list()

        # Quick actions
        st.markdown("---")
        col1, col2 = st.columns(2)

        with col1:
            if st.button("📂 Add from LaCie", use_container_width=True):
                self._add_from_lacie()

        with col2:
            if st.button("🗑️ Clear All", use_container_width=True):
                self._clear_uploads()
                st.rerun()

    def _process_uploads(self, uploaded_files):
        """Process uploaded files."""
        for file in uploaded_files:
            # Check file size
            file_size_mb = len(file.getvalue()) / (1024 * 1024)
            if file_size_mb > self.MAX_FILE_SIZE_MB:
                st.warning(
                    f"⚠️ {file.name} is too large ({file_size_mb:.1f}MB). Max: {self.MAX_FILE_SIZE_MB}MB"
                )
                continue

            # Save file
            file_path = self.upload_dir / file.name
            with open(file_path, "wb") as f:
                f.write(file.getvalue())

            # Add to session state
            if file.name not in [f["name"] for f in st.session_state.uploaded_files]:
                st.session_state.uploaded_files.append(
                    {
                        "name": file.name,
                        "path": str(file_path),
                        "size": f"{file_size_mb:.1f}MB",
                        "type": file.type,
                    }
                )

        st.success(f"✅ Uploaded {len(uploaded_files)} file(s)")

    def _render_file_list(self):
        """Render list of uploaded files."""
        if not st.session_state.uploaded_files:
            st.info("📎 No files uploaded yet")
            return

        st.markdown(f"**{len(st.session_state.uploaded_files)} file(s) uploaded:**")

        for i, file_info in enumerate(st.session_state.uploaded_files):
            col1, col2, col3 = st.columns([3, 1, 1])

            with col1:
                icon = self._get_file_icon(file_info["type"])
                st.markdown(f"{icon} {file_info['name']}")

            with col2:
                st.caption(file_info["size"])

            with col3:
                if st.button("🗑️", key=f"delete_{i}"):
                    self._remove_file(i)
                    st.rerun()

    def _get_file_icon(self, file_type: str) -> str:
        """Get icon for file type."""
        icons = {
            "application/pdf": "📄",
            "application/vnd.openxmlformats-officedocument.presentationml.presentation": "📊",
            "application/vnd.ms-powerpoint": "📊",
            "application/msword": "📝",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "📝",
            "text/plain": "📃",
        }
        return icons.get(file_type, "📎")

    def _add_from_lacie(self):
        """Add files from LaCie reference library."""
        ref_path = Path(
            "/Users/kimhawk/Library/CloudStorage/Dropbox/Paper/Hematology_paper_writer/References"
        )

        if not ref_path.exists():
            st.error("❌ LaCie drive not mounted")
            return

        # List available reference files
        st.markdown("### Available Reference Files")

        ref_files = {
            "Classification": ["WHO_2022.pdf", "ICC_2022.pdf"],
            "Therapeutic": ["ELN_AML_2022.pdf", "ELN_CML_2025.pdf"],
            "GVHD": ["NIH_cGVHD_I.pdf", "NIH_cGVHD_II.pdf", "NIH_cGVHD_III.pdf"],
            "Nomenclature": ["ISCN 2024.pdf", "HGVS Nomenclature 2024.pdf"],
        }

        for category, files in ref_files.items():
            with st.expander(f"📚 {category}"):
                for file in files:
                    file_path = lacie_path / file
                    if file_path.exists():
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.markdown(f"📄 {file}")
                        with col2:
                            if st.button("➕ Add", key=f"add_{file}"):
                                self._copy_from_lacie(file_path)
                                st.rerun()
                    else:
                        st.markdown(f"❌ {file} (not found)")

    def _copy_from_lacie(self, source_path: Path):
        """Copy file from LaCie to upload directory."""
        dest_path = self.upload_dir / source_path.name
        shutil.copy2(source_path, dest_path)

        file_size_mb = dest_path.stat().st_size / (1024 * 1024)

        st.session_state.uploaded_files.append(
            {
                "name": source_path.name,
                "path": str(dest_path),
                "size": f"{file_size_mb:.1f}MB",
                "type": "application/pdf",
            }
        )

        st.success(f"✅ Added {source_path.name}")

    def _remove_file(self, index: int):
        """Remove file from list and disk."""
        file_info = st.session_state.uploaded_files[index]
        file_path = Path(file_info["path"])

        if file_path.exists():
            file_path.unlink()

        st.session_state.uploaded_files.pop(index)

    def _clear_uploads(self):
        """Clear all uploaded files."""
        for file_info in st.session_state.uploaded_files:
            file_path = Path(file_info["path"])
            if file_path.exists():
                file_path.unlink()

        st.session_state.uploaded_files = []

    def get_uploaded_files(self) -> List[dict]:
        """Get list of uploaded files."""
        return st.session_state.uploaded_files
