"""
SolidWorks Connection Management
Handles connection to SolidWorks application and template management
"""

import win32com.client
import pythoncom
import glob
import logging
import os
import time
from typing import Optional

logger = logging.getLogger(__name__)


class SolidWorksConnection:
    """Manages connection to SolidWorks application"""
    
    def __init__(self):
        self.app = None
        self.template_path = None
        self.assembly_template_path = None
        
    def connect(self) -> bool:
        """Connect to SolidWorks application"""
        try:
            # Try to connect to existing instance
            try:
                self.app = win32com.client.GetActiveObject("SldWorks.Application")
                logger.info("Connected to existing SolidWorks instance")
            except Exception:
                # Launch new instance and wait for it to be ready
                logger.info("SolidWorks not running, launching new instance...")
                self.app = win32com.client.Dispatch("SldWorks.Application")
                self.app.Visible = True
                for i in range(30):
                    try:
                        _ = self.app.RevisionNumber
                        logger.info("SolidWorks instance is ready")
                        break
                    except Exception:
                        logger.info(f"Waiting for SolidWorks to start ({i+1}/30)...")
                        time.sleep(1)
                else:
                    raise Exception("SolidWorks failed to start within 30 seconds")

            version = self.app.RevisionNumber
            logger.info(f"SolidWorks version: {version}")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to SolidWorks: {e}")
            self.app = None
            return False
    
    def _sw_year(self) -> Optional[int]:
        """Derive the SolidWorks release year from the COM revision number.
        Revision major 33 = SW2025 (year = 1992 + major)."""
        try:
            major = int(str(self.app.RevisionNumber).split(".")[0])
            return 1992 + major
        except Exception:
            return None

    def _pick_template(self, patterns) -> Optional[str]:
        """Glob for a template, preferring the one matching the running SW version.
        Machines with multiple SW versions installed have templates for each year."""
        hits = []
        for pattern in patterns:
            hits.extend(sorted(glob.glob(pattern), key=str.casefold))
        if not hits:
            return None
        year = self._sw_year()
        if year:
            for hit in hits:
                if str(year) in hit:
                    return hit
        return hits[0]

    @staticmethod
    def _is_template_file(path: Optional[str], extension: str) -> bool:
        """Return whether *path* is an existing template of the requested type."""
        return bool(
            path
            and os.path.isfile(path)
            and os.path.splitext(path)[1].lower() == extension.lower()
        )

    def _configured_template(self, preference: int, extension: str) -> Optional[str]:
        """Resolve a template from a SolidWorks Default Templates preference.

        SolidWorks normally stores a concrete template file here, but older or
        manually migrated installations can contain one or more directories.
        Supporting both forms also makes localized names such as
        ``gb_part.prtdot`` work without hard-coding a language.
        """
        try:
            configured = self.app.GetUserPreferenceStringValue(preference)
        except Exception as exc:
            logger.warning(
                "Could not read SolidWorks template preference %s: %s",
                preference,
                exc,
            )
            return None

        for raw_entry in str(configured or "").split(";"):
            cleaned = raw_entry.strip().strip('"')
            if not cleaned:
                continue
            entry = os.path.abspath(os.path.expandvars(os.path.expanduser(cleaned)))
            if self._is_template_file(entry, extension):
                return entry
            if os.path.isdir(entry):
                matches = sorted(
                    glob.glob(os.path.join(entry, f"*{extension}")),
                    key=str.casefold,
                )
                if matches:
                    return matches[0]
        return None

    def find_template(self) -> Optional[str]:
        """Find Part template automatically"""
        override = os.environ.get("SW_PART_TEMPLATE")
        if override:
            from pathlib import Path
            candidate = Path(os.path.expandvars(override)).expanduser()
            if not candidate.is_absolute():
                candidate = Path(__file__).resolve().parents[2] / candidate
            if not self._is_template_file(str(candidate), ".prtdot"):
                raise ValueError("SW_PART_TEMPLATE must point to an existing .prtdot template")
            self.template_path = str(candidate.resolve())
            return self.template_path
        if self._is_template_file(self.template_path, ".prtdot"):
            return self.template_path

        self.template_path = self._configured_template(24, ".prtdot")
        if not self.template_path:
            self.template_path = self._pick_template([
                os.path.join(os.environ.get("PROGRAMDATA", ""), "SOLIDWORKS", "SOLIDWORKS *", "templates", "*.prtdot"),
            ])
        if self.template_path:
            logger.info(f"Found template: {self.template_path}")
            return self.template_path

        logger.error("No Part template found")
        return None

    def find_assembly_template(self) -> Optional[str]:
        """Find Assembly template automatically"""
        override = os.environ.get("SW_ASSEMBLY_TEMPLATE")
        if override:
            from pathlib import Path
            candidate = Path(os.path.expandvars(override)).expanduser()
            if not candidate.is_absolute():
                candidate = Path(__file__).resolve().parents[2] / candidate
            if not self._is_template_file(str(candidate), ".asmdot"):
                raise ValueError("SW_ASSEMBLY_TEMPLATE must point to an existing .asmdot template")
            self.assembly_template_path = str(candidate.resolve())
            return self.assembly_template_path
        if self._is_template_file(self.assembly_template_path, ".asmdot"):
            return self.assembly_template_path

        self.assembly_template_path = self._configured_template(25, ".asmdot")
        if not self.assembly_template_path:
            self.assembly_template_path = self._pick_template([
                os.path.join(os.environ.get("PROGRAMDATA", ""), "SOLIDWORKS", "SOLIDWORKS *", "templates", "*.asmdot"),
            ])
        if self.assembly_template_path:
            logger.info(f"Found assembly template: {self.assembly_template_path}")
            return self.assembly_template_path

        logger.error("No Assembly template found")
        return None

    def create_new_assembly(self):
        """Create a brand new assembly document"""
        template = self.find_assembly_template()
        if not template:
            raise Exception("No Assembly template found")

        logger.info("Creating new assembly document")
        doc = self.app.NewDocument(template, 0, 0, 0)

        if not doc:
            raise Exception("Failed to create assembly document")

        logger.info("✓ New assembly document created")
        return doc

    def open_document(self, file_path: str, doc_type: int):
        """Silently open a document from disk. doc_type: 1=part, 2=assembly, 3=drawing.
        Note: OpenDoc6 activates the opened document."""
        errs = win32com.client.VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)
        warns = win32com.client.VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)
        doc = self.app.OpenDoc6(file_path, doc_type, 1, "", errs, warns)  # option 1 = silent
        if not doc:
            raise Exception(
                f"Failed to open document: {file_path} "
                f"(errors={errs.value}, warnings={warns.value})"
            )
        return doc

    def activate_document(self, title: str):
        """Activate an already-open document by title. Tries the title as given,
        then with document extensions appended (titles may include extensions
        depending on Windows Explorer settings)."""
        err = win32com.client.VARIANT(pythoncom.VT_BYREF | pythoncom.VT_I4, 0)
        candidates = [title]
        if "." not in title:
            candidates += [f"{title}.SLDPRT", f"{title}.SLDASM", f"{title}.SLDDRW"]
        for name in candidates:
            doc = self.app.ActivateDoc3(name, False, 2, err)  # 2 = rebuild on activation
            if doc:
                return doc
        raise Exception(f"Could not activate document: {title}")
    
    def create_new_part(self):
        """Create a brand new part document"""
        template = self.find_template()
        if not template:
            raise Exception("No Part template found")
        
        logger.info("Creating new part document")
        doc = self.app.NewDocument(template, 0, 0, 0)
        
        if not doc:
            raise Exception("Failed to create part document")
        
        logger.info("✓ New part document created")
        return doc
    
    def get_active_doc(self):
        """Get the currently active document"""
        return self.app.ActiveDoc if self.app else None

    def is_alive(self) -> bool:
        """Check if the COM connection to SolidWorks is still alive."""
        if not self.app:
            return False
        try:
            _ = self.app.RevisionNumber
            return True
        except Exception:
            return False

    def reconnect(self) -> bool:
        """Drop the current COM handle and establish a fresh connection."""
        logger.warning("Attempting to reconnect to SolidWorks...")
        self.app = None
        self.template_path = None
        self.assembly_template_path = None
        # Brief pause to let SolidWorks stabilize if it just restarted
        time.sleep(2)
        return self.connect()

    def close_all_docs(self):
        """Close all open documents without saving.

        Bounded loop: QuitDoc can decline to close a document (e.g. a modal
        dialog is up), in which case ActiveDoc keeps returning the same doc —
        an unbounded `while True` here would spin forever.
        """
        if not self.is_alive():
            return
        closed = 0
        last_title = None
        for _ in range(50):
            doc = self.app.ActiveDoc
            if not doc:
                break
            title = doc.GetTitle
            if title == last_title:
                logger.warning(
                    f"QuitDoc did not close '{title}'; aborting close_all_docs"
                )
                break
            self.app.QuitDoc(title)
            last_title = title
            closed += 1
        else:
            logger.warning("close_all_docs hit the 50-iteration bound")
        if closed:
            logger.info(f"Closed {closed} document(s)")

    def get_sw_version(self) -> str:
        """Return the SolidWorks revision string, or 'unknown'."""
        if not self.is_alive():
            return "unknown"
        try:
            return str(self.app.RevisionNumber)
        except Exception:
            return "unknown"

    def ensure_connection(self):
        """Ensure we have a live connection, reconnecting if needed."""
        if self.is_alive():
            return
        logger.warning("SolidWorks COM connection is dead, reconnecting...")
        if not self.reconnect():
            raise Exception(
                "Failed to connect to SolidWorks. "
                "Ensure SolidWorks is running and responsive."
            )
