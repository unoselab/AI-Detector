# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line4724_lm, name=generate) ===
def generate(self):
    """
    Generates the report
    """
    self.generate_header()
    self.generate_body()
    self.generate_footer()

# === BLOCK 2 (label=human, source_idx=line747_human, name=posterior_predictive_to_xarray) ===
def posterior_predictive_to_xarray(self):
        """Convert posterior_predictive samples to xarray."""
        posterior_predictive = self.posterior_predictive
        columns = self.posterior[0].columns
        if (
            isinstance(posterior_predictive, (tuple, list))
            and posterior_predictive[0].endswith(".csv")
        ) or (isinstance(posterior_predictive, str) and posterior_predictive.endswith(".csv")):
            if isinstance(posterior_predictive, str):
                posterior_predictive = [posterior_predictive]
            chain_data = []
            for path in posterior_predictive:
                parsed_output = _read_output(path)
                for sample, *_ in parsed_output:
                    chain_data.append(sample)
            data = _unpack_dataframes(chain_data)
        else:
            if isinstance(posterior_predictive, str):
                posterior_predictive = [posterior_predictive]
            posterior_predictive_cols = [
                col
                for col in columns
                if any(item == col.split(".")[0] for item in posterior_predictive)
            ]
            data = _unpack_dataframes([item[posterior_predictive_cols] for item in self.posterior])
        return dict_to_dataset(data, coords=self.coords, dims=self.dims)

# === BLOCK 3 (label=human, source_idx=line387_human, name=delete_interface_from_router) ===
def delete_interface_from_router(self, segment_id, router_name, server):
        """Deletes an interface from existing HW router on Arista HW device.

        :param segment_id: VLAN Id associated with interface that is added
        :param router_name: globally unique identifier for router/VRF
        :param server: Server endpoint on the Arista switch to be configured
        """

        if not segment_id:
            segment_id = DEFAULT_VLAN
        cmds = []
        for c in self._interfaceDict['remove']:
            cmds.append(c.format(segment_id))

        self._run_config_cmds(cmds, server)

# === BLOCK 4 (label=lm, source_idx=line3577_lm, name=leading_whitespace_in_current_line) ===
def leading_whitespace_in_current_line(self):
        """ The leading whitespace in the left margin of the current line.  """
        return self.line_start_index - self.line_start_index_of_first_non_whitespace

# === BLOCK 5 (label=human, source_idx=line322_human, name=set_editor_cursor) ===
def set_editor_cursor(self, editor, cursor):
        """Set the cursor of an editor."""
        pos = cursor.position()
        anchor = cursor.anchor()

        new_cursor = QTextCursor()
        if pos == anchor:
            new_cursor.movePosition(pos)
        else:
            new_cursor.movePosition(anchor)
            new_cursor.movePosition(pos, QTextCursor.KeepAnchor)
        editor.setTextCursor(cursor)

# === BLOCK 6 (label=lm, source_idx=line2487_lm, name=_returnPD) ===
def _returnPD(self, code, tablename, **kwargs):
        """
        private function to take a sas code normally to create a table, generate pandas data frame and cleanup.

        :param code: string of SAS code
        :param tablename: the name of the SAS Data Set
        :param kwargs:
        :return: Pandas Data Frame
        """
        # create a temporary SAS data set
        self.sas.submit(code)
        # create a pandas data frame
        df = self.sas.sasdata(tablename, 'work').to_df()
        # drop the temporary SAS data set
        self.sas.drop(tablename, libref='work')
        # return the pandas data frame
        return df
