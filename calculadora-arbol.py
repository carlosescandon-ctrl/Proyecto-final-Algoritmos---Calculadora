"""
Calculadora Básica con Árbol de Expresión
Batería 3 - Ejercicio 2
Estructuras de datos implementadas desde cero:
  - Nodo / ArbolExpresion : árbol binario de expresión
  - Pila                  : pila enlazada (para convertir infija -> árbol)
  - Cola                  : cola enlazada (para los tokens)
  - Historial             : lista enlazada con máximo 10 elementos

Uso:
    python calculadora_arbol.py            -> menú interactivo
    python calculadora_arbol.py --pruebas  -> ejecuta solo el bloque de pruebas
"""

import sys

MAX_HISTORIAL = 10


# EXCEPCIONES PROPIAS

class ErrorCalculadora(Exception):
    """Clase base de los errores de la calculadora."""


class ErrorSintaxis(ErrorCalculadora):
    """La expresión está mal escrita."""


class ErrorMatematico(ErrorCalculadora):
    """Operación matemática no válida (división por cero, etc.)."""


# FUNCIONES AUXILIARES

def prioridad(operador):
    """Precedencia: potencia (3) > multiplicación/división (2) > suma/resta (1)."""
    if operador == '^':
        return 3
    if operador == '*' or operador == '/':
        return 2
    if operador == '+' or operador == '-':
        return 1
    return 0


def es_operador(caracter):
    return caracter in '+-*/^'


def formatear(numero):
    """Muestra 11.0 como '11' y 2.5 como '2.5'."""
    if numero == int(numero):
        return str(int(numero))
    return f"{numero:.10g}"


# ESTRUCTURAS BÁSICAS: NODO ENLAZADO, PILA Y COLA

class NodoLista:
    """Nodo simple para pila, cola e historial."""

    def __init__(self, dato, siguiente=None):
        self.dato = dato
        self.siguiente = siguiente


class Pila:
    """Pila (LIFO) enlazada. push/pop/tope en O(1)."""

    def __init__(self):
        self._tope = None
        self._tamano = 0

    def esta_vacia(self):
        return self._tope is None

    def push(self, dato):
        self._tope = NodoLista(dato, self._tope)
        self._tamano += 1

    def pop(self):
        if self.esta_vacia():
            raise ErrorSintaxis("Expresión incompleta (faltan operandos).")
        dato = self._tope.dato
        self._tope = self._tope.siguiente
        self._tamano -= 1
        return dato

    def tope(self):
        if self.esta_vacia():
            return None
        return self._tope.dato

    def tamano(self):
        return self._tamano


class Cola:
    """Cola (FIFO) enlazada. encolar/desencolar en O(1)."""

    def __init__(self):
        self._frente = None
        self._final = None

    def esta_vacia(self):
        return self._frente is None

    def encolar(self, dato):
        nuevo = NodoLista(dato)
        if self._final is None:
            self._frente = nuevo
        else:
            self._final.siguiente = nuevo
        self._final = nuevo

    def desencolar(self):
        dato = self._frente.dato
        self._frente = self._frente.siguiente
        if self._frente is None:
            self._final = None
        return dato


# ÁRBOL BINARIO DE EXPRESIÓN

class Nodo:
    """
    Nodo del árbol de expresión.
      - Nodo interno: valor = operador (str), con hijo izquierdo y derecho.
      - Nodo hoja:    valor = número (float), sin hijos.
    """

    def __init__(self, valor, izq=None, der=None):
        self.valor = valor
        self.izq = izq
        self.der = der

    def es_hoja(self):
        return self.izq is None and self.der is None


