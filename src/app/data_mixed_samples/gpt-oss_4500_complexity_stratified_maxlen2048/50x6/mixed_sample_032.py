# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line4652_lm, name=on_lstUnits_itemSelectionChanged) ===
def on_lstUnits_itemSelectionChanged(self):
        """Update unit description label and field widgets.

        .. note:: This is an automatic Qt slot
           executed when the unit selection changes.
        """
        selected_items = self.lstUnits.selectedItems()
        if not selected_items:
            # No selection: clear description and disable all field widgets
            if hasattr(self, "lblUnitDescription"):
                self.lblUnitDescription.setText("")
            for w in getattr(self, "fieldWidgets", []):
                w.setEnabled

# === BLOCK 2 (label=human, source_idx=line702_human, name=set_ventilation) ===
async def set_ventilation(self, pct, timeout=OTGW_DEFAULT_TIMEOUT):
        """
        Configure a ventilation setpoint override value (0-100%).
        Return the newly accepted value, or None on failure.
        @pct :int: Must be between 0 and 100.

        This method is a coroutine
        """
        if not 0 <= pct <= 100:
            return None
        cmd = OTGW_CMD_VENT
        status = {}
        ret = await self._wait_for_cmd(cmd, pct, timeout)
        if ret is None:
            return
        ret = int(ret)
        status[DATA_COOLING_CONTROL] = ret
        self._update_status(status)
        return ret

# === BLOCK 3 (label=human, source_idx=line3967_human, name=__create_csv_eps) ===
def __create_csv_eps(self, metric1, metric2, csv_labels, file_label,
                         title_label, project=None):
        """
        Generate the CSV data and EPS figs files for two metrics
        :param metric1: first metric class
        :param metric2: second metric class
        :param csv_labels: labels to be used in the CSV file
        :param file_label: shared filename token to be included in csv and eps files
        :param title_label: title for the EPS figures
        :param project: name of the project for which to generate the data
        :return:
        """

        logger.debug("CSV file %s generation in progress", file_label)

        esfilters = None
        csv_labels = csv_labels.replace("_", "")  # LaTeX not supports

        if project and project != self.GLOBAL_PROJECT:
            esfilters = {"project": project}
        m1 = metric1(self.es_url, self.get_metric_index(metric1),
                     esfilters=esfilters,
                     start=self.start, end=self.end)
        m1_ts = m1.get_ts()

        if metric2:
            m2 = metric2(self.es_url, self.get_metric_index(metric2),
                         esfilters=esfilters,
                         start=self.start, end=self.end)
            m2_ts = m2.get_ts()

        csv = csv_labels + '\n'
        for i in range(0, len(m1_ts['date'])):
            if self.interval == 'quarter':
                date_str = self.build_period_name(parser.parse(m1_ts['date'][i]), start_date=True)
            else:
                date_str = parser.parse(m1_ts['date'][i]).strftime("%y-%m")
            csv += date_str
            csv += "," + self.str_val(m1_ts['value'][i])
            if metric2:
                csv += "," + self.str_val(m2_ts['value'][i])
            csv += "\n"

        data_path = os.path.join(self.data_dir, "data")

        if project:
            file_name = os.path.join(data_path, file_label + "_" + project + ".csv")
        else:
            file_name = os.path.join(data_path, file_label + ".csv")

        os.makedirs(os.path.dirname(file_name), exist_ok=True)
        with open(file_name, "w") as f:
            f.write(csv)

        logger.debug("CSV file %s was generated", file_label)

        fig_path = os.path.join(self.data_dir, "figs")

        if project:
            file_name = os.path.join(fig_path, file_label + "_" + project + ".eps")
            title = title_label + ": " + project
        else:
            file_name = os.path.join(fig_path, file_label + ".eps")
            title = title_label

        if self.interval != 'quarter':
            x_val = [parser.parse(val).strftime("%y-%m") for val in m1_ts['date']]
        else:
            x_val = []
            for val in m1_ts['date']:
                period = self.build_period_name(parser.parse(val), start_date=True)
                x_val.append(period)
        if metric2:
            self.bar_chart(title, x_val, m1_ts['value'],
                           file_name, m2_ts['value'],
                           legend=[m1.name, m2.name])
        else:
            self.bar_chart(title, x_val, m1_ts['value'], file_name,
                           legend=[m1.name])

# === BLOCK 4 (label=lm, source_idx=line3593_lm, name=localDirPath) ===
def localDirPath(self):
        """
        The path to the directory containing the resource on the worker.
        """
        import os
        for attr in ('path', 'resource_path', 'resourcePath'):
            p = getattr(self, attr, None)
            if p:
                return os.path.abspath(os.path.dirname(p))
        raise AttributeError("Unable to determine resource path for localDirPath")

# === BLOCK 5 (label=human, source_idx=line3201_human, name=add_md) ===
def add_md(text, s, level=0):
    """Adds text to the readme at the given level"""
    if level > 0:
        if text != "":
            text += "\n"
        text += "#" * level
        text += " "

    text += s + "\n"

    if level > 0:
        text += "\n"

    return text

# === BLOCK 6 (label=lm, source_idx=line2383_lm, name=derivesha512address) ===
def derivesha512address(self):
        """ Derive address using ``RIPEMD160(SHA512(x))`` """
        import hashlib

        # Obtain the input data: prefer a 'public_key' attribute, otherwise use the object itself if bytes-like
        data = getattr(self, "public_key", None)
        if data is None:
            if isinstance(self, (bytes, bytearray)):
                data = self
            else:
                raise AttributeError("Object lacks a 'public_key' attribute and is not bytes-like")
        # Ensure we are working with bytes
        if isinstance(data, str):
            data = data.encode()
