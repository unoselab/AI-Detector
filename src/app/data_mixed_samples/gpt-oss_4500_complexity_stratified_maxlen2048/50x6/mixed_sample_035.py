# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line772_human, name=_create_body) ===
def _create_body(self, name, description=None, volume=None, force=False):
        """
        Used to create the dict required to create a new snapshot
        """
        body = {"snapshot": {
                "display_name": name,
                "display_description": description,
                "volume_id": volume.id,
                "force": str(force).lower(),
                }}
        return body

# === BLOCK 2 (label=human, source_idx=line2314_human, name=link) ===
def link(self):
    """str: full path of the linked file entry."""
    if not self.IsLink():
      return ''

    location = getattr(self.path_spec, 'location', None)
    if location is None:
      return ''

    return self._file_system.GetDataByPath(location)

# === BLOCK 3 (label=lm, source_idx=line373_lm, name=process_delete_records) ===
def process_delete_records(delete_records):
    """Process the requests for S3 bucket deletions"""
    import boto3
    from botocore.exceptions import ClientError

    client = boto3.client('s3')
    deleted = []
    errors = []

    for record in delete_records:
        bucket = record.get('Bucket')
        key = record.get('Key')
        if not bucket or not key:
            errors.append((bucket, key, ValueError("Missing 'Bucket' or 'Key'")))
            continue
        try:
            client.delete_object(Bucket=bucket, Key=key)
            deleted.append((bucket, key))
        except ClientError as e:
            errors.append((bucket, key, e))

    return {'deleted': deleted, 'errors': errors}

# === BLOCK 4 (label=human, source_idx=line2031_human, name=subontology) ===
def subontology(self, nodes=None, minimal=False, relations=None):
        """
        Return a new ontology that is an extract of this one

        Arguments
        ---------
        - nodes: list
            list of node IDs to include in subontology. If None, all are used
        - relations: list
            list of relation IDs to include in subontology. If None, all are used

        """
        g = None
        if nodes is not None:
            g = self.subgraph(nodes)
        else:
            g = self.get_graph()
        if minimal:
            from ontobio.slimmer import get_minimal_subgraph
            g = get_minimal_subgraph(g, nodes)

        ont = Ontology(graph=g, xref_graph=self.xref_graph) # TODO - add metadata
        if relations is not None:
            g = ont.get_filtered_graph(relations)
            ont = Ontology(graph=g, xref_graph=self.xref_graph)
        return ont

# === BLOCK 5 (label=lm, source_idx=line2270_lm, name=reduce_activities) ===
def reduce_activities(stmts_in, **kwargs):
    """Reduce the activity types in a list of statements

    Parameters
    ----------
    stmts_in : list[indra.statements.Statement]
        A list of statements to reduce activity types in.
    save : Optional[str]
        The name of a pickle file to save the results (stmts_out) into.

    Returns
    -------
    stmts_out : list[indra.statements.Statement]
        A list of reduced activity statements.
    """

# === BLOCK 6 (label=lm, source_idx=line2103_lm, name=_validate) ===
def _validate(self):
        """ check if this Swagger API valid or not.

        :param bool strict: when in strict mode, exception would be raised if not valid.
        :return: validation errors
        :rtype: list of tuple(where, type, msg).
        """
