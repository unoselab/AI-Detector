# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line1516_human, name=_margtime_loglr) ===
def _margtime_loglr(self, mf_snr, opt_snr):
        """Returns the log likelihood ratio marginalized over time.
        """
        return special.logsumexp(mf_snr, b=self._deltat) - 0.5*opt_snr

# === BLOCK 2 (label=lm, source_idx=line2836_lm, name=filtered_archs) ===
def filtered_archs(self):
        """Return archs of self.ctx that are valid build archs
        for the Recipe."""
        return [arch for arch in self.ctx if self.ctx[arch].valid_build_arch]

# === BLOCK 3 (label=human, source_idx=line2388_human, name=is_ome) ===
def is_ome(self):
        """Page contains OME-XML in ImageDescription tag."""
        if self.index > 1 or not self.description:
            return False
        d = self.description
        return d[:14] == '<?xml version=' and d[-6:] == '</OME>'

# === BLOCK 4 (label=lm, source_idx=line4007_lm, name=ffd) ===
def ffd(items, targets, **kwargs):
    """First-Fit Decreasing

    This is perhaps the simplest packing heuristic;
    it simply packs items in the next available bin.

    This algorithm differs only from Next-Fit Decreasing
    in having a 'sort'; that is, the items are pre-sorted
    (largest to smallest).

    Complexity O(n^2)
    """
    items.sort(reverse=True)
    bins = []
    for item in items:
        for bin in bins:
            if bin.can_fit(item):
                bin.add(item)
                break
        else:
            bin = Bin()
            bin.add(item)
            bins.append(bin)
    return bins

# === BLOCK 5 (label=lm, source_idx=line594_lm, name=find_segment) ===
def find_segment(self, ea):
        """ do a linear search for the given address in the segment list """
        for segment in self.segments:
            if segment.start_ea <= ea < segment.end_ea:
                return segment
        return None

# === BLOCK 6 (label=human, source_idx=line4083_human, name=trim_trailing_silence) ===
def trim_trailing_silence(self):
        """Trim the trailing silences of the pianorolls of all tracks. Trailing
        silences are considered globally."""
        active_length = self.get_active_length()
        for track in self.tracks:
            track.pianoroll = track.pianoroll[:active_length]
