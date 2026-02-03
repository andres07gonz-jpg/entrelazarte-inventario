# Sistema de Inventario - ENTRELAZARTE
## Versión Python con Flask y SQLite

Sistema de gestión de inventario y ventas desarrollado en Python con Flask y SQLite.

## ✨ Ventajas de esta versión

- ✅ **Sin instalación de MySQL** - SQLite viene incluido con Python
- ✅ **Base de datos automática** - Se crea al iniciar el servidor
- ✅ **Datos de prueba incluidos** - Productos pre-cargados para probar
- ✅ **Portátil** - Un solo archivo de base de datos (inventario.db)
- ✅ **Fácil de usar** - Solo necesitas Python

## 📋 Características

- ✅ Gestión de productos (crear, leer, actualizar, eliminar)
- ✅ Control de stock en tiempo real
- ✅ Sistema de ventas con carrito de compras
- ✅ Generación de tickets de venta
- ✅ Registro de movimientos de inventario
- ✅ Gestión de fechas especiales por producto
- ✅ Reportes de ventas
- ✅ Protección con contraseña de administrador

## 🛠️ Tecnologías Utilizadas

- **Backend**: Python 3.8+ con Flask
- **Base de datos**: SQLite (incluido con Python)
- **Frontend**: HTML5, CSS3, JavaScript vanilla

## 📦 Instalación Rápida

### 1. Requisitos previos

- Python 3.8 o superior (SQLite viene incluido)
- pip (gestor de paquetes de Python)

### 2. Descargar el proyecto

Extrae el archivo ZIP en tu computadora.

### 3. Abrir en VS Code

1. Abre Visual Studio Code
2. File → Open Folder
3. Selecciona la carpeta `inventario-python-sqlite`

### 4. Abrir la terminal en VS Code

Presiona **Ctrl + Ñ** (o **Ctrl + `**)

### 5. Crear entorno virtual

**Windows (CMD):**
```cmd
python -m venv venv
venv\Scripts\activate.bat
```

**Mac/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 6. Instalar dependencias

```cmd
pip install -r requirements.txt
```

### 7. Crear archivo .env (opcional)

```cmd
copy .env.example .env
```

Puedes cambiar el puerto o la contraseña de admin si quieres.

### 8. ¡Ejecutar el servidor!

```cmd
python app.py
```

**¡Eso es todo!** La base de datos se crea automáticamente con datos de prueba.

### 9. Abrir en el navegador

Ve a: **http://localhost:3000**

## 📁 Estructura del Proyecto

```
inventario-python-sqlite/
│
├── app.py                 # Aplicación principal de Flask
├── database.py            # Gestión de SQLite
├── requirements.txt       # Dependencias (solo 3!)
├── .env                   # Configuración (opcional)
├── inventario.db          # Base de datos SQLite (se crea automáticamente)
│
├── routes/
│   ├── __init__.py
│   ├── productos.py       # Endpoints de productos
│   └── ventas.py          # Endpoints de ventas
│
├── index.html             # Página principal (gestión de inventario)
└── carrito.html           # Página de ventas (carrito)
```

## 🚀 Uso

### Página de Inventario (`http://localhost:3000`)

1. **Ver productos**: Los productos de prueba ya están cargados
2. **Agregar productos**: Completa el formulario y haz clic en "Agregar"
3. **Buscar productos**: Usa la barra de búsqueda
4. **Ver detalles**: Haz clic en cualquier producto

### Página de Ventas (`http://localhost:3000/carrito.html`)

1. Agrega productos al carrito desde el inventario
2. Revisa el carrito de compras
3. Haz clic en "Registrar Venta"
4. Ingresa el dinero recibido
5. Se genera automáticamente un ticket imprimible

## 🔐 Seguridad

- Contraseña de administrador por defecto: **admin123**
- Puedes cambiarla en el archivo `.env`

## 📊 Datos de Prueba

Al iniciar por primera vez, se crean automáticamente:

**Productos:**
- Laptop ($800.00, stock: 15)
- Escritorio ($150.00, stock: 20)
- Collar de plata ($250.00, stock: 10)
- Silla ($75.00, stock: 25)
- Monitor ($300.00, stock: 18)

**Categorías:**
- Electrónica
- Muebles
- Joyería

**Proveedores:**
- Proveedor A
- Proveedor B

## 🐛 Solución de Problemas

### Error: Module not found

```cmd
pip install -r requirements.txt
```

### El puerto 3000 ya está en uso

Crea un archivo `.env` y cambia el puerto:
```
PORT=5000
```

### Quiero empezar de cero (borrar la base de datos)

Simplemente elimina el archivo `inventario.db` y vuelve a ejecutar:
```cmd
python app.py
```

Se creará una nueva base de datos con datos de prueba.

## 💾 Base de Datos

La base de datos SQLite se guarda en un archivo llamado `inventario.db` en la misma carpeta del proyecto.

**Ventajas:**
- ✅ No necesita servidor de base de datos
- ✅ Se crea automáticamente
- ✅ Fácil de respaldar (solo copia el archivo .db)
- ✅ Perfecto para desarrollo y aplicaciones pequeñas

## 🔄 Respaldo

Para hacer un respaldo, simplemente copia el archivo `inventario.db` a otro lugar.

Para restaurar, reemplaza el archivo `inventario.db` con tu respaldo.

## 📝 Comandos Útiles

```cmd
# Activar entorno virtual
venv\Scripts\activate.bat

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar servidor
python app.py

# Desactivar entorno virtual
deactivate
```

## 🎓 Diferencias con la versión MySQL

- ✅ **Más fácil**: No requiere instalación de MySQL
- ✅ **Más rápida**: Setup en minutos
- ✅ **Más portable**: Un solo archivo de base de datos
- ⚠️ **Menos escalable**: No recomendado para producción con muchos usuarios concurrentes

## 🤝 Contribuciones

Este es un proyecto educativo. Siéntete libre de mejorarlo y adaptarlo a tus necesidades.

## 📄 Licencia

Proyecto de código abierto para uso educativo.

## 👨‍💻 Autor

Sistema desarrollado para ENTRELAZARTE

---

**¿Necesitas ayuda?** Revisa este README o contacta al desarrollador.
