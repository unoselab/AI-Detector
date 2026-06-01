# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line4121_human, name=orders_from_events) ===
def orders_from_events(events, sell_delay=5, num_shares=100):
    """Create a DataFrame of orders (signed share quantities) based on event triggers (T/F or 0/1 matrix)

    Arguments:
      events (DataFrame): mask table to indicate occurrence of buy event (1 = buy, NaN/0/False = do nothing)
      sell_delay (int): number of days after the buy order to initiate a sell order of those shares
      num_shares (int): number of shares to buy and sell at each event

    Returns:
      DataFrame: Signed integer numbers of shares to buy (+) or sell (-)
        columns are stock ticker symbols
        index is datetime at end of trading day (16:00 in NY)
    """

    buy = events.copy() * num_shares
    sell = -1 * pd.DataFrame(buy.copy().values[:-sell_delay], index=buy.index[sell_delay:], columns=buy.columns)
    sell = pd.concat([0 * buy.iloc[:sell_delay], sell])
    for i in range(sell_delay):
        sell.iloc[-1] -= buy.iloc[-sell_delay + i]
    orders = buy + sell
    return orders

# === BLOCK 2 (label=lm, source_idx=line8747_lm, name=set_widgets) ===
def set_widgets(self):
        """Set widgets on the Aggregation Layer from Canvas tab."""
        canvas_tab = self.get_canvas_tab()
        aggregation_layer = self.get_aggregation_layer()

        widgets = canvas_tab.get_widgets()
        for widget in widgets:
            aggregation_layer.add_widget(widget)

        aggregation_layer.refresh()

# === BLOCK 3 (label=human, source_idx=line3970_human, name=from_maildir) ===
def from_maildir(self, codes: str) -> FrozenSet[Flag]:
        """Return the set of IMAP flags that correspond to the letter codes.

        Args:
            codes: The letter codes to map.

        """
        flags = set()
        for code in codes:
            if code == ',':
                break
            to_sys = self._to_sys.get(code)
            if to_sys is not None:
                flags.add(to_sys)
            else:
                to_kwd = self._to_kwd.get(code)
                if to_kwd is not None:
                    flags.add(to_kwd)
        return frozenset(flags)

# === BLOCK 4 (label=human, source_idx=line6038_human, name=on_service_modify) ===
def on_service_modify(self, svc_ref, old_properties):
        """
        Called when a service has been modified in the framework

        :param svc_ref: A service reference
        :param old_properties: Previous properties values
        :return: A tuple (added, (service, reference)) if the dependency has
                 been changed, else None
        """
        with self._lock:
            if svc_ref not in self.services:
                # A previously registered service now matches our filter
                return self.on_service_arrival(svc_ref)
            else:
                # Get the property values
                service = self.services[svc_ref]
                old_value = old_properties.get(self._key)
                prop_value = svc_ref.get_property(self._key)

                if old_value != prop_value:
                    # Key changed
                    if prop_value is not None or self._allow_none:
                        # New property accepted
                        if old_value is not None or self._allow_none:
                            self.__remove_service(old_value, service)

                        self.__store_service(prop_value, service)

                        # Notify the property modification, with a value change
                        self._ipopo_instance.update(
                            self, service, svc_ref, old_properties, True
                        )
                    else:
                        # Consider the service as gone
                        self.__remove_service(old_value, service)
                        del self.services[svc_ref]
                        self._ipopo_instance.unbind(self, service, svc_ref)
                else:
                    # Simple property update
                    self._ipopo_instance.update(
                        self, service, svc_ref, old_properties, False
                    )

            return None

# === BLOCK 5 (label=lm, source_idx=line5847_lm, name=find_by_id) ===
def find_by_id(self, user, params={}, **options): 
        """Returns the full user record for the single user with the provided ID.

        Parameters
        ----------
        user : {String} An identifier for the user. Can be one of an email address,
        the globally unique identifier for the user, or the keyword `me`
        to indicate the current user making the request.
        [params] : {Object} Parameters for the request
        """
        if user == 'me':
            user = options.get('current_user_id', user)

        endpoint = f"/users/{user}"
        return self.request('GET', endpoint, params=params, **options)

# === BLOCK 6 (label=lm, source_idx=line7275_lm, name=__get_new) ===
def __get_new(self, hueobjecttype):
        """
        Get a list of newly found Hue object
        """
        new_objects = []
        for obj in self.objects:
            if obj.type == hueobjecttype and obj.is_new:
                new_objects.append(obj)
                obj.is_new = False
        return new_objects
