"""
config.py
Parametros de configuracion del nodo de telemetria.
Todo lo que puede cambiar entre una instalacion y otra vive aqui.
Ningun otro archivo del proyecto debe contener un numero literal.
Unidad 2 - Programacion en Python para sistemas IoT
Facultad de Ingenieria de Sistemas Computacionales - UTP
"""
import os

# --------------------------------------------------------------------------
# Identificacion del nodo
# --------------------------------------------------------------------------
NODO = "laptop-joselyn"
UBICACION = "Laboratorio 3 - UTP - FISC"

# --------------------------------------------------------------------------
# Periodos de muestreo, en segundos.
# Cada metrica tiene el suyo: leer los procesos es caro, leer la CPU no.
# --------------------------------------------------------------------------
PERIODO_RAPIDO = 1.0   # cpu, memoria, red
PERIODO_LENTO = 5.0    # disco, procesos, bateria
PERIODO_REPORTE = 30.0 # resumen periodico hacia la bitacora
REFRESCO_MS = 200      # cada cuanto refresca el dashboard (milisegundos)

# --------------------------------------------------------------------------
# Umbrales. Dos valores por metrica: uno para entrar en alarma y otro,
# mas bajo, para salir de ella. Esa diferencia es la HISTERESIS y evita
# que una lectura oscilando en el limite genere decenas de eventos falsos.
# --------------------------------------------------------------------------
CPU_ALTO = 70.0
CPU_BAJO = 50.0
CPU_NUCLEO_SATURADO = 90.0  # un nucleo individual por encima de esto

# LABORATORIO - bajados de 85.0/75.0 (valor original) a 50.0/40.0 para
# poder disparar cpu_alta/ram_alta con facilidad durante la demo en
# clase. Regresar a 85.0/75.0 antes de una instalacion real.
RAM_ALTA = 50.0
RAM_BAJA = 40.0

DISCO_LLENO = 90.0     # porcentaje de ocupacion
DISCO_ALIVIADO = 85.0

RED_PICO_KBS = 500.0   # kilobytes por segundo
RED_CALMA_KBS = 200.0

BATERIA_BAJA = 20.0
BATERIA_RECUPERADA = 30.0

PROCESO_PESADO = 50.0  # % de CPU de un solo proceso

# Variacion brusca entre dos muestras consecutivas: evento de anomalia.
SALTO_ANOMALO = 40.0

# --------------------------------------------------------------------------
# Ventana movil y almacenamiento
# --------------------------------------------------------------------------
VENTANA = 10            # muestras que se promedian para evaluar el umbral
MAX_EVENTOS_LOG = 200    # eventos que se conservan en pantalla
ARCHIVO_BITACORA = "bitacora.json"

# --------------------------------------------------------------------------
# Unidad de disco a vigilar. Se detecta sola segun el sistema operativo.
# --------------------------------------------------------------------------
UNIDAD_DISCO = "C:\\" if os.name == "nt" else "/"

# Cantidad de procesos que se muestran en el ranking.
TOP_PROCESOS = 8

# Procesos del sistema que no vale la pena reportar: en Linux los
# 'kworker' y 'kthread' aparecen y desaparecen constantemente y llenarian
# la bitacora de ruido.
PROCESOS_IGNORADOS = ("kworker", "kthread", "ksoftirqd", "migration",
                      "rcu_", "irq/", "svchost")

# ==========================================================================
# ALERTAS SONORAS - LABORATORIO
# ==========================================================================

# LABORATORIO - Modo silencioso: True = no suena nada (para el salon).
# Tambien se activa desde la consola con:  python main.py --silencio
MODO_SILENCIOSO = False

# LABORATORIO - Reproductor de alertas
INTERVALO_COLA_SONIDO = 0.05    # espera del hilo cuando la cola esta vacia (s)
MAX_COLA_SONIDOS = 10           # alertas pendientes como maximo
ENFRIAMIENTO_ALERTA_S = 5.0     # un mismo tipo de alerta no se repite antes
MS_POR_SEGUNDO = 1000           # conversion de milisegundos a segundos

# LABORATORIO - Conexion de red
PERIODO_COMPROBACION_RED = 3.0  # cada cuanto el hilo prueba la conexion (s)
RECORDATORIO_RED_S = 10.0       # recordatorio mientras siga desconectada (s)
HOST_PRUEBA_RED = "8.8.8.8"
PUERTO_PRUEBA_RED = 53
TIEMPO_ESPERA_RED = 1.0


# ==========================================================================
# SONIDOS: (frecuencia en Hz, duracion en ms). Frecuencia 0 = pausa.
# Cada alerta tiene un ritmo y un tono propios para reconocerla de oido.
# ==========================================================================

# LABORATORIO - CPU: tres pitidos agudos y cortos (urgente, tipo alarma)
SONIDO_CPU = (
    (1000, 120), (37, 80),
    (1000, 120), (37, 80),
    (1000, 120),
)

# LABORATORIO - Memoria: un solo tono grave y largo (algo "pesado")
SONIDO_MEMORIA = (
    (350, 700),
)

# LABORATORIO - Trafico: arpegio ascendente rapido (subida de flujo)
SONIDO_TRAFICO = (
    (600, 90),
    (900, 90),
    (1200, 90),
)

# LABORATORIO - Red desconectada: tres tonos descendentes (se cae)
SONIDO_RED_DESCONECTADA = (
    (300, 250),
    (200, 500),
    (300, 500),
)

# LABORATORIO - Red conectada: acorde mayor ascendente (buena noticia)
SONIDO_RED_CONECTADA = (
    (500, 150),
    (700, 150),
    (900, 150),
    (1200, 400),
)

# LABORATORIO - Red sigue desconectada: golpes graves con pausas (recordatorio)
SONIDO_RED_SIGUE_DESCONECTADA = (
    (300, 200),
    (300, 200),
    (500, 400),
)

# LABORATORIO - Cargador conectado: dos tonos cortos y ascendentes (aviso
# breve y positivo, mucho mas suave que red_conectada porque no es critico)
SONIDO_CARGADOR_CONECTADO = (
    (700, 90),
    (1000, 150),
)

# LABORATORIO - Cargador desconectado: dos tonos cortos y descendentes
# (aviso informativo, no de alarma: seguir con bateria no es un problema)
SONIDO_CARGADOR_DESCONECTADO = (
    (700, 150),
    (500, 150),
)