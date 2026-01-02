#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para corregir SOLO los ingredientes de las recetas.
NO toca ningún otro campo (thumbnail, categorías, descripción, etc.)
"""

import os
import re
from html import unescape

CARPETA_HTML = "recetas"
CARPETA_MD = "_recetas"

# Las 61 recetas con ingredientes incompletos
RECETAS = [
    "albondigas-de-soja-texturizada-en-salsa-de-tomate",
    "bao-buns-con-pulled-pork-y-cebolla-caramelizada",
    "bechamel-de-calabacin",
    "canelones-bechamel-morada",
    "canelones-de-calabacin-con-bolonesa-de-lentejas",
    "ceviche-atun",
    "cheesecake-de-tofu-y-arandanos",
    "cocktail-de-gambas-con-salsa-rosa-de-huevo-duro",
    "coleslaw-lombarda",
    "crackers-de-semillas",
    "crema-de-calabaza-y-romero",
    "crema-de-guisantes",
    "crema-de-tomate-y-albahaca",
    "curry-de-pollo-expres",
    "curry-panang",
    "empanadas-criollas-veganas",
    "empanadas-de-masa-de-yuca",
    "ensalada-alemana-de-patata-kartoffelsalat",
    "ensalada-thai",
    "ensaladilla-de-salmon",
    "falafel-con-salsa-de-yogur",
    "fiambre-de-pavo-y-pollo",
    "gachas-de-avena-proteicas",
    "galletas-cacao-crema-cacahuete",
    "galletas-de-avena",
    "galletas-de-avena-y-crema-de-cacahuete",
    "gazpacho-de-fresas",
    "gazpacho-de-mango",
    "gyozas",
    "hamburguesa-de-berenjena",
    "hamburguesa-de-lentejas",
    "helado-de-frutas",
    "hummus-aguacate-cilantro",
    "hummus-altramuces-tomate-seco",
    "hummus-cacao",
    "hummus-de-alubias-blancas-y-remolacha",
    "hummus-de-lentejas",
    "lasana-berenjena",
    "masa-de-pizza-de-yuca",
    "mini-hamburguesas-tofu",
    "natillas-de-caqui",
    "noodles-salsa-teriyaki",
    "pan-moreno-mallorquin-con-alioli",
    "pastelitos-de-remolacha-y-cacao",
    "patata-rellena-de-pulled-pork-en-olla-lenta",
    "pimientos-de-piquillo-rellenos-de-merluza",
    "pollo-teriyaki-expres",
    "porridge-con-manzana-especiada",
    "potaje-de-lentejas-con-verduras",
    "pudding-de-quinoa-y-avena",
    "pulled-pork-jackfruit",
    "pulled-pork-vegano",
    "risotto-de-champinones-shiitake-y-trufa",
    "risotto-negro",
    "rollitos-de-primavera",
    "rollitos-vietnamitas",
    "seitan",
    "sopa-fria-sandia",
    "sopa-miso",
    "sopa-thai",
    "tofu-agridulce",
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


def extraer_ingredientes_html(html):
    """Extrae todos los ingredientes del HTML incluyendo subtítulos"""
    patron = re.compile(
        r'<h5[^>]*>\s*INGREDIENTES\s*</h5>(.*?)(?:<h5[^>]*>\s*PREPARACI[ÓO]N|<div[^>]*style="flex-basis:66)',
        re.IGNORECASE | re.DOTALL
    )
    
    match = patron.search(html)
    if not match:
        return []
    
    seccion = match.group(1)
    elementos = []
    
    # Encontrar párrafos (subtítulos)
    for m in re.finditer(r'<p[^>]*>(.*?)</p>', seccion, re.IGNORECASE | re.DOTALL):
        texto = limpiar_html(m.group(1))
        if texto and (texto.endswith(':') or (len(texto) < 40 and not texto.startswith('http'))):
            elementos.append((m.start(), 'subtitulo', texto))
    
    # Encontrar listas
    for m in re.finditer(r'<ul[^>]*>(.*?)</ul>', seccion, re.IGNORECASE | re.DOTALL):
        elementos.append((m.start(), 'lista', m.group(1)))
    
    # Ordenar por posición
    elementos.sort(key=lambda x: x[0])
    
    # Procesar en orden
    ingredientes = []
    for pos, tipo, contenido in elementos:
        if tipo == 'subtitulo':
            ingredientes.append(f"\n{contenido}")
        else:
            items = re.findall(r'<li[^>]*>(.*?)</li>', contenido, re.IGNORECASE | re.DOTALL)
            for item in items:
                texto = limpiar_html(item)
                if texto:
                    ingredientes.append(texto)
    
    return ingredientes


def actualizar_solo_ingredientes(md_path, ingredientes):
    """Actualiza SOLO el campo ingredientes del archivo MD"""
    contenido = leer_archivo(md_path)
    if not contenido:
        return False
    
    # Verificar que tiene front matter
    if not contenido.startswith('---'):
        return False
    
    # Encontrar el final del front matter
    segundo_guion = contenido.find('---', 3)
    if segundo_guion == -1:
        return False
    
    front_matter = contenido[3:segundo_guion]
    resto = contenido[segundo_guion:]
    
    # Crear nuevo valor de ingredientes
    nuevo_ingredientes = "ingredientes: |\n"
    for ing in ingredientes:
        # Escapar comillas si las hay
        ing_limpio = ing.replace('"', "'")
        nuevo_ingredientes += f"  {ing_limpio}\n"
    
    # Buscar y reemplazar el campo ingredientes existente
    # Patrón: ingredientes: seguido de contenido hasta el siguiente campo o fin de front matter
    patron_ing = re.compile(
        r'^ingredientes:.*?(?=\n[a-z_]+:|\Z)', 
        re.MULTILINE | re.DOTALL
    )
    
    if patron_ing.search(front_matter):
        # Reemplazar ingredientes existentes
        nuevo_front = patron_ing.sub(nuevo_ingredientes.rstrip(), front_matter)
    else:
        # Añadir ingredientes al final del front matter
        nuevo_front = front_matter.rstrip() + '\n' + nuevo_ingredientes
    
    # Reconstruir archivo
    nuevo_contenido = '---' + nuevo_front + resto
    
    # Guardar
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(nuevo_contenido)
    
    return True


def main():
    print("=" * 70)
    print("CORRECCIÓN DE INGREDIENTES")
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
        ingredientes = extraer_ingredientes_html(html)
        
        if not ingredientes:
            print(f"  ⚠️ Sin ingredientes en HTML")
            fallo += 1
            continue
        
        print(f"  Encontrados: {len(ingredientes)} items")
        
        if actualizar_solo_ingredientes(md_path, ingredientes):
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
