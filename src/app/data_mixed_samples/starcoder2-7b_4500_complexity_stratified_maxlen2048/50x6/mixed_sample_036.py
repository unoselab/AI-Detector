# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line3045_human, name=abort) ===
def abort(self, reason):
        """This function is called when the application would like to abort the
        transaction.  There is no notification back to the application."""
        if _debug: ServerSSM._debug("abort %r", reason)

        # change the state to aborted
        self.set_state(ABORTED)

        # return an abort APDU
        return AbortPDU(True, self.invokeID, reason)

# === BLOCK 2 (label=lm, source_idx=line3686_lm, name=DrawIconAndLabel) ===
def DrawIconAndLabel(self, dc, node, x, y, w, h, depth):
        """ Draw the icon, if any, and the label, if any, of the node. """
        if node.icon:
            dc.DrawBitmap(node.icon, x, y, w, h)
        if node.label:
            dc.DrawText(node.label, x, y)

# === BLOCK 3 (label=human, source_idx=line6795_human, name=resize_image) ===
def resize_image(fullfile,fullfile_resized,_megapixels):
    """Resizes image (fullfile), saves to fullfile_resized. Image
    aspect ratio is conserved, will be scaled to be close to _megapixels in 
    size. Eg if _megapixels=2, will resize 2560x1920 so each dimension
    is scaled by ((2**(20+1*MP))/float(2560*1920))**2"""

    logger.debug("%s - Resizing to %s MP"%(fullfile,_megapixels))

    img = Image.open(fullfile)
    width,height=img.size
    current_megapixels=width*height/(2.0**20)

    # Compute new width and height for image
    new_width,new_height=resize_compute_width_height(\
            fullfile,_megapixels)

    # Not scaling
    if not new_width:
        logger.debug("%s - NOT Resizing, scale is > 1"%(fullfile))
        return False

    logger.info("%s - Resizing image from %0.1f to %0.1f MP (%dx%d) to (%dx%d)"\
            %(fullfile,current_megapixels,_megapixels,width,height,new_width,new_height))
    # Resize the image
    imageresize = img.resize((new_width,new_height), Image.ANTIALIAS)
    #imageresize.save(fullfile_resized, 'JPEG', quality=75)
    #FIXME: What quality to save as?
    imageresize.save(fullfile_resized, 'JPEG')

    # ---- Transfer over EXIF info ----
    if not update_exif_GEXIV2(fullfile,fullfile_resized):
        return False


    return True

# === BLOCK 4 (label=human, source_idx=line4257_human, name=load_js) ===
def load_js(js_url=None, version='5.2.0'):
        """Load Dropzone's js resources with given version.

        .. versionadded:: 1.4.4

        :param js_url: The JS url for Dropzone.js.
        :param version: The version of Dropzone.js.
        """
        js_filename = 'dropzone.min.js'
        serve_local = current_app.config['DROPZONE_SERVE_LOCAL']

        if serve_local:
            js = '<script src="%s"></script>\n' % url_for('dropzone.static', filename=js_filename)
        else:
            js = '<script src="https://cdn.jsdelivr.net/npm/dropzone@%s/dist/%s"></script>\n' % (version, js_filename)

        if js_url:
            js = '<script src="%s"></script>\n' % js_url
        return Markup(js)

# === BLOCK 5 (label=lm, source_idx=line3212_lm, name=process_data) ===
def process_data(self, data):
        """Convert an unknown data input into a geojson dictionary."""
        if isinstance(data, dict):
            return data
        elif isinstance(data, str):
            return json.loads(data)
        elif isinstance(data, bytes):
            return json.loads(data.decode('utf-8'))
        else:
            raise TypeError("Data must be a dict, str, or bytes.")

# === BLOCK 6 (label=lm, source_idx=line735_lm, name=rgb_to_name) ===
def rgb_to_name(rgb_triplet, spec=u'css3'):
    """
    Convert a 3-tuple of integers, suitable for use in an ``rgb()``
    color triplet, to its corresponding normalized color name, if any
    such name exists.

    The optional keyword argument ``spec`` determines which
    specification's list of color names will be used; valid values are
    ``html4``, ``css2``, ``css21`` and ``css3``, and the default is
    ``css3``.

    If there is no matching name, ``ValueError`` is raised.

    """
    if spec == 'html4':
        return _html4_names.get(rgb_triplet)
    elif spec == 'css2':
        return _css2_names.get(rgb_triplet)
    elif spec == 'css21':
        return _css21_names.get(rgb_triplet)
    elif spec == 'css3':
        return _css3_names.get(rgb_triplet)
    else:
        raise ValueError("Unknown specification '%s'" % spec)
