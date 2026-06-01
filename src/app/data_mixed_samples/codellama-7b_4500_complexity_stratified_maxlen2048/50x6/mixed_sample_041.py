# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line6133_human, name=get_type) ===
def get_type(full_path):
    """Get the type (socket, file, dir, symlink, ...) for the provided path"""
    status = {'type': []}
    if os.path.ismount(full_path):
        status['type'] += ['mount-point']
    elif os.path.islink(full_path):
        status['type'] += ['symlink']
    if os.path.isfile(full_path):
        status['type'] += ['file']
    elif os.path.isdir(full_path):
        status['type'] += ['dir']
    if not status['type']:
        if os.stat.S_ISSOCK(status['mode']):
            status['type'] += ['socket']
        elif os.stat.S_ISCHR(status['mode']):
            status['type'] += ['special']
        elif os.stat.S_ISBLK(status['mode']):
            status['type'] += ['block-device']
        elif os.stat.S_ISFIFO(status['mode']):
            status['type'] += ['pipe']
    if not status['type']:
        status['type'] += ['unknown']
    elif status['type'] and status['type'][-1] == 'symlink':
        status['type'] += ['broken']
    return status['type']

# === BLOCK 2 (label=human, source_idx=line4090_human, name=symmetric_difference_update) ===
def symmetric_difference_update(self, that):
        """
        Update the set, keeping only elements found in either *self* or *that*,
        but not in both.
        """
        _set = self._set
        _list = self._list
        _set.symmetric_difference_update(that)
        _list.clear()
        _list.update(_set)
        return self

# === BLOCK 3 (label=lm, source_idx=line336_lm, name=get_files) ===
def get_files():
    """
    Read all the template's files
    """
    files = []
    for root, dirs, files in os.walk(TEMPLATE_DIR):
        for file in files:
            files.append(os.path.join(root, file))
    return files

# === BLOCK 4 (label=lm, source_idx=line2580_lm, name=build_url_field) ===
def build_url_field(self, field_name, model_class):
        """
        Create a field representing the object's own URL.
        """
        field = models.URLField(
            verbose_name=field_name,
            blank=True,
            help_text=_("The URL of the object's own page."),
        )
        field.contribute_to_class(model_class, field_name)
        return field

# === BLOCK 5 (label=human, source_idx=line4997_human, name=extract) ===
def extract(what, calc_id, webapi=True):
    """
    Extract an output from the datastore and save it into an .hdf5 file.
    By default uses the WebAPI, otherwise the extraction is done locally.
    """
    with performance.Monitor('extract', measuremem=True) as mon:
        if webapi:
            obj = WebExtractor(calc_id).get(what)
        else:
            obj = Extractor(calc_id).get(what)
        fname = '%s_%d.hdf5' % (what.replace('/', '-').replace('?', '-'),
                                calc_id)
        obj.save(fname)
        print('Saved', fname)
    if mon.duration > 1:
        print(mon)

# === BLOCK 6 (label=lm, source_idx=line4524_lm, name=write_document) ===
def write_document(self, name, document):
        """
        This function will write a document to an XML file.
        """
        # Create a new XML file
        xml_file = open(name, 'w')

        # Write the XML header
        xml_file.write('<?xml version="1.0" encoding="UTF-8"?>\n')

        # Write the XML document
        xml_file.write(document)

        # Close the XML file
        xml_file.close()
