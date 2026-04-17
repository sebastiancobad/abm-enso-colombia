# Instalación

## Requisitos de sistema

- Python ≥ 3.11
- ~2 GB de espacio en disco (datos + dependencias geoespaciales)
- Conexión a internet para la descarga inicial de datos

En Linux y macOS la instalación es directa. En Windows se recomienda usar **Miniforge** o **WSL2** por las dependencias geoespaciales (`gdal`, `rasterio`, `geopandas`), que son difíciles de compilar desde `pip` en Windows puro.

## Paso 1 — Clonar el repo

```bash
git clone https://github.com/sebastiancobad/abm-enso-colombia.git
cd abm-enso-colombia
```

## Paso 2 — Crear entorno virtual

### Opción A: `venv` (Python estándar)

```bash
python -m venv .venv
source .venv/bin/activate        # Linux/macOS
# .venv\Scripts\activate         # Windows PowerShell
```

### Opción B: `conda` / `mamba` (recomendado para Windows)

```bash
mamba create -n abm-enso python=3.11 gdal geopandas rasterio -c conda-forge
mamba activate abm-enso
```

Conda resuelve los binarios GDAL/GEOS sin necesidad de compilar.

## Paso 3 — Instalar el paquete

Para uso normal:

```bash
pip install -r requirements.txt
```

Para desarrollo (incluye pytest, ruff, mkdocs, jupyter):

```bash
pip install -e ".[dev]"
```

## Paso 4 — Configurar credenciales Copernicus CDS

ERA5 requiere una cuenta gratuita en Copernicus Climate Data Store.

1. Regístrate en [cds.climate.copernicus.eu](https://cds.climate.copernicus.eu/user/register)
2. Copia tu `UID` y `API key` desde [tu perfil](https://cds.climate.copernicus.eu/user)
3. Crea `~/.cdsapirc` con el siguiente contenido:

```
url: https://cds.climate.copernicus.eu/api
key: <UID>:<API-KEY>
```

4. Acepta los términos del dataset ERA5-Land monthly means al menos una vez desde el navegador.

## Paso 5 — Verificar la instalación

```bash
pytest tests/ -v
```

Si los tests pasan, el paquete está correctamente instalado. Ya puedes correr:

```bash
abm-enso --help
```

## Solución de problemas

### `ImportError: libgdal.so.XX`

GDAL no está instalado. En Ubuntu/Debian:

```bash
sudo apt install libgdal-dev
pip install --force-reinstall rasterio geopandas
```

O usa conda-forge (paso 2, opción B).

### `cdsapi.exceptions.APIException: authentication failed`

Revisa `~/.cdsapirc`. La clave es `<UID>:<API-KEY>` con dos puntos, no `<API-KEY>` solo.

### Solara no abre el navegador

Forzar host y puerto manualmente:

```bash
solara run src/abm_enso/viz/app.py --host 0.0.0.0 --port 8765
```

Luego abre `http://localhost:8765` manualmente.
