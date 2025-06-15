# Análisis comparativo de métodos aproximados en solucionadores CDCL SAT

**Autora:** Massiel Paz  
**Tutor:** Dr. Luciano García Garrido, Prof. Titular Consultante  
**Facultad de Matemática y Computación, Universidad de La Habana, Cuba**  
**Fecha de entrega:** 15 de junio de 2025

---

## Descripción del proyecto

Este proyecto realiza un análisis comparativo de métodos aproximados en solucionadores de satisfacibilidad booleana (SAT) basados en el paradigma CDCL (Conflict-Driven Clause Learning), utilizando como base el solucionador CaDiCaL. El objetivo principal es evaluar el desempeño de distintas heurísticas de decisión y estrategias de reinicio en la resolución de instancias SAT de diversa naturaleza y dificultad.

---

## Características técnicas

- **Solucionador base:** CaDiCaL v2.1.3
- **Heurísticas analizadas:**
  - **VSIDS + restart**
  - **VSIDS sin restart**
  - **DLIS + restart**
  - **DLIS sin restart**
- **Modificaciones realizadas:** Integración de la heurística DLIS en el código fuente de CaDiCaL, incluyendo la implementación de métodos de selección de variables y la activación mediante flags específicos.
- **Parámetros de ejecución:**  
  - `--score=false` (para VSIDS puro)
  - `--restart=false` (para desactivar reinicios)
  - `--dlis=true` (para activar DLIS)
  - `-t 120` (timeout de 120 segundos)
  - `--stats` (para mostrar estadísticas adicionales)

---

## Conjuntos de problemas SAT

Se generaron y analizaron 135 instancias SAT, cubriendo las siguientes familias de problemas:

- **Random 3-SAT** (15 instancias)
- **Pigeonhole Principle** (15 instancias)
- **Random 4-SAT** (15 instancias)
- **Graph Coloring en Grafos Aleatorios** (10 instancias)
- **Parity (XOR) Constraints** (10 instancias)
- **BMC de Flip-Flop Simple** (10 instancias)
- **Problemas DLIS-friendly** (30 instancias)
- **Problemas no DLIS-friendly** (30 instancias)

Cada familia varía en parámetros clave como número de variables, relación cláusulas/variables, sesgo en literales, tamaño de cláusula, profundidad, etc., asegurando diversidad estructural y de dificultad.

---

## Dependencias

### Compilación y ejecución de CaDiCaL

- **Compilador C++:** gcc/g++ compatible con C++11 o superior
- **Sistema operativo:** Linux
- **Make** (para la compilación del solver)

### Análisis estadístico y generación de gráficos

Todos los requerimientos necesarios se encuentran en el archivo *requirements.txt*. Para instalarlos basta con ejecutar el comando *pip install -r requirements.txt*


### Generación de benchmarks

- **Python** (versión 3.11)
- **Bibliotecas estándar:** `os`, `random`, `csv`

---

## Hardware utilizado

Los experimentos se realizaron en una laptop con las siguientes características:

- **Procesador:** 11th Gen Intel(R) Core(TM) i5-1135G7 @ 2.40GHz (2.42 GHz)
- **RAM:** 12.0 GB (11.8 GB usable)

---

## Instalación y ejecución

1. **Clonar el repositorio:**
- git clone [URL_DEL_REPOSITORIO]
- cd [NOMBRE_DEL_REPOSITORIO]

2. **Compilar CaDiCaL modificado:**
- ./configure
- make

3. **Ejecutar experimentos:**
Desde la raíz del proyecto, ejecutar:\\
python run_experiments.py\\
Los resultados se guaradarán en un csv. La ejecución de todas las pruebas tardó aproximadamente 9 horas. En el peor caso puede tardar 18 horas.

## Métricas de evaluación

El análisis estadístico se realizó mediante el archivo `stats_analysis.ipynb`. Se incluyeron las siguientes métricas y pruebas:

- **Análisis de distribución de problemas con TIMEOUT vs. resueltos**
- **Análisis de tiempo de ejecución para problemas resueltos**
- **Comparación de características mediante Mann-Whitney U**
- **Gráficas de caja y bigotes para visualización**
- **Regresión logística para analizar probabilidad de TIMEOUT**
- **Correlación de Spearman entre características de problemas y tiempo**
- **Test de Kruskal-Wallis y Dunn para comparar tiempos entre heurísticas**
- **Regresión lineal múltiple para identificar predictores del tiempo de resolución**

---

## Resultados clave

- **Diferencias estadísticamente significativas** entre instancias resueltas y con TIMEOUT en variables como número de variables y densidad.
- **Análisis comparativo** de rendimiento entre heurísticas mediante pruebas no paramétricas y regresión lineal.
- **Visualización de resultados** mediante gráficas de caja y bigotes.

---

## Referencias y recursos

- **CaDiCaL SAT Solver:** [GitHub](https://github.com/arminbiere/cadical)
- **Implementación de CDCL SAT solvers:** [PDF](http://ssa-school-2016.it.uu.se/wp-content/uploads/2016/06/LaurentSimon.pdf)
- **VSIDS Branching Heuristics:** [PDF](https://mk.cs.msu.ru/images/1/1f/SAT_SMT_Vijay_Ganesh_HVC2015.pdf)

---

## Contacto

- **Autora:** Massiel Paz  
- **Tutor:** Dr. Prof. Titular Consultante Luciano García Garrido
- **Facultad de Matemática y Computación, Universidad de La Habana, Cuba**

