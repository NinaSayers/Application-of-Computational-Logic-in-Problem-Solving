"""
Script para ejecutar pruebas con CaDiCaL 2.1.3 sobre instancias CNF usando distintas heurísticas.

Requisitos:
- Tener CaDiCaL 2.1.3 instalado y accesible desde el PATH como 'cadical'.
- Colocar las instancias CNF en la carpeta './problemas_sat/'.
- Ejecutar con: python3 experimento_cadical.py

El resultado se guarda en 'resultados_experimento.csv'.
El análisis estadístico posterior se realiza por separado (p. ej., en pandas o R).
"""

import os
import subprocess
import csv
import time
import re
from collections import Counter

# ====================================================
#         CONFIGURACIÓN DE FLAGS DE CADICAL
# ====================================================
FLAG_VSIDS = "--score=false"  # VSIDS implícito
FLAG_DLIS_TRUE = "--dlis=true --score=false --bump=false --bumpreason=false"
FLAG_DLIS_FALSE = "--dlis=false"
FLAG_RESTART = "--restart=true"
FLAG_NO_RESTART = "--restart=false"
FLAG_STATS = "--stats"
FLAG_TIME = "-t 360"
CADICAL_EXECUTABLE = "./cadical/build/cadical"  # Ajusta la ruta si es necesario
# ====================================================

INPUT_DIR = "./run/media/massy/massyta/universidad_nuevo/tesis/muestra_representativa/"
OUTPUT_CSV = "resultados_experimento.csv"

COMBINACIONES = [
    {"vsids": 1, "dlis": 0, "restart": 1},
    {"vsids": 1, "dlis": 0, "restart": 0},
    {"vsids": 0, "dlis": 1, "restart": 1},
    {"vsids": 0, "dlis": 1, "restart": 0},
]

def extraer_caracteristicas_cnf(path):
    with open(path, 'r') as f:
        lineas = f.readlines()

    num_vars = num_clausulas = 0
    clausulas = []
    literal_counter = Counter()

    for linea in lineas:
        linea = linea.strip()
        if linea.startswith('c') or linea == '':
            continue
        if linea.startswith('p'):
            partes = linea.split()
            if len(partes) >= 4:
                num_vars = int(partes[2])
                num_clausulas = int(partes[3])
            continue

        literales = list(map(int, linea.split()))
        if literales and literales[-1] == 0:
            literales.pop()
        clausulas.append(literales)
        for lit in literales:
            literal_counter[lit] += 1

    densidad = num_clausulas / num_vars if num_vars else 0
    tamanio_prom_clausula = sum(len(c) for c in clausulas) / len(clausulas) if clausulas else 0
    dist_lit = Counter(len(c) for c in clausulas)
    dist_longitudes = {f"clausulas_len_{k}": dist_lit[k] / num_clausulas for k in dist_lit}

    positivos = sum(1 for l in literal_counter if l > 0)
    negativos = sum(1 for l in literal_counter if l < 0)

    return {
        "num_vars": num_vars,
        "num_clausulas": num_clausulas,
        "densidad": densidad,
        "tamanio_prom_clausula": tamanio_prom_clausula,
        "vars_positivas": positivos,
        "vars_negativas": negativos,
        **dist_longitudes
    }

def construir_flags(comb):
    flags = [FLAG_STATS]
    flags += FLAG_TIME.split()

    if comb["vsids"]:
        flags += FLAG_VSIDS.split()

    flags += (FLAG_DLIS_TRUE if comb["dlis"] else FLAG_DLIS_FALSE).split()
    flags += (FLAG_RESTART if comb["restart"] else FLAG_NO_RESTART).split()
    return flags

import re

