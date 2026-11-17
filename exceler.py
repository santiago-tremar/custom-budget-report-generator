import pandas as pd


def excel_styler(dataframe, save_path, summary_dataframe=None):
    from openpyxl import load_workbook
    from openpyxl.styles import Alignment, Font, PatternFill

    if 'Cuenta' not in dataframe.columns:
        raise ValueError("The dataframe must contain a 'Cuenta' column.")

    money_columns = [
        'PRESUPUESTO ANUAL',
        'PRESUPUESTO MENSUAL',
        'EJERCIDO EN EL MES',
        'VARIACION',
        'EJER ACUM AL PERIODO',
        'POR EJERCER',
    ]
    with pd.ExcelWriter(save_path, engine='openpyxl') as writer:
        dataframe.to_excel(writer, sheet_name='Sheet1', index=False)
        if summary_dataframe is not None:
            summary_dataframe.to_excel(writer, sheet_name='Sheet2', index=False)

    workbook = load_workbook(save_path)

    header_font = Font(name='Calibri', size=11, bold=True, color='FFFFFF')
    header_fill = PatternFill(fill_type='solid', fgColor='1F4E78')
    regular_font = Font(name='Calibri', size=11)
    highlighted_font = Font(
        name='Calibri',
        size=13,
        bold=True,
        italic=True,
        color='000000',
    )
    highlighted_fill = PatternFill(fill_type='solid', fgColor='FFFF00')
    centered = Alignment(horizontal='center')

    for worksheet in workbook.worksheets:
        worksheet.freeze_panes = 'A2'
        column_positions = {
            cell.value: cell.column
            for cell in worksheet[1]
        }
        for cell in worksheet[1]:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = centered

        for column in money_columns:
            if column in column_positions:
                column_index = column_positions[column]
                for row in range(2, worksheet.max_row + 1):
                    worksheet.cell(row=row, column=column_index).number_format = '$#,##0.00'

        for column in ('% EJERCIDO', '% VARIACION'):
            if column in column_positions:
                column_index = column_positions[column]
                for row in range(2, worksheet.max_row + 1):
                    worksheet.cell(row=row, column=column_index).number_format = '0.0%'

        key_column = 'Cuenta' if 'Cuenta' in column_positions else 'CONCEPTO DEL GASTO'
        key_column_index = column_positions.get(key_column)
        for row in range(2, worksheet.max_row + 1):
            key_value = (
                worksheet.cell(row=row, column=key_column_index).value
                if key_column_index is not None
                else None
            )
            key = '' if key_value is None else str(key_value).strip()
            if key_column == 'Cuenta':
                highlight_row = not key or key.endswith('000-000')
            else:
                highlight_row = key == 'SUBTOTAL OPERATIVO'

            for column in range(1, worksheet.max_column + 1):
                cell = worksheet.cell(row=row, column=column)
                cell.font = highlighted_font if highlight_row else regular_font
                if highlight_row:
                    cell.fill = highlighted_fill

    workbook.save(save_path)
