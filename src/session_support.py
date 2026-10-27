"""Track exactly which documents a test owns, even after Save As renames."""

from solidworks.com_utils import com_prop


class OwnedDocuments:
    def __init__(self, app):
        self.app = app
        self.originals = list(com_prop(app, "GetDocuments") or [])
        self.original_active = app.ActiveDoc
        self.documents = []

    def register(self, doc):
        if doc is None:
            raise RuntimeError("Cannot register a missing test document")
        title = str(com_prop(doc, "GetTitle"))
        for original in self.originals:
            if str(com_prop(original, "GetTitle")) == title:
                raise RuntimeError(f"Refusing to take ownership of existing document: {title}")
        self.documents.append(doc)
        return doc

    def close_owned(self):
        failures = []
        for doc in reversed(self.documents):
            try:
                title = str(com_prop(doc, "GetTitle"))
            except Exception:
                continue  # A test may already have closed this COM object.
            open_titles = {str(com_prop(d, "GetTitle"))
                           for d in (com_prop(self.app, "GetDocuments") or [])}
            if title not in open_titles:
                continue
            original_titles = {str(com_prop(d, "GetTitle")) for d in self.originals}
            if title in original_titles:
                failures.append(f"Refusing to close original document: {title}")
                continue
            self.app.QuitDoc(title)
            remaining = {str(com_prop(d, "GetTitle"))
                         for d in (com_prop(self.app, "GetDocuments") or [])}
            if title in remaining:
                failures.append(f"Test document did not close: {title}")
        if failures:
            raise RuntimeError("; ".join(failures))
        self.documents.clear()

    def assert_originals_open(self):
        titles = {str(com_prop(d, "GetTitle"))
                  for d in (com_prop(self.app, "GetDocuments") or [])}
        for original in self.originals:
            title = str(com_prop(original, "GetTitle"))
            if title not in titles:
                raise RuntimeError(f"Original document disappeared: {title}")


class TrackingApplication:
    """Proxy test document creation; ordinary application calls are unchanged."""

    def __init__(self, owner):
        self.owner = owner

    def __getattr__(self, name):
        member = getattr(self.owner.app, name)
        if name in {"NewDocument", "OpenDoc6", "LoadFile4"}:
            def create(*args, **kwargs):
                return self.owner.register(member(*args, **kwargs))
            return create
        return member
