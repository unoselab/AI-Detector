# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line3983_lm, name=sendTemplate) ===
def sendTemplate(mailer, sender, recipient, template, context, hook=_nop):
    """
    Simple case for sending some e-mail using a template.
    """
    message = template.render(context)
    mailer.send(sender, recipient, message)
    hook(sender, recipient, message)

# === BLOCK 2 (label=human, source_idx=line4647_human, name=_mutate_probability_vec) ===
def _mutate_probability_vec(probability_vec, mutation_chance, mutation_adjust_rate):
    """Randomly adjust probabilities.

    WARNING: Modifies probability_vec argument.
    """
    bits_to_mutate = numpy.random.random(probability_vec.size) <= mutation_chance
    probability_vec[bits_to_mutate] = _adjust(
        probability_vec[bits_to_mutate],
        numpy.random.random(numpy.sum(bits_to_mutate)), mutation_adjust_rate)

# === BLOCK 3 (label=lm, source_idx=line4612_lm, name=getreferingobjs) ===
def getreferingobjs(referedobj, iddgroups=None, fields=None):
    """Get a list of objects that refer to this object"""
    if iddgroups is None:
        iddgroups = []
    if fields is None:
        fields = []
    referingobjs = []
    for obj in iddgroups:
        if obj.id == referedobj.id:
            referingobjs.append(obj)
    for field in fields:
        if field.id == referedobj.id:
            referingobjs.append(field)

    return referingobjs

# === BLOCK 4 (label=lm, source_idx=line2167_lm, name=deserialize) ===
def deserialize(cls, target_class, obj):
        """
        :type target_class: object_.MonetaryAccountReference|type
        :type obj: dict

        :rtype: object_.MonetaryAccountReference
        """
        if target_class == object_.MonetaryAccountReference:
            return object_.MonetaryAccountReference(
                type=obj.get("type"),
                id=obj.get("id"),
            )
        else:
            raise ValueError("Invalid target_class")

# === BLOCK 5 (label=human, source_idx=line4725_human, name=format_tsv_line) ===
def format_tsv_line(source, edge, target, value=None, metadata=None):
    """
    Render a single line for TSV file with data flow described

    :type source str
    :type edge str
    :type target str
    :type value float
    :type metadata str
    :rtype: str
    """
    return '{source}\t{edge}\t{target}\t{value}\t{metadata}'.format(
        source=source,
        edge=edge,
        target=target,
        value='{:.4f}'.format(value) if value is not None else '',
        metadata=metadata or ''
    ).rstrip(' \t')

# === BLOCK 6 (label=human, source_idx=line2712_human, name=_get_columns) ===
def _get_columns(self):
        """ List of child TreeViewColumns including 
            this item as the first column
        """
        return [self] + [c for c in self.children
                         if isinstance(c, TreeViewColumn)]