class ArbolExpresion:
    def __init__(self, raiz=None):
        self.raiz = raiz

    # 1) TOKENIZACIÓN: convierte el texto en una Cola de tokens

    @staticmethod
    def _tokenizar(texto):
        """
        Devuelve una Cola de tuplas (tipo, valor):
          ('num', 3.0)  ('op', '+')  ('(', '(')  (')', ')')
        Permite números negativos (ej: -3 + 5, 2 * -3).
        """
        tokens = Cola()
        esperando_operando = True   # ¿toca un número o '('?
        i = 0
        n = len(texto)
        while i < n:
            c = texto[i]
            if c == ' ' or c == '\t':
                i += 1
                continue

            # Número (con signo negativo opcional si se espera un operando)
            negativo = (c == '-' and esperando_operando)
            if c.isdigit() or c == '.' or negativo:
                j = i + 1 if negativo else i
                if j >= n or not (texto[j].isdigit() or texto[j] == '.'):
                    raise ErrorSintaxis(
                        "El signo '-' unario solo se permite antes de un número.")
                inicio = j
                while j < n and (texto[j].isdigit() or texto[j] == '.'):
                    j += 1
                try:
                    valor = float(texto[inicio:j])
                except ValueError:
                    raise ErrorSintaxis(f"Número inválido: '{texto[inicio:j]}'.")
                if negativo:
                    valor = -valor
                tokens.encolar(('num', valor))
                esperando_operando = False
                i = j
                continue

            if es_operador(c):
                tokens.encolar(('op', c))
                esperando_operando = True
            elif c == '(':
                tokens.encolar(('(', c))
                esperando_operando = True
            elif c == ')':
                tokens.encolar((')', c))
                esperando_operando = False
            else:
                raise ErrorSintaxis(f"Carácter no permitido: '{c}'.")
            i += 1
        return tokens

    # 2) CONSTRUCCIÓN: notación infija -> árbol (algoritmo Shunting-Yard
    #    usando una pila de operadores y una pila de nodos)

    @staticmethod
    def _reducir(pila_ops, pila_nodos):
        """Saca un operador y dos subárboles y crea un nodo interno."""
        operador = pila_ops.pop()
        derecho = pila_nodos.pop()
        izquierdo = pila_nodos.pop()
        pila_nodos.push(Nodo(operador, izquierdo, derecho))

    @staticmethod
    def construir(expresion):
        """Crea un ArbolExpresion a partir de una expresión infija (str)."""
        tokens = ArbolExpresion._tokenizar(expresion)
        pila_ops = Pila()      # operadores y paréntesis
        pila_nodos = Pila()    # subárboles ya construidos
        esperando_operando = True

        while not tokens.esta_vacia():
            tipo, valor = tokens.desencolar()

            if tipo == 'num':
                if not esperando_operando:
                    raise ErrorSintaxis("Falta un operador entre dos números.")
                pila_nodos.push(Nodo(valor))
                esperando_operando = False

            elif tipo == '(':
                if not esperando_operando:
                    raise ErrorSintaxis("Falta un operador antes de '('.")
                pila_ops.push('(')

            elif tipo == 'op':
                if esperando_operando:
                    raise ErrorSintaxis(f"Operador '{valor}' sin operando a su izquierda.")
                # Reducir mientras el operador del tope tenga mayor precedencia
                # (o igual, si el operador actual es asociativo por la izquierda).
                # La potencia '^' es asociativa por la derecha.
                while (not pila_ops.esta_vacia() and pila_ops.tope() != '('
                       and (prioridad(pila_ops.tope()) > prioridad(valor)
                            or (prioridad(pila_ops.tope()) == prioridad(valor)
                                and valor != '^'))):
                    ArbolExpresion._reducir(pila_ops, pila_nodos)
                pila_ops.push(valor)
                esperando_operando = True

            elif tipo == ')':
                if esperando_operando:
                    raise ErrorSintaxis("Paréntesis ')' sin operando (¿expresión vacía '()' ?).")
                while not pila_ops.esta_vacia() and pila_ops.tope() != '(':
                    ArbolExpresion._reducir(pila_ops, pila_nodos)
                if pila_ops.esta_vacia():
                    raise ErrorSintaxis("Paréntesis ')' sin su '(' correspondiente.")
                pila_ops.pop()   # descarta el '('
                esperando_operando = False

        if esperando_operando:
            raise ErrorSintaxis("Expresión incompleta o vacía.")
        while not pila_ops.esta_vacia():
            if pila_ops.tope() == '(':
                raise ErrorSintaxis("Paréntesis '(' sin cerrar.")
            ArbolExpresion._reducir(pila_ops, pila_nodos)

        arbol = ArbolExpresion(pila_nodos.pop())
        return arbol

    # 3) EVALUACIÓN RECURSIVA

    def evaluar(self):
        return self._evaluar(self.raiz)

    def _evaluar(self, nodo):
        # Caso base: una hoja es un número
        if nodo.es_hoja():
            return nodo.valor
        # Caso recursivo: evaluar hijos y aplicar el operador
        izq = self._evaluar(nodo.izq)
        der = self._evaluar(nodo.der)
        op = nodo.valor
        if op == '+':
            return izq + der
        if op == '-':
            return izq - der
        if op == '*':
            return izq * der
        if op == '/':
            if der == 0:
                raise ErrorMatematico("División por cero.")
            return izq / der
        if op == '^':
            try:
                resultado = izq ** der
            except ZeroDivisionError:
                raise ErrorMatematico("División por cero (0 elevado a exponente negativo).")
            except OverflowError:
                raise ErrorMatematico("El resultado es demasiado grande.")
            if isinstance(resultado, complex):
                raise ErrorMatematico("Raíz de un número negativo (resultado no real).")
            return resultado
        raise ErrorSintaxis(f"Operador desconocido: {op}")

    # 4) RECORRIDOS

    def inorder(self, total=False):
        """
        Recorrido inorder (izquierda, raíz, derecha) = expresión infija.
        total=False -> solo los paréntesis necesarios por precedencia.
        total=True  -> paréntesis en cada subexpresión (muestra la estructura).
        """
        return self._inorder(self.raiz, total)

    def _inorder(self, nodo, total):
        if nodo.es_hoja():
            texto = formatear(nodo.valor)
            return f"({texto})" if nodo.valor < 0 else texto
        izq = self._inorder_hijo(nodo, nodo.izq, False, total)
        der = self._inorder_hijo(nodo, nodo.der, True, total)
        return f"{izq} {nodo.valor} {der}"

    def _inorder_hijo(self, padre, hijo, es_derecho, total):
        texto = self._inorder(hijo, total)
        if hijo.es_hoja():
            return texto
        if total:
            return f"({texto})"
        p_hijo, p_padre = prioridad(hijo.valor), prioridad(padre.valor)
        if p_hijo < p_padre:
            necesita = True
        elif p_hijo == p_padre:
            # '^' es asociativa por la derecha; las demás por la izquierda
            necesita = (not es_derecho) if padre.valor == '^' else es_derecho
        else:
            necesita = False
        return f"({texto})" if necesita else texto

    def postorder(self):
        """Recorrido postorder (izquierda, derecha, raíz) = notación postfija."""
        return self._postorder(self.raiz).strip()

    def _postorder(self, nodo):
        if nodo.es_hoja():
            return formatear(nodo.valor) + " "
        return self._postorder(nodo.izq) + self._postorder(nodo.der) + nodo.valor + " "


    # 5) VISUALIZACIÓN DEL ÁRBOL EN TEXTO
  
    def dibujar(self):
        """Devuelve el árbol dibujado como texto (raíz arriba)."""
        lineas = self._dibujar(self.raiz)[0]
        resultado = ""
        for linea in lineas:
            resultado += linea.rstrip() + "\n"
        return resultado.rstrip("\n")

    def _dibujar(self, nodo):
        """
        Devuelve (lineas, ancho, alto, posicion_media) del subárbol.
        Cada subárbol se dibuja recursivamente y luego se unen los dos
        dibujos (izquierdo y derecho) bajo el operador.
        """
        if nodo.es_hoja():
            texto = formatear(nodo.valor)
            return [texto], len(texto), 1, len(texto) // 2

        izq, n, p, x = self._dibujar(nodo.izq)
        der, m, q, y = self._dibujar(nodo.der)
        s = nodo.valor
        u = len(s)

        primera = (x + 1) * ' ' + (n - x - 1) * '_' + s + y * '_' + (m - y) * ' '
        segunda = x * ' ' + '/' + (n - x - 1 + u + y) * ' ' + '\\' + (m - y - 1) * ' '

        # Igualar alturas de ambos subárboles
        if p < q:
            izq = izq + [n * ' '] * (q - p)
        elif q < p:
            der = der + [m * ' '] * (p - q)

        lineas = [primera, segunda]
        for k in range(max(p, q)):
            lineas.append(izq[k] + u * ' ' + der[k])
        return lineas, n + m + u, max(p, q) + 2, n + u // 2


