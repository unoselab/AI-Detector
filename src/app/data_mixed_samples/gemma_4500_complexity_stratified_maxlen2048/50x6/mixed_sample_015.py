# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line2739_lm, name=handleOneNodeMsg) ===
def handleOneNodeMsg(self, wrappedMsg):
        """
        Validate and process one message from a node.

        :param wrappedMsg: Tuple of message and the name of the node that sent
        the message
        """
        msg, node_name = wrappedMsg
        if msg is None or node_name is None:
            return False

        try:
            self.process_message(node_name, msg)
            return True
        except Exception:
            return False

# === BLOCK 2 (label=human, source_idx=line2156_human, name=_result) ===
def _result(self):  # type: () -> SolverResult
        """
        Creates a #SolverResult from the decisions in _solution
        """
        decisions = self._solution.decisions

        return SolverResult(
            self._root,
            [p for p in decisions if not p.is_root()],
            self._solution.attempted_solutions,
        )

# === BLOCK 3 (label=lm, source_idx=line5775_lm, name=register_rml) ===
def register_rml(self, filepath, **kwargs):
        """
        Registers the filepath for an rml mapping

        Args:
        -----
            filepath: the path the rml file
        """
        if not hasattr(self, 'rml_mappings'):
            self.rml_mappings = {}
        self.rml_mappings[filepath] = kwargs

# === BLOCK 4 (label=human, source_idx=line3966_human, name=addStyle) ===
def addStyle(w):
    """
    Styles the GUI: global fonts and colours.

    Parameters
    ----------
    w : tkinter.tk
        widget element to style
    """
    # access global container in root widget
    root = get_root(w)
    g = root.globals
    fsize = g.cpars['font_size']
    family = g.cpars['font_family']

    # Default font
    g.DEFAULT_FONT = font.nametofont("TkDefaultFont")
    g.DEFAULT_FONT.configure(size=fsize, weight='bold', family=family)
    w.option_add('*Font', g.DEFAULT_FONT)

    # Menu font
    g.MENU_FONT = font.nametofont("TkMenuFont")
    g.MENU_FONT.configure(family=family)
    w.option_add('*Menu.Font', g.MENU_FONT)

    # Entry font
    g.ENTRY_FONT = font.nametofont("TkTextFont")
    g.ENTRY_FONT.configure(size=fsize, family=family)
    w.option_add('*Entry.Font', g.ENTRY_FONT)

    # position and size
    # root.geometry("320x240+325+200")

    # Default colours. Note there is a difference between
    # specifying 'background' with a capital B or lowercase b
    w.option_add('*background', g.COL['main'])
    w.option_add('*HighlightBackground', g.COL['main'])
    w.config(background=g.COL['main'])

# === BLOCK 5 (label=human, source_idx=line5456_human, name=strToTempfile) ===
def strToTempfile(s, suffix=None, prefix=None, dir=None, binary=False):
    """Create a new tempfile, write ``s`` to it and return the filename.
    `suffix`, `prefix` and `dir` are like in `tempfile.mkstemp`.
    """
    fd, filename = tempfile.mkstemp(**dict((k,v) for (k,v) in
                                           [('suffix',suffix),('prefix',prefix),('dir', dir)]
                                           if v is not None))
    spitOut(s, fd, binary)
    return filename

# === BLOCK 6 (label=lm, source_idx=line1012_lm, name=getEPrintURL) ===
def getEPrintURL(self, CorpNum, MgtKey, UserID=None):
        """ 공급받는자용 인쇄 URL 확인
            args
                CorpNum : 팝빌회원 사업자번호
                MgtKey : 문서관리번호
                UserID : 팝빌회원 아이디
            return
                팝빌 URL as str
            raise
                PopbillException
        """
        params = {
            'CorpNum': CorpNum,
            'MgtKey': MgtKey
        }
        if UserID:
            params['UserID'] = UserID

        response = self.send_request('getEPrintURL', params)
        return response['Code'] == '0000' and response.get('URL', '') or self._handle_error(response)
