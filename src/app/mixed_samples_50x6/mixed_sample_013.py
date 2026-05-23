# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line2109_human, name=get_urls) ===
def get_urls(self):
        """
        Add aditional moderate url.
        """
        from django.conf.urls import url
        urls = super(AdminModeratorMixin, self).get_urls()
        info = self.model._meta.app_label, self.model._meta.model_name
        return [
            url(r'^(.+)/moderate/$',
                self.admin_site.admin_view(self.moderate_view),
                name='%s_%s_moderate' % info),
        ] + urls

# === BLOCK 2 (label=human, source_idx=line68_human, name=get_peers_in_established) ===
def get_peers_in_established(self):
        """Returns list of peers in established state."""
        est_peers = []
        for peer in self._peers.values():
            if peer.in_established:
                est_peers.append(peer)
        return est_peers

# === BLOCK 3 (label=human, source_idx=line2181_human, name=op_range) ===
def op_range(self, start, end):
        """
        Iterate through positions of opcodes, skipping
        arguments.
        """
        while start < end:
            yield start
            start += instruction_size(self.code[start], self.opc)

# === BLOCK 4 (label=lm, source_idx=line1097_lm, name=_is_exempt) ===
def _is_exempt(self, environ):
        """
        Returns True if this request's URL starts with one of the
        excluded paths.
        """
        path = environ.get('PATH_INFO', '')
        for excluded_path in self.excluded_paths:
            if path.startswith(excluded_path):
                return True
        return False

# === BLOCK 5 (label=lm, source_idx=line374_lm, name=git_status_all_repos) ===
def git_status_all_repos(cat, hard=True, origin=False, clean=True):
    """Perform a 'git status' in each data repository.
    """
    if hard:
        print("'git status' with the --hard option")
    elif origin:
        print("'git status' with the --origin option")
    elif clean:
        print("'git status' with the --clean option")
    else:
        print("'git status'")

# === BLOCK 6 (label=lm, source_idx=line2634_lm, name=location) ===
def location(name, uri, default):
    """Create new location."""
    return {"name": name, "uri": uri, "default": default}