# HISTORIAL: lista enlazada con las últimas 10 evaluaciones

class Historial:
    """Guarda las últimas MAX_HISTORIAL expresiones (la más reciente primero)."""

    def __init__(self, maximo=MAX_HISTORIAL):
        self._cabeza = None
        self._tamano = 0
        self._maximo = maximo

    def agregar(self, expresion, resultado):
        """Inserta al inicio (O(1)) y elimina la más antigua si se pasa del máximo."""
        self._cabeza = NodoLista((expresion, resultado), self._cabeza)
        self._tamano += 1
        if self._tamano > self._maximo:
            actual = self._cabeza
            while actual.siguiente.siguiente is not None:
                actual = actual.siguiente
            actual.siguiente = None
            self._tamano -= 1

    def tamano(self):
        return self._tamano

    def mostrar(self):
        if self._cabeza is None:
            print("  (El historial está vacío)")
            return
        actual = self._cabeza
        numero = 1
        while actual is not None:
            expresion, resultado = actual.dato
            print(f"  {numero:>2}. {expresion}  =  {formatear(resultado)}")
            actual = actual.siguiente
            numero += 1


# CALCULADORA (une árbol + historial) Y MENÚ

class Calculadora:
    def __init__(self):
        self.historial = Historial()

    def procesar(self, expresion):
        """Construye el árbol, lo muestra, lo evalúa y guarda en el historial."""
        arbol = ArbolExpresion.construir(expresion)
        resultado = arbol.evaluar()

        print("\nÁrbol:")
        print(arbol.dibujar())
        print(f"\nRecorrido inorder   (expresión original): {arbol.inorder()}")
        print(f"Recorrido postorder (notación postfija) : {arbol.postorder()}")
        print(f"\nResultado: {arbol.inorder(total=True)} = {formatear(resultado)}")

        self.historial.agregar(expresion.strip(), resultado)
        return resultado


