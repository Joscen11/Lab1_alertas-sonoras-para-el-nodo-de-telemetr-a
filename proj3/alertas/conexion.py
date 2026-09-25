"""
alertas/conexion.py
Detector de conexion de red - LABORATORIO

Version corregida: el ciclo principal (nucleo.ciclo) NUNCA abre un
socket. Antes, comprobar_conexion() se llamaba directamente dentro de
detectar(), y esa llamada bloqueaba hasta config.TIEMPO_ESPERA_RED
segundos -- justo cuando la red esta caida, que es el peor momento
posible para congelar el dashboard.

Ahora, igual que ReproductorAlertas, la prueba real de conectividad
corre en un hilo en segundo plano que se ejecuta cada
config.PERIODO_COMPROBACION_RED segundos y solo actualiza una bandera
booleana protegida por un lock. detectar() -- llamado desde
nucleo.ciclo() -- unicamente LEE esa bandera: es una operacion de
microsegundos, nunca espera una respuesta de red.
"""

import socket
import threading
import time

import config


class DetectorConexion:
    """Detecta cambios y recordatorios de conexion de red."""

    def __init__(self):
        self.estado_anterior = None
        self.momento_desconexion = None

        # LABORATORIO - bandera compartida entre el hilo de sondeo y el
        # ciclo principal. None = todavia no hay ninguna medicion.
        self._conectada_actual = None
        self._lock = threading.Lock()

        # LABORATORIO - hilo de sondeo: el UNICO lugar del programa que
        # abre un socket. Se ejecuta en segundo plano y nunca es llamado
        # desde nucleo.ciclo().
        self.activo = True
        self._hilo = threading.Thread(target=self._sondear, daemon=True)
        self._hilo.start()

    def _probar_conexion(self):
        """Prueba real de conectividad (puede tardar hasta
        TIEMPO_ESPERA_RED segundos). Solo la llama self._hilo, nunca el
        ciclo principal."""
        try:
            socket.create_connection(
                (config.HOST_PRUEBA_RED, config.PUERTO_PRUEBA_RED),
                timeout=config.TIEMPO_ESPERA_RED,
            )
            return True
        except OSError:
            return False

    def _sondear(self):
        """Bucle del hilo en segundo plano."""
        while self.activo:
            conectada = self._probar_conexion()
            with self._lock:
                self._conectada_actual = conectada
            time.sleep(config.PERIODO_COMPROBACION_RED)

    def comprobar_conexion(self):
        """Ultimo estado conocido de la red, leido sin bloquear.

        No abre ningun socket: solo lee la bandera que actualiza
        _sondear(). Devuelve None si el hilo aun no hizo su primera
        medicion (los primeros instantes tras iniciar el programa).
        """
        with self._lock:
            return self._conectada_actual

    def detectar(self):
        """Detecta los eventos de conexion. No bloquea."""
        conectada = self.comprobar_conexion()

        if conectada is None:
            return []  # el hilo de sondeo todavia no midio nada

        if self.estado_anterior is None:
            self.estado_anterior = conectada
            if not conectada:
                self.momento_desconexion = time.monotonic()
                return [("red_desconectada", {"conectada": False})]
            return []

        eventos = []

        if self.estado_anterior and not conectada:
            self.momento_desconexion = time.monotonic()
            eventos.append(("red_desconectada", {"conectada": False}))

        elif not self.estado_anterior and conectada:
            self.momento_desconexion = None
            eventos.append(("red_conectada", {"conectada": True}))

        elif not conectada and self.momento_desconexion is not None:
            tiempo_desconectada = time.monotonic() - self.momento_desconexion
            if tiempo_desconectada >= config.RECORDATORIO_RED_S:
                eventos.append((
                    "red_sigue_desconectada",
                    {"conectada": False, "segundos": tiempo_desconectada},
                ))
                self.momento_desconexion = time.monotonic()

        self.estado_anterior = conectada
        return eventos

    def detener(self):
        """Detiene el hilo de sondeo."""
        self.activo = False
