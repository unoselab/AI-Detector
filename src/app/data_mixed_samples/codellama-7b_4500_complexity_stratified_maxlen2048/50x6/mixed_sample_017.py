# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line2166_lm, name=_on_work_finished) ===
def _on_work_finished(self, results):
        """
        Display results.

        :param status: Response status
        :param results: Response data, messages.
        """
        if results:
            for result in results:
                self._display_result(result)

# === BLOCK 2 (label=lm, source_idx=line4688_lm, name=body_block_supplementary_material_render) ===
def body_block_supplementary_material_render(supp_tags, base_url=None):
    """fig and media tag caption may have supplementary material"""
    if not supp_tags:
        return ''
    if base_url is None:
        base_url = ''
    return '<div class="supplementary-material">' + \
        ''.join(
            '<div class="supplementary-material-{0}">{1}</div>'.format(
                tag['type'],
                '<a href="{0}{1}">{2}</a>'.format(
                    base_url,
                    tag['href'],
                    tag['caption']
                )
            ) for tag in supp_tags
        ) + \
        '</div>'

# === BLOCK 3 (label=lm, source_idx=line1234_lm, name=all_fields) ===
def all_fields(self):
        """
        Returns a list of all fields. Subtype fields come before this type's
        fields.
        """
        return self.all_fields_by_name.values()

# === BLOCK 4 (label=human, source_idx=line7111_human, name=my_on_connect) ===
def my_on_connect(client):
    """
    Example on_connect handler.
    """
    client.send('You connected from %s\n' % client.addrport())
    if CLIENTS:
        client.send('Also connected are:\n')
        for neighbor in CLIENTS:
            client.send('%s\n' % neighbor.addrport())
    else:
        client.send('Sadly, you are alone.\n')
    CLIENTS.append(client)

# === BLOCK 5 (label=human, source_idx=line4244_human, name=_merge_fix) ===
def _merge_fix(d):
    """Fixes keys that start with "&" and "-"
        d = {
          "&steve": 10,
          "-gary": 4
        }
        result = {
          "steve": 10,
          "gary": 4
        }
    """
    if type(d) is dict:
        for key in d.keys():
            if key[0] in ('&', '-'):
                d[key[1:]] = _merge_fix(d.pop(key))
    return d

# === BLOCK 6 (label=human, source_idx=line6019_human, name=add_method_drop_down) ===
def add_method_drop_down(self, col_number, col_label):
        """
        Add drop-down-menu options for magic_method_codes columns
        """
        if self.data_type == 'age':
            method_list = vocab.age_methods
        elif '++' in col_label:
            method_list = vocab.pmag_methods
        elif self.data_type == 'result':
            method_list = vocab.pmag_methods
        else:
            method_list = vocab.er_methods
        self.choices[col_number] = (method_list, True)
