#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generar_manifest.py
====================

Script para GENERAR el archivo manifest.json del modpack.

USO:
  1. Coloca este script en la MISMA carpeta donde tienes la estructura
     de tu modpack (mods/, config/, resourcepacks/, etc.)
     O BIEN indica --carpeta /ruta/a/modpack
  2. Ejecuta:
         python generar_manifest.py
  3. Se creará un archivo manifest.json listo para subir a GitHub / tu servidor.

El launcher descargará luego este manifest y comparará los hashes SHA-256
para saber qué archivos son nuevos, cambiaron o fueron eliminados.

Archivos y carpetas que se incluyen en el manifest (puedes editar la lista
INCLUIR_CARPETAS más abajo):
  - mods/          (.jar de mods)
  - config/        (configuraciones de mods)
  - resourcepacks/ (paquetes de recursos)
  - shaderpacks/   (shaders)
  - options.txt    (opciones generales de Minecraft)
  - servers.dat    (lista de servidores)

Puedes añadir carpetas o archivos extra según las necesidades de tu pack.
"""

import hashlib
import json
import os
import sys
import argparse
from pathlib import Path

# ======================================================================
# LISTA DE CARPETAS / PATRONES QUE SE INCLUYEN EN EL MANIFEST.
# Edítalo si tu modpack necesita más directorios.
# ======================================================================
INCLUIR_CARPETAS = [
    "mods",
    "config",
    "resourcepacks",
    "shaderpacks",
]
INCLUIR_ARCHIVOS_SOLTOS = [
    "options.txt",
    "servers.dat",
    "optionsshaders.txt",
]

# Archivos a ignorar incluso si están dentro de las carpetas anteriores
IGNORAR_EXTENSIONES = {".tmp", ".crash", ".log", ".bak", ".old"}
IGNORAR_ARCHIVOS = {".DS_Store", "Thumbs.db", "desktop.ini"}


def sha256_de_archivo(ruta: Path) -> str:
    """Devuelve el hash SHA-256 (hex lowercase) de un archivo."""
    h = hashlib.sha256()
    with open(ruta, "rb") as f:
        for bloque in iter(lambda: f.read(1024 * 1024), b""):
            h.update(bloque)
    return h.hexdigest()


def recorrer_carpeta(carpeta: Path, base: Path):
    """
    Recorre 'carpeta' y produce tuplas (ruta_relativa, hash_sha256)
    por cada archivo que cumpla los filtros.
    """
    for raiz, _, archivos in os.walk(carpeta):
        for nombre in archivos:
            if nombre in IGNORAR_ARCHIVOS:
                continue
            ext = Path(nombre).suffix.lower()
            if ext in IGNORAR_EXTENSIONES:
                continue

            ruta_abs = Path(raiz) / nombre
            ruta_rel = ruta_abs.relative_to(base)
            yield ruta_rel.as_posix(), sha256_de_archivo(ruta_abs)


def generar_manifest(carpeta_pack: Path, version_pack: str = "1.0.0") -> dict:
    """Construye la estructura dict del manifest (lista Files + Version)."""
    archivos = []

    # 1) Carpetas especiales
    for nombre_carpeta in INCLUIR_CARPETAS:
        ruta = carpeta_pack / nombre_carpeta
        if ruta.is_dir():
            for rel, h in recorrer_carpeta(ruta, carpeta_pack):
                archivos.append({"Path": rel, "Hash": h})
        else:
            print(f"[info] Carpeta no encontrada (se salta): {nombre_carpeta}")

    # 2) Archivos sueltos en la raíz
    for nombre in INCLUIR_ARCHIVOS_SOLTOS:
        ruta = carpeta_pack / nombre
        if ruta.is_file():
            h = sha256_de_archivo(ruta)
            archivos.append({"Path": nombre, "Hash": h})

    # Ordenar por ruta para que el manifest sea determinista y difs limpios
    archivos.sort(key=lambda x: x["Path"])

    return {
        "Version": version_pack,
        "Files": archivos,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Genera manifest.json para el launcher de Minecraft."
    )
    parser.add_argument(
        "--carpeta",
        default=".",
        help="Ruta a la carpeta raíz del modpack (mods/, config/, etc.). Por defecto: el directorio actual.",
    )
    parser.add_argument(
        "--version",
        default="1.0.0",
        help="Versión del modpack a escribir en el manifest. Por defecto 1.0.0.",
    )
    parser.add_argument(
        "--salida",
        default="manifest.json",
        help="Ruta del archivo de salida. Por defecto: manifest.json en la carpeta del modpack.",
    )
    args = parser.parse_args()

    carpeta_pack = Path(args.carpeta).resolve()
    if not carpeta_pack.is_dir():
        print(f"[error] La carpeta del modpack no existe: {carpeta_pack}")
        sys.exit(1)

    print(f"=== Generando manifest para modpack en: {carpeta_pack} ===")
    manifest = generar_manifest(carpeta_pack, args.version)

    # Escribir salida (por defecto: <carpeta_pack>/manifest.json)
    if args.salida == "manifest.json":
        ruta_salida = carpeta_pack / "manifest.json"
    else:
        ruta_salida = Path(args.salida).resolve()

    ruta_salida.parent.mkdir(parents=True, exist_ok=True)
    with open(ruta_salida, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    total = len(manifest["Files"])
    print(f"\n[OK] Listo. Se escribieron {total} archivos en:")
    print(f"   {ruta_salida}")
    print("\nSube esta carpeta a tu repositorio GitHub o servidor web y asegúrate")
    print("de que MODPACK_BASE_URL en DevConfig.cs apunte a la URL correcta.")


if __name__ == "__main__":
    main()
