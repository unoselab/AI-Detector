# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line2365_lm, name=is_on_curve) ===
def is_on_curve(self, point):
        """
        Checks whether a point is on the curve.

        Args:
            point (AffinePoint): Point to be checked.

        Returns:
            bool: True if point is on the curve, False otherwise.
        """
        y_squared = (point.y ** 2) % self.p
        x_cubed = (point.x ** 3) % self.p
        left_hand_side = y_squared % self.p
        right_hand_side = (x_cubed + self.a * point.x + self.b) % self.p
        return left_hand_side == right_hand_side

# === BLOCK 2 (label=human, source_idx=line2124_human, name=enable_host_notifications) ===
def enable_host_notifications(self, host):
        """Enable notifications for a host
        Format of the line that triggers function call::

        ENABLE_HOST_NOTIFICATIONS;<host_name>

        :param host: host to edit
        :type host: alignak.objects.host.Host
        :return: None
        """
        if not host.notifications_enabled:
            host.modified_attributes |= \
                DICT_MODATTR["MODATTR_NOTIFICATIONS_ENABLED"].value
            host.notifications_enabled = True
            self.send_an_element(host.get_update_status_brok())

# === BLOCK 3 (label=lm, source_idx=line35_lm, name=setFixedHeight) ===
def setFixedHeight(self, height):
        """
        Sets the maximum height value to the inputed height and emits the \
        sizeConstraintChanged signal.

        :param      height | <int>
        """
        self._maxHeight = height
        self.sizeConstraintChanged.emit()

# === BLOCK 4 (label=human, source_idx=line1983_human, name=_run) ===
def _run(self):
        """Run the iterative optimizer"""
        success = self.initialize()
        while success is None:
            success = self.propagate()
        return success
