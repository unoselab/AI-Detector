# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line3045_lm, name=expand_paths) ===
def expand_paths(inputs):
    """Yield sys.path directories that might contain "old-style" packages"""
    for path in sys.path:
        if os.path.isdir(path):
            yield path

# === BLOCK 2 (label=human, source_idx=line887_human, name=add_controls) ===
def add_controls(self, env, target_name='control',
                     file_name='control.json',
                     encoder_cls=SConsEncoder):
        """
        Adds a target to build a control file at each of the current leaves.

        :param env: SCons Environment object
        :param target_name: Name for target in nest
        :param file_name: Name for output file.
        """
        if not HAS_SCONS:
            raise ImportError('SCons not available')

        @self.add_target(name=target_name)
        def control(outdir, c):
            return env.Command(os.path.join(outdir, file_name),
                               [],
                               action=_create_control_file,
                               control_dict=c,
                               encoder_cls=encoder_cls)

# === BLOCK 3 (label=lm, source_idx=line4463_lm, name=getEditPerson) ===
def getEditPerson(self, name):
        """
        Get an L{EditPersonView} for editing the person named C{name}.

        @param name: A person name.
        @type name: C{unicode}

        @rtype: L{EditPersonView}
        """
        person = self.model.getPerson(name)
        return EditPersonView(person)

# === BLOCK 4 (label=human, source_idx=line3982_human, name=_create_bv_circuit) ===
def _create_bv_circuit(self, bit_map: Dict[str, str]) -> Program:
        """
        Implementation of the Bernstein-Vazirani Algorithm.

        Given a list of input qubits and an ancilla bit, all initially in the
        :math:`\\vert 0\\rangle` state, create a program that can find :math:`\\vec{a}` with one
        query to the given oracle.

        :param Dict[String, String] bit_map: truth-table of a function for Bernstein-Vazirani with
            the keys being all possible bit vectors strings and the values being the function values
        :rtype: Program
        """
        unitary, _ = self._compute_unitary_oracle_matrix(bit_map)
        full_bv_circuit = Program()

        full_bv_circuit.defgate("BV-ORACLE", unitary)

        # Put ancilla bit into minus state
        full_bv_circuit.inst(X(self.ancilla), H(self.ancilla))

        full_bv_circuit.inst([H(i) for i in self.computational_qubits])
        full_bv_circuit.inst(
            tuple(["BV-ORACLE"] + sorted(self.computational_qubits + [self.ancilla], reverse=True)))
        full_bv_circuit.inst([H(i) for i in self.computational_qubits])
        return full_bv_circuit

# === BLOCK 5 (label=human, source_idx=line2596_human, name=__update_service_status) ===
def __update_service_status(self, statuscode):
        """Set the internal status of the service object, and notify frontend."""
        if self.__service_status != statuscode:
            self.__service_status = statuscode
            self.__send_service_status_to_frontend()

# === BLOCK 6 (label=lm, source_idx=line4418_lm, name=find_module_defining_flag) ===
def find_module_defining_flag(self, flagname, default=None):
    """Return the name of the module defining this flag, or default.

    Args:
      flagname: str, name of the flag to lookup.
      default: Value to return if flagname is not defined. Defaults
          to None.

    Returns:
      The name of the module which registered the flag with this name.
      If no such module exists (i.e. no flag with this name exists),
      we return default.
    """
    for module_name, module_flags in self._modules_flags_dict.items():
        if flagname in module_flags:
            return module_name
    return default
