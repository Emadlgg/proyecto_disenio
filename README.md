# Generador de Analizadores Léxicos — YALex

Implementación de un generador de analizadores léxicos basado en el formato **YALex**. A partir de un archivo `.yal` con la especificación de tokens, el sistema construye automáticamente un analizador léxico capaz de reconocer tokens o detectar errores léxicos en cualquier archivo de texto.

---

## ¿Cómo funciona?

El generador sigue el pipeline clásico de la teoría de compiladores:

```
archivo.yal
    → Expresiones Regulares
    → AFN (construcción de Thompson)
    → AFD (construcción de subconjuntos)
    → lexer.py generado
    → tokenización de archivos
```

Cada regla del `.yal` se convierte en un AFN usando el algoritmo de Thompson. Todos los AFNs se unifican en uno solo y se convierte a AFD mediante la construcción de subconjuntos. En caso de conflicto entre tokens, se aplica **longest match** y se respeta el **orden de definición** como criterio de prioridad.

---

## Instalación

**Requisitos:**
- Python 3.8+
- Graphviz (para visualizaciones)

```bash
# Instalar dependencia Python
pip install graphviz

# Instalar Graphviz en el sistema
# Ubuntu/Debian
sudo apt install graphviz

# macOS
brew install graphviz
```

No se requiere instalar el proyecto como paquete. Clonar el repositorio y correr directamente.

---

## Uso

### 1. Generar un lexer desde un `.yal`

```bash
python yalex.py java.yal -o java_lexer.py
```

### 2. Usar el lexer generado sobre un archivo

```bash
python java_lexer.py codigo.txt
```

Con modo verbose para ver los lexemas completos:

```bash
python java_lexer.py codigo.txt --verbose
```

### 3. Generar el lexer con visualizaciones

```bash
# Árboles de expresión regular
python yalex.py java.yal -o java_lexer.py --tree

# Grafo del AFD
python yalex.py java.yal -o java_lexer.py --afd

# Todo junto
python yalex.py java.yal -o java_lexer.py --all
```

### 4. Probar rápido sin archivo

```bash
python yalex.py java.yal -run "int x = 10 + 5;"
```

---

## Estructura del proyecto

```
proyecto/
├── automata/
│   ├── afn.py          # Autómata Finito No Determinista + merge de AFNs
│   ├── afd.py          # Autómata Finito Determinista + longest match
│   ├── thompson.py     # Construcción de Thompson (regex → AFN)
│   └── subset.py       # Construcción de subconjuntos (AFN → AFD)
├── regex/
│   ├── regex_node.py   # Nodos del árbol de expresión regular
│   └── regex_parser.py # Parser de expresiones regulares
├── yalex/
│   ├── yalex_parser.py # Parser del formato .yal
│   ├── lexer_builder.py# Construcción del AFD desde la especificación
│   ├── generator.py    # Generador del archivo lexer.py
│   ├── visualizer.py   # Graficación de árboles y AFD
│   └── yalex_reader.py # Lectura de archivos .yal
├── yalex.py            # CLI principal
├── java.yal            # Especificación léxica de Java
├── ejemplo_correcto.txt
└── ejemplo_errores.txt
```

---

## Ejemplos de output

### Sin errores léxicos

```bash
python java_lexer.py ejemplo_correcto.txt --verbose
```

```
=======================================================
  TOKENS: 212
=======================================================
  KW_PUBLIC                 'public'
  KW_CLASS                  'class'
  ID                        'SistemaEstudiantes'
  LBRACE                    '{'
  KW_STATIC                 'static'
  KW_INT                    'int'
  ID                        'totalEstudiantes'
  OP_ASSIGN                 '='
  INT_LIT                   '0'
  SEMICOLON                 ';'
  ...

  Sin errores lexicos.
=======================================================
```

### Con errores léxicos

```bash
python java_lexer.py ejemplo_errores.txt --verbose
```

```
=======================================================
  TOKENS: 198
=======================================================
  KW_PUBLIC                 'public'
  KW_CLASS                  'class'
  ID                        'SistemaInventario'
  ...

=======================================================
  ERRORES LEXICOS: 11
=======================================================
  Error lexico en posicion 187: caracter inesperado '@'
  Error lexico en posicion 188: caracter inesperado '@'
  Error lexico en posicion 312: caracter inesperado '#'
  Error lexico en posicion 489: caracter inesperado '`'
  Error lexico en posicion 497: caracter inesperado '`'
  Error lexico en posicion 601: caracter inesperado '\'
  Error lexico en posicion 634: caracter inesperado '§'
  Error lexico en posicion 821: caracter inesperado '¿'
=======================================================
```

> El lexer **no se detiene** al encontrar un error. Reporta todos los errores léxicos encontrados y continúa analizando el resto del archivo.

---

## Formato del archivo `.yal`

```
(* comentario *)

let NOMBRE = expresion_regular

rule gettoken =
    expresion { return TOKEN }
  | expresion { return TOKEN }
```

**Ejemplo:**

```
let _WS    = [' ''\t''\n']+
let DIGIT  = [0-9]
let NUM    = {DIGIT}+
let ID     = [a-zA-Z]([a-zA-Z]|[0-9])*

rule gettoken =
    {_WS}  { return _WS }
  | {NUM}  { return NUM }
  | {ID}   { return ID }
  | "+"    { return PLUS }
```

> Tokens cuyo nombre empieza con `_` se ignoran en el output (whitespace, comentarios, etc).