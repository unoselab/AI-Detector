# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line3758_lm, name=otu_iter_nexson_proxy) ===
def otu_iter_nexson_proxy(nexson_proxy, otu_sort=None):
    """otu_sort can be None (not sorted or stable), True (sorted by ID lexigraphically)
    or a key function for a sort function on list of otuIDs

    Note that if there are multiple OTU groups, the NexSON specifies the order of sorting
        of the groups (so the sort argument here only refers to the sorting of OTUs within
        a group)
    """
    if otu_sort is None:
        otu_sort = lambda x: x
    for otu_group in nexson_proxy['nexml']['otus']:
        otu_ids = [otu['@id'] for otu in otu_group['otu']]
        for otu_id in sorted(otu_ids, key=otu_sort):
            yield otu_id

# === BLOCK 2 (label=human, source_idx=line3302_human, name=OnSelectReader) ===
def OnSelectReader(self, reader):
        """Called when a reader is selected by clicking on the reader
        tree control or toolbar."""
        SimpleSCardAppEventObserver.OnSelectReader(self, reader)
        self.feedbacktext.SetLabel('Selected reader: ' + repr(reader))

# === BLOCK 3 (label=lm, source_idx=line5121_lm, name=connect_ws) ===
def connect_ws(self, path: str) -> _WSRequestContextManager:
        """
        Connect to a websocket in order to use API parameters

        In reality, aiohttp.session.ws_connect returns a aiohttp.client._WSRequestContextManager instance.
        It must be used in a with statement to get the ClientWebSocketResponse instance from it (__aenter__).
        At the end of the with statement, aiohttp.client._WSRequestContextManager.__aexit__ is called
        and close the ClientWebSocketResponse in it.

        :param path: the url path
        :return:
        """
        return self._session.ws_connect(self._url + path)

# === BLOCK 4 (label=human, source_idx=line1674_human, name=clean_dataframe) ===
def clean_dataframe(df):
    """Fill NaNs with the previous value, the next value or if all are NaN then 1.0"""
    df = df.fillna(method='ffill')
    df = df.fillna(0.0)
    return df

# === BLOCK 5 (label=human, source_idx=line4409_human, name=init) ===
def init(self, permits):
        """
        Try to initialize this Semaphore instance with the given permit count.

        :param permits: (int), the given permit count.
        :return: (bool), ``true`` if initialization success.
        """
        check_not_negative(permits, "Permits cannot be negative!")
        return self._encode_invoke(semaphore_init_codec, permits=permits)

# === BLOCK 6 (label=lm, source_idx=line2621_lm, name=modify_column_if_table_exists) ===
def modify_column_if_table_exists(self,
                                      tablename: str,
                                      fieldname: str,
                                      newdef: str) -> Optional[int]:
        """Alters a column's definition without renaming it."""
        if tablename not in self.tables:
            return None
        if fieldname not in self.tables[tablename]:
            return None
        self.tables[tablename][fieldname] = newdef
