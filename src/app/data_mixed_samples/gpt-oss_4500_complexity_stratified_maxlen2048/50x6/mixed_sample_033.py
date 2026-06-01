# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line608_lm, name=tree) ===
def tree(c):
    """
    Display documentation contents with the 'tree' program.
    """
    import os
    import subprocess

    # Resolve the path; default to current directory if None or empty
    path = c or "."
    path = os.path.abspath(str(path))

    # Try to use the external 'tree' command if available
    try:
        result = subprocess.run(
            ["tree", path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            return result.stdout
    except (FileNotFoundError, OSError):
        # 'tree' command not found or cannot be executed
        pass

    # Fallback: generate a simple tree representation using os.walk
    lines = []
    for root, dirs, files in os.walk(path):
        # Compute the depth relative to the base path
        rel_root = os.path.relpath(root, path)
        depth = 0 if rel_root == "." else rel_root.count(os.sep) + 1

        indent = "│   " * (depth - 1) + ("├── " if depth > 0 else "")
        lines.append(f"{indent}{os.path.basename(root)}/")

        # Sort for deterministic output
        dirs.sort()
        files.sort()
        for i, name in enumerate(files):
            file_indent = "│   " * depth + ("└── " if i == len(files) - 1 else "├── ")
            lines.append(f"{file_indent}{name}")

    return "\n".join(lines) + ("\n" if lines else "")

# === BLOCK 2 (label=lm, source_idx=line1745_lm, name=track_purchase) ===
def track_purchase(self, user, items, total, purchase_id= None, campaign_id=None, 
					   template_id=None, created_at=None,
					   data_fields=None):
		"""
			The 'purchase_id' argument maps to 'id' for this API endpoint.
			This name is used to distinguish it from other instances where
			'id' is a part of the API request with other Iterable endpoints.
		"""

# === BLOCK 3 (label=human, source_idx=line1093_human, name=client_updates_config) ===
def client_updates_config(artwork=True, now_playing=True,
                          volume=True, keyboard=True):
    """Create a new CLIENT_UPDATES_CONFIG_MESSAGE."""
    message = create(protobuf.CLIENT_UPDATES_CONFIG_MESSAGE)
    config = message.inner()
    config.artworkUpdates = artwork
    config.nowPlayingUpdates = now_playing
    config.volumeUpdates = volume
    config.keyboardUpdates = keyboard
    return message

# === BLOCK 4 (label=human, source_idx=line6672_human, name=_before_flush_handler) ===
def _before_flush_handler(session, _flush_context, _instances):
    """Update version ID for all dirty, modified rows"""
    dialect = get_dialect(session)
    for row in session.dirty:
        if isinstance(row, SavageModelMixin) and is_modified(row, dialect):
            # Update row version_id
            row.update_version_id()

# === BLOCK 5 (label=human, source_idx=line5178_human, name=_set_repository_view) ===
def _set_repository_view(self, session):
        """Sets the underlying repository view to match current view"""
        if self._repository_view == FEDERATED:
            try:
                session.use_federated_repository_view()
            except AttributeError:
                pass
        else:
            try:
                session.use_isolated_repository_view()
            except AttributeError:
                pass

# === BLOCK 6 (label=lm, source_idx=line1965_lm, name=get_chunk) ===
def get_chunk(self, ji):
        """Get a EOCubeChunk"""
        # Ensure the internal chunk storage exists
        if not hasattr(self, "_chunks"):
            self._chunks = {}
        # Return cached chunk if present
        if ji in self._chunks:
            return self._chunks[ji]
        # Attempt to load/create the chunk using a helper if available
        if hasattr(self, "_load_chunk") and callable(self._load_chunk):
            chunk = self._load_chunk(ji)
        else:
            raise KeyError(f"Chunk {ji} not found and no loader defined")
        # Cache and return the newly obtained chunk
        self._chunks[ji] = chunk
        return chunk