def mostrar_menu():
    print("\n" + "=" * 44)
    print("  CALCULADORA CON ÁRBOL DE EXPRESIÓN")
    print("=" * 44)
    print("  1. Evaluar una expresión")
    print("  2. Ver historial (últimas 10)")
    print("  3. Ejecutar pruebas automáticas")
    print("  0. Salir")


def menu():
    calc = Calculadora()
    while True:
        mostrar_menu()
        opcion = input("Elige una opción: ").strip()
        if opcion == '1':
            print("Operadores: + - * / ^   |  Se permiten paréntesis y decimales")
            expresion = input("Expresión: ")
            try:
                calc.procesar(expresion)
            except ErrorSintaxis as e:
                print(f"\n[Error de sintaxis] {e}")
            except ErrorMatematico as e:
                print(f"\n[Error matemático] {e}")
        elif opcion == '2':
            print("\nHistorial:")
            calc.historial.mostrar()
        elif opcion == '3':
            ejecutar_pruebas()
        elif opcion == '0':
            print("¡Hasta pronto!")
            break
        else:
            print("Opción no válida.")


# BLOQUE DE PRUEBAS

def ejecutar_pruebas():
    print("\n--- PRUEBAS AUTOMÁTICAS ---")
    correctas = 0
    total = 0

    # (expresión, resultado esperado)
    casos_validos = [
        ("3 + 4 * 2", 11),
        ("(3 + 4) * 2", 14),
        ("2 ^ 3 ^ 2", 512),          # potencia asociativa por la derecha
        ("2 ^ 3 * 2", 16),           # potencia > multiplicación
        ("10 - 4 - 3", 3),           # resta asociativa por la izquierda
        ("10 / 4", 2.5),
        ("-3 + 5", 2),
        ("2 * (3 + (4 - 1))", 12),
        ("8 / 2 / 2", 2),
        ("1.5 + 2.5", 4),
    ]
    for expresion, esperado in casos_validos:
        total += 1
        try:
            obtenido = ArbolExpresion.construir(expresion).evaluar()
            ok = abs(obtenido - esperado) < 1e-9
        except ErrorCalculadora:
            obtenido, ok = "error", False
        correctas += ok
        print(f"  [{'OK' if ok else 'FALLA'}] {expresion:<20} -> {obtenido}")

    # Expresiones que deben producir error
    casos_error = [
        ("5 / 0", ErrorMatematico),
        ("5 / (3 - 3)", ErrorMatematico),
        ("0 ^ -1", ErrorMatematico),
        ("3 +", ErrorSintaxis),
        ("(3 + 4", ErrorSintaxis),
        ("3 + 4)", ErrorSintaxis),
        ("3 4", ErrorSintaxis),
        ("2 $ 3", ErrorSintaxis),
        ("()", ErrorSintaxis),
        ("", ErrorSintaxis),
    ]
    for expresion, tipo_error in casos_error:
        total += 1
        try:
            ArbolExpresion.construir(expresion).evaluar()
            ok = False
        except tipo_error:
            ok = True
        except ErrorCalculadora:
            ok = False
        correctas += ok
        print(f"  [{'OK' if ok else 'FALLA'}] {expresion!r:<20} -> debe dar {tipo_error.__name__}")

    # Prueba del historial (máximo 10 elementos)
    total += 1
    historial = Historial()
    for k in range(15):
        historial.agregar(f"{k} + 1", k + 1)
    ok = historial.tamano() == 10
    correctas += ok
    print(f"  [{'OK' if ok else 'FALLA'}] Historial conserva solo las últimas 10")

    # Prueba de recorridos y dibujo con el ejemplo del enunciado
    total += 1
    arbol = ArbolExpresion.construir("3 + 4 * 2")
    ok = arbol.postorder() == "3 4 2 * +" and arbol.inorder(total=True) == "3 + (4 * 2)"
    correctas += ok
    print(f"  [{'OK' if ok else 'FALLA'}] Recorridos de '3 + 4 * 2'")
    print("\nÁrbol de ejemplo:")
    print(arbol.dibujar())

    print(f"\nResultado: {correctas}/{total} pruebas correctas.")


if __name__ == "__main__":
    if "--pruebas" in sys.argv:
        ejecutar_pruebas()
    else:
        menu()