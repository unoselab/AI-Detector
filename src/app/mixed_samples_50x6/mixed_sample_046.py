# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line2736_lm, name=link_pyqt) ===
def link_pyqt(sys_python, venv_python):
    """Symlink the systemwide PyQt/sip into the venv."""
    sys_pyqt_path = os.path.join(sys_python, 'lib', 'python3.8','site-packages')
    venv_pyqt_path = os.path.join(venv_python, 'lib', 'python3.8','site-packages')
    os.symlink(sys_pyqt_path, venv_pyqt_path)

# === BLOCK 2 (label=lm, source_idx=line461_lm, name=getCipherText) ===
def getCipherText(self, iv, key, plaintext):
        """
        :type iv: bytearray
        :type key: bytearray
        :type plaintext: bytearray
        """
        algorithm = algorithms.AES(key)
        mode = modes.CBC(iv)
        cipher = Cipher(algorithm, mode)
        encryptor = cipher.encryptor()
        padder = padding.PKCS7(algorithm.block_size).padder()
        padded_plaintext = padder.update(plaintext) + padder.finalize()
        ciphertext = encryptor.update(padded_plaintext) + encryptor.finalize()

        return ciphertext

# === BLOCK 3 (label=human, source_idx=line2711_human, name=fpr) ===
def fpr(y, z):
    """False positive rate `fp / (fp + tn)`
    """
    tp, tn, fp, fn = contingency_table(y, z)
    return fp / (fp + tn)

# === BLOCK 4 (label=human, source_idx=line2834_human, name=_compute_edges) ===
def _compute_edges(self):
        """Compute the edges of the current surface.

        Returns:
            Tuple[~curve.Curve, ~curve.Curve, ~curve.Curve]: The edges of
            the surface.
        """
        nodes1, nodes2, nodes3 = _surface_helpers.compute_edge_nodes(
            self._nodes, self._degree
        )
        edge1 = _curve_mod.Curve(nodes1, self._degree, _copy=False)
        edge2 = _curve_mod.Curve(nodes2, self._degree, _copy=False)
        edge3 = _curve_mod.Curve(nodes3, self._degree, _copy=False)
        return edge1, edge2, edge3

# === BLOCK 5 (label=human, source_idx=line2736_human, name=link_pyqt) ===
def link_pyqt(sys_python, venv_python):
    """Symlink the systemwide PyQt/sip into the venv."""
    real_site = site_dir(sys_python)
    venv_site = site_dir(venv_python)

    for f in ['sip.so', 'PyQt5']:
        (venv_site/f).symlink_to(real_site/f)

# === BLOCK 6 (label=lm, source_idx=line2016_lm, name=exit) ===
def exit(exit_code=0):
  r"""A function to support exiting from exit hooks.

  Could also be used to exit from the calling scripts in a thread safe manner.
  """
  sys.exit(exit_code)
