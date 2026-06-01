# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line7502_human, name=_labels_from_pyclusters) ===
def _labels_from_pyclusters(self):
        """
        Computes and returns the list of labels indicating the data points and the corresponding cluster ids.

        :return: The list of labels
        """
        clusters = self.model.get_clusters()
        labels = []
        for i in range(0, len(clusters)):
            for j in clusters[i]:
                labels.insert(int(j), i)
        return labels

# === BLOCK 2 (label=lm, source_idx=line2229_lm, name=add_or_update) ===
def add_or_update(self, app_id, value):
        """
        Adding or updating the evalution.
        :param app_id:  the ID of the post.
        :param value: the evaluation
        :return:  in JSON format.
        """
        try:
            app = self.get_app(app_id)
            app.eval = value
            app.save()
            return app.to_json()
        except:
            return None

# === BLOCK 3 (label=human, source_idx=line7904_human, name=setposition) ===
def setposition(self, position):
        """
        The move format is in long algebraic notation.

        Takes list of stirngs = ['e2e4', 'd7d5']
        OR
        FEN = 'rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1'
        """
        try:
            if isinstance(position, list):
                self.send('position startpos moves {}'.format(
                    self.__listtostring(position)))
                self.isready()
            elif re.match('\s*^(((?:[rnbqkpRNBQKP1-8]+\/){7})[rnbqkpRNBQKP1-8]+)\s([b|w])\s([K|Q|k|q|-]{1,4})\s(-|[a-h][1-8])\s(\d+\s\d+)$', position):
                regexList = re.match('\s*^(((?:[rnbqkpRNBQKP1-8]+\/){7})[rnbqkpRNBQKP1-8]+)\s([b|w])\s([K|Q|k|q|-]{1,4})\s(-|[a-h][1-8])\s(\d+\s\d+)$', position).groups()
                fen = regexList[0].split("/")
                if len(fen) != 8:
                    raise ValueError("expected 8 rows in position part of fen: {0}".format(repr(fen)))

                for fenPart in fen:
                    field_sum = 0
                    previous_was_digit, previous_was_piece = False, False

                    for c in fenPart:
                        if c in ["1", "2", "3", "4", "5", "6", "7", "8"]:
                            if previous_was_digit:
                                raise ValueError("two subsequent digits in position part of fen: {0}".format(repr(fen)))
                            field_sum += int(c)
                            previous_was_digit = True
                            previous_was_piece = False
                        elif c == "~":
                            if not previous_was_piece:
                                raise ValueError("~ not after piece in position part of fen: {0}".format(repr(fen)))
                            previous_was_digit, previous_was_piece = False, False
                        elif c.lower() in ["p", "n", "b", "r", "q", "k"]:
                            field_sum += 1
                            previous_was_digit = False
                            previous_was_piece = True
                        else:
                            raise ValueError("invalid character in position part of fen: {0}".format(repr(fen)))

                    if field_sum != 8:
                        raise ValueError("expected 8 columns per row in position part of fen: {0}".format(repr(fen)))  
                self.send('position fen {}'.format(position))
                self.isready()
            else: raise ValueError("fen doesn`t match follow this example: rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1 ")  

        except ValueError as e:
            print('\nCheck position correctness\n')
            sys.exit(e.message)

# === BLOCK 4 (label=human, source_idx=line3165_human, name=walk) ===
def walk(self, top, file_list={}):
        """Walks the walk. nah, seriously: reads the file and stores a hashkey
        corresponding to its content."""
        for root, dirs, files in os.walk(top, topdown=False):
            if os.path.basename(root) in self.ignore_dirs:
                # Do not dig in ignored dirs
                continue

            for name in files:
                full_path = os.path.join(root, name)
                if self.include(full_path):
                    if os.path.isfile(full_path):
                        # preventing fail if the file vanishes
                        content = open(full_path).read()
                        hashcode = hashlib.sha224(content).hexdigest()
                        file_list[full_path] = hashcode
            for name in dirs:
                if name not in self.ignore_dirs:
                    self.walk(os.path.join(root, name), file_list)
        return file_list

# === BLOCK 5 (label=lm, source_idx=line4997_lm, name=extract) ===
def extract(what, calc_id, webapi=True):
    """
    Extract an output from the datastore and save it into an .hdf5 file.
    By default uses the WebAPI, otherwise the extraction is done locally.
    """
    if webapi:
        return _extract_webapi(what, calc_id)
    else:
        return _extract_local(what, calc_id)

# === BLOCK 6 (label=lm, source_idx=line7974_lm, name=GetPattern) ===
def GetPattern(self):
    """Return a tuple of Stop objects, in the order visited"""
    return self.pattern
