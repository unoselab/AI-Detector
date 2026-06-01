# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line6677_lm, name=emitGeometryChanged) ===
def emitGeometryChanged( self, point = None ):
        """
        Emits the geometryChanged signal, provided the dispatcher's \
        signals are not currently blocked.  If the point value is not \
        provided, the object's current position will be used.

        :param      point      | <QPointF> || None

        :return     <bool> emitted
        """

        if point is None:
            point = self.pos()

        if self.dispatcher.signalsBlocked():
            return False

        return self.emit( QtCore.SIGNAL( 'geometryChanged( QPointF )' ), point )

# === BLOCK 2 (label=human, source_idx=line834_human, name=send) ===
def send(self, message, _sender=None):
        """Sends a message to the actor represented by this `Ref`."""
        if not _sender:
            context = get_context()
            if context:
                _sender = context.ref
        if self._cell:
            if not self._cell.stopped:
                self._cell.receive(message, _sender)
                return
            else:
                self._cell = None
        if not self.is_local:
            if self.uri.node != self.node.nid:
                self.node.send_message(message, remote_ref=self, sender=_sender)
            else:
                self._cell = self.node.guardian.lookup_cell(self.uri)
                self.is_local = True
                self._cell.receive(message, _sender)
        else:
            if self.node and self.node.guardian:
                cell = self.node.guardian.lookup_cell(self.uri)
                if cell:
                    cell.receive(message, _sender)  # do NOT set self._cell--it will never be unset and will cause a memleak
                    return
            if ('_watched', ANY) == message:
                message[1].send(('terminated', self), _sender=self)
            elif (message == ('terminated', ANY) or message == ('_unwatched', ANY) or message == ('_node_down', ANY) or
                  message == '_stop' or message == '_kill' or message == '__done'):
                pass
            else:
                Events.log(DeadLetter(self, message, _sender))

# === BLOCK 3 (label=human, source_idx=line1361_human, name=point_to_index) ===
def point_to_index(self, point):
        """
        Convert a point to an index in the matrix array.

        Parameters
        ----------
        point: (3,) float, point in space

        Returns
        ---------
        index: (3,) int tuple, index in self.matrix
        """
        indices = points_to_indices(points=[point],
                                    pitch=self.pitch,
                                    origin=self.origin)
        index = tuple(indices[0])
        return index

# === BLOCK 4 (label=lm, source_idx=line6892_lm, name=loading) ===
def loading(self):
        """Context manager for when you need to instantiate entities upon unpacking"""
        self.loading = True
        yield
        self.loading = False

# === BLOCK 5 (label=lm, source_idx=line6623_lm, name=setRect) ===
def setRect( self, rect ):
        """
        Sets the rect for this node, ensuring that the width and height \
        meet the minimum requirements.

        :param      rect        <QRectF>
        """
        rect.setWidth( max( rect.width(), self.minWidth ) )
        rect.setHeight( max( rect.height(), self.minHeight ) )
        self.rect = rect
        self.update()

# === BLOCK 6 (label=human, source_idx=line503_human, name=_calc_avg_and_last_val) ===
def _calc_avg_and_last_val(self, has_no_column, sum_existing_columns):
        """
        Calculate the average of all columns and return a rounded down number.
        Store the remainder and add it to the last row. Could be implemented
        better. If the enduser wants more control, he can also just add the
        amount of columns. Will work fine with small number (<4) of items in a
        row.

        :param has_no_column:
        :param sum_existing_columns:
        :return: average, columns_for_last_element
        """
        sum_no_columns = len(has_no_column)
        columns_left = self.ALLOWED_COLUMNS - sum_existing_columns

        if sum_no_columns == 0:
            columns_avg = columns_left
        else:
            columns_avg = int(columns_left / sum_no_columns)

        remainder = columns_left - (columns_avg * sum_no_columns)
        columns_for_last_element = columns_avg + remainder
        return columns_avg, columns_for_last_element
