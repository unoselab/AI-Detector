# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line4176_human, name=all_in) ===
def all_in(self, name) -> iter:
        """Yield all (power) nodes contained in given (power) node"""
        for elem in self.inclusions[name]:
            yield elem
            yield from self.all_in(elem)

# === BLOCK 2 (label=human, source_idx=line3846_human, name=write) ===
def write(self, more):
        """Append the Unicode representation of `s` to our output."""
        if more:
            self.output += str(more).upper()
            self.output += '\n'

# === BLOCK 3 (label=lm, source_idx=line5071_lm, name=acquire_metadata) ===
def acquire_metadata(self):
        """
        Handles the acquisition of metadata for both collection mode and single
        mode, uses the metadata methods belonging to the article's publisher
        attribute.
        """
        if self.collection_mode:
            self.acquire_collection_metadata()
        else:
            self.acquire_single_metadata()

# === BLOCK 4 (label=lm, source_idx=line211_lm, name=rerun) ===
def rerun(client, run, job):
    """Re-run existing workflow or tool using CWL runner."""
    if run.workflow_id:
        workflow = Workflow.objects.get(id=run.workflow_id)
        workflow.run(client, job)
    else:
        tool = Tool.objects.get(id=run.tool_id)
        tool.run(client, job)

# === BLOCK 5 (label=human, source_idx=line5487_human, name=value) ===
def value(self, raw_value):
        """Decode param with Base64."""
        try:
            return base64.b64decode(bytes(raw_value, 'utf-8')).decode('utf-8')
        except binascii.Error as err:
            raise ValueError(str(err))

# === BLOCK 6 (label=lm, source_idx=line2846_lm, name=get_ccle_cna) ===
def get_ccle_cna():
    """Get CCLE CNA
    -2 = homozygous deletion
    -1 = hemizygous deletion
     0 = neutral / no change
     1 = gain
     2 = high level amplification
    """
    ccle_cna = pd.read_csv(
        os.path.join(DATA_DIR, 'ccle_cna.csv.gz'), index_col=0
    )
    ccle_cna.columns = ccle_cna.columns.astype(int)
    ccle_cna = ccle_cna.T
    ccle_cna = ccle_cna.sort_index()
    ccle_cna = ccle_cna.loc[
        ccle_cna.index.intersection(
            get_ccle_mutations().index.get_level_values(0)
        )
    ]
    return ccle_cna
