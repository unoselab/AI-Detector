# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line328_human, name=login_user) ===
def login_user(user, remember=None):
    """Perform the login routine.

    If SECURITY_TRACKABLE is used, make sure you commit changes after this
    request (i.e. ``app.security.datastore.commit()``).

    :param user: The user to login
    :param remember: Flag specifying if the remember cookie should be set.
                     Defaults to ``False``
    """

    if remember is None:
        remember = config_value('DEFAULT_REMEMBER_ME')

    if not _login_user(user, remember):  # pragma: no cover
        return False

    if _security.trackable:
        remote_addr = request.remote_addr or None  # make sure it is None

        old_current_login, new_current_login = (
            user.current_login_at, _security.datetime_factory()
        )
        old_current_ip, new_current_ip = user.current_login_ip, remote_addr

        user.last_login_at = old_current_login or new_current_login
        user.current_login_at = new_current_login
        user.last_login_ip = old_current_ip
        user.current_login_ip = new_current_ip
        user.login_count = user.login_count + 1 if user.login_count else 1

        _datastore.put(user)

    identity_changed.send(current_app._get_current_object(),
                          identity=Identity(user.id))
    return True

# === BLOCK 2 (label=lm, source_idx=line2662_lm, name=connection) ===
def connection(self, shareable=True):
        """Get a steady, cached DB-API 2 connection from the pool.

        If shareable is set and the underlying DB-API 2 allows it,
        then the connection may be shared with other threads.

        """
        return self._pool.connection(shareable=shareable)

# === BLOCK 3 (label=lm, source_idx=line211_lm, name=openTypeHheaCaretSlopeRiseFallback) ===
def openTypeHheaCaretSlopeRiseFallback(info):
    """
    Fallback to *openTypeHheaCaretSlopeRise*. If the italicAngle is zero,
    return 1. If italicAngle is non-zero, compute the slope rise from the
    complementary openTypeHheaCaretSlopeRun, if the latter is defined.
    Else, default to an arbitrary fixed reference point (1000).
    """
    if info.italicAngle == 0:
        return 1
    elif info.openTypeHheaCaretSlopeRun is not None:
        return info.openTypeHheaCaretSlopeRun / info.italicAngle
    else:
        return 1000

# === BLOCK 4 (label=human, source_idx=line1057_human, name=one_vertical_total_stress) ===
def one_vertical_total_stress(self, z_c):
        """
        Determine the vertical total stress at a single depth z_c.

        :param z_c: depth from surface
        """
        total_stress = 0.0
        depths = self.depths
        end = 0
        for layer_int in range(1, len(depths) + 1):
            l_index = layer_int - 1
            if z_c > depths[layer_int - 1]:
                if l_index < len(depths) - 1 and z_c > depths[l_index + 1]:
                    height = depths[l_index + 1] - depths[l_index]
                    bottom_depth = depths[l_index + 1]
                else:
                    end = 1
                    height = z_c - depths[l_index]
                    bottom_depth = z_c

                if bottom_depth <= self.gwl:
                    total_stress += height * self.layer(layer_int).unit_dry_weight
                else:
                    if self.layer(layer_int).unit_sat_weight is None:
                        raise AnalysisError("Saturated unit weight not defined for layer %i." % layer_int)
                    sat_height = bottom_depth - max(self.gwl, depths[l_index])
                    dry_height = height - sat_height
                    total_stress += dry_height * self.layer(layer_int).unit_dry_weight + \
                                    sat_height * self.layer(layer_int).unit_sat_weight
            else:
                end = 1
            if end:
                break
        return total_stress

# === BLOCK 5 (label=lm, source_idx=line1493_lm, name=create) ===
def create(self, message, mid=None, age=60, force=True):
        """
        create session
            force if you pass `force = False`, it may raise SessionError
                due to duplicate message id
        """
        if not force and mid in self.sessions:
            raise SessionError("Duplicate message id")
        self.sessions[mid] = {
            "message": message,
            "age": age
        }

# === BLOCK 6 (label=human, source_idx=line168_human, name=collect_spans) ===
def collect_spans(ast: AST) -> List[Tuple[str, Tuple[int, int]]]:
    """Collect flattened list of spans of BEL syntax types

    Provide simple list of BEL syntax type spans for highlighting.
    Function names, NSargs, NS prefix, NS value and StrArgs will be
    tagged.

    Args:
        ast: AST of BEL assertion

    Returns:
        List[Tuple[str, Tuple[int, int]]]: list of span objects (<type>, (<start>, <end>))
    """

    spans = []

    if ast.get("subject", False):
        spans.extend(collect_spans(ast["subject"]))

    if ast.get("object", False):
        spans.extend(collect_spans(ast["object"]))

    if ast.get("nested", False):
        spans.extend(collect_spans(ast["nested"]))

    if ast.get("function", False):
        log.debug(f"Processing function")
        spans.append(("Function", ast["function"]["name_span"]))
        log.debug(f"Spans: {spans}")

    if ast.get("args", False):
        for idx, arg in enumerate(ast["args"]):
            log.debug(f"Arg  {arg}")

            if arg.get("function", False):
                log.debug(f"Recursing on arg function")
                results = collect_spans(arg)
                log.debug(f"Results {results}")
                spans.extend(results)  # Recurse arg function
            elif arg.get("nsarg", False):
                log.debug(f"Processing NSArg   Arg {arg}")
                spans.append(("NSArg", arg["span"]))
                spans.append(("NSPrefix", arg["nsarg"]["ns_span"]))
                spans.append(("NSVal", arg["nsarg"]["ns_val_span"]))
            elif arg["type"] == "StrArg":
                spans.append(("StrArg", arg["span"]))

    log.debug(f"Spans: {spans}")
    return spans
