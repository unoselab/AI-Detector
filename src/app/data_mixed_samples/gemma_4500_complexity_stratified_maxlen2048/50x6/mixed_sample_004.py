# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line3156_lm, name=get_cache_context) ===
def get_cache_context(self):
        """
        Retrieve a context cache from disk
        """
        import os
        import pickle
        cache_path = getattr(self, 'cache_path', '.cache_context.pkl')
        if os.path.exists(cache_path):
            with open(cache_path, 'rb') as f:
                return pickle.load(f)
        return None

# === BLOCK 2 (label=lm, source_idx=line3735_lm, name=get_provider) ===
def get_provider(self, module_member: str) -> Optional['ProviderResource']:
        """
        Fetches the provider for the given module member, if this resource has been provided a specific
        provider for the given module member.

        Returns None if no provider was provided.

        :param str module_member: The requested module member.
        :return: The :class:`ProviderResource` associated with the given module member, or None if one does not exist.
        :rtype: Optional[ProviderResource]
        """
        return self._providers.get(module_member)

# === BLOCK 3 (label=human, source_idx=line5124_human, name=_parseAtImports) ===
def _parseAtImports(self, src):
        """[ import [S|CDO|CDC]* ]*"""
        result = []
        while isAtRuleIdent(src, 'import'):
            ctxsrc = src
            src = stripAtRuleIdent(src)

            import_, src = self._getStringOrURI(src)
            if import_ is None:
                raise self.ParseError('Import expecting string or url', src, ctxsrc)

            mediums = []
            medium, src = self._getIdent(src.lstrip())
            while medium is not None:
                mediums.append(medium)
                if src[:1] == ',':
                    src = src[1:].lstrip()
                    medium, src = self._getIdent(src)
                else:
                    break

            # XXX No medium inherits and then "all" is appropriate
            if not mediums:
                mediums = ["all"]

            if src[:1] != ';':
                raise self.ParseError('@import expected a terminating \';\'', src, ctxsrc)
            src = src[1:].lstrip()

            stylesheet = self.cssBuilder.atImport(import_, mediums, self)
            if stylesheet is not None:
                result.append(stylesheet)

            src = self._parseSCDOCDC(src)
        return src, result

# === BLOCK 4 (label=lm, source_idx=line2593_lm, name=collage) ===
def collage(imgs, size, padding=10, bg=COL_BLACK):
    """
    Constructs a collage of same-sized images with specified padding.

    :param imgs: Array of images. Either 1d-array or 2d-array.
    :param size: (no. of rows, no. of cols)
    :param padding: Padding space between each image
    :param bg: Background color for the collage. Default: Black
    :return: New collage
    """
    import numpy as np

    rows, cols = size
    if len(imgs) == 1 and isinstance(imgs[0], (list, np.ndarray)) and len(np.shape(imgs[0])) > 0:
        img_list = imgs[0]
    else:
        img_list = imgs

    if not img_list:
        return np.full((0, 0, 3), bg, dtype=np.uint8)

    first_img = np.array(img_list[0])
    h, w, c = first_img.shape

    collage_h = rows * h + (rows + 1) * padding
    collage_w = cols * w + (cols + 1) * padding

    res = np.full((collage_h, collage_w, c), bg, dtype=np.uint8)

    for idx, img in enumerate(img_list):
        if idx >= rows * cols:
            break
        r = idx // cols
        c_idx = idx % cols

        y = (r + 1) * padding + r * h
        x = (c_idx + 1) * padding + c_idx * w

        img_arr = np.array(img)
        res[y:y+h, x:x+w] = img_arr

    return res

# === BLOCK 5 (label=human, source_idx=line7499_human, name=htmlNewDoc) ===
def htmlNewDoc(URI, ExternalID):
    """Creates a new HTML document """
    ret = libxml2mod.htmlNewDoc(URI, ExternalID)
    if ret is None:raise treeError('htmlNewDoc() failed')
    return xmlDoc(_obj=ret)

# === BLOCK 6 (label=human, source_idx=line4215_human, name=render) ===
def render(self, name, value, attrs=None):
        """
        Render the ``icekit_events/recurrence_rule_widget/render.html``
        template with the following context:

            rendered_widgets
                The rendered widgets.
            id
                The ``id`` attribute from the ``attrs`` keyword argument.
            recurrence_rules
                A JSON object mapping recurrence rules to their primary keys.

        The default template adds JavaScript event handlers that update the
        ``Textarea`` and ``Select`` widgets when they are updated.
        """
        rendered_widgets = super(RecurrenceRuleWidget, self).render(
            name, value, attrs)
        template = loader.get_template(
            'icekit_events/recurrence_rule_widget/render.html')
        recurrence_rules = json.dumps(dict(
            self.queryset.values_list('pk', 'recurrence_rule')))
        context = Context({
            'rendered_widgets': rendered_widgets,
            'id': attrs['id'],
            'recurrence_rules': recurrence_rules,
        })
        return template.render(context)
