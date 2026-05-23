# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line1249_lm, name=read_busiest_date) ===
def read_busiest_date(path: str) -> Tuple[datetime.date, FrozenSet[str]]:
    """Find the earliest date with the most trips"""
    date_counts = {}
    with open(path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            date = datetime.datetime.strptime(row['pickup_datetime'], '%Y-%m-%d %H:%M:%S').date()
            date_counts[date] = date_counts.get(date, 0) + 1
    busiest_date = max(date_counts, key=date_counts.get)
    busiest_date_trips = set()
    with open(path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            date = datetime.datetime.strptime(row['pickup_datetime'], '%Y-%m-%d %H:%M:%S').date()
            if date == busiest_date:
                busiest_date_trips.add(row['trip_id'])
    return busiest_date, frozenset(busiest_date_trips)

# === BLOCK 2 (label=human, source_idx=line1973_human, name=VCStoreRefs) ===
def VCStoreRefs(self):
        """
        Microsoft Visual C++ store references Libraries
        """
        if self.vc_ver < 14.0:
            return []
        return [os.path.join(self.si.VCInstallDir, r'Lib\store\references')]

# === BLOCK 3 (label=human, source_idx=line2123_human, name=filter) ===
def filter(cls, parent=None, **filters):
        """
        Gets all resources of the given type and parent (if provided) which match the given filters.
        This will trigger an api GET request.
        :param parent ResourceBase: the parent of the resource - used for nesting the request url, optional
        :param **filters: any number of keyword arguments to filter by, e.g name='example name'
        :returns: a list of matching resources
        """
        data = cls._process_filter_request(parent, **filters)
        return cls._load_resources(data)

# === BLOCK 4 (label=lm, source_idx=line773_lm, name=paginate) ===
def paginate(self, page, per_page=20, error_out=True):
        """Returns ``per_page`` items from page ``page`` By default, it will
        abort with 404 if no items were found and the page was larger than 1.
        This behaviour can be disabled by setting ``error_out`` to ``False``.

        Returns a :class:`Pagination` object."""
        if page < 1:
            page = 1
        items = self.query.all()
        if not items and page!= 1 and error_out:
            abort(404)
        paginated_items = items[(page - 1) * per_page:page * per_page]
        return Pagination(self, page, per_page, len(items), paginated_items)

# === BLOCK 5 (label=human, source_idx=line1686_human, name=is_valid) ===
def is_valid(self, request_data, request_id=None, raise_exceptions=False):
        """
        Determines if the SAML LogoutResponse is valid
        :param request_id: The ID of the LogoutRequest sent by this SP to the IdP
        :type request_id: string

        :param raise_exceptions: Whether to return false on failure or raise an exception
        :type raise_exceptions: Boolean

        :return: Returns if the SAML LogoutResponse is or not valid
        :rtype: boolean
        """
        self.__error = None
        try:
            idp_data = self.__settings.get_idp_data()
            idp_entity_id = idp_data['entityId']
            get_data = request_data['get_data']

            if self.__settings.is_strict():
                res = OneLogin_Saml2_XML.validate_xml(self.document, 'saml-schema-protocol-2.0.xsd', self.__settings.is_debug_active())
                if isinstance(res, str):
                    raise OneLogin_Saml2_ValidationError(
                        'Invalid SAML Logout Request. Not match the saml-schema-protocol-2.0.xsd',
                        OneLogin_Saml2_ValidationError.INVALID_XML_FORMAT
                    )

                security = self.__settings.get_security_data()

                # Check if the InResponseTo of the Logout Response matches the ID of the Logout Request (requestId) if provided
                in_response_to = self.document.get('InResponseTo', None)
                if request_id is not None and in_response_to and in_response_to != request_id:
                    raise OneLogin_Saml2_ValidationError(
                        'The InResponseTo of the Logout Response: %s, does not match the ID of the Logout request sent by the SP: %s' % (in_response_to, request_id),
                        OneLogin_Saml2_ValidationError.WRONG_INRESPONSETO
                    )

                # Check issuer
                issuer = self.get_issuer()
                if issuer is not None and issuer != idp_entity_id:
                    raise OneLogin_Saml2_ValidationError(
                        'Invalid issuer in the Logout Response (expected %(idpEntityId)s, got %(issuer)s)' %
                        {
                            'idpEntityId': idp_entity_id,
                            'issuer': issuer
                        },
                        OneLogin_Saml2_ValidationError.WRONG_ISSUER
                    )

                current_url = OneLogin_Saml2_Utils.get_self_url_no_query(request_data)

                # Check destination
                destination = self.document.get('Destination', None)
                if destination and current_url not in destination:
                    raise OneLogin_Saml2_ValidationError(
                        'The LogoutResponse was received at %s instead of %s' % (current_url, destination),
                        OneLogin_Saml2_ValidationError.WRONG_DESTINATION
                    )

                if security['wantMessagesSigned']:
                    if 'Signature' not in get_data:
                        raise OneLogin_Saml2_ValidationError(
                            'The Message of the Logout Response is not signed and the SP require it',
                            OneLogin_Saml2_ValidationError.NO_SIGNED_MESSAGE
                        )
            return True
        # pylint: disable=R0801
        except Exception as err:
            self.__error = str(err)
            debug = self.__settings.is_debug_active()
            if debug:
                print(err)
            if raise_exceptions:
                raise
            return False

# === BLOCK 6 (label=lm, source_idx=line2314_lm, name=extract_to_disk) ===
def extract_to_disk(self):
        """Extract all files and write them to disk."""
        for file in self.files:
            file.extract(self.output_dir)
