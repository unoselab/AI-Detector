# Auto-generated mixed-authorship test sample.
# Block boundaries are marked with a `# === BLOCK ... ===` comment.
# Markers include the ground-truth label; agc_detector strips them at scan time.

# === BLOCK 1 (label=human, source_idx=line5228_human, name=add) ===
def add(self, coro, args=(), kwargs={}, first=True):
        """Add a coroutine in the scheduler. You can add arguments
        (_args_, _kwargs_) to init the coroutine with."""
        assert callable(coro), "'%s' not a callable object" % coro
        coro = coro(*args, **kwargs)
        if first:
            self.active.append( (None, coro) )
        else:
            self.active.appendleft( (None, coro) )
        return coro

# === BLOCK 2 (label=lm, source_idx=line2043_lm, name=_convert_point) ===
def _convert_point(self, metric, ts, point, sd_point):
        """Convert an OC metric point to a SD point."""
        if point is None:
            return None

        if metric.type == 'gauge':
            return sd_point.set_value(point)
        elif metric.type == 'counter':
            return sd_point.set_value(point)
        elif metric.type == 'histogram':
            return sd_point.set_value(point)
        elif metric.type =='summary':
            return sd_point.set_value(point)
        elif metric.type == 'untyped':
            return sd_point.set_value(point)
        else:
            raise Exception('Unknown metric type: %s' % metric.type)

# === BLOCK 3 (label=lm, source_idx=line322_lm, name=set_editor_cursor) ===
def set_editor_cursor(self, editor, cursor):
        """Set the cursor of an editor."""
        self.editor_cursor = cursor
        self.editor_cursor.set_editor(editor)

# === BLOCK 4 (label=lm, source_idx=line3047_lm, name=discover_slave) ===
async def discover_slave(self, service, timeout, **kwargs):
        """Perform Slave discovery for specified service."""
        self.logger.debug("Discovering slave for service: %s", service)
        return await self.discover_service(
            service, timeout, **kwargs
        )

# === BLOCK 5 (label=human, source_idx=line478_human, name=pkcs_i2osp) ===
def pkcs_i2osp(x,xLen):
    """
    Converts a long (the first parameter) to the associated byte string
    representation of length l (second parameter). Basically, the length
    parameters allow the function to perform the associated padding.

    Input : x        nonnegative integer to be converted
            xLen     intended length of the resulting octet string

    Output: x        corresponding nonnegative integer

    Reverse function is pkcs_os2ip().
    """
    z = number.long_to_bytes(x)
    padlen = max(0, xLen-len(z))
    return '\x00'*padlen + z

# === BLOCK 6 (label=human, source_idx=line4683_human, name=BuscarCertConSaldoDisponible) ===
def BuscarCertConSaldoDisponible(self, cuit_depositante=None,
                        cod_grano=2, campania=1314, coe=None, 
                        fecha_emision_des=None,
                        fecha_emision_has=None,
                 ):
        """Devuelve los certificados de depósito en los que un productor tiene
        saldo disponible para Liquidar/Retirar/Transferir"""

        ret = self.client.cgBuscarCertConSaldoDisponible(
                    auth={
                        'token': self.Token, 'sign': self.Sign,
                        'cuit': self.Cuit, },
                    cuitDepositante=cuit_depositante or self.Cuit,
                    codGrano=cod_grano, campania=campania,
                    coe=coe,
                    fechaEmisionDes=fecha_emision_des,
                    fechaEmisionHas=fecha_emision_has,
                        )['oReturn']
        self.__analizar_errores(ret)
        array = ret.get('certificado', [])
        self.Excepcion = self.Traceback = ""
        self.params_out['certificados'] = []
        for cert in array:
            self.params_out['certificados'].append(dict(
                coe=cert['coe'],
                tipo_certificado=cert['tipoCertificado'],
                campania=cert['campania'],
                cuit_depositante=cert['cuitDepositante'],
                cuit_depositario=cert['cuitDepositario'],
                nro_planta=cert['nroPlanta'],
                kilos_disponibles=cert['kilosDisponibles'],
                cod_grano=cert['codGrano'],
            ))
        return True
