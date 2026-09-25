"""
pruebas/test_alertas.py
Pruebas unitarias del paquete alertas - LABORATORIO

Cubren:
  - Que encolar() nunca bloquea, aunque reproducir un sonido tarde.
  - Que el modo silencioso realmente impide que algo se encole.
  - Que el enfriamiento evita repetir el mismo tipo de alerta muy rapido.
  - Que la cola de sonidos no crece sin limite.
  - La maquina de estados de DetectorConexion: primera lectura,
    flanco de perdida, flanco de recuperacion y el recordatorio por
    tiempo (que no se dispare antes de tiempo y que si se dispare
    despues del periodo configurado).
"""

import os
import sys
import time
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
from alertas.reproductor import ReproductorAlertas
from alertas.conexion import DetectorConexion


class TestReproductorAlertas(unittest.TestCase):

    def setUp(self):
        self._silencioso_original = config.MODO_SILENCIOSO
        self._enfriamiento_original = config.ENFRIAMIENTO_ALERTA_S
        config.MODO_SILENCIOSO = False

    def tearDown(self):
        config.MODO_SILENCIOSO = self._silencioso_original
        config.ENFRIAMIENTO_ALERTA_S = self._enfriamiento_original

    def test_encolar_no_bloquea_el_llamador(self):
        """encolar() debe regresar casi de inmediato, aunque reproducir
        un sonido (simulado aqui como lento) tarde mucho."""
        rep = ReproductorAlertas()
        rep._reproducir_sonido = lambda secuencia: time.sleep(0.5)

        inicio = time.monotonic()
        rep.encolar("cpu")
        duracion = time.monotonic() - inicio

        rep.detener()
        self.assertLess(
            duracion, 0.05,
            "encolar() no deberia esperar a que el sonido termine")

    def test_modo_silencioso_no_encola_nada(self):
        config.MODO_SILENCIOSO = True
        rep = ReproductorAlertas()
        rep.encolar("cpu")
        rep.detener()
        self.assertEqual(len(rep.cola), 0)

    def test_enfriamiento_evita_repeticion_inmediata(self):
        config.ENFRIAMIENTO_ALERTA_S = 5.0
        rep = ReproductorAlertas()
        rep.activo = False  # el hilo no vacia la cola durante la prueba
        rep.encolar("cpu")
        rep.encolar("cpu")  # deberia ser descartado por enfriamiento
        self.assertEqual(len(rep.cola), 1)
        rep.detener()

    def test_enfriamiento_no_afecta_tipos_distintos(self):
        config.ENFRIAMIENTO_ALERTA_S = 5.0
        rep = ReproductorAlertas()
        rep.activo = False
        rep.encolar("cpu")
        rep.encolar("memoria")
        self.assertEqual(len(rep.cola), 2)
        rep.detener()

    def test_cola_no_crece_sin_limite(self):
        rep = ReproductorAlertas()
        rep.activo = False
        for i in range(config.MAX_COLA_SONIDOS + 5):
            rep.cola.append(f"tipo_{i}")
        self.assertEqual(len(rep.cola), config.MAX_COLA_SONIDOS)
        rep.detener()

    def test_catalogo_tiene_sonido_de_cargador_conectado(self):
        rep = ReproductorAlertas()
        rep.detener()
        self.assertEqual(
            rep._obtener_sonido("cargador_conectado"),
            config.SONIDO_CARGADOR_CONECTADO,
        )

    def test_catalogo_tiene_sonido_de_cargador_desconectado(self):
        rep = ReproductorAlertas()
        rep.detener()
        self.assertEqual(
            rep._obtener_sonido("cargador_desconectado"),
            config.SONIDO_CARGADOR_DESCONECTADO,
        )


class TestDetectorConexion(unittest.TestCase):

    def _detector_controlado(self):
        """Crea un DetectorConexion y detiene su hilo de sondeo real,
        para poder fijar el estado de conexion a mano en cada prueba."""
        det = DetectorConexion()
        det.detener()
        det.estado_anterior = None
        det.momento_desconexion = None
        det._conectada_actual = None
        return det

    def test_sin_medicion_no_genera_eventos(self):
        det = self._detector_controlado()
        self.assertEqual(det.detectar(), [])

    def test_primera_lectura_desconectada_genera_evento(self):
        det = self._detector_controlado()
        det._conectada_actual = False
        eventos = det.detectar()
        nombres = [nombre for nombre, _ in eventos]
        self.assertEqual(nombres, ["red_desconectada"])

    def test_primera_lectura_conectada_no_genera_evento(self):
        det = self._detector_controlado()
        det._conectada_actual = True
        eventos = det.detectar()
        self.assertEqual(eventos, [])

    def test_flanco_de_perdida_de_conexion(self):
        det = self._detector_controlado()
        det._conectada_actual = True
        det.detectar()  # primera lectura: fija estado_anterior=True
        det._conectada_actual = False
        eventos = det.detectar()
        nombres = [nombre for nombre, _ in eventos]
        self.assertEqual(nombres, ["red_desconectada"])

    def test_flanco_de_recuperacion(self):
        det = self._detector_controlado()
        det._conectada_actual = False
        det.detectar()
        det._conectada_actual = True
        eventos = det.detectar()
        nombres = [nombre for nombre, _ in eventos]
        self.assertEqual(nombres, ["red_conectada"])

    def test_recordatorio_no_se_dispara_antes_de_tiempo(self):
        det = self._detector_controlado()
        det._conectada_actual = False
        det.detectar()               # dispara red_desconectada
        eventos = det.detectar()     # instantes despues: aun no toca
        self.assertEqual(eventos, [])

    def test_recordatorio_se_dispara_tras_el_periodo(self):
        det = self._detector_controlado()
        det._conectada_actual = False
        det.detectar()
        # Simulamos que paso el tiempo configurado sin usar sleep real.
        det.momento_desconexion -= (config.RECORDATORIO_RED_S + 1)
        eventos = det.detectar()
        nombres = [nombre for nombre, _ in eventos]
        self.assertEqual(nombres, ["red_sigue_desconectada"])

    def test_detectar_no_bloquea(self):
        """detectar() solo debe leer una bandera: debe ser casi
        instantaneo aunque TIEMPO_ESPERA_RED sea de 1 segundo."""
        det = self._detector_controlado()
        det._conectada_actual = True
        det.detectar()
        det._conectada_actual = False

        inicio = time.monotonic()
        det.detectar()
        duracion = time.monotonic() - inicio

        self.assertLess(
            duracion, 0.01,
            "detectar() no deberia abrir un socket ni esperar nada")


if __name__ == "__main__":
    unittest.main(verbosity=2)
