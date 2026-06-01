# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line5421_lm, name=map_to_precursors) ===
def map_to_precursors(seqs, names, loci, out_file, args):
    """map sequences to precursors with razers3"""

# === BLOCK 2 (label=human, source_idx=line6761_human, name=fuzzy_match_tipnames) ===
def fuzzy_match_tipnames(ttree, names, wildcard, regex, mrca=True, mono=True):
    """
    Used in multiple internal functions (e.g., .root()) and .drop_tips())
    to select an internal mrca node, or multiple tipnames, using fuzzy matching
    so that every name does not need to be written out by hand.

    name: verbose list
    wildcard: matching unique string
    regex: regex expression
    mrca: return mrca node of selected tipnames. 
    mono: raise error if selected tipnames are not monophyletic    
    """
    # require arguments
    if not any([names, wildcard, regex]):
        raise ToytreeError(
            "must enter an outgroup, wildcard selector, or regex pattern")

    # get list of **nodes** from {list, wildcard, or regex}
    tips = []
    if names:
        if isinstance(names, (str, int)):
            names = [names]
        notfound = [i for i in names if i not in ttree.get_tip_labels()]
        if any(notfound):
            raise ToytreeError(
                "Sample {} is not in the tree".format(notfound))
        tips = [i for i in ttree.treenode.get_leaves() if i.name in names]

    # use regex to match tipnames
    elif regex:
        tips = [
            i for i in ttree.treenode.get_leaves() if re.match(regex, i.name)
        ]               
        if not any(tips):
            raise ToytreeError("No Samples matched the regular expression")

    # use wildcard substring matching
    elif wildcard:
        tips = [i for i in ttree.treenode.get_leaves() if wildcard in i.name]
        if not any(tips):
            raise ToytreeError("No Samples matched the wildcard")

    # build list of **tipnames** from matched nodes
    if not tips:
        raise ToytreeError("no matching tipnames")       
    tipnames = [i.name for i in tips]

    # if a single tipname matched no need to check for monophyly
    if len(tips) == 1:
        if mrca:
            return tips[0]
        else:
            return tipnames

    # if multiple nodes matched, check if they're monophyletic
    mbool, mtype, mnames = (
        ttree.treenode.check_monophyly(
            tipnames, "name", ignore_missing=True)
    )

    # get mrca node
    node = ttree.treenode.get_common_ancestor(tips)

    # raise an error if required to be monophyletic but not
    if mono:
        if not mbool:
            raise ToytreeError(
                "Taxon list cannot be paraphyletic")

    # return tips or nodes
    if not mrca:
        return tipnames
    else:
        return node

# === BLOCK 3 (label=human, source_idx=line2386_human, name=update_connector_resource) ===
def update_connector_resource(name, server=None, **kwargs):
    """
    Update a connection resource
    """
    # You're not supposed to update jndiName, if you do so, it will crash, silently
    if 'jndiName' in kwargs:
        del kwargs['jndiName']
    return _update_element(name, 'resources/connector-resource', kwargs, server)

# === BLOCK 4 (label=human, source_idx=line2905_human, name=_get_object_as_soft) ===
def _get_object_as_soft(self):
        """Get the object as SOFT formatted string."""
        soft = ["^%s = %s" % (self.geotype, self.name),
                self._get_metadata_as_string()]
        return "\n".join(soft)

# === BLOCK 5 (label=lm, source_idx=line312_lm, name=_build_data) ===
def _build_data(self, amplification_group):
        """
        Creates the numpy array tables from the hdf5 tables
        """
        import numpy as np
        import h5py

        tables = {}

        def _traverse(group, prefix=""):
            for name, obj in group.items():
                full_name = f"{prefix}{name}"
                if isinstance(obj, h5py.Dataset):
                    tables[full_name] = np.array(obj)
                elif isinstance(obj, h5py.Group):
                    _traverse(obj, prefix=full_name + "/")

        _traverse(amplification_group)
        self.tables = tables
        return tables

# === BLOCK 6 (label=lm, source_idx=line508_lm, name=avail_images) ===
def avail_images(call=None):
    """
    returns a list of images available to you
    """
    if call is not None:
        return call()
    try:
        import docker
        client = docker.from_env()
        imgs = client.images.list()
        result = []
        for img in imgs:
            if img.tags:
                result.extend(img.tags)
        return result
    except Exception:
        return []
