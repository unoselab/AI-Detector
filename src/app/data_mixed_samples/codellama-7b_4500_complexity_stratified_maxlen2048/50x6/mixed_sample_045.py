# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line6779_lm, name=disconnect) ===
def disconnect(self, connection):
        """
        Removes a subscriber connection, ensuring that any pending commands get requeued.

        @param connection: The client connection to unsubscribe.
        @type connection: L{coilmq.server.StompConnection}
        """
        if connection in self.subscribers:
            self.subscribers.remove(connection)
            self.requeue_pending_commands(connection)

# === BLOCK 2 (label=human, source_idx=line3386_human, name=unhook) ===
def unhook(self, addr):
        """
        Remove a hook.

        :param addr:    The address of the hook.
        """
        if not self.is_hooked(addr):
            l.warning("Address %s not hooked", self._addr_to_str(addr))
            return

        del self._sim_procedures[addr]

# === BLOCK 3 (label=lm, source_idx=line4549_lm, name=parse_schema_definition) ===
def parse_schema_definition(lexer: Lexer) -> SchemaDefinitionNode:
    """SchemaDefinition"""
    lexer.advance()
    lexer.expect_token(TokenKind.NAME)
    name = lexer.token.value
    lexer.advance()
    lexer.expect_token(TokenKind.BRACE_L)
    directives = parse_directives(lexer)
    operation_types = []
    while lexer.token.kind == TokenKind.NAME:
        operation_types.append(parse_operation_type_definition(lexer))
    lexer.expect_token(TokenKind.BRACE_R)
    return SchemaDefinitionNode(
        location=lexer.location,
        name=name,
        directives=directives,
        operation_types=operation_types,
    )

# === BLOCK 4 (label=human, source_idx=line8475_human, name=stringpatterncounter) ===
def stringpatterncounter(table, field):
    """
    Profile string patterns in the given field, returning a :class:`dict`
    mapping patterns to counts.

    """

    trans = maketrans(
        'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789',
        'AAAAAAAAAAAAAAAAAAAAAAAAAAaaaaaaaaaaaaaaaaaaaaaaaaaa9999999999'
    )
    counter = Counter()
    for v in values(table, field):
        p = str(v).translate(trans)
        counter[p] += 1
    return counter

# === BLOCK 5 (label=lm, source_idx=line1595_lm, name=add_host) ===
def add_host(host):
    """ Put your host information in the prefix object. """
    prefix = host.split('.')[0]
    return prefix

# === BLOCK 6 (label=human, source_idx=line6_human, name=isiterable) ===
def isiterable(element, exclude=None):
    """Check whatever or not if input element is an iterable.

    :param element: element to check among iterable types.
    :param type/tuple exclude: not allowed types in the test.

    :Example:

    >>> isiterable({})
    True
    >>> isiterable({}, exclude=dict)
    False
    >>> isiterable({}, exclude=(dict,))
    False
    """

    # check for allowed type
    allowed = exclude is None or not isinstance(element, exclude)
    result = allowed and isinstance(element, Iterable)

    return result
