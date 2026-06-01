# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line5697_lm, name=timemeter) ===
def timemeter(msg=None):
    """Timer meter

        Use this annotation method can calculate the execute time.
    :param msg: custom message output
    :return: fn values
    """

# === BLOCK 2 (label=human, source_idx=line8838_human, name=clean_upload) ===
def clean_upload(self, query='/content/uploads/'):
        """
        pulp leaves droppings if you don't specifically tell it
        to clean up after itself. use this to do so.
        """
        query = query + self.uid + '/'
        _r = self.connector.delete(query)

        if _r.status_code == Constants.PULP_DELETE_OK:
            juicer.utils.Log.log_info("Cleaned up after upload request.")
        else:
            _r.raise_for_status()

# === BLOCK 3 (label=human, source_idx=line4549_human, name=parse_schema_definition) ===
def parse_schema_definition(lexer: Lexer) -> SchemaDefinitionNode:
    """SchemaDefinition"""
    start = lexer.token
    expect_keyword(lexer, "schema")
    directives = parse_directives(lexer, True)
    operation_types = many_nodes(
        lexer, TokenKind.BRACE_L, parse_operation_type_definition, TokenKind.BRACE_R
    )
    return SchemaDefinitionNode(
        directives=directives, operation_types=operation_types, loc=loc(lexer, start)
    )

# === BLOCK 4 (label=lm, source_idx=line4207_lm, name=split_every) ===
def split_every(iterable, n):  # TODO: Remove this, or make it return a generator.
    """
    A generator of n-length chunks of an input iterable
    """
    iterable = iter(iterable)
    while True:
        chunk = tuple(itertools.islice(iterable, n))
        if not chunk:
            return
        yield chunk

# === BLOCK 5 (label=human, source_idx=line3777_human, name=convert_machine_list_value) ===
def convert_machine_list_value(name: str, value: str) -> \
        Union[datetime.datetime, str, int]:
    """Convert sizes and time values.

    Size will be ``int`` while time value will be :class:`datetime.datetime`.
    """
    if name == 'modify':
        return convert_machine_list_time_val(value)
    elif name == 'size':
        return int(value)
    else:
        return value

# === BLOCK 6 (label=lm, source_idx=line2618_lm, name=gather) ===
def gather(weights, indices, dim, output_shape=None):
  """Shorthand for einsum([one_hot(indices, dim)], weights, reduced_dims=[dim]).

  Args:
    weights: a Tensor
    indices: a Tensor with integer type
    dim: a Dimension
    output_shape: an optional mtf.Shape
  Returns:
    a Tensor
  """
