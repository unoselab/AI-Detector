# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=lm, source_idx=line8307_lm, name=plot_cast) ===
def plot_cast(df, secondary_y=False, label=None, *args, **kwargs):
    """
    Plot a CTD variable with the index in the y-axis instead of x-axis.

    """
    if secondary_y:
        ax = df.plot(secondary_y=True, *args, **kwargs)
    else:
        ax = df.plot(*args, **kwargs)

    ax.set_ylabel(label)
    ax.set_xlabel('Depth (m)')

    return ax

# === BLOCK 2 (label=human, source_idx=line3505_human, name=_matmul_with_relative_keys_2d) ===
def _matmul_with_relative_keys_2d(x, y, heads_share_relative_embedding):
  """Helper function for dot_product_unmasked_self_attention_relative_2d."""
  if heads_share_relative_embedding:
    ret = tf.einsum("bhxyd,md->bhxym", x, y)
  else:
    ret = tf.einsum("bhxyd,hmd->bhxym", x, y)
  return ret

# === BLOCK 3 (label=lm, source_idx=line1126_lm, name=wxRect_to_Rect) ===
def wxRect_to_Rect(self, wr):
        """ Return a shrunk fitz.Rect for given wx.Rect."""
        return Rect(wr.x, wr.y, wr.width, wr.height)

# === BLOCK 4 (label=human, source_idx=line6483_human, name=authorized_signup_handler) ===
def authorized_signup_handler(resp, remote, *args, **kwargs):
    """Handle sign-in/up functionality.

    :param remote: The remote application.
    :param resp: The response.
    :returns: Redirect response.
    """
    # Remove any previously stored auto register session key
    session.pop(token_session_key(remote.name) + '_autoregister', None)

    # Store token in session
    # ----------------------
    # Set token in session - token object only returned if
    # current_user.is_autenticated().
    token = response_token_setter(remote, resp)
    handlers = current_oauthclient.signup_handlers[remote.name]

    # Sign-in/up user
    # ---------------
    if not current_user.is_authenticated:
        account_info = handlers['info'](resp)
        account_info_received.send(
            remote, token=token, response=resp, account_info=account_info
        )

        user = oauth_get_user(
            remote.consumer_key,
            account_info=account_info,
            access_token=token_getter(remote)[0],
        )

        if user is None:
            # Auto sign-up if user not found
            form = create_csrf_disabled_registrationform()
            form = fill_form(
                form,
                account_info['user']
            )
            user = oauth_register(form)

            # if registration fails ...
            if user is None:
                # requires extra information
                session[
                    token_session_key(remote.name) + '_autoregister'] = True
                session[token_session_key(remote.name) +
                        '_account_info'] = account_info
                session[token_session_key(remote.name) +
                        '_response'] = resp
                db.session.commit()
                return redirect(url_for(
                    '.signup',
                    remote_app=remote.name,
                ))

        # Authenticate user
        if not oauth_authenticate(remote.consumer_key, user,
                                  require_existing_link=False):
            return current_app.login_manager.unauthorized()

        # Link account
        # ------------
        # Need to store token in database instead of only the session when
        # called first time.
        token = response_token_setter(remote, resp)

    # Setup account
    # -------------
    if not token.remote_account.extra_data:
        account_setup = handlers['setup'](token, resp)
        account_setup_received.send(
            remote, token=token, response=resp, account_setup=account_setup
        )
        db.session.commit()
        account_setup_committed.send(remote, token=token)
    else:
        db.session.commit()

    # Redirect to next
    next_url = get_session_next_url(remote.name)
    if next_url:
        return redirect(next_url)
    return redirect(url_for('invenio_oauthclient_settings.index'))

# === BLOCK 5 (label=lm, source_idx=line7865_lm, name=_validate_schema) ===
def _validate_schema(self):
        """
        Validates provider schema for syntax issues. Raises :class:`~notifiers.exceptions.SchemaError` if relevant

        :raises: :class:`~notifiers.exceptions.SchemaError`
        """
        try:
            self.schema.validate(self.provider_schema)
        except SchemaError as e:
            raise SchemaError(e)

# === BLOCK 6 (label=human, source_idx=line6295_human, name=do_vim) ===
def do_vim(self, arg):
        """v(im)
    switch to debugging with vimpdb"""
        self.vimpdb = make_instance()
        self.vimpdb.set_trace_without_step(self.botframe)
        if self.has_gone_up():
            self.vimpdb.update_state(self)
            self.vimpdb.cmdloop()
        else:
            self.vimpdb.interaction(self.curframe, None)
        return 1
