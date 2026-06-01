# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line1270_lm, name=summarize_failing_examples) ===
def summarize_failing_examples(app, exception):
    """Collects the list of falling examples and prints them with a traceback.

    Raises ValueError if there where failing examples.
    """
    failing_examples = []
    for example in app.examples:
        try:
            example.run()
        except exception:
            failing_examples.append(example)
    if not failing_examples:
        raise ValueError("No failing examples found.")
    for example in failing_examples:
        print(f"Failed example: {example}")
        print(f"Traceback: {example.traceback}")

# === BLOCK 2 (label=human, source_idx=line245_human, name=handle_label) ===
def handle_label(self, label, **options):
        """
        Command handler.
        """
        if not hasattr(commands, 'sync_%s' % label):
            raise CommandError('"%s" is not a valid command.' % label)

        getattr(commands, 'sync_%s' % label)(**sanitize_command_options(options))

# === BLOCK 3 (label=lm, source_idx=line1434_lm, name=_breakup_gfe) ===
def _breakup_gfe(self, gfe):
        """
        creates GFE from HLA sequence and locus

        :param locus: string containing HLA locus.
        :param sequence: string containing sequence data.

        :return: GFEobject.
        """
        locus, sequence = gfe.split('*')
        return GFEobject(locus, sequence)

# === BLOCK 4 (label=human, source_idx=line3382_human, name=_build_file) ===
def _build_file(self, cif_str):
        """Build :class:`~nmrstarlib.nmrstarlib.CIFFile` object.

        :param cif_str: NMR-STAR-formatted string.
        :type cif_str: :py:class:`str` or :py:class:`bytes`
        :return: instance of :class:`~nmrstarlib.nmrstarlib.CIFFile`.
        :rtype: :class:`~nmrstarlib.nmrstarlib.CIFFile`
        """
        odict = self
        comment_count = 0
        loop_count = 0
        lexer = bmrblex(cif_str)
        token = next(lexer)

        while token != u"":
            try:
                if token[0:5] == u"data_":
                    self.id = token[5:]
                    self[u"data"] = self.id

                elif token.lstrip().startswith(u"#"):
                    odict[u"comment_{}".format(comment_count)] = token
                    comment_count += 1

                elif token[0] == u"_":
                    # This strips off the leading underscore of tagnames for readability
                    value = next(lexer)
                    odict[token[1:]] = value

                elif token == u"loop_":
                    odict[u"loop_{}".format(loop_count)] = self._build_loop(lexer)
                    loop_count += 1

                else:
                    print("Error: Invalid token {}".format(token), file=sys.stderr)
                    print("In _build_file try block", file=sys.stderr)
                    raise InvalidToken("{}".format(token))

            except IndexError:
                print("Error: Invalid token {}".format(token), file=sys.stderr)
                print("In _build_file except block", file=sys.stderr)
                raise

            finally:
                token = next(lexer)
        return self

# === BLOCK 5 (label=lm, source_idx=line2290_lm, name=merge_leaderboards) ===
def merge_leaderboards(self, destination, keys, aggregate='SUM'):
        """
        Merge leaderboards given by keys with this leaderboard into a named destination leaderboard.

        @param destination [String] Destination leaderboard name.
        @param keys [Array] Leaderboards to be merged with the current leaderboard.
        @param options [Hash] Options for merging the leaderboards.
        """
        for key in keys:
            if aggregate == 'SUM':
                for user_id, score in self.redis.zscan_iter(key):
                    self.redis.zincrby(destination, user_id, score)
            elif aggregate == 'MAX':
                for user_id, score in self.redis.zscan_iter(key):
                    if self.redis.zscore(destination, user_id) < score:
                        self.redis.zadd(destination, {user_id: score})
            elif aggregate == 'MIN':
                for user_id, score in self.redis.zscan_iter(key):
                    if self.redis.zscore(destination, user_id) > score:
                        self.redis.zadd(destination, {user_id: score})
            else:
                raise ValueError("Invalid aggregate function: {}".format(aggregate))

# === BLOCK 6 (label=human, source_idx=line2722_human, name=restore_default) ===
def restore_default(self, key):
        """
        Restore (and return) default value for the specified key.

        This method will only work for a ConfigObj that was created
        with a configspec and has been validated.

        If there is no default value for this key, ``KeyError`` is raised.
        """
        default = self.default_values[key]
        dict.__setitem__(self, key, default)
        if key not in self.defaults:
            self.defaults.append(key)
        return default
