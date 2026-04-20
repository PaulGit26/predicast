#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Convertir CSV de criterios a Excel formateado con xlsxwriter
"""

import pandas as pd
import xlsxwriter

# Leer CSV
df = pd.read_csv('39_CRITERIOS_ACEPTACION_REALISTAS.csv')

# Crear archivo Excel
output_file = '39_CRITERIOS_ACEPTACION_REALISTAS.xlsx'
writer = pd.ExcelWriter(output_file, engine='xlsxwriter')
df.to_excel(writer, sheet_name='Criterios', index=False)

# Obtener workbook y worksheet
workbook = writer.book
worksheet = writer.sheets['Criterios']

# Definir formatos
header_format = workbook.add_format({
    'bg_color': '#1F4E78',
    'font_color': '#FFFFFF',
    'bold': True,
    'font_size': 11,
    'align': 'center',
    'valign': 'vcenter',
    'border': 1,
    'text_wrap': True
})

# Color por épica
epic_colors = {
    'Datos': '#D9E1F2',
    'ML': '#E2EFDA',
    'Recomendación': '#FFF2CC',
    'Dashboard': '#FCE4D6',
    'API': '#F4B084',
    'Económico': '#E2EFDA',
    'Documentación': '#D9D9E3'
}

# Aplicar formato header
for col_num, value in enumerate(df.columns.values):
    worksheet.write(0, col_num, value, header_format)

# Aplicar formatos a celdas de datos
for row_num, (idx, row) in enumerate(df.iterrows(), start=1):
    epic = row['Épica']
    color = epic_colors.get(epic, '#FFFFFF')
    
    cell_format = workbook.add_format({
        'bg_color': color,
        'border': 1,
        'align': 'left',
        'valign': 'top',
        'text_wrap': True,
        'font_size': 10
    })
    
    for col_num, value in enumerate(row):
        worksheet.write(row_num, col_num, value, cell_format)

# Ajustar ancho columnas
widths = {
    0: 8,   # HU
    1: 14,  # Épica
    2: 25,  # Título
    3: 30,  # Dado
    4: 30,  # Cuando
    5: 35   # Entonces
}

for col, width in widths.items():
    worksheet.set_column(col, col, width)

# Alto filas
worksheet.set_row(0, 30)
for row in range(1, len(df) + 1):
    worksheet.set_row(row, 50)

# Congelar header
worksheet.freeze_panes(1, 0)

# Guardar
writer.close()
print(f"✅ Excel creado: {output_file}")
print(f"📊 Filas: {len(df)}")
print(f"📋 Columnas: {len(df.columns)}")
print(f"🎨 Formato: Colores por épica, header congelado")
