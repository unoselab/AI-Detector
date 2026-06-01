# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line3105_lm, name=remove) ===
def remove(self, fieldspec):
        """
        Removes fields or subfields according to `fieldspec`.

        If a non-control field subfield removal leaves no other subfields,
        delete the field entirely.
        """
        fields = self.fields
        for field in fields:
            if field.tag in fieldspec:
                if field.tag in MARC21_CONTROL_FIELDS:
                    continue
                for subfield in field.subfields:
                    if subfield.code in fieldspec[field.tag]:
                        field.remove_subfield(subfield.code)
                if not field.subfields:
                    self.remove_field(field)

# === BLOCK 2 (label=lm, source_idx=line1311_lm, name=send) ===
def send(self, url, data, headers):
        """
        Sends a request to an SQS queue -- to be later popped off
        later for submission into Sentry.
        Note: This will simply raise any Boto ClientErrors that are encountered.
        """
        self.logger.debug("Sending data to SQS: %s", data)
        self.sqs_client.send_message(
            QueueUrl=url,
            MessageBody=data,
            MessageAttributes=headers
        )

# === BLOCK 3 (label=lm, source_idx=line1323_lm, name=clear) ===
def clear(self, pat=None):
        """
        Minor diversion with built-in dict here;  clear can take a glob
        style expression and remove keys based on that expression.
        """
        if pat is None:
            self.clear()
        else:
            for k in self.keys():
                if fnmatch.fnmatch(k, pat):
                    del self[k]

# === BLOCK 4 (label=lm, source_idx=line6431_lm, name=add_sub_directory) ===
def add_sub_directory(self, key, path):
        """Adds a sub-directory to the results directory.

        Parameters
        ----------
        key: str
            A look-up key for the directory path.
        path: str
            The relative path from the root of the results directory to the sub-directory.

        Returns
        -------
        str:
            The absolute path to the sub-directory.
        """
        sub_dir = os.path.join(self.path, path)
        if not os.path.exists(sub_dir):
            os.makedirs(sub_dir)
        self.sub_dirs[key] = sub_dir
        return sub_dir

# === BLOCK 5 (label=lm, source_idx=line1805_lm, name=fetch) ===
def fetch(self, _filter=None, ignore_incremental=False):
        """ Fetch the items from raw or enriched index. An optional _filter
        could be provided to filter the data collected """
        if self.raw_index:
            return self.fetch_from_raw_index(_filter)
        else:
            return self.fetch_from_enriched_index(_filter, ignore_incremental)

# === BLOCK 6 (label=lm, source_idx=line4836_lm, name=update_pidfile) ===
def update_pidfile(pidfile):
    """Update pidfile.

    Notice:
        We should call this function only after we have successfully acquired
        a lock and never before. It exits main program if it fails to parse
        and/or write pidfile.

    Arguments:
        pidfile (str): pidfile to update

    """
    try:
        with open(pidfile, 'w') as f:
            f.write(str(os.getpid()))
    except IOError:
        print('Failed to write pidfile: {}'.format(pidfile))
        sys.exit(1)
