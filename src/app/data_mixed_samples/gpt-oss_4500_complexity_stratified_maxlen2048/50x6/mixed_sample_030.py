# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line1686_lm, name=has_child_objective_banks) ===
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
        if objective_bank_id is None:
            raise NullArgument()
        try:
            # Assume a hierarchy session provides child IDs for a given parent ID
            child_ids = self._objective_bank_hierarchy_session.get_child_objective_bank_ids(objective_bank_id)
            return bool(child_ids)
        except NotFound:
            raise
        except PermissionDenied:
            raise
        except Exception as e:
            raise OperationFailed(str(e))

# === BLOCK 2 (label=human, source_idx=line18_human, name=log_stop) ===
def log_stop(self, start):
        """log a summary line on how the request went"""
        if not logger.isEnabledFor(logging.INFO): return

        stop = time.time()
        get_elapsed = lambda start, stop, multiplier, rnd: round(abs(stop - start) * float(multiplier), rnd)
        elapsed = get_elapsed(start, stop, 1000.00, 1)
        total = "%0.1f ms" % (elapsed)
        logger.info("RESPONSE {} {} in {}".format(self.response.code, self.response.status, total))

# === BLOCK 3 (label=lm, source_idx=line6225_lm, name=list_returners) ===
def list_returners(*args):
    """
    List the returners loaded on the minion

    .. versionadded:: 2014.7.0

    CLI Example:

    .. code-block:: bash

        salt '*' sys.list_returners

    Returner names can be specified as globs.

    .. versionadded:: 2015.5.0

    .. code-block:: bash

        salt '*' sys.list_returners 's*'

    """

# === BLOCK 4 (label=lm, source_idx=line2820_lm, name=_axis_properties) ===
def _axis_properties(self, axis, title_size, title_offset, label_angle,
                         label_align, color):
        """Assign axis properties"""

# === BLOCK 5 (label=human, source_idx=line5497_human, name=postage_update) ===
def postage_update(self, tid, post_fee, session):
        """taobao.trade.postage.update 修改订单邮费价格

        修改订单邮费接口，通过传入订单编号和邮费价格，修改订单的邮费，返回修改时间modified,邮费post_fee,总费用total_fee。"""
        request = TOPRequest('taobao.trade.postage.update')
        request['tid'] = tid
        request['post_fee'] = post_fee
        self.create(self.execute(request, session)['trade'])
        return self

# === BLOCK 6 (label=human, source_idx=line1502_human, name=_get_str) ===
def _get_str(self, f, off):
        """
        Convenience function to quickly pull out strings.
        """
        f.seek(off)
        return f.read(2 * struct.unpack('>B', f.read(1))[0]).decode('utf-16')
