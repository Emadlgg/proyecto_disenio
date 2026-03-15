"""
visualizer.py — Graficación del árbol de expresión regular y del AFD.

Uso:
    from yalex.visualizer import draw_tree, draw_afd
    draw_tree(regex_node, "output_tree")   → genera output_tree.png
    draw_afd(afd, "output_afd")            → genera output_afd.png
"""

from graphviz import Digraph


# ─────────────────────────────────────────────
# Árbol de expresión regular
# ─────────────────────────────────────────────

def draw_tree(root, filename="expression_tree", title=""):
    """
    Grafica el árbol de expresión regular producido por RegexParser.

    Nodos internos: OR, CONCAT, STAR, PLUS, OPTIONAL
    Hojas:          SYMBOL(valor)

    Parámetros:
        root      — RegexNode raíz del árbol
        filename  — nombre del archivo de salida (sin extensión)
        title     — título opcional que aparece en el gráfico
    """
    dot = Digraph(
        name="ExpressionTree",
        comment=title or "Expression Tree",
        graph_attr={
            "rankdir": "TB",
            "label": title,
            "labelloc": "t",
            "fontsize": "14",
            "fontname": "Helvetica",
            "bgcolor": "white",
        },
        node_attr={
            "fontname": "Helvetica",
            "fontsize": "11",
        },
        edge_attr={
            "fontname": "Helvetica",
            "fontsize": "9",
        }
    )

    counter = [0]  # lista para poder mutar desde closure

    def add_node(node):
        if node is None:
            return None

        node_id = str(counter[0])
        counter[0] += 1

        if node.type == "SYMBOL":
            label = _symbol_label(node.value)
            dot.node(node_id, label=label, shape="ellipse",
                     style="filled", fillcolor="#AED6F1", color="#2E86C1")

        elif node.type in ("STAR", "PLUS", "OPTIONAL"):
            op = {"STAR": "★  *", "PLUS": "✚  +", "OPTIONAL": "?"}[node.type]
            dot.node(node_id, label=op, shape="diamond",
                     style="filled", fillcolor="#A9DFBF", color="#1E8449")
            child_id = add_node(node.left)
            if child_id:
                dot.edge(node_id, child_id)

        elif node.type == "CONCAT":
            dot.node(node_id, label="·\nCONCAT", shape="rectangle",
                     style="filled", fillcolor="#FAD7A0", color="#CA6F1E")
            left_id  = add_node(node.left)
            right_id = add_node(node.right)
            if left_id:  dot.edge(node_id, left_id,  label="L")
            if right_id: dot.edge(node_id, right_id, label="R")

        elif node.type == "OR":
            dot.node(node_id, label="|  OR", shape="rectangle",
                     style="filled", fillcolor="#D7BDE2", color="#6C3483")
            left_id  = add_node(node.left)
            right_id = add_node(node.right)
            if left_id:  dot.edge(node_id, left_id,  label="L")
            if right_id: dot.edge(node_id, right_id, label="R")

        else:
            dot.node(node_id, label=node.type, shape="rectangle",
                     style="filled", fillcolor="#F9E79F", color="#B7950B")

        return node_id

    add_node(root)
    out = dot.render(filename, format="png", cleanup=True)
    print(f"Árbol guardado: {out}")
    return out


def _symbol_label(value):
    """Convierte el valor de un SYMBOL a una etiqueta legible."""
    if value == "ε":
        return "ε"
    if value == "\n":
        return "\\n"
    if value == "\t":
        return "\\t"
    if value == "\r":
        return "\\r"
    if value == " ":
        return "' '"
    if value == "eof":
        return "eof"
    return repr(value) if len(value) == 1 else value


# ─────────────────────────────────────────────
# AFD
# ─────────────────────────────────────────────

