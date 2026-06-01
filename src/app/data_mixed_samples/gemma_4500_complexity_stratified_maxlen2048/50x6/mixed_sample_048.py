# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line4904_human, name=append) ===
def append(self, other):
        """
        Append a Printable Image at the end of the current instance.
        :param other: another PrintableImage
        :return: PrintableImage containing data from both self and other
        """
        self.data.extend(other.data)
        self.height = self.height + other.height
        return self

# === BLOCK 2 (label=human, source_idx=line5156_human, name=files_delete) ===
def files_delete(self, *, id: str, **kwargs) -> SlackResponse:
        """Deletes a file.

        Args:
            id (str): The file id. e.g. 'F1234467890'
        """
        kwargs.update({"id": id})
        return self.api_call("files.delete", json=kwargs)

# === BLOCK 3 (label=human, source_idx=line376_human, name=where) ===
def where(cond, a, b, use_numexpr=True):
    """ evaluate the where condition cond on a and b

        Parameters
        ----------

        cond : a boolean array
        a :    return if cond is True
        b :    return if cond is False
        use_numexpr : whether to try to use numexpr (default True)
        """

    if use_numexpr:
        return _where(cond, a, b)
    return _where_standard(cond, a, b)

# === BLOCK 4 (label=lm, source_idx=line8737_lm, name=get_sidecar_nodes) ===
def get_sidecar_nodes(self) -> Iterator[PostSidecarNode]:
        """Sidecar nodes of a Post with typename==GraphSidecar."""
        return (node for node in self.nodes if getattr(node, 'typename', None) == 'GraphSidecar')

# === BLOCK 5 (label=lm, source_idx=line5550_lm, name=tag) ===
def tag(self, utterance, context_trie=None):
        """
        Tag known entities within the utterance.
        Args:
            utterance(str): a string of natural language text
            context_trie(trie): optional, a trie containing only entities from context
                for this request

        Returns: dictionary, with the following keys
            match(str): the proper entity matched
            key(str): the string that was matched to the entity
            start_token(int): 0-based index of the first token matched
            end_token(int): 0-based index of the last token matched
            entities(list): a list of entity kinds as strings (Ex: Artist, Location)
        """
        tokens = utterance.split()
        results = []

        # Combine global trie and context trie if provided
        tries = [self.trie]
        if context_trie:
            tries.append(context_trie)

        for i in range(len(tokens)):
            for trie in tries:
                # Search for the longest match starting at index i
                current_node = trie.root
                match_found = None

                for j in range(i, len(tokens)):
                    token = tokens[j]
                    if token in current_node.children:
                        current_node = current_node.children[token]
                        if current_node.is_end:
                            match_found = {
                                'match': current_node.value,
                                'key': ' '.join(tokens[i:j+1]),
                                'start_token': i,
                                'end_token': j,
                                'entities': current_node.entities
                            }
                    else:
                        break

                if match_found:
                    results.append(match_found)
                    break # Prioritize first trie match

        # Return the longest match or the first match found
        if not results:
            return {}

        return max(results, key=lambda x: x['end_token'] - x['start_token'])

# === BLOCK 6 (label=lm, source_idx=line6890_lm, name=replace) ===
def replace(old_value, new_value, full_match=False):
    """
    Replace string or full line matches in switch's running config

    If full_match is set to True, then the whole line will need to be matched
    as part of the old value.

    .. code-block:: bash

        salt '*' onyx.cmd replace 'TESTSTRINGHERE' 'NEWTESTSTRINGHERE'
    """
    config = __salt__['onyx.get_config']()
    new_config = []
    for line in config.splitlines():
        if full_match:
            if line == old_value:
                new_config.append(new_value)
            else:
                new_config.append(line)
        else:
            new_config.append(line.replace(old_value, new_value))

    final_config = "\n".join(new_config)
    return __salt__['onyx.set_config'](final_config)
