#!/usr/bin/env python3
"""
Script para convertir recetas HTML antiguas de Realfoodaholic a formato Markdown.
Ejecutar desde la raíz del repositorio: python convertir_recetas.py
"""

import os
import re
from html.parser import HTMLParser
from html import unescape

# Mapeo de nombres de categorías a slugs
CATEGORIAS_MAP = {
    "platos principales": "platos-principales",
    "ensaladas": "ensaladas",
    "desayunos": "desayunos-2",
    "postres": "postres",
    "veganas": "recetas-veganas",
    "recetas veganas": "recetas-veganas",
    "snacks dulces": "snacks-2",
    "snacks salados": "snacks",
    "sopas y cremas": "sopas-y-cremas",
    "salsas y patés": "salsas",
    "salsas": "salsas",
    "acompañamientos": "acompanamientos",
    "acompanamientos": "acompanamientos",
    "olla lenta": "olla-lenta",
    "microondas": "microondas",
}

def limpiar_texto(texto):
    """Limpia el texto de HTML y espacios extra."""
    if not texto:
        return ""
    texto = unescape(texto)
    texto = re.sub(r'<[^>]+>', '', texto)
    texto = re.sub(r'\s+', ' ', texto)
    return texto.strip()

def extraer_datos_receta(html_content, filename):
    """Extrae los datos de una receta desde el HTML."""
    datos = {
        'title': '',
        'thumbnail': '',
        'date': '',
        'categories': [],
        'descripcion': '',
        'ingredientes': [],
        'preparacion': []
    }
    
    # Extraer título
    match = re.search(r'<h1[^>]*>([^<]+)</h1>', html_content)
    if match:
        datos['title'] = limpiar_texto(match.group(1))
    
    # Extraer imagen destacada
    match = re.search(r'<img[^>]+class="recipe-featured-img"[^>]+src="([^"]+)"', html_content)
    if not match:
        match = re.search(r'<img[^>]+src="([^"]+)"[^>]+class="recipe-featured-img"', html_content)
    if match:
        img_path = match.group(1)
        # Normalizar la ruta (quitar ../ y poner /)
        img_path = re.sub(r'^\.\./', '/', img_path)
        if not img_path.startswith('/'):
            img_path = '/' + img_path
        datos['thumbnail'] = img_path
    
    # Extraer fecha
    match = re.search(r'📅\s*(\d{4}-\d{2}-\d{2})', html_content)
    if match:
        datos['date'] = match.group(1)
    
    # Extraer categorías
    match = re.search(r'📁\s*([^<]+)</span>', html_content)
    if match:
        cats_texto = match.group(1)
        cats_lista = [c.strip().lower() for c in cats_texto.split(',')]
        for cat in cats_lista:
            if cat in CATEGORIAS_MAP:
                datos['categories'].append(CATEGORIAS_MAP[cat])
            else:
                # Intentar encontrar coincidencia parcial
                for nombre, slug in CATEGORIAS_MAP.items():
                    if nombre in cat or cat in nombre:
                        datos['categories'].append(slug)
                        break
    
    # Extraer descripción (párrafos antes de ingredientes)
    # Buscar el contenido entre recipe-body y INGREDIENTES
    match = re.search(r'<div class="recipe-body">(.*?)<h5>INGREDIENTES</h5>', html_content, re.DOTALL)
    if match:
        desc_html = match.group(1)
        # Extraer solo los párrafos <p>
        parrafos = re.findall(r'<p[^>]*>(.+?)</p>', desc_html, re.DOTALL)
        descripcion_limpia = []
        for p in parrafos:
            texto = limpiar_texto(p)
            if texto and len(texto) > 10:  # Ignorar párrafos muy cortos
                descripcion_limpia.append(texto)
        datos['descripcion'] = '\n\n'.join(descripcion_limpia)
    
    # Extraer ingredientes
    match = re.search(r'<h5>INGREDIENTES</h5>\s*<ul>(.*?)</ul>', html_content, re.DOTALL)
    if match:
        items = re.findall(r'<li>(.+?)</li>', match.group(1), re.DOTALL)
        datos['ingredientes'] = [limpiar_texto(item) for item in items]
    
    # Extraer preparación
    match = re.search(r'<h5>PREPARACIÓN</h5>\s*<ol>(.*?)</ol>', html_content, re.DOTALL)
    if match:
        pasos = re.findall(r'<li>(.+?)</li>', match.group(1), re.DOTALL)
        datos['preparacion'] = [limpiar_texto(paso) for paso in pasos]
    
    return datos

