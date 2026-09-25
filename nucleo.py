"""
nucleo.py
Motor de monitoreo. Aqui esta el bucle orientado a eventos.

Diseno clave: el ciclo NO usa time.sleep() para esperar. Cada metrica
guarda su propia marca de tiempo y se lee cuando le toca. Asi un solo
ciclo atiende tareas con periodos distintos sin bloquearse, que es el
patron recomendado de la Unidad 2.

La funcion ciclo() no bloquea: se puede llamar cada 200 ms desde un
dashboard grafico o desde un bucle de consola. Ella decide sola que
hay que leer en ese instante.
"""

# LABORATORIO
from alertas.reproductor import ReproductorAlertas

# LABORATORIO
from alertas.conexion import DetectorConexion

import time

import config
import sensores
import eventos
import almacenamiento as registro


# --------------------------------------------------------------------------
# Grupos de sensores
# --------------------------------------------------------------------------

# Que metricas se leen rapido y cuales despacio. Consultar los procesos
# es caro; consultar la CPU no lo es.
GRUPO_RAPIDO = ["cpu", "memoria", "red"]
GRUPO_LENTO = ["disco", "procesos", "bateria"]


# --------------------------------------------------------------------------
# Marcas de tiempo
# --------------------------------------------------------------------------

# Marcas de tiempo: la ultima vez que se ejecuto cada tarea.
_marcas = {
    "rapido": 0.0,
    "lento": 0.0,
    "reporte": 0.0
}


# --------------------------------------------------------------------------
# Estado del nodo
# --------------------------------------------------------------------------

# Ultima lectura conocida de cada metrica, para que el dashboard siempre
# tenga algo que mostrar aunque en este instante no toque leer.
_ultimas = {}

_activos = []


# ==========================================================================
# Componentes de alertas
# ==========================================================================
_reproductor_alertas = None
_detector_conexion = None


# --------------------------------------------------------------------------
# Inicializacion
# --------------------------------------------------------------------------

def iniciar():
    """Detecta que sensores existen en este equipo y prepara el ciclo."""

    global _activos

    # LABORATORIO
    global _reproductor_alertas

    # LABORATORIO
    global _detector_conexion

    _activos = sensores.disponibles()

    ahora = time.time()

    for clave in _marcas:
        _marcas[clave] = ahora

    # ----------------------------------------------------------------------
    # Inicializar el reproductor de alertas y el detector de conexion.
    # ----------------------------------------------------------------------
    _reproductor_alertas = ReproductorAlertas()
    _detector_conexion = DetectorConexion()

    # ----------------------------------------------------------------------
    # Lectura de calentamiento
    # ----------------------------------------------------------------------

    # Lectura de calentamiento: se descarta. La CPU siempre devuelve 0.0
    # la primera vez y la red necesita dos contadores para calcular una
    # velocidad. Sin este paso, la primera vuelta generaria eventos falsos.

    for clave in _activos:
        _ultimas[clave] = sensores.leer(clave)

    ausentes = [
        c for c in sensores.LECTORES
        if c not in _activos
    ]

    for clave in ausentes:
        eventos.atender(
            "sensor_ausente",
            {"metrica": clave}
        )

    registro.registrar_evento(
        "INFO",
        "sistema",
        f"Nodo {config.NODO} iniciado | sensores activos: "
        f"{', '.join(_activos)}"
    )

    return _activos


# --------------------------------------------------------------------------
# Lectura de grupos
# --------------------------------------------------------------------------

def _leer_grupo(claves):
    """Lee un grupo de metricas y despacha los eventos que provoquen."""

    nuevos = []

    for clave in claves:

        if clave not in _activos:
            continue

        lectura = sensores.leer(clave)

        _ultimas[clave] = lectura

        if lectura is not None:
            registro.agregar(
                clave,
                lectura["valor"]
            )

        for nombre, dato in eventos.detectar(
            clave,
            lectura
        ):

            # --------------------------------------------------------------
            # Atender el evento normalmente.
            # --------------------------------------------------------------

            nuevos.append(
                eventos.atender(
                    nombre,
                    dato
                )
            )

            # --------------------------------------------------------------
            # Asociar los eventos existentes con sus sonidos.
            # --------------------------------------------------------------

            sonidos = {
                "cpu_alta": "cpu",
                "ram_alta": "memoria",
                "red_pico": "trafico",
            }

            tipo_sonido = sonidos.get(nombre)

            if (
                tipo_sonido is not None
                and _reproductor_alertas is not None
            ):
                _reproductor_alertas.encolar(
                    tipo_sonido
                )

    return nuevos


