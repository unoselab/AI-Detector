# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line5532_lm, name=_tupleCompare) ===
def _tupleCompare(tuple1, ineq, tuple2,
                 eq=lambda a,b: (a==b),
                 ander=AND,
                 orer=OR):
    """
    Compare two 'in-database tuples'.  Useful when sorting by a compound key
    and slicing into the middle of that query.
    """
    if ineq == '==':
        return eq(tuple1, tuple2)
    elif ineq == '!=':
        return not eq(tuple1, tuple2)
    elif ineq == '<':
        return tuple1 < tuple2
    elif ineq == '<=':
        return tuple1 <= tuple2
    elif ineq == '>':
        return tuple1 > tuple2
    elif ineq == '>=':
        return tuple1 >= tuple2
    elif ineq == 'AND':
        return ander(tuple1, tuple2)
    elif ineq == 'OR':
        return orer(tuple1, tuple2)
    else:
        raise ValueError("Unknown inequality operator: %s" % ineq)

# === BLOCK 2 (label=human, source_idx=line2915_human, name=centroid_refine_triangulation_by_triangles) ===
def centroid_refine_triangulation_by_triangles(self, triangles):
        """
        return points defining a refined triangulation obtained by bisection of all edges
        in the triangulation that are associated with the triangles in the list provided.

        Notes
        -----
         The triangles are here represented as a single index.
         The vertices of triangle i are given by self.simplices[i].
        """

        # Remove duplicates from the list of triangles

        triangles = np.unique(np.array(triangles))

        mlons, mlats = self.face_midpoints(simplices=self.simplices[triangles])

        lonv1 = np.concatenate((self.lons, mlons), axis=0)
        latv1 = np.concatenate((self.lats, mlats), axis=0)

        return lonv1, latv1

# === BLOCK 3 (label=lm, source_idx=line387_lm, name=delete_interface_from_router) ===
def delete_interface_from_router(self, segment_id, router_name, server):
        """Deletes an interface from existing HW router on Arista HW device.

        :param segment_id: VLAN Id associated with interface that is added
        :param router_name: globally unique identifier for router/VRF
        :param server: Server endpoint on the Arista switch to be configured
        """
        self.logger.debug("Deleting interface from router")
        self.logger.debug("segment_id: %s", segment_id)
        self.logger.debug("router_name: %s", router_name)
        self.logger.debug("server: %s", server)
        self.logger.debug("router_name: %s", router_name)
        self.logger.debug("server: %s", server)
        self.logger.debug("segment_id: %s", segment_id)
        self.logger.debug("router_name: %s", router_name)
        self.logger.debug("server: %s", server)
        self.logger.debug("segment_id: %s", segment_id)
        self.logger.debug("router_name: %s", router_name)
        self.logger.debug("server: %s", server)
        self.logger.debug("segment_id: %s", segment_id)
        self.logger.debug("router_name: %s", router_name)
        self.logger.debug("server: %s", server)
        self.logger.debug("segment_id: %s", segment_id)
        self.logger.debug("router_name: %s", router_name)
        self.logger.debug("server: %s", server)
        self.logger.debug("segment_id: %s", segment_id)
        self.logger.debug("router_name: %s", router_name)
        self.logger.debug("server: %s", server)
        self.logger.debug("segment_id: %s", segment_id)
        self.logger.debug("router_name: %s", router_name)
        self.logger.debug("server: %s", server)
        self.logger.debug("segment_id: %s", segment_id)
        self.logger.debug("router_name: %s", router_name)
        self.logger.debug("server: %s", server)
        self.logger.debug("segment_id: %s", segment_id)
        self.logger.debug("router_name: %s", router_name)
        self.logger.debug("server: %s", server)
        self.logger.debug("segment_id: %s", segment_id)

# === BLOCK 4 (label=human, source_idx=line6929_human, name=default) ===
def default(self, value):
        """Convert rogue and mysterious data types.
        Conversion notes:

        - ``datetime.date`` and ``datetime.datetime`` objects are
        converted into datetime strings.
        """

        if isinstance(value, datetime):
            return value.isoformat()
        elif isinstance(value, date):
            dt = datetime(value.year, value.month, value.day, 0, 0, 0)
            return dt.isoformat()
        elif isinstance(value, Decimal):
            return float(str(value))
        elif isinstance(value, set):
            return list(value)
        # raise TypeError
        return super(ESJsonEncoder, self).default(value)

# === BLOCK 5 (label=lm, source_idx=line1381_lm, name=_get_file_name) ===
def _get_file_name(self, contentDisposition,
                       url, ext=".unknown"):
        """ gets the file name from the header or url if possible """
        if contentDisposition:
            filename = contentDisposition.get_filename()
            if filename:
                return filename
        if url:
            return url.split("/")[-1]
        return "file" + ext

# === BLOCK 6 (label=human, source_idx=line4993_human, name=scalarmult_B) ===
def scalarmult_B(e):
    """
    Implements scalarmult(B, e) more efficiently.
    """
    # scalarmult(B, l) is the identity
    e = e % l
    P = ident
    for i in range(253):
        if e & 1:
            P = edwards_add(P, Bpow[i])
        e = e // 2
    assert e == 0, e
    return P