def draw_afd(afd, filename="afd", title="AFD", max_states=150):
    """
    Grafica el AFD con estados numerados.

    - Estado inicial: flecha entrante sin origen
    - Estados finales: doble círculo con el nombre del token
    - Transiciones: agrupadas por destino para reducir aristas

    Parámetros:
        afd      — objeto AFD con states, initial_state, final_states,
                   transitions, token_map
        filename — nombre del archivo de salida (sin extensión)
        title    — título del gráfico
    """
    # Renumerar estados frozenset → int para etiquetas legibles
    state_list = list(afd.states)
    s2i = {s: i for i, s in enumerate(state_list)}

    total = len(afd.states)
    if total > max_states:
        print(f"  [info] AFD tiene {total} estados, graficando los primeros {max_states}")
        # Tomar solo los estados alcanzables desde el inicial por BFS
        from collections import deque
        q = deque([afd.initial_state])
        visible = set()
        while q and len(visible) < max_states:
            cur = q.popleft()
            if cur in visible: continue
            visible.add(cur)
            for (st, sym), tgt in afd.transitions.items():
                if st == cur and tgt not in visible:
                    q.append(tgt)
        # Filtrar a solo estados visibles
        class PartialAFD:
            pass
        p = PartialAFD()
        p.states      = visible
        p.initial_state = afd.initial_state
        p.final_states  = {s for s in afd.final_states if s in visible}
        p.transitions   = {(s,sym):t for (s,sym),t in afd.transitions.items()
                           if s in visible and t in visible}
        p.token_map     = {s:tok for s,tok in afd.token_map.items() if s in visible}
        afd   = p
        s2i   = {s: i for i, s in enumerate(afd.states)}
        title = title + f" (parcial: {max_states}/{total} estados)"

    dot = Digraph(
        name="AFD",
        comment=title,
        graph_attr={
            "rankdir": "LR",
            "label": title,
            "labelloc": "t",
            "fontsize": "14",
            "fontname": "Helvetica",
            "bgcolor": "white",
        },
        node_attr={"fontname": "Helvetica", "fontsize": "10"},
        edge_attr={"fontname": "Helvetica", "fontsize": "9"},
    )

    # Nodo fantasma para flecha inicial
    dot.node("__start__", label="", shape="none", width="0", height="0")
    dot.edge("__start__", str(s2i[afd.initial_state]))

    # Agregar todos los estados
    for state in afd.states:
        idx = s2i[state]
        is_final = state in afd.final_states

        if is_final:
            token = afd.token_map.get(state, "?")
            label = f"q{idx}\n{token}"
            dot.node(str(idx), label=label, shape="doublecircle",
                     style="filled", fillcolor="#A9DFBF", color="#1E8449")
        else:
            dot.node(str(idx), label=f"q{idx}", shape="circle",
                     style="filled", fillcolor="#D6EAF8", color="#2E86C1")

    # Agrupar transiciones por (origen, destino) para combinar etiquetas
    edge_labels = {}
    for (state, symbol), target in afd.transitions.items():
        key = (s2i[state], s2i[target])
        if key not in edge_labels:
            edge_labels[key] = []
        edge_labels[key].append(_symbol_label(symbol))

    for (src, tgt), symbols in edge_labels.items():
        # Agrupar símbolos en rangos si son muchos (ej: a-z)
        label = _compress_symbols(symbols)
        dot.edge(str(src), str(tgt), label=label)

    out = dot.render(filename, format="png", cleanup=True)
    print(f"AFD guardado: {out}")
    return out


def _compress_symbols(symbols):
    """
    Comprime una lista de símbolos en una etiqueta legible.
    Si hay más de 8 símbolos, muestra los primeros y "..."
    """
    # Filtrar y ordenar
    cleaned = sorted(set(symbols))

    if len(cleaned) <= 6:
        return ", ".join(cleaned)

    # Detectar rangos consecutivos ASCII
    ranges = _find_ranges(cleaned)
    label = ", ".join(ranges)

    if len(label) > 40:
        label = label[:37] + "..."

    return label


def _find_ranges(symbols):
    """Convierte ['a','b','c','d'] en ['a-d'] para legibilidad."""
    result = []
    printable = [s for s in symbols if len(s) == 1 and s.isprintable()]
    other = [s for s in symbols if s not in printable]

    if printable:
        ords = sorted(ord(c) for c in printable)
        i = 0
        while i < len(ords):
            j = i
            while j + 1 < len(ords) and ords[j+1] == ords[j] + 1:
                j += 1
            if j - i >= 2:
                result.append(f"{chr(ords[i])}-{chr(ords[j])}")
            else:
                result.extend(chr(ords[k]) for k in range(i, j+1))
            i = j + 1

    result.extend(other)
    return result