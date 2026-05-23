# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line1998_lm, name=set_local_interface) ===
def set_local_interface(self, value=None, default=False, disable=False):
        """Configures the mlag local-interface value

        Args:
            value (str): The value to configure the local-interface
            default (bool): Configures the local-interface using the
                default keyword
            disable (bool): Negates the local-interface using the no keyword

        Returns:
            bool: Returns True if the commands complete successfully
        """
        commands = []
        if default:
            commands.append('default local-interface')
        elif disable:
            commands.append('no local-interface')
        elif value:
            commands.append(f'local-interface {value}')
        else:
            return False
        return self.configure(commands)

# === BLOCK 2 (label=lm, source_idx=line948_lm, name=lindblad_operator) ===
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
    return A * rho * A.adjoint() - (A.adjoint() * A * rho + rho * A.adjoint() * A) / 2

# === BLOCK 3 (label=human, source_idx=line2016_human, name=exit) ===
def exit(exit_code=0):
  r"""A function to support exiting from exit hooks.

  Could also be used to exit from the calling scripts in a thread safe manner.
  """
  core.processExitHooks()

  if state.isExitHooked and not hasattr(sys, 'exitfunc'): # The function is called from the exit hook
    sys.stderr.flush()
    sys.stdout.flush()
    os._exit(exit_code) #pylint: disable=W0212

  sys.exit(exit_code)

# === BLOCK 4 (label=lm, source_idx=line72_lm, name=equals) ===
def equals(self, controller):
        """ Verify if the controller corresponds
            to the current one.

        """
        return self == controller

# === BLOCK 5 (label=human, source_idx=line461_human, name=getCipherText) ===
def getCipherText(self, iv, key, plaintext):
        """
        :type iv: bytearray
        :type key: bytearray
        :type plaintext: bytearray
        """
        cipher = AESCipher(key, iv)
        return cipher.encrypt(bytes(plaintext))

# === BLOCK 6 (label=human, source_idx=line2441_human, name=default) ===
def default(self):
        """Return last changes in truncated unified diff format"""
        output = ensure_unicode(self.git.log(
            '-1',
            '-p',
            '--no-color',
            '--format=%s',
        ).stdout)
        lines = output.splitlines()
        return u'\n'.join(
            itertools.chain(
                lines[:1],
                itertools.islice(
                    itertools.dropwhile(
                        lambda x: not x.startswith('+++'),
                        lines[1:],
                    ),
                    1,
                    None,
                ),
            )
        )
