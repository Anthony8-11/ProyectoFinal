# print('Hola Python')
# def mi_funcion(param1, param2):
#   resultado = param1 + param2
#   print(f"El resultado es: {resultado}")
#   return resultado

# x = 10
# y = 20
# mi_funcion(x, y)
# # Esto es un comentario
# if x > 5:
#     print("x es mayor que 5")
#     if y > 15:
#         print("y también es mayor que 15")
# else:
#     print("x no es mayor que 5")

# # Otro comentario

# prueba_python.py

# print('Hola Python desde main.py')

# def mi_funcion(param1, param2):
#   resultado = param1 + param2 # Expresión aditiva
#   print(f"El resultado dentro de mi_funcion es: {resultado}")
#   if resultado > 0:
#       print("El resultado es positivo.")
#   return resultado

# x = 10
# y = 20
# z = mi_funcion(x, y)
# print(f"El valor de z (retornado por mi_funcion) es: {z}")

# if x > 5 and y < 30: # Expresión comparativa y lógica (a implementar)
#     print("x es mayor que 5 Y y es menor que 30")
#     if y > 25: 
#         print("y también es mayor que 25")
#     elif y > 10:
#         print("y es mayor que 10 pero no que 25")
#     else:
#         print("y no es mayor que 10 ni que 25")
# else:
#     print("La condición principal del if no se cumplió")

# if z == 30:
#     print("z es 30, ¡correcto!")
# else:
#     print(f"z no es 30, es {z}")

# # Bucle While
# print("Iniciando bucle while...")
# contador_while = 0
# while contador_while < 3: # Condición simple
#     print(f"Iteración while: {contador_while}")
#     contador_while = contador_while + 1
# print("Bucle while finalizado.")

# # Bucle For (simplificado, sobre un rango)
# print("Iniciando bucle for...")
# # Asumiremos que el parser puede manejar "range(3)" como una expresión iterable más adelante.
# # Por ahora, el parser se enfocará en la estructura "for var in expresion:"
# # La semántica de "range" se manejará en el intérprete.
# for i in range(3): # range(3) es una llamada a función
#     print(f"Iteración for: {i}")
# print("Bucle for finalizado.")

# def otra_funcion():
#     k = 0
#     while k < 2:
#         print(f"k en while: {k}")
#         k = k + 1
#         if k == 1:
#             print("k es 1, continuando...")
#             # continue # 'continue' no implementado aún
#         # break # 'break' no implementado aún
#     return k

# valor_k = otra_funcion()
# print(f"Valor de k retornado: {valor_k}")

# prueba_python.py

print('Hola Python desde main.py')

def mi_funcion(param1, param2):
  resultado = param1 + param2 
  print(f"El resultado dentro de mi_funcion es: {resultado}")
  if resultado > 0:
      print("El resultado es positivo.")
  return resultado

x = 10
y = 20
z = mi_funcion(x, y)
print(f"El valor de z (retornado por mi_funcion) es: {z}")

if x > 5 and y < 30: 
    print("x es mayor que 5 Y y es menor que 30")
    if y > 25: 
        print("y también es mayor que 25")
    elif y > 10:
        print("y es mayor que 10 pero no que 25")
    else:
        print("y no es mayor que 10 ni que 25")
else:
    print("La condición principal del if no se cumplió")

if z == 30:
    print("z es 30, ¡correcto!")
else:
    print(f"z no es 30, es {z}")

# Bucle While con break y continue
print("Iniciando bucle while con break/continue...")
contador_while = 0
while contador_while < 10:
    contador_while = contador_while + 1
    if contador_while == 3:
        print(f"While: contador es {contador_while}, aplicando continue.")
        continue
    if contador_while == 7:
        print(f"While: contador es {contador_while}, aplicando break.")
        break
    print(f"Iteración while (después de checks): {contador_while}")
print(f"Bucle while finalizado. Contador: {contador_while}")

# Bucle For con break y continue
print("Iniciando bucle for con break/continue...")
resultado_for_bc = ""
for i in range(5): # 0, 1, 2, 3, 4
    if i == 1:
        resultado_for_bc = resultado_for_bc + f"For: i es {i}, aplicando continue. "
        continue
    if i == 4:
        resultado_for_bc = resultado_for_bc + f"For: i es {i}, aplicando break. "
        break
    resultado_for_bc = resultado_for_bc + f"Iteracion for (después de checks): {i}. "
print(resultado_for_bc)
print("Bucle for finalizado.")

def otra_funcion():
    k = 0
    while k < 2:
        print(f"k en while: {k}")
        k = k + 1
        if k == 1:
            print("k es 1, continuando...")
            # continue # 'continue' no implementado aún en esta función específica
    return k

valor_k = otra_funcion()
print(f"Valor de k retornado: {valor_k}")