# --------------------------------------------------------------------------
# Ciclo principal
# --------------------------------------------------------------------------

def ciclo():
    """Una vuelta del bucle de monitoreo. No bloquea.

    Devuelve un diccionario con las ultimas lecturas y con los eventos
    generados en esta vuelta.
    """

    ahora = time.time()

    nuevos = []

    # ======================================================================
    # Detectar cambios en la conexion de red.
    # ======================================================================

    if _detector_conexion is not None:

        # LABORATORIO
        eventos_conexion = _detector_conexion.detectar()

        # LABORATORIO
        for nombre, dato in eventos_conexion:

            # LABORATORIO
            nuevos.append(
                eventos.atender(
                    nombre,
                    dato
                )
            )

            # LABORATORIO
            if _reproductor_alertas is not None:
                _reproductor_alertas.encolar(
                    nombre
                )

    # ----------------------------------------------------------------------
    # Grupo rapido
    # ----------------------------------------------------------------------

    if ahora - _marcas["rapido"] >= config.PERIODO_RAPIDO:

        nuevos += _leer_grupo(
            GRUPO_RAPIDO
        )

        _marcas["rapido"] = ahora

    # ----------------------------------------------------------------------
    # Grupo lento
    # ----------------------------------------------------------------------

    if ahora - _marcas["lento"] >= config.PERIODO_LENTO:

        nuevos += _leer_grupo(
            GRUPO_LENTO
        )

        _marcas["lento"] = ahora

    # ----------------------------------------------------------------------
    # Evento por tiempo: reporte
    # ----------------------------------------------------------------------

    # Evento por tiempo: no lo dispara ningun sensor, lo dispara el reloj.
    if ahora - _marcas["reporte"] >= config.PERIODO_REPORTE:

        nuevos.append(
            generar_reporte()
        )

        _marcas["reporte"] = ahora

    return {
        "lecturas": dict(_ultimas),
        "eventos": nuevos
    }


# --------------------------------------------------------------------------
# Generacion de reportes
# --------------------------------------------------------------------------

def generar_reporte():
    """Resume el periodo, lo guarda en la bitacora y vacia el historial."""

    datos = registro.resumen()

    registro.guardar_bitacora(
        datos
    )

    registro.limpiar_periodo()

    return eventos.atender(
        "reporte",
        {
            "metricas": len(
                datos["metricas"]
            )
        }
    )


# --------------------------------------------------------------------------
# Consultas
# --------------------------------------------------------------------------

def lecturas():
    """Ultimas lecturas conocidas, sin forzar una nueva medicion."""

    return dict(_ultimas)


def activos():
    return list(_activos)


# --------------------------------------------------------------------------
# Ejecucion directa
# --------------------------------------------------------------------------

if __name__ == "__main__":

    iniciar()

    print()
    print("=" * 60)
    print("MONITOR IoT EJECUTANDOSE")
    print("Desconecta el Wi-Fi para probar la alerta de red.")
    print("Presiona Ctrl+C para terminar.")
    print("=" * 60)
    print()

    try:
        while True:

            resultado = ciclo()

            for e in resultado["eventos"]:

                print(
                    f"{e['hora']} "
                    f"[{e['nivel']}] "
                    f"{e['mensaje']}"
                )

            # LABORATORIO
            time.sleep(config.REFRESCO_MS / config.MS_POR_SEGUNDO)

    except KeyboardInterrupt:

        print()
        print("Monitor detenido por el usuario.")

    finally:

        if _reproductor_alertas is not None:
            _reproductor_alertas.detener()

        # LABORATORIO
        if _detector_conexion is not None:
            _detector_conexion.detener()