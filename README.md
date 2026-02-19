# 📘 Manual de Instalación y Ejecución – KALLPA-UNL Backend

Este manual detalla paso a paso cómo configurar el entorno, la base de datos y ejecutar el proyecto junto con sus pruebas automatizadas.

**Rama objetivo:** `main`

---

## 🛠️ 1. Requisitos Previos

Antes de comenzar, asegúrate de tener instalado:
*   **Python 3.12+**: [Descargar Python](https://www.python.org/downloads/)
*   **PostgreSQL**: [Descargar PostgreSQL](https://www.postgresql.org/download/)
*   **Git**: [Descargar Git](https://git-scm.com/downloads)

---

## 🚀 2. Clonación y Configuración del Repositorio

### 2.1. Clonar el proyecto
Abre tu terminal (PowerShell, CMD, o Bash) y ejecuta:

```bash
git clone https://github.com/ThiagoAbrigo/kallpa-unl-backend.git
cd kallpa-unl-backend
```

### 2.2. Cambiar a la rama principal (Main)
Es **CRUCIAL** cambiar a la rama `main` para tener la versión correcta y estable del código:

```bash
git checkout main
```

---

## 🐍 3. Configuración del Entorno Virtual

Sigue las instrucciones según tu sistema operativo:

### 🖥️ Windows

1.  **Crear el entorno virtual:**
    ```powershell
    python -m venv venv
    ```
2.  **Activar el entorno:**
    ```powershell
    .\venv\Scripts\activate
    ```
    *(Verás `(venv)` al inicio de tu línea de comandos)*

### 🐧 Linux / 🍎 MacOS

1.  **Crear el entorno virtual:**
    ```bash
    python3 -m venv venv
    ```
2.  **Activar el entorno:**
    ```bash
    source venv/bin/activate
    ```

### 3.1. Instalar dependencias
Con el entorno activado, instala las librerías necesarias:

```bash
pip install -r requirements.txt
```

---

## 🗄️ 4. Configuración de la Base de Datos

### 4.1. Crear la Base de Datos
Debes crear una base de datos llamada `kallpa_bd`. Puedes usar pgAdmin o la terminal:

```bash
createdb -h localhost -U postgres kallpa_bd
```
*Te pedirá la contraseña de tu usuario postgres.*

### 4.2. Configurar Variables de Entorno (.env)
Copia el archivo de ejemplo y edítalo con tus credenciales:

```bash
cp .env.example .env
```

Luego edita el archivo `.env` con tu configuración:

```ini
FLASK_APP=Kallpa
FLASK_ENV=development

# Configuración de Base de Datos
USE_POSTGRES=true
PGUSER=postgres
PGPASSWORD=TU_PASSWORD_AQUI
PGHOST=localhost
PGDATABASE=kallpa_bd
PGPORT=5432

# Claves secretas
SECRET_KEY=kallpa123
JWT_SECRET_KEY=jwt_secret_kallpa
```

> [!IMPORTANT]
> Asegúrate de que `PGPASSWORD` coincida con la contraseña de tu usuario `postgres` local.

---

## ▶️ 5. Ejecución del Proyecto

Para iniciar el servidor de desarrollo:

```bash
python index.py
```
Si todo es correcto, verás: `Running on http://127.0.0.1:5000`

---

## ✅ 6. Ejecución de Pruebas

Las pruebas utilizan **mocks** y **NO requieren** que el servidor esté corriendo ni conexión a la base de datos.

Ejecuta el siguiente comando desde la raíz del proyecto:

```bash
python3 -m unittest tests.pruebas_finales -v
```

Deberías ver una salida indicando `OK` si todas las pruebas pasan correctamente.