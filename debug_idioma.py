"""
Script de debug para el sistema de internacionalización
Ejecutar: python debug_idioma.py
"""

import os
import re
from pathlib import Path


def check_template_file(filepath):
    """Analiza un archivo de template buscando problemas"""
    print(f"\n{'='*80}")
    print(f"📄 Analizando: {filepath}")
    print('='*80)

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    issues = []
    warnings = []

    # 1. Verificar que exista el bloque scripts
    if '{% block scripts %}' not in content:
        issues.append("❌ No se encontró {% block scripts %}")
    else:
        print("✅ Bloque {% block scripts %} encontrado")

    # 2. Verificar declaraciones de clases
    class_declarations = re.findall(r'class\s+(\w+)\s*{', content)
    if class_declarations:
        print(f"✅ Clases declaradas: {', '.join(class_declarations)}")

        # Verificar duplicados
        if len(class_declarations) != len(set(class_declarations)):
            duplicates = [
                c for c in class_declarations if class_declarations.count(c) > 1]
            issues.append(f"❌ Clases duplicadas: {', '.join(set(duplicates))}")

    # 3. Verificar i18n
    i18n_found = 'const i18n = {' in content or 'const i18n=' in content
    if i18n_found:
        print("✅ Objeto i18n encontrado")
    else:
        warnings.append("⚠️  Objeto i18n no encontrado")

    # 4. Verificar I18nManager
    if 'class I18nManager' in content:
        print("✅ Clase I18nManager encontrada")
    else:
        issues.append("❌ Clase I18nManager no encontrada")

    # 5. Verificar CinemaSearch
    if 'class CinemaSearch' in content or 'window.CinemaSearch = class' in content:
        print("✅ Clase CinemaSearch encontrada")
    else:
        issues.append("❌ Clase CinemaSearch no encontrada")

    # 6. Verificar event listeners para idioma
    if "langSelector.addEventListener('change'" in content or 'langSelector.addEventListener("change"' in content:
        print("✅ Event listener para cambio de idioma encontrado")
    else:
        issues.append("❌ Event listener para cambio de idioma no encontrado")

    # 7. Verificar elementos con data-i18n
    data_i18n_elements = re.findall(r'data-i18n="(\w+)"', content)
    if data_i18n_elements:
        print(f"✅ Elementos con data-i18n: {len(data_i18n_elements)}")
        print(f"   Llaves: {', '.join(set(data_i18n_elements[:10]))}...")
    else:
        warnings.append("⚠️  No se encontraron elementos con data-i18n")

    # 8. Verificar selector de idioma
    if 'id="language"' in content:
        print("✅ Selector de idioma encontrado")
    else:
        issues.append("❌ Selector de idioma (id='language') no encontrado")

    # 9. Verificar localStorage
    if 'localStorage' in content:
        print("✅ Uso de localStorage detectado")
        if 'try' in content and 'catch' in content:
            print("✅ localStorage con manejo de errores")
        else:
            warnings.append(
                "⚠️  localStorage sin try-catch (puede causar errores)")

    # 10. Verificar método handleLanguageChange
    if 'handleLanguageChange' in content:
        print("✅ Método handleLanguageChange encontrado")
    else:
        issues.append("❌ Método handleLanguageChange no encontrado")

    # 11. Verificar método showLanguageDialog
    if 'showLanguageDialog' in content:
        print("✅ Método showLanguageDialog encontrado")
    else:
        issues.append("❌ Método showLanguageDialog no encontrado")

    # 12. Verificar traducciones
    lang_codes = ['es', 'en', 'fr', 'de']
    for lang in lang_codes:
        if f"{lang}:" in content or f'"{lang}"' in content:
            print(f"✅ Traducciones para '{lang}' encontradas")
        else:
            warnings.append(
                f"⚠️  Traducciones para '{lang}' posiblemente faltantes")

    # Resumen
    print(f"\n{'='*80}")
    print("📊 RESUMEN")
    print('='*80)

    if not issues and not warnings:
        print("✅ ¡TODO PERFECTO! No se encontraron problemas.")
    else:
        if issues:
            print(f"\n❌ PROBLEMAS CRÍTICOS ({len(issues)}):")
            for issue in issues:
                print(f"   {issue}")

        if warnings:
            print(f"\n⚠️  ADVERTENCIAS ({len(warnings)}):")
            for warning in warnings:
                print(f"   {warning}")

    return len(issues), len(warnings)