def parsear_stats(salida, exit_code):
    stats = {}

    # Mapear el código de salida a un resultado textual
    codigos_resultado = {
        10: "SATISFIABLE",
        20: "UNSATISFIABLE",
        0: "FINALIZACION_OK",
        1: "ERROR"
    }

    # Añadir el resultado al diccionario
    stats['resultado'] = codigos_resultado.get(exit_code, f"DESCONOCIDO_{exit_code}")

    # Parsear las estadísticas del texto
    for linea in salida.splitlines():
        if not linea.startswith("c "):
            continue
        m = re.match(r"c\s+([^:]+):\s+([^\s]+)", linea)
        if m:
            clave = m.group(1).strip().lower().replace(" ", "_").replace("/", "_por_")
            valor = m.group(2)
            try:
                if '.' in valor or 'e' in valor.lower():
                    valor = float(valor)
                else:
                    valor = int(valor)
                stats[clave] = valor
            except ValueError:
                continue
    
    # print(f"{stats['resultado']}!!!!!!!!!!!!!!!!!!!!!!")
    # print(f"{codigos_resultado.get(exit_code, f"DESCONOCIDO_{exit_code}")}")

    return stats

def detectar_resultado_solver(exit_code):
    if exit_code == 10:
        return "SAT"
    elif exit_code == 20:
        return "UNSAT"
    elif exit_code == 0:
        return "OK"
    elif exit_code == 1:
        return "ERROR"
    else:
        return "unknown"

    
def limpiar_output_modelo(salida):
    """Elimina las líneas del modelo SAT (que empiezan con 'v ')"""
    return "\n".join(linea for linea in salida.splitlines() if not linea.startswith("v "))


def ejecutar_solver(path_cnf, flags):
    try:
        inicio = time.time()
        resultado = subprocess.run(
            [CADICAL_EXECUTABLE] + flags + [path_cnf],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=360,
            text=True
        )
        duracion = time.time() - inicio
        salida = resultado.stdout + resultado.stderr

        # 🧹 Eliminar modelo SAT del output
        salida = limpiar_output_modelo(salida)

        # ✅ Pasar también el código de salida
        stats = parsear_stats(salida, resultado.returncode)
        stats['tiempo_segundos'] = duracion
        #stats['resultado'] = detectar_resultado_solver(resultado.returncode)
        return stats

    except subprocess.TimeoutExpired:
        print(f"⚠️ Timeout: {path_cnf} con flags {flags}")
        return {
            "tiempo_segundos": 60,
            "resultado": "TIMEOUT"
        }
    except Exception as e:
        print(f"❌ Error al ejecutar CaDiCaL: {e}")
        return {
            "tiempo_segundos": None,
            "resultado": "ERROR",
            "error": str(e)
        }



def main():
    if not os.path.exists(INPUT_DIR):
        print(f"Error: Carpeta '{INPUT_DIR}' no encontrada.")
        return

    archivos_cnf = [f for f in os.listdir(INPUT_DIR) if f.endswith('.cnf')]
    if not archivos_cnf:
        print("No se encontraron archivos .cnf en la carpeta de entrada.")
        return

    with open(OUTPUT_CSV, 'w', newline='') as csvfile:
        writer = None

        for archivo in archivos_cnf:
            path_cnf = os.path.join(INPUT_DIR, archivo)
            caracteristicas = extraer_caracteristicas_cnf(path_cnf)

            for comb in COMBINACIONES:
                flags = construir_flags(comb)
                print(f"Procesando {archivo} con VSIDS={comb['vsids']} DLIS={comb['dlis']} RESTART={comb['restart']}...")
                stats = ejecutar_solver(path_cnf, flags)

                fila = {
                    "nombre_cnf": archivo,
                    "vsids": comb["vsids"],
                    "dlis": comb["dlis"],
                    "restart": comb["restart"],
                    "resultado": stats.get("resultado", "UNKNOWN"),
                    **caracteristicas,
                    **{k: v for k, v in stats.items() if k not in {"resultado", "timeout", "error"}}

                }

                if writer is None:
                    columnas = list(fila.keys())
                    writer = csv.DictWriter(csvfile, fieldnames=columnas)
                    writer.writeheader()
                    # Rellenar valores faltantes con None
                fila_filtrada = {col: fila.get(col, None) for col in writer.fieldnames}
                writer.writerow(fila_filtrada)

                #fila_filtrada = {k: fila[k] for k in writer.fieldnames}


if __name__ == "__main__":
    main()
