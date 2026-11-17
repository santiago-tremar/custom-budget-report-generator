import pandas as pd
from openpyxl import load_workbook

from exceler import excel_styler


def test_excel_styler_writes_and_formats_both_sheets(tmp_path):
    results = pd.DataFrame({
        'Cuenta': ['001-001', ''],
        'CONCEPTO DEL GASTO': ['OPERACION', 'TOTAL'],
        'PRESUPUESTO ANUAL': [100, 100],
        'EJER ACUM AL PERIODO': [25, 25],
    })
    summary = pd.DataFrame({
        'CONCEPTO DEL GASTO': ['OPERACION', 'SUBTOTAL OPERATIVO'],
        'PRESUPUESTO ANUAL': [100, 100],
        'EJER ACUM AL PERIODO': [25, 25],
        '% VARIACION': [0.25, None],
    })
    save_path = tmp_path / 'reporte.xlsx'

    excel_styler(results, save_path, summary)

    workbook = load_workbook(save_path)
    assert workbook.sheetnames == ['Sheet1', 'Sheet2']
    assert workbook['Sheet1'].freeze_panes == 'A2'
    assert workbook['Sheet2'].freeze_panes == 'A2'
    assert workbook['Sheet1']['C2'].number_format == '$#,##0.00'
    assert workbook['Sheet2']['D2'].number_format == '0.0%'
    assert workbook['Sheet2']['A3'].fill.fgColor.rgb.endswith('FFFF00')
