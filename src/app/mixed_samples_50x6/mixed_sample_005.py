# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line2410_human, name=from_bytes) ===
def from_bytes(rawbytes):
        """
        Takes a byte string as a parameter and returns a list of
        IPOption objects.
        """
        ipopts = IPOptionList()

        i = 0
        while i < len(rawbytes):
            opttype = rawbytes[i]
            optcopied = opttype >> 7         # high order 1 bit
            optclass = (opttype >> 5) & 0x03 # next 2 bits
            optnum = opttype & 0x1f          # low-order 5 bits are optnum
            optnum = IPOptionNumber(optnum)
            obj = IPOptionClasses[optnum]()
            eaten = obj.from_bytes(rawbytes[i:])
            i += eaten
            ipopts.append(obj)
        return ipopts

# === BLOCK 2 (label=lm, source_idx=line368_lm, name=partial_update) ===
def partial_update(self, request, *args, **kwargs):
    """ We do not include the mixin as we want only PATCH and no PUT """
    instance = self.get_object()
    serializer = self.get_serializer(instance, data=request.data, partial=True)
    serializer.is_valid(raise_exception=True)
    self.perform_update(serializer)
    return Response(serializer.data)

# === BLOCK 3 (label=human, source_idx=line1493_human, name=create) ===
def create(self, message, mid=None, age=60, force=True):
        """
        create session
            force if you pass `force = False`, it may raise SessionError
                due to duplicate message id
        """
        with self.session_lock:
            if not hasattr(message, "id"):
                message.__setattr__("id", "event-%s" % (uuid.uuid4().hex,))
            if self.session_list.get(message.id, None) is not None:
                if force is False:
                    raise SessionError("Message id: %s duplicate!" %
                                       message.id)
                else:
                    message = Message(message.to_dict(), generate_id=True)

            session = {
                "status": Status.CREATED,
                "message": message,
                "age": age,
                "mid": mid,
                "created_at": time(),
                "is_published": Event(),
                "is_resolved": Event()
            }
            self.session_list.update({
                message.id: session
            })

            return session

# === BLOCK 4 (label=lm, source_idx=line342_lm, name=movie) ===
def movie(args):
    """
    %prog movie test.tour test.clm ref.contigs.last

    Plot optimization history.
    """
    import os
    import sys
    import subprocess

    if len(args)!= 3:
        sys.stderr.write("ERROR: Incorrect number of arguments\n")
        sys.exit(1)

    test_tour = args[0]
    test_clm = args[1]
    ref_contigs_last = args[2]

    if not os.path.isfile(test_tour) or not os.path.isfile(test_clm) or not os.path.isfile(ref_contigs_last):
        sys.stderr.write("ERROR: One or more input files do not exist\n")
        sys.exit(1)

    command = f"t_plotter -tour {test_tour} -clm {test_clm} -ref {ref_contigs_last}"
    subprocess.call(command, shell=True)

# === BLOCK 5 (label=human, source_idx=line1154_human, name=filter_by_maf) ===
def filter_by_maf(min_maf=0.01):
    """
    return function that filters by maf
    (takes minimum maf, default is 0.01)
    """

    def f(G, bim):
        maf = 0.5 * G.mean(0)
        maf[maf > 0.5] = 1.0 - maf[maf > 0.5]
        Isnp = maf > min_maf
        G_out = G[:, Isnp]
        bim_out = bim[Isnp]
        return G_out, bim_out

    return f

# === BLOCK 6 (label=lm, source_idx=line2813_lm, name=_get_names) ===
def _get_names(self):
        """Get the list of first names.

        :return: A list of first name entries.
        """
        return [self.first_name]
