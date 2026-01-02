#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para corregir recetas con ingredientes y/o preparación incompletos.
Extrae TODAS las listas del HTML original y actualiza los archivos MD.
"""

import os
import re
from html import unescape

# Carpetas
CARPETA_HTML = "recetas"
CARPETA_MD = "_recetas"

# Lista de las 78 recetas a corregir
RECETAS_A_CORREGIR = [
    "albondigas-de-soja-texturizada-en-salsa-de-tomate",
    "arepas-con-perico",
    "bao-buns-con-pulled-pork-y-cebolla-caramelizada",
    "bechamel-de-calabacin",
    "bocadillo-de-pulled-pork-vegano-con-guacamole-y-chips",
    "canelones-bechamel-morada",
    "canelones-de-calabacin-con-bolonesa-de-lentejas",
    "ceviche-atun",
    "cheesecake-de-tofu-y-arandanos",
    "cocktail-de-gambas-con-salsa-rosa-de-huevo-duro",
    "coleslaw-lombarda",
    "compota-de-pera-especiada",
    "crackers-de-semillas",
    "crema-de-calabaza-y-romero",
    "crema-de-guisantes",
    "crema-de-tomate-y-albahaca",
    "crema-naranja",
    "croquetas-al-horno",
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
    "guiso-de-pavo-con-manzana",
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
    "lasana-con-bechamel-de-coliflor",
    "masa-de-pizza-de-yuca",
    "mini-hamburguesas-tofu",
    "natillas-de-caqui",
    "noodles-salsa-teriyaki",
    "pan-moreno-mallorquin-con-alioli",
    "panacota-de-coco-y-platano-con-compota-especiada-de-cerezas",
    "pastelitos-de-remolacha-y-cacao",
    "patata-rellena-de-pulled-pork-en-olla-lenta",
    "pica-pica-de-sepia",
    "pimientos-de-piquillo-rellenos-de-merluza",
    "pollo-teriyaki-expres",
    "porridge-con-manzana-especiada",
    "potaje-de-garbanzos",
    "potaje-de-lentejas-con-verduras",
    "pudding-de-quinoa-y-avena",
    "pulled-pork-jackfruit",
    "pulled-pork-vegano",
    "quesadillas-de-queso-aguacate-y-tomate-con-salsa-dip",
    "quiche-integral-de-espinacas-y-leche-de-coco",
    "risotto-de-champinones-shiitake-y-trufa",
    "risotto-negro",
    "rollitos-de-primavera",
    "rollitos-vietnamitas",
    "seitan",
    "sopa-fria-sandia",
    "sopa-miso",
    "sopa-thai",
    "tacos-de-garbanzo",
    "tofu-agridulce",
    "tofu-general-tso",
    "tomates-cherry-al-horno",
    "tortilla-tofu-rellena",
    "vichyssoise-de-manzana",
]


def limpiar_html(texto):
    """Elimina etiquetas HTML y decodifica entidades"""
    texto = re.sub(r'<[^>]+>', '', texto)
    texto = unescape(texto)
    return texto.strip()


def leer_archivo(filepath):
    """Lee un archivo probando diferentes encodings"""
    for encoding in ['utf-8', 'latin-1', 'cp1252']:
        try:
            with open(filepath, 'r', encoding=encoding) as f:
                return f.read()
        except UnicodeDecodeError:
            continue
    return None


def extraer_ingredientes_html(html):
    """Extrae TODOS los ingredientes del HTML (todas las listas <ul> en la sección)"""
    # Buscar la sección de ingredientes (entre INGREDIENTES y PREPARACIÓN)
    patron_seccion = re.compile(
        r'<h5[^>]*>\s*INGREDIENTES\s*</h5>(.*?)(?:<h5[^>]*>\s*PREPARACI[ÓO]N|<div class="wp-block-column"[^>]*style="flex-basis:66)',
        re.IGNORECASE | re.DOTALL
    )
    
    match = patron_seccion.search(html)
    if not match:
        return []
    
    seccion = match.group(1)
    ingredientes = []
    
    # Buscar párrafos que son subtítulos (para incluirlos en orden)
    parrafos_pos = [(m.start(), limpiar_html(m.group(1))) for m in re.finditer(r'<p[^>]*>(.*?)</p>', seccion, re.IGNORECASE | re.DOTALL)]
    
    # Buscar todas las listas <ul>
    listas = list(re.finditer(r'<ul[^>]*>(.*?)</ul>', seccion, re.IGNORECASE | re.DOTALL))
    
    for idx, lista in enumerate(listas):
        pos_lista = lista.start()
        
        # Ver si hay un subtítulo antes de esta lista (solo para listas después de la primera)
        if idx > 0:
            for pos_p, texto_p in parrafos_pos:
                # El subtítulo debe estar entre la lista anterior y esta
                pos_lista_anterior = listas[idx-1].end() if idx > 0 else 0
                if pos_lista_anterior < pos_p < pos_lista and (texto_p.endswith(':') or texto_p.isupper()):
                    ingredientes.append(f"\n{texto_p}")
                    break
        
        # Extraer los items de esta lista
        items = re.findall(r'<li[^>]*>(.*?)</li>', lista.group(1), re.IGNORECASE | re.DOTALL)
        for item in items:
            texto = limpiar_html(item)
            if texto:
                ingredientes.append(texto)
    
    return ingredientes


def extraer_preparacion_html(html):
    """Extrae TODOS los pasos de preparación del HTML"""
    # Buscar la sección de preparación
    patron_seccion = re.compile(
        r'<h5[^>]*>\s*PREPARACI[ÓO]N\s*</h5>(.*?)(?:</div>\s*</div>\s*(?:<div[^>]*>|$)|<div[^>]*style="height|<h5|$)',
        re.IGNORECASE | re.DOTALL
    )
    
    match = patron_seccion.search(html)
    if not match:
        return []
    
    seccion = match.group(1)
    pasos = []
    
    # Extraer TODOS los <li> de la sección
    items = re.findall(r'<li[^>]*>(.*?)</li>', seccion, re.IGNORECASE | re.DOTALL)
    for item in items:
        texto = limpiar_html(item)
        if texto:
            pasos.append(texto)
    
    return pasos


def actualizar_md(filepath, ingredientes, preparacion):
    """Actualiza un archivo MD con los ingredientes y preparación"""
    try:
        contenido = leer_archivo(filepath)
        if not contenido:
            return False
        
        # Separar front matter del contenido
        if not contenido.startswith('---'):
            return False
        
        partes = contenido.split('---', 2)
        if len(partes) < 3:
            return False
        
        front_matter = partes[1]
        body = partes[2]
        
        # Función para reemplazar o añadir un campo
        def actualizar_campo(fm, campo, valores):
            if not valores:
                return fm
            
            # Crear el nuevo valor del campo
            nuevo_valor = f'{campo}: |\n'
            for v in valores:
                # Escapar caracteres problemáticos para YAML
                v_escapado = v.replace('"', '\\"')
                nuevo_valor += f'  {v_escapado}\n'
            
            # Buscar si el campo ya existe
            patron = re.compile(rf'^{campo}:.*?(?=\n[a-z_]+:|\Z)', re.MULTILINE | re.DOTALL)
            
            if re.search(patron, fm):
                # Reemplazar el campo existente
                fm = patron.sub(nuevo_valor.rstrip(), fm)
            else:
                # Añadir el campo al final
                fm = fm.rstrip() + '\n' + nuevo_valor
            
            return fm
        
        # Actualizar ingredientes
        if ingredientes:
            front_matter = actualizar_campo(front_matter, 'ingredientes', ingredientes)
        
        # Actualizar preparación
        if preparacion:
            front_matter = actualizar_campo(front_matter, 'preparacion', preparacion)
        
        # Reconstruir el archivo
        nuevo_contenido = f'---{front_matter}---{body}'
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(nuevo_contenido)
        
        return True
        
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False


def main():
    print("=" * 80)
    print("CORRECCIÓN DE RECETAS - Extrayendo datos completos")
    print("=" * 80)
    
    corregidas = 0
    fallidas = 0
    
    for slug in RECETAS_A_CORREGIR:
        html_path = os.path.join(CARPETA_HTML, f"{slug}.html")
        md_path = os.path.join(CARPETA_MD, f"{slug}.md")
        
        print(f"\n📄 {slug}")
        
        if not os.path.exists(html_path):
            print(f"  ⚠️ No existe HTML: {html_path}")
            fallidas += 1
            continue
        
        if not os.path.exists(md_path):
            print(f"  ⚠️ No existe MD: {md_path}")
            fallidas += 1
            continue
        
        html = leer_archivo(html_path)
        if not html:
            print(f"  ⚠️ No se pudo leer el HTML")
            fallidas += 1
            continue
        
        # Extraer datos
        ingredientes = extraer_ingredientes_html(html)
        preparacion = extraer_preparacion_html(html)
        
        print(f"  Ingredientes: {len(ingredientes)} | Preparación: {len(preparacion)}")
        
        if not ingredientes and not preparacion:
            print(f"  ⚠️ No se encontraron datos")
            fallidas += 1
            continue
        
        # Actualizar MD
        if actualizar_md(md_path, ingredientes, preparacion):
            print(f"  ✅ Actualizado")
            corregidas += 1
        else:
            print(f"  ❌ Error al actualizar")
            fallidas += 1
    
    # Resumen
    print("\n" + "=" * 80)
    print("RESUMEN")
    print("=" * 80)
    print(f"✅ Corregidas: {corregidas}")
    print(f"❌ Fallidas: {fallidas}")
    print(f"Total: {len(RECETAS_A_CORREGIR)}")


if __name__ == "__main__":
    main()
