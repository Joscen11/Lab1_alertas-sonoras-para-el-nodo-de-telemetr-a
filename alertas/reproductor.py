"""
alertas/reproductor.py
Reproductor de alertas sonoras - LABORATORIO

El reproductor usa una cola (deque) y un hilo independiente para
evitar bloquear el ciclo principal del nodo: encolar() solo agrega un
elemento al deque y regresa de inmediato; el hilo _procesar_cola va
tomando alertas y reproduciendolas una por una en segundo plano.
"""

from collections import deque
import threading
import time

import config


class ReproductorAlertas:
    """Administra la reproduccion no bloqueante de alertas."""

    def __init__(self):
        # Cola acotada: en una rafaga de eventos no crece
        # sin limite: si se llena, deque descarta sola el elemento mas
        # viejo al agregar uno nuevo.
        self.cola = deque(maxlen=config.MAX_COLA_SONIDOS)
        self.activo = True

        # Ultima vez que se ENCOLO cada tipo de alerta,
        # para el enfriamiento: evita que el mismo tipo se repita
        # demasiado rapido si el evento que lo dispara ocurre varias
        # veces seguidas.
        self._ultimo_encolado = {}

        self.hilo = threading.Thread(
            target=self._procesar_cola,
            daemon=True
        )
        self.hilo.start()

    def encolar(self, tipo_alerta):
        """Agrega una alerta a la cola para ser reproducida."""

        # Modo silencioso: el evento se sigue registrando
        # en la bitacora
        if config.MODO_SILENCIOSO:
            return

        #Enfriamiento por tipo de alerta.
        ahora = time.monotonic()
        ultimo = self._ultimo_encolado.get(tipo_alerta)
        if ultimo is not None and (ahora - ultimo) < config.ENFRIAMIENTO_ALERTA_S:
            return
        self._ultimo_encolado[tipo_alerta] = ahora

        self.cola.append(tipo_alerta)

    def _obtener_sonido(self, tipo_alerta):
        """
        Obtiene la secuencia de sonidos correspondiente
        al tipo de alerta.
        """
        sonidos = {
            "cpu": config.SONIDO_CPU,
            "memoria": config.SONIDO_MEMORIA,
            "trafico": config.SONIDO_TRAFICO,
            "red_desconectada": config.SONIDO_RED_DESCONECTADA,
            "red_conectada": config.SONIDO_RED_CONECTADA,
            "red_sigue_desconectada": config.SONIDO_RED_SIGUE_DESCONECTADA,
        }

        return sonidos.get(tipo_alerta)

    def _reproducir_sonido(self, secuencia):
        """
        Reproduce una secuencia de frecuencias y duraciones.
        """
        try:
            import winsound

            for frecuencia, duracion in secuencia:
                if not self.activo:
                    break

                winsound.Beep(frecuencia, duracion)

        except ImportError:
            print("\a", end="", flush=True)

    def _procesar_cola(self):
        """
        Procesa las alertas de la cola en segundo plano.
        """
        while self.activo:

            if self.cola:
                tipo_alerta = self.cola.popleft()
                secuencia = self._obtener_sonido(tipo_alerta)

                if secuencia is not None:
                    self._reproducir_sonido(secuencia)

            else:
                time.sleep(config.INTERVALO_COLA_SONIDO)

    def detener(self):
        """Detiene el reproductor."""
        self.activo = False