def generar_markdown(datos):
    """Genera el contenido Markdown para una receta."""
    # Front matter
    md = '---\n'
    md += 'layout: receta\n'
    md += f'title: "{datos["title"]}"\n'
    md += f'date: {datos["date"]}\n'
    md += f'thumbnail: "{datos["thumbnail"]}"\n'
    
    # Categorías como array YAML
    if datos['categories']:
        md += 'categories:\n'
        for cat in datos['categories']:
            md += f'  - {cat}\n'
    
    # Ingredientes como texto multilínea
    if datos['ingredientes']:
        md += 'ingredientes: |\n'
        for ing in datos['ingredientes']:
            md += f'  {ing}\n'
    
    # Preparación como texto multilínea
    if datos['preparacion']:
        md += 'preparacion: |\n'
        for paso in datos['preparacion']:
            md += f'  {paso}\n'
    
    md += '---\n\n'
    
    # Contenido (descripción)
    if datos['descripcion']:
        md += datos['descripcion']
    
    return md

def convertir_recetas():
    """Función principal que convierte todas las recetas."""
    carpeta_html = 'recetas'
    carpeta_md = '_recetas'
    
    # Verificar que estamos en el directorio correcto
    if not os.path.exists(carpeta_html):
        print(f"ERROR: No se encuentra la carpeta '{carpeta_html}'")
        print("Asegúrate de ejecutar este script desde la raíz del repositorio.")
        return
    
    # Crear carpeta de salida si no existe
    if not os.path.exists(carpeta_md):
        os.makedirs(carpeta_md)
        print(f"Creada carpeta '{carpeta_md}'")
    
    # Obtener lista de archivos HTML
    archivos_html = [f for f in os.listdir(carpeta_html) if f.endswith('.html')]
    print(f"\nEncontradas {len(archivos_html)} recetas para convertir.\n")
    
    convertidas = 0
    errores = []
    categorias_no_encontradas = set()
    
    for archivo in archivos_html:
        ruta_html = os.path.join(carpeta_html, archivo)
        nombre_base = archivo.replace('.html', '')
        ruta_md = os.path.join(carpeta_md, f'{nombre_base}.md')
        
        try:
            with open(ruta_html, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            datos = extraer_datos_receta(html_content, archivo)
            
            # Verificar datos mínimos
            if not datos['title']:
                errores.append(f"{archivo}: No se encontró título")
                continue
            
            if not datos['categories']:
                errores.append(f"{archivo}: No se encontraron categorías")
            
            markdown = generar_markdown(datos)
            
            with open(ruta_md, 'w', encoding='utf-8') as f:
                f.write(markdown)
            
            convertidas += 1
            print(f"✓ {datos['title'][:50]}...")
            
        except Exception as e:
            errores.append(f"{archivo}: {str(e)}")
    
    # Resumen
    print(f"\n{'='*50}")
    print(f"CONVERSIÓN COMPLETADA")
    print(f"{'='*50}")
    print(f"Recetas convertidas: {convertidas}")
    print(f"Errores: {len(errores)}")
    
    if errores:
        print(f"\nERRORES:")
        for error in errores:
            print(f"  - {error}")
    
    print(f"\nLos archivos .md se han guardado en: {carpeta_md}/")
    print("\nPRÓXIMOS PASOS:")
    print("1. Revisa algunas recetas convertidas para verificar que están bien")
    print("2. Haz commit de los cambios: git add . && git commit -m 'Convertir recetas a Markdown'")
    print("3. Sube a GitHub: git push")

if __name__ == '__main__':
    convertir_recetas()
