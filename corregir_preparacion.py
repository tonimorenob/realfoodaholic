#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para corregir SOLO la preparación de las recetas.
NO toca ningún otro campo (thumbnail, categorías, ingredientes, descripción, etc.)
"""

import os
import re
from html import unescape

CARPETA_HTML = "recetas"
CARPETA_MD = "_recetas"

# Las 30 recetas con preparación incompleta
RECETAS = [
    "canelones-bechamel-morada",
    "crema-de-calabaza-y-romero",
    "crema-de-guisantes",
    "crema-de-tomate-y-albahaca",
    "curry-de-pollo-expres",
    "empanadas-criollas-veganas",
    "empanadas-de-masa-de-yuca",
    "galletas-cacao-crema-cacahuete",
    "galletas-de-avena-y-crema-de-cacahuete",
    "gazpacho-de-fresas",
    "gazpacho-de-mango",
    "guiso-de-pavo-con-manzana",
    "hamburguesa-de-lentejas",
    "hummus-aguacate-cilantro",
    "hummus-altramuces-tomate-seco",
    "hummus-cacao",
    "hummus-de-alubias-blancas-y-remolacha",
    "hummus-de-lentejas",
    "masa-de-pizza-de-yuca",
    "natillas-de-caqui",
    "pica-pica-de-sepia",
    "potaje-de-garbanzos",
    "potaje-de-lentejas-con-verduras",
    "pudding-de-quinoa-y-avena",
    "sopa-fria-sandia",
    "sopa-miso",
    "sopa-thai",
    "tofu-general-tso",
    "tomates-cherry-al-horno",
    "vichyssoise-de-manzana",
]


def limpiar_html(texto):
    texto = re.sub(r'<[^>]+>', '', texto)
    texto = unescape(texto)
    return texto.strip()


def leer_archivo(filepath):
    for encoding in ['utf-8', 'latin-1', 'cp1252']:
        try:
            with open(filepath, 'r', encoding=encoding) as f:
                return f.read()
        except UnicodeDecodeError:
            continue
    return None


def extraer_preparacion_html(html):
    """Extrae todos los pasos de preparación del HTML"""
    patron = re.compile(
        r'<h5[^>]*>\s*PREPARACI[ÓO]N\s*</h5>(.*?)(?:</div>\s*</div>|<div[^>]*style="height|<h5|$)',
        re.IGNORECASE | re.DOTALL
    )
    
    match = patron.search(html)
    if not match:
        return []
    
    seccion = match.group(1)
    pasos = []
    
    # Extraer todos los <li> de listas ordenadas y no ordenadas
    items = re.findall(r'<li[^>]*>(.*?)</li>', seccion, re.IGNORECASE | re.DOTALL)
    for item in items:
        texto = limpiar_html(item)
        if texto:
            pasos.append(texto)
    
    return pasos


def actualizar_solo_preparacion(md_path, preparacion):
    """Actualiza SOLO el campo preparacion del archivo MD"""
    contenido = leer_archivo(md_path)
    if not contenido:
        return False
    
    if not contenido.startswith('---'):
        return False
    
    segundo_guion = contenido.find('---', 3)
    if segundo_guion == -1:
        return False
    
    front_matter = contenido[3:segundo_guion]
    resto = contenido[segundo_guion:]
    
    # Crear nuevo valor de preparación
    nuevo_preparacion = "preparacion: |\n"
    for paso in preparacion:
        paso_limpio = paso.replace('"', "'")
        nuevo_preparacion += f"  {paso_limpio}\n"
    
    # Buscar y reemplazar el campo preparacion existente
    patron_prep = re.compile(
        r'^preparacion:.*?(?=\n[a-z_]+:|\Z)', 
        re.MULTILINE | re.DOTALL
    )
    
    if patron_prep.search(front_matter):
        nuevo_front = patron_prep.sub(nuevo_preparacion.rstrip(), front_matter)
    else:
        # No existe, añadir al final del front matter
        nuevo_front = front_matter.rstrip() + '\n' + nuevo_preparacion
    
    nuevo_contenido = '---' + nuevo_front + resto
    
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(nuevo_contenido)
    
    return True


def main():
    print("=" * 70)
    print("CORRECCIÓN DE PREPARACIÓN")
    print("=" * 70)
    
    exito = 0
    fallo = 0
    
    for slug in RECETAS:
        html_path = os.path.join(CARPETA_HTML, f"{slug}.html")
        md_path = os.path.join(CARPETA_MD, f"{slug}.md")
        
        print(f"\n{slug}")
        
        if not os.path.exists(html_path):
            print(f"  ⚠️ No existe HTML")
            fallo += 1
            continue
        
        if not os.path.exists(md_path):
            print(f"  ⚠️ No existe MD")
            fallo += 1
            continue
        
        html = leer_archivo(html_path)
        preparacion = extraer_preparacion_html(html)
        
        if not preparacion:
            print(f"  ⚠️ Sin preparación en HTML")
            fallo += 1
            continue
        
        print(f"  Encontrados: {len(preparacion)} pasos")
        
        if actualizar_solo_preparacion(md_path, preparacion):
            print(f"  ✅ OK")
            exito += 1
        else:
            print(f"  ❌ Error")
            fallo += 1
    
    print("\n" + "=" * 70)
    print(f"✅ Corregidas: {exito}")
    print(f"❌ Fallidas: {fallo}")


if __name__ == "__main__":
    main()
