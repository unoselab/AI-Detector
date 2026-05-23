# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line2728_human, name=find_executable) ===
def find_executable(executable, path=None):
    """
    As distutils.spawn.find_executable, but on Windows, look up
    every extension declared in PATHEXT instead of just `.exe`
    """
    if sys.platform != 'win32':
        return distutils.spawn.find_executable(executable, path)

    if path is None:
        path = os.environ['PATH']

    paths = path.split(os.pathsep)
    extensions = os.environ.get('PATHEXT', '.exe').split(os.pathsep)
    base, ext = os.path.splitext(executable)

    if not os.path.isfile(executable):
        for p in paths:
            for ext in extensions:
                f = os.path.join(p, base + ext)
                if os.path.isfile(f):
                    return f
        return None
    else:
        return executable

# === BLOCK 2 (label=lm, source_idx=line2276_lm, name=_add_single_session_to_to_ordered_dict) ===
def _add_single_session_to_to_ordered_dict(self, d, dataset_index, recommended_only):
        """
        Save a single session to an ordered dictionary.
        """
        session = self.sessions[dataset_index]
        if recommended_only and not session.recommended:
            return
        d[dataset_index] = session

# === BLOCK 3 (label=human, source_idx=line2425_human, name=_on_changed) ===
def _on_changed(self):
        """
        Update the tree items
        """
        self._updating = True
        to_collapse = []
        self.clear()
        if self._editor and self._outline_mode and self._folding_panel:
            items, to_collapse = self.to_tree_widget_items(
                self._outline_mode.definitions, to_collapse=to_collapse)
            if len(items):
                self.addTopLevelItems(items)
                self.expandAll()
                for item in reversed(to_collapse):
                    self.collapseItem(item)
                self._updating = False
                return

        # no data
        root = QtWidgets.QTreeWidgetItem()
        root.setText(0, _('No data'))
        root.setIcon(0, icons.icon(
            'dialog-information', ':/pyqode-icons/rc/dialog-info.png',
            'fa.info-circle'))
        self.addTopLevelItem(root)
        self._updating = False
        self.sync()

# === BLOCK 4 (label=human, source_idx=line249_human, name=on_select_level_name) ===
def on_select_level_name(self,event,called_by_parent=False):
        """
        change this objects specimens_list to control which specimen interpretatoins are displayed in this objects logger
        @param: event -> the wx.ComboBoxEvent that triggered this function
        """
        high_level_name=str(self.level_names.GetValue())

        if self.level_box.GetValue()=='sample':
            self.specimens_list=self.parent.Data_hierarchy['samples'][high_level_name]['specimens']
        elif self.level_box.GetValue()=='site':
            self.specimens_list=self.parent.Data_hierarchy['sites'][high_level_name]['specimens']
        elif self.level_box.GetValue()=='location':
            self.specimens_list=self.parent.Data_hierarchy['locations'][high_level_name]['specimens']
        elif self.level_box.GetValue()=='study':
            self.specimens_list=self.parent.Data_hierarchy['study']['this study']['specimens']

        if not called_by_parent:
            self.parent.level_names.SetStringSelection(high_level_name)
            self.parent.onSelect_level_name(event,True)

        self.specimens_list.sort(key=spec_key_func)
        self.update_editor()

# === BLOCK 5 (label=lm, source_idx=line2950_lm, name=disable_passive_host_checks) ===
def disable_passive_host_checks(self, host):
        """Disable passive checks for a host
        Format of the line that triggers function call::

        DISABLE_PASSIVE_HOST_CHECKS;<host_name>

        :param host: host to edit
        :type host: alignak.objects.host.Host
        :return: None
        """
        host.passive_checks_enabled = 0

# === BLOCK 6 (label=lm, source_idx=line632_lm, name=rmdup) ===
def rmdup(args):
    """
    %prog rmdup *.bam > rmdup.cmds

    Remove PCR duplicates from BAM files, generate a list of commands.
    """
    commands = []
    for bam in args:
        rmdup_bam = bam.replace(".bam", ".rmdup.bam")
        command = f"samtools rmdup {bam} {rmdup_bam}"
        commands.append(command)
    return commands
