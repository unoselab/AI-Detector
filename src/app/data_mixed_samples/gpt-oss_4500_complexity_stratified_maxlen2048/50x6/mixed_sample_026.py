# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line1686_human, name=has_child_objective_banks) ===
def has_child_objective_banks(self, objective_bank_id):
        """Tests if an objective bank has any children.

        arg:    objective_bank_id (osid.id.Id): the ``Id`` of an
                objective bank
        return: (boolean) - ``true`` if the ``objective_bank_id`` has
                children, ``false`` otherwise
        raise:  NotFound - ``objective_bank_id`` is not found
        raise:  NullArgument - ``objective_bank_id`` is ``null``
        raise:  OperationFailed - unable to complete request
        raise:  PermissionDenied - authorization failure
        *compliance: mandatory -- This method must be implemented.*

        """
        # Implemented from template for
        # osid.resource.BinHierarchySession.has_child_bins
        if self._catalog_session is not None:
            return self._catalog_session.has_child_catalogs(catalog_id=objective_bank_id)
        return self._hierarchy_session.has_children(id_=objective_bank_id)

# === BLOCK 2 (label=human, source_idx=line4755_human, name=run) ===
def run(self, n_steps=None):
        r"""
        Perform the algorithm

        Parameters
        ----------
        n_steps : int
            The number of throats to invaded during this step

        """
        if n_steps is None:
            n_steps = sp.inf

        queue = self.queue
        if len(queue) == 0:
            logger.warn('queue is empty, this network is fully invaded')
            return
        t_sorted = self['throat.sorted']
        t_order = self['throat.order']
        t_inv = self['throat.invasion_sequence']
        p_inv = self['pore.invasion_sequence']

        count = 0
        while (len(queue) > 0) and (count < n_steps):
            # Find throat at the top of the queue
            t = hq.heappop(queue)
            # Extract actual throat number
            t_next = t_sorted[t]
            t_inv[t_next] = self._tcount
            # If throat is duplicated
            while len(queue) > 0 and queue[0] == t:
                # Note: Preventing duplicate entries below might save some time
                t = hq.heappop(queue)
            # Find pores connected to newly invaded throat
            Ps = self.project.network['throat.conns'][t_next]
            # Remove already invaded pores from Ps
            Ps = Ps[p_inv[Ps] < 0]
            if len(Ps) > 0:
                p_inv[Ps] = self._tcount
                Ts = self.project.network.find_neighbor_throats(pores=Ps)
                Ts = Ts[t_inv[Ts] < 0]  # Remove invaded throats from Ts
                [hq.heappush(queue, T) for T in t_order[Ts]]
            count += 1
            self._tcount += 1
        self['throat.invasion_sequence'] = t_inv
        self['pore.invasion_sequence'] = p_inv

# === BLOCK 3 (label=lm, source_idx=line5661_lm, name=get_chat_member) ===
def get_chat_member(self, chat_id, user_id):
        """
        Use this method to get information about a member of a chat. Returns a ChatMember object on success.
        :param chat_id:
        :param user_id:
        :return:
        """
        payload = {
            "chat_id": chat_id,
            "user_id": user_id,
        }
        return self._post("getChatMember", payload)

# === BLOCK 4 (label=human, source_idx=line3162_human, name=DP_calc) ===
def DP_calc(TPR, TNR):
    """
    Calculate DP (Discriminant power).

    :param TNR: specificity or true negative rate
    :type TNR : float
    :param TPR: sensitivity, recall, hit rate, or true positive rate
    :type TPR : float
    :return: DP as float
    """
    try:
        X = TPR / (1 - TPR)
        Y = TNR / (1 - TNR)
        return (math.sqrt(3) / math.pi) * (math.log(X, 10) + math.log(Y, 10))
    except Exception:
        return "None"

# === BLOCK 5 (label=lm, source_idx=line1899_lm, name=findspan) ===
def findspan(self, *words):
        """Returns the span element which spans over the specified words or morphemes.

        See also:
            :meth:`Word.findspans`
        """

# === BLOCK 6 (label=lm, source_idx=line1463_lm, name=__getRefererUrl) ===
def __getRefererUrl(self, url=None):
        """
        gets the referer url for the token handler
        """
        import urllib.parse

        if url:
            return url

        req = getattr(self, "request", None)
        if not req:
            return None

        referer = req.headers.get("Referer")
        if not referer:
            return None

        parsed = urllib.parse.urlparse(referer)
        if not parsed.scheme:
            base = getattr(req, "host_url", "")
            referer = urllib.parse.urljoin(base, referer)

        return referer
