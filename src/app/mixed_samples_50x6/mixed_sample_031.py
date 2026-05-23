# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line1064_lm, name=get) ===
def get(url: str, *args, **kwargs) -> tuple:
    """Send a GET request. Returns a dict or :class:`requests.Response <Response>`"""
    response = requests.get(url, *args, **kwargs)
    if response.headers['Content-Type'] == 'application/json':
        return response.json()
    else:
        return response

# === BLOCK 2 (label=human, source_idx=line2825_human, name=pex_hash) ===
def pex_hash(cls, d):
    """Return a reproducible hash of the contents of a directory."""
    names = sorted(f for f in cls._iter_files(d) if not (f.endswith('.pyc') or f.startswith('.')))
    def stream_factory(name):
      return open(os.path.join(d, name), 'rb')  # noqa: T802
    return cls._compute_hash(names, stream_factory)

# === BLOCK 3 (label=human, source_idx=line948_human, name=lindblad_operator) ===
def lindblad_operator(A, rho):
    r"""This function returns the action of a Lindblad operator A on a density
    matrix rho. This is defined as :
        L(A,rho) = A*rho*A.adjoint()
                 - (A.adjoint()*A*rho + rho*A.adjoint()*A)/2.

    >>> rho=define_density_matrix(3)
    >>> lindblad_operator( ketbra(1,2,3) ,rho )
    Matrix([
    [   rho22, -rho12/2,        0],
    [-rho21/2,   -rho22, -rho23/2],
    [       0, -rho32/2,        0]])

    """
    return A*rho*A.adjoint() - (A.adjoint()*A*rho + rho*A.adjoint()*A)/2

# === BLOCK 4 (label=human, source_idx=line1702_human, name=get_used_key_frames) ===
def get_used_key_frames(self):
        """Returns a list of the keyframes used by this channel, sorted with
        time. Each element in the list is a tuple. The first element is the
        key_name and the second is the channel data at that keyframe."""

        skl = self.key_frame_list.sorted_key_list()
        # each element in used_key_frames is a tuple (key_name, key_dict)
        used_key_frames = []
        for kf in skl:
            if kf in self.dct['keys']:
                used_key_frames.append((kf, self.dct['keys'][kf]))
        return used_key_frames

# === BLOCK 5 (label=lm, source_idx=line1044_lm, name=msg) ===
def msg(self, message, title=None, title_color=None, color='BLUE', ident=0):
        """
        Hint message.

        :param message:
        :param title:
        :param title_color:
        :param color:
        :param ident:
        :return:
        """
        if title:
            print(f'{title}: {message}')
        else:
            print(message)

# === BLOCK 6 (label=lm, source_idx=line2487_lm, name=load_and_set_file_content) ===
def load_and_set_file_content(self, file_system_path):
        """ Implements the abstract method of the ExternalEditor class.
        """
        with open(file_system_path, 'r') as file:
            content = file.read()
        self.set_file_content(content)
