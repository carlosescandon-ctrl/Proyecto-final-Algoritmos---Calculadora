"""
Calculadora Básica con Árbol de Expresión - Batería 3, Ejercicio 2
Uso:  python calculadora_arbol.py            (menú)
      python calculadora_arbol.py --pruebas  (solo pruebas)
"""
import sys

PRIORIDAD = {'+': 1, '-': 1, '*': 2, '/': 2, '^': 3}   # ^ > * / > + -
MAX_HISTORIAL = 10


class ErrorSintaxis(Exception):
    """La expresión está mal escrita."""


class ErrorMatematico(Exception):
    """Operación no válida (división por cero, etc.)."""


def fmt(n):
    """Muestra 11.0 como '11' y 2.5 como '2.5'."""
    return str(int(n)) if n == int(n) else f"{n:.10g}"


# PILA____________________________________________________________
class Pila:
    """Pila (LIFO): push, pop y tope en O(1)."""
    def __init__(self):
        self.items = []

    def push(self, x):
        self.items.append(x)

    def pop(self):
        if not self.items:
            raise ErrorSintaxis("Expresión incompleta (faltan operandos).")
        return self.items.pop()

    def tope(self):
        return self.items[-1] if self.items else None

    def vacia(self):
        return not self.items


# ÁRBOL____________________________________________________________
class Nodo:
    """Nodo interno: operador (str) con dos hijos. Hoja: número (float)."""
    def __init__(self, valor, izq=None, der=None):
        self.valor, self.izq, self.der = valor, izq, der

    def es_hoja(self):
        return self.izq is None


def tokenizar(texto):
    """Convierte el texto en una lista de tokens: números (float), operadores y paréntesis."""
    tokens, i, espera = [], 0, True          # espera = ¿toca un operando?
    while i < len(texto):
        c = texto[i]
        if c == ' ':
            i += 1
        elif c.isdigit() or c == '.' or (c == '-' and espera):   # número (puede ser negativo)
            j = i + 1
            while j < len(texto) and (texto[j].isdigit() or texto[j] == '.'):
                j += 1
            try:
                tokens.append(float(texto[i:j]))
            except ValueError:
                raise ErrorSintaxis(f"Número inválido: '{texto[i:j]}'.")
            espera, i = False, j
        elif c in PRIORIDAD or c in '()':
            tokens.append(c)
            espera, i = (c != ')'), i + 1
        else:
            raise ErrorSintaxis(f"Carácter no permitido: '{c}'.")
    return tokens


def reducir(ops, nodos):
    """Saca un operador y dos subárboles y crea un nodo interno."""
    op = ops.pop()
    der = nodos.pop()
    izq = nodos.pop()
    nodos.push(Nodo(op, izq, der))


def construir(expresion):
    """Infija -> árbol, con una pila de operadores y otra de subárboles."""
    ops, nodos, espera = Pila(), Pila(), True
    for t in tokenizar(expresion):
        if isinstance(t, float):                       # número
            if not espera:
                raise ErrorSintaxis("Falta un operador entre dos números.")
            nodos.push(Nodo(t))
            espera = False
        elif t == '(':
            if not espera:
                raise ErrorSintaxis("Falta un operador antes de '('.")
            ops.push(t)
        elif t == ')':
            if espera:
                raise ErrorSintaxis("Paréntesis vacío o falta un operando.")
            while ops.tope() not in (None, '('):
                reducir(ops, nodos)
            if ops.vacia():
                raise ErrorSintaxis("Paréntesis ')' sin su '('.")
            ops.pop()                                  # descarta el '('
            espera = False
        else:                                          # operador
            if espera:
                raise ErrorSintaxis(f"Operador '{t}' sin operando a su izquierda.")
            # reduce mientras el tope tenga mayor precedencia (o igual, salvo en '^')
            while ops.tope() not in (None, '(') and (
                    PRIORIDAD[ops.tope()] > PRIORIDAD[t] or
                    (PRIORIDAD[ops.tope()] == PRIORIDAD[t] and t != '^')):
                reducir(ops, nodos)
            ops.push(t)
            espera = True
    if espera:
        raise ErrorSintaxis("Expresión incompleta o vacía.")
    while not ops.vacia():
        if ops.tope() == '(':
            raise ErrorSintaxis("Paréntesis '(' sin cerrar.")
        reducir(ops, nodos)
    return nodos.pop()


def evaluar(n):
    """Evaluación recursiva: la hoja devuelve su número; el nodo aplica su operador."""
    if n.es_hoja():
        return n.valor
    a, b = evaluar(n.izq), evaluar(n.der)
    if n.valor == '+': return a + b
    if n.valor == '-': return a - b
    if n.valor == '*': return a * b
    if n.valor == '/':
        if b == 0:
            raise ErrorMatematico("División por cero.")
        return a / b
    try:
        r = a ** b
    except (ZeroDivisionError, OverflowError):
        raise ErrorMatematico("Potencia no válida (0 con exponente negativo o resultado enorme).")
    if isinstance(r, complex):
        raise ErrorMatematico("Raíz de un número negativo (resultado no real).")
    return r


def inorder(n, total=False):
    """Izquierda-raíz-derecha = expresión infija. total=True pone paréntesis en todo."""
    if n.es_hoja():
        return f"({fmt(n.valor)})" if n.valor < 0 else fmt(n.valor)

    def hijo(h, derecho):
        t = inorder(h, total)
        if h.es_hoja():
            return t
        ph, pn = PRIORIDAD[h.valor], PRIORIDAD[n.valor]
        # '^' se asocia por la derecha; los demás por la izquierda
        pide = total or ph < pn or (ph == pn and derecho != (n.valor == '^'))
        return f"({t})" if pide else t
    return f"{hijo(n.izq, False)} {n.valor} {hijo(n.der, True)}"