def check_javascript_syntax(filepath):
    """Verifica sintaxis básica de JavaScript"""
    print(f"\n{'='*80}")
    print("🔍 VERIFICACIÓN DE SINTAXIS JAVASCRIPT")
    print('='*80)

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Extraer bloques de script
    script_blocks = re.findall(r'<script>(.*?)</script>', content, re.DOTALL)

    if not script_blocks:
        print("❌ No se encontraron bloques <script>")
        return

    print(f"✅ Encontrados {len(script_blocks)} bloques de script")

    for i, script in enumerate(script_blocks, 1):
        print(f"\n--- Bloque {i} ---")

        # Verificar llaves balanceadas
        open_braces = script.count('{')
        close_braces = script.count('}')

        if open_braces == close_braces:
            print(f"✅ Llaves balanceadas: {open_braces} pares")
        else:
            print(
                f"❌ Llaves desbalanceadas: {open_braces} '{{' vs {close_braces} '}}'")

        # Verificar paréntesis
        open_parens = script.count('(')
        close_parens = script.count(')')

        if open_parens == close_parens:
            print(f"✅ Paréntesis balanceados: {open_parens} pares")
        else:
            print(
                f"❌ Paréntesis desbalanceados: {open_parens} '(' vs {close_parens} ')'")

        # Verificar corchetes
        open_brackets = script.count('[')
        close_brackets = script.count(']')

        if open_brackets == close_brackets:
            print(f"✅ Corchetes balanceados: {open_brackets} pares")
        else:
            print(
                f"❌ Corchetes desbalanceados: {open_brackets} '[' vs {close_brackets} ']'")


def find_templates_dir():
    """Encuentra el directorio de templates"""
    possible_paths = [
        'templates/index.html',
        '../templates/index.html',
        './templates/index.html',
        'index.html'
    ]

    for path in possible_paths:
        if os.path.exists(path):
            return path

    return None


def main():
    print("🔍 SISTEMA DE DEBUG PARA INTERNACIONALIZACIÓN")
    print("=" * 80)

    # Buscar archivo
    template_path = find_templates_dir()

    if not template_path:
        print("❌ No se pudo encontrar el archivo search.html")
        print("\nBuscado en:")
        print("  - templates/search.html")
        print("  - ../templates/search.html")
        print("  - ./templates/search.html")
        print("  - search.html")
        print("\n💡 Ejecuta este script desde la raíz del proyecto Flask")
        return

    print(f"✅ Archivo encontrado: {template_path}\n")

    # Análisis
    critical_issues, warnings = check_template_file(template_path)
    check_javascript_syntax(template_path)

    # Recomendaciones
    print(f"\n{'='*80}")
    print("💡 RECOMENDACIONES")
    print('='*80)

    if critical_issues > 0:
        print("\n🔴 Hay problemas críticos que deben resolverse:")
        print("   1. Verifica que todas las clases estén definidas correctamente")
        print("   2. Asegúrate de que no haya declaraciones duplicadas")
        print("   3. Revisa que todos los event listeners estén configurados")

    if warnings > 0:
        print("\n🟡 Hay advertencias que deberías revisar:")
        print("   1. Añade manejo de errores (try-catch) para localStorage")
        print("   2. Verifica que todas las traducciones estén completas")

    if critical_issues == 0 and warnings == 0:
        print("\n✅ El código parece estar bien estructurado")
        print("\n🔍 Si aún no funciona, verifica:")
        print("   1. Que el servidor Flask esté en modo debug (debug=True)")
        print("   2. Que hayas limpiado la caché del navegador (Ctrl+Shift+R)")
        print("   3. Que no haya errores en la consola del navegador (F12)")
        print("   4. Que el archivo search.html sea el que Flask está sirviendo")

    print(f"\n{'='*80}")
    print("FIN DEL ANÁLISIS")
    print('='*80)


if __name__ == '__main__':
    main()
