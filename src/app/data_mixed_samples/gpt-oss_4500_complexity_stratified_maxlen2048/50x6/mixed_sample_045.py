# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line5494_lm, name=method_by_name) ===
def method_by_name(self, method_name):
        """
        Look up a method by its name from the module ``methods`` list.
        :param method_name: the name of the method to look up
        :type method_name: str

        :return: the method ( if it is found)
        :rtype: ``boa.code.method.Method``
        """
        for m in getattr(self, 'methods', []):
            if getattr(m, 'name', None) == method_name:
                return m
        mod = getattr(self, 'module', None)
        if mod:
            for m in getattr(mod, 'methods', []):
                if getattr(m, 'name', None) == method_name:
                    return m
        return None

# === BLOCK 2 (label=human, source_idx=line2886_human, name=_skip_whitespace) ===
def _skip_whitespace(self):
        """Increment over whitespace, counting characters."""
        i = 0
        while self._cur_token['type'] is TT.ws and not self._finished:
            self._increment()
            i += 1

        return i

# === BLOCK 3 (label=lm, source_idx=line3967_lm, name=__create_csv_eps) ===
def __create_csv_eps(self, metric1, metric2, csv_labels, file_label,
                         title_label, project=None):
        """
        Generate the CSV data and EPS figs files for two metrics
        :param metric1: first metric class
        :param metric2: second metric class
        :param csv_labels: labels to be used in the CSV file
        :param file_label: shared filename token to be included in csv and eps files
        :param title_label: title for the EPS figures
        :param project: name of the project for which to generate the data
        :return:
        """

# === BLOCK 4 (label=human, source_idx=line6842_human, name=instant_name_to_class_name) ===
def instant_name_to_class_name(name):
    """
        This will convert from 'parent_name.child_name' to
        'ParentName_ChildName'
    :param name: str of the name to convert
    :return: str of the converted name
    """
    name2 = ''.join([e.title() for e in name.split('_')])
    return '_'.join([e[0].upper() + e[1:] for e in name2.split('.')])

# === BLOCK 5 (label=lm, source_idx=line1483_lm, name=from_dict) ===
def from_dict(cls, d, fmt=None):
        """
        Reconstitute a Structure object from a dict representation of Structure
        created using as_dict().

        Args:
            d (dict): Dict representation of structure.

        Returns:
            Structure object
        """
        if d is None:
            return None

# === BLOCK 6 (label=human, source_idx=line4871_human, name=_check_id) ===
def _check_id(entity, entity_type):
    """Check whether the ID is valid.

    First check if the ID is missing, and then check if it is a qualified
    string type, finally check if the string is empty. For all checks, it
    would raise a ParseError with the corresponding message.

    Args:
        entity: a string type object to be checked.
        entity_type: a string that shows the type of entities to check, usually
            `Compound` or 'Reaction'.
    """

    if entity is None:
        raise ParseError('{} ID missing'.format(entity_type))
    elif not isinstance(entity, string_types):
        msg = '{} ID must be a string, id was {}.'.format(entity_type, entity)
        if isinstance(entity, bool):
            msg += (' You may have accidentally used an ID value that YAML'
                    ' interprets as a boolean, such as "yes", "no", "on",'
                    ' "off", "true" or "false". To use this ID, you have to'
                    ' quote it with single or double quotes')
        raise ParseError(msg)
    elif len(entity) == 0:
        raise ParseError('{} ID must not be empty'.format(entity_type))