def postorder(n):
    """Izquierda-derecha-raíz = notación postfija."""
    if n.es_hoja():
        return fmt(n.valor)
    return f"{postorder(n.izq)} {postorder(n.der)} {n.valor}"


def dibujar(n):
    """Devuelve (líneas, ancho, posición_media). Une recursivamente los dibujos de los hijos."""
    if n.es_hoja():
        t = fmt(n.valor)
        return [t], len(t), len(t) // 2
    izq, a, x = dibujar(n.izq)
    der, b, y = dibujar(n.der)
    linea1 = ' ' * (x + 1) + '_' * (a - x - 1) + n.valor + '_' * y + ' ' * (b - y)
    linea2 = ' ' * x + '/' + ' ' * (a - x + y) + '\\' + ' ' * (b - y - 1)
    alto = max(len(izq), len(der))
    izq += [' ' * a] * (alto - len(izq))
    der += [' ' * b] * (alto - len(der))
    return [linea1, linea2] + [i + ' ' + d for i, d in zip(izq, der)], a + b + 1, a


# ---------------------------------------------------------------- CALCULADORA
historial = []        # las últimas 10 evaluaciones; la más reciente va primero


def procesar(expresion):
    arbol = construir(expresion)
    resultado = evaluar(arbol)
    print("\nÁrbol:")
    print("\n".join(l.rstrip() for l in dibujar(arbol)[0]))
    print(f"\nInorder   (expresión original): {inorder(arbol)}")
    print(f"Postorder (notación postfija) : {postorder(arbol)}")
    print(f"\nResultado: {inorder(arbol, True)} = {fmt(resultado)}")
    historial.insert(0, (expresion.strip(), resultado))
    del historial[MAX_HISTORIAL:]                      # conserva solo las últimas 10


def mostrar_historial():
    print("\nHistorial:")
    for k, (e, r) in enumerate(historial, 1):
        print(f"  {k:>2}. {e}  =  {fmt(r)}")
    if not historial:
        print("  (vacío)")


def menu():
    while True:
        print("\n=== CALCULADORA CON ÁRBOL DE EXPRESIÓN ===")
        print("1. Evaluar expresión\n2. Ver historial\n3. Ejecutar pruebas\n0. Salir")
        op = input("Elige una opción: ").strip()
        if op == '1':
            try:
                procesar(input("Expresión (+ - * / ^ y paréntesis): "))
            except ErrorSintaxis as e:
                print(f"\n[Error de sintaxis] {e}")
            except ErrorMatematico as e:
                print(f"\n[Error matemático] {e}")
        elif op == '2':
            mostrar_historial()
        elif op == '3':
            pruebas()
        elif op == '0':
            print("¡Hasta pronto!")
            break
        else:
            print("Opción no válida.")


# ---------------------------------------------------------------- PRUEBAS
def pruebas():
    print("\n--- PRUEBAS AUTOMÁTICAS ---")
    validos = [("3 + 4 * 2", 11), ("(3 + 4) * 2", 14), ("2 ^ 3 ^ 2", 512), ("2 ^ 3 * 2", 16),
               ("10 - 4 - 3", 3), ("10 / 4", 2.5), ("-3 + 5", 2), ("2 * (3 + (4 - 1))", 12),
               ("8 / 2 / 2", 2), ("1.5 + 2.5", 4)]
    errores = [("5 / 0", ErrorMatematico), ("5 / (3 - 3)", ErrorMatematico),
               ("0 ^ -1", ErrorMatematico), ("3 +", ErrorSintaxis), ("(3 + 4", ErrorSintaxis),
               ("3 + 4)", ErrorSintaxis), ("3 4", ErrorSintaxis), ("2 $ 3", ErrorSintaxis),
               ("()", ErrorSintaxis), ("", ErrorSintaxis)]
    resultados = []                                    # lista de (descripción, ok)
    for e, esperado in validos:
        try:
            ok = abs(evaluar(construir(e)) - esperado) < 1e-9
        except (ErrorSintaxis, ErrorMatematico):
            ok = False
        resultados.append((f"{e!r} = {esperado}", ok))
    for e, tipo in errores:
        try:
            evaluar(construir(e))
            ok = False
        except tipo:
            ok = True
        except (ErrorSintaxis, ErrorMatematico):
            ok = False
        resultados.append((f"{e!r} debe dar {tipo.__name__}", ok))
    arbol = construir("3 + 4 * 2")
    resultados.append(("Recorridos de '3 + 4 * 2'",
                       postorder(arbol) == "3 4 2 * +" and inorder(arbol, True) == "3 + (4 * 2)"))
    historial.clear()
    for k in range(15):
        historial.insert(0, (f"{k}+1", k + 1))
        del historial[MAX_HISTORIAL:]
    resultados.append(("Historial conserva solo las últimas 10", len(historial) == 10))
    historial.clear()
    for descripcion, ok in resultados:
        print(f"  [{'OK' if ok else 'FALLA'}] {descripcion}")
    print("\nÁrbol de ejemplo:")
    print("\n".join(l.rstrip() for l in dibujar(arbol)[0]))
    print(f"\nResultado: {sum(ok for _, ok in resultados)}/{len(resultados)} pruebas correctas.")


if __name__ == "__main__":
    pruebas() if "--pruebas" in sys.argv else menu()
