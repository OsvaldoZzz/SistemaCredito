# Validaciones

Las reglas compartidas están en `app/logica/validaciones.py`.
Los formularios muestran los errores y las operaciones CRUD vuelven a validar
antes de escribir en MySQL.

| Entrada | Regla |
|---|---|
| Nombre del cliente | 2 a 80 caracteres; letras, espacios, apóstrofos, puntos y guiones |
| Cédula | 6 a 20 letras, números o guiones; sin duplicados |
| Correo | Formato de correo, máximo 100 caracteres; sin duplicados |
| Dirección | 5 a 40 caracteres, sin caracteres de control |
| Contraseña nueva | 8 a 128 caracteres, sin caracteres de control ni contenido compuesto solo por espacios |
| Contraseña al editar | Vacía conserva la actual |
| Usuario con rol | 2 a 100 letras, números, puntos, guiones o guiones bajos; sin duplicados |
| Roles | Administrador, recepcionista o cobrador; se protege la cuenta activa y al último administrador |
| Montos e ingresos | Finitos, positivos, hasta C$ 100,000,000 y máximo dos decimales |
| Monto del registro de cliente | También admite cero |
| Plazo | Entero entre 1 y 360; capital suficiente para al menos un centavo por cuota |
| Frecuencia | Semanal, quincenal o mensual |
| Abono | Mayor que cero y no mayor al saldo de la cuota consultado dentro de la operación |
| Citas | Fecha de hoy o futura, sin repetir cliente y fecha |
| Primera cuota de un préstamo nuevo | Fecha de hoy o futura |
| Solicitud | Ingreso obligatorio; solo se resuelve si sigue pendiente |

El login bloquea la sesión tras tres intentos fallidos y reinicia el contador
al autenticar correctamente. Si falla la carga de clientes, no se habilitan
las antiguas cuentas de ejemplo.

La comprobación de duplicados de clientes consulta MySQL para incluir cambios
de otras ventanas. Para garantizar unicidad ante escrituras simultáneas de
varias aplicaciones, la base de datos también debe tener restricciones únicas;
esta revisión no modifica esos índices ni elimina registros existentes.

## Pruebas

Desde la raíz del proyecto:

```powershell
python -m unittest discover -s tests -v
```

Las pruebas usan conexiones simuladas y Qt sin mostrar ventanas.
La integración con el servidor MySQL debe verificarse con la base de datos local.
