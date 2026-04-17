# Instalación

## Opción 1: conda (recomendado para Windows/Mac/Linux)

```bash
git clone https://github.com/sebastiancobad/abm-enso-colombia.git
cd abm-enso-colombia
conda env create -f environment.yml
conda activate abm-enso
```

El `environment.yml` instala todas las dependencias desde conda-forge, incluyendo GDAL/GEOS/PROJ pre-compilados. Esto es crítico en Windows donde la instalación pip de `geopandas` suele fallar.

Tiempo total: ~5–10 minutos.

## Opción 2: pip (avanzado)

Requiere GDAL/GEOS/PROJ instalados en el sistema.

```bash
git clone https://github.com/sebastiancobad/abm-enso-colombia.git
cd abm-enso-colombia
python -m venv .venv
source .venv/bin/activate   # Linux/Mac
# o: .venv\Scripts\activate  # Windows
pip install -e .
```

## Configuración de Copernicus (solo la primera vez)

Para descargar ERA5 necesitas una cuenta gratuita de Copernicus CDS:

1. Registrarse en https://cds.climate.copernicus.eu/user/register
2. Copiar tu API key desde https://cds.climate.copernicus.eu/user (abajo del perfil)
3. Crear `~/.cdsapirc` (Linux/Mac) o `%USERPROFILE%\.cdsapirc` (Windows):

```
url: https://cds.climate.copernicus.eu/api
key: tu-key-aqui
```

4. Aceptar términos del dataset ERA5-Land en https://cds.climate.copernicus.eu/datasets/reanalysis-era5-land?tab=download

Sin este último paso, tu primer `abm-enso download` fallará con error 403.

## Verificación

```bash
pytest tests/ -v
```

Debes ver **70 passed** (1 skipped si geopandas no está instalado).

```bash
abm-enso --help
```

Debe imprimir los 4 subcomandos disponibles.

## Troubleshooting

### `conda: command not found` en Windows

Usa el shortcut **Miniforge Prompt** del menú Start en lugar de PowerShell. El PATH de conda no se configura automáticamente en PowerShell.

### GDAL import errors

Ocurre con instalación pip. Solución: usar `conda env create -f environment.yml` en su lugar.

### Copernicus: `ModuleNotFoundError: cdsapi`

```bash
pip install cdsapi
```

### Solara: `ModuleNotFoundError: anywidget`

```bash
pip install anywidget ipywidgets
```

### Windows: netCDF4 falla con rutas con tildes

Algunas versiones de netCDF4 fallan al leer archivos en rutas con caracteres especiales (`ñ`, tildes, espacios). Workaround: mover temporalmente el archivo a `C:\tmp\` y procesar desde ahí.
