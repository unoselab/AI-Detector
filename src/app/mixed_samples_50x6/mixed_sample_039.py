# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line1702_lm, name=get_used_key_frames) ===
def get_used_key_frames(self):
        """Returns a list of the keyframes used by this channel, sorted with
        time. Each element in the list is a tuple. The first element is the
        key_name and the second is the channel data at that keyframe."""
        key_frames = []
        for key_name, key_data in self.key_frames.items():
            key_frames.append((key_name, key_data))
        key_frames.sort(key=lambda x: x[1]["time"])
        return key_frames

# === BLOCK 2 (label=human, source_idx=line1334_human, name=superreload) ===
def superreload(module, reload=reload, old_objects={}):
    """Enhanced version of the builtin reload function.

    superreload remembers objects previously in the module, and

    - upgrades the class dictionary of every old class in the module
    - upgrades the code object of every old function and method
    - clears the module's namespace before reloading

    """

    # collect old objects in the module
    for name, obj in list(module.__dict__.items()):
        if not hasattr(obj, '__module__') or obj.__module__ != module.__name__:
            continue
        key = (module.__name__, name)
        try:
            old_objects.setdefault(key, []).append(weakref.ref(obj))
        except TypeError:
            pass

    # reload module
    try:
        # clear namespace first from old cruft
        old_dict = module.__dict__.copy()
        old_name = module.__name__
        module.__dict__.clear()
        module.__dict__['__name__'] = old_name
        module.__dict__['__loader__'] = old_dict['__loader__']
    except (TypeError, AttributeError, KeyError):
        pass

    try:
        module = reload(module)
    except:
        # restore module dictionary on failed reload
        module.__dict__.update(old_dict)
        raise

    # iterate over all objects and update functions & classes
    for name, new_obj in list(module.__dict__.items()):
        key = (module.__name__, name)
        if key not in old_objects: continue

        new_refs = []
        for old_ref in old_objects[key]:
            old_obj = old_ref()
            if old_obj is None: continue
            new_refs.append(old_ref)
            update_generic(old_obj, new_obj)

        if new_refs:
            old_objects[key] = new_refs
        else:
            del old_objects[key]

    return module

# === BLOCK 3 (label=lm, source_idx=line2711_lm, name=fpr) ===
def fpr(y, z):
    """False positive rate `fp / (fp + tn)`
    """
    fp = 0
    tn = 0
    for i in range(len(y)):
        if y[i] == 0 and z[i] == 1:
            fp += 1
        elif y[i] == 0 and z[i] == 0:
            tn += 1
    return fp / (fp + tn)

# === BLOCK 4 (label=human, source_idx=line2881_human, name=_fix_namespace) ===
def _fix_namespace(self):
    """Internal helper to fix the namespace.

    This is called to ensure that for queries without an explicit
    namespace, the namespace used by async calls is the one in effect
    at the time the async call is made, not the one in effect when the
    the request is actually generated.
    """
    if self.namespace is not None:
      return self
    namespace = namespace_manager.get_namespace()
    return self.__class__(kind=self.kind, ancestor=self.ancestor,
                          filters=self.filters, orders=self.orders,
                          app=self.app, namespace=namespace,
                          default_options=self.default_options,
                          projection=self.projection, group_by=self.group_by)

# === BLOCK 5 (label=human, source_idx=line1458_human, name=create_seq) ===
def create_seq(self, project):
        """Create and return a new sequence

        :param project: the project for the sequence
        :type deps: :class:`jukeboxcore.djadapter.models.Project`
        :returns: The created sequence or None
        :rtype: None | :class:`jukeboxcore.djadapter.models.Sequence`
        :raises: None
        """
        dialog = SequenceCreatorDialog(project=project, parent=self)
        dialog.exec_()
        seq = dialog.sequence
        return seq

# === BLOCK 6 (label=lm, source_idx=line325_lm, name=main) ===
def main():
    """Invoked by the script installed by setuptools."""
    pass
