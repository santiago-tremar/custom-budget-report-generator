def excel_styler(dataframe, save_path):
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
    dataframe.to_excel(save_path, sheet_name='Reporte', index=False)
    workbook = load_workbook(save_path)
    worksheet = workbook['Reporte']
    worksheet.freeze_panes = 'A2'

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

    if '% EJERCIDO' in column_positions:
        column_index = column_positions['% EJERCIDO']
        for row in range(2, worksheet.max_row + 1):
            worksheet.cell(row=row, column=column_index).number_format = '0.0%'

    account_column = column_positions['Cuenta']
    for row in range(2, worksheet.max_row + 1):
        account_value = worksheet.cell(row=row, column=account_column).value
        account = '' if account_value is None else str(account_value).strip()
        highlight_row = not account or account.endswith('000-000')
        for column in range(1, worksheet.max_column + 1):
            cell = worksheet.cell(row=row, column=column)
            cell.font = highlighted_font if highlight_row else regular_font
            if highlight_row:
                cell.fill = highlighted_fill

    workbook.save(save_path)
