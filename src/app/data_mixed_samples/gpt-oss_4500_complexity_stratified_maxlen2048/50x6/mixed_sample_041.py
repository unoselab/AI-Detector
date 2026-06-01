# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line5029_human, name=_post_data) ===
def _post_data(options=None, xml=None):
    """
    Post data to Nagios NRDP
    """
    params = {'token': options['token'].strip(), 'cmd': 'submitcheck', 'XMLDATA': xml}

    res = salt.utils.http.query(
        url=options['url'],
        method='POST',
        params=params,
        data='',
        decode=True,
        status=True,
        header_dict={},
        opts=__opts__,
    )

    if res.get('status', None) == salt.ext.six.moves.http_client.OK:
        if res.get('dict', None) and isinstance(res['dict'], list):
            _content = res['dict'][0]
            if _content.get('status', None):
                return True
            else:
                return False
        else:
            log.error('No content returned from Nagios NRDP.')
            return False
    else:
        log.error(
            'Error returned from Nagios NRDP. Status code: %s.',
            res.status_code
        )
        return False

# === BLOCK 2 (label=human, source_idx=line3481_human, name=commentdoc) ===
def commentdoc(text):
    """Returns a Doc representing a comment `text`. `text` is
    treated as words, and any whitespace may be used to break
    the comment to multiple lines."""
    if not text:
        raise ValueError(
            'Expected non-empty comment str, got {}'.format(repr(text))
        )

    commentlines = []
    for line in text.splitlines():
        alternating_words_ws = list(filter(None, WHITESPACE_PATTERN_TEXT.split(line)))
        starts_with_whitespace = bool(
            WHITESPACE_PATTERN_TEXT.match(alternating_words_ws[0])
        )

        if starts_with_whitespace:
            prefix = alternating_words_ws[0]
            alternating_words_ws = alternating_words_ws[1:]
        else:
            prefix = NIL

        if len(alternating_words_ws) % 2 == 0:
            # The last part must be whitespace.
            alternating_words_ws = alternating_words_ws[:-1]

        for idx, tup in enumerate(zip(alternating_words_ws, cycle([False, True]))):
            part, is_ws = tup
            if is_ws:
                alternating_words_ws[idx] = flat_choice(
                    when_flat=part,
                    when_broken=always_break(
                        concat([
                            HARDLINE,
                            '# ',
                        ])
                    )
                )

        commentlines.append(
            concat([
                '# ',
                prefix,
                fill(alternating_words_ws)
            ])
        )

    outer = identity

    if len(commentlines) > 1:
        outer = always_break

    return annotate(
        Token.COMMENT_SINGLE,
        outer(concat(intersperse(HARDLINE, commentlines)))
    )

# === BLOCK 3 (label=lm, source_idx=line2834_lm, name=reset_default) ===
def reset_default(verbose=False):
    """Remove custom.css and custom fonts"""
    import os
    import shutil
    from pathlib import Path

    base_path = Path.cwd()
    css_path = base_path / "custom.css"
    fonts_path = base_path / "fonts"

    removed = False

    if css_path.is_file():
        try:
            css_path.unlink()
            removed = True
            if verbose:
                print(f"Removed {css_path}")
        except Exception as e:
            if verbose:
                print(f"Failed to remove {css_path}: {e}")

    if fonts_path.is_dir():
        try:
            shutil.rmtree(fonts_path)
            removed = True
            if verbose:
                print(f"Removed {fonts_path}")
        except Exception as e:
            if verbose:
                print(f"Failed to remove {fonts_path}: {e}")

    return removed

# === BLOCK 4 (label=lm, source_idx=line2314_lm, name=link) ===
def link(self):
    """str: full path of the linked file entry."""
    import os
    try:
        target = os.readlink(self.path)
    except (AttributeError, OSError):
        # If self has no path attribute or not a symlink, return its own path if available
        return getattr(self, "path", None)
    if not os.path.isabs(target):
        target = os.path.normpath(os.path.join(os.path.dirname(self.path), target))
    return target

# === BLOCK 5 (label=human, source_idx=line4353_human, name=cumsum) ===
def cumsum(self, axis=0, *args, **kwargs):
        """
        Cumulative sum of non-NA/null values.

        When performing the cumulative summation, any non-NA/null values will
        be skipped. The resulting SparseSeries will preserve the locations of
        NaN values, but the fill value will be `np.nan` regardless.

        Parameters
        ----------
        axis : {0}

        Returns
        -------
        cumsum : SparseSeries
        """
        nv.validate_cumsum(args, kwargs)
        # Validate axis
        if axis is not None:
            self._get_axis_number(axis)

        new_array = self.values.cumsum()

        return self._constructor(
            new_array, index=self.index,
            sparse_index=new_array.sp_index).__finalize__(self)

# === BLOCK 6 (label=lm, source_idx=line3947_lm, name=create_scaling_policy) ===
def create_scaling_policy(self, scaling_policy):
        """
        Creates a new Scaling Policy.

        :type scaling_policy: :class:`boto.ec2.autoscale.policy.ScalingPolicy`
        :param scaling_policy: ScalingPolicy object.
        """
