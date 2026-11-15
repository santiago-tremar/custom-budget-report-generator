import pandas as pd
from pathlib import Path
import os
import aesthetic
import time
import numpy as np

def rawdata_get_xlsx(folder_path):
    """Load and prepare rawdata."""
    # Get all CSV files using absolute paths
    work_files = list(folder_path.glob('*.xlsx'))
    if not work_files:
        return []  # Return empty list if no files found

    dataframes = [] # Initialize the dataframe LIST

    # Load the data
    for file in work_files:
        current_file = pd.read_excel(file,skiprows=6) # Skip empty rows at the beginning.
        basename = Path(file).stem.split()
        month = basename[-2]
        year = basename[-1]
        origen_name = str(month) + ' ' + str(year)
        current_file['Origen'] = origen_name
        dataframes.append(current_file)

    # Concatenate properly whether there is 1 or multiple files
    rawdata = pd.concat(dataframes, ignore_index=True)

    rawdata.columns = ['Cuenta',
                       'Nombre',
                       'Saldo Inicial: Deudor',
                       'Saldo Inicial: Acreedor',
                       'Cargos',
                       'Abonos',
                       'Saldos Actuales: Deudor',
                       'Saldos Actuales: Acreedor',
                       'Origen',
                       ]

    return rawdata

def template_generator(type):
    """
    Generate template to be used with the script.
    """
    application_path = Path(__file__).parent
    static_files_path = application_path / 'static_files'
    template_path = static_files_path / 'account_names.csv'
    base_template = pd.read_csv(template_path, sep='\t')

    while True:
        print('Por favor selecciona una opción:')
        type = input('¿Prorrateo \033[4mA\033[0mutomático o \033[4mM\033[0manual?: ').lower()

        if type == 'a' or type == 'm':
            break
        else:
            pass

    if type == 'a': # 'a' de Automático
        base_template['Presupuesto anual'] = ''
    elif type == 'm': # 'm; de Manual
        base_template['enero'] = ''
        base_template['febrero'] = ''
        base_template['marzo'] = ''
        base_template['abril'] = ''
        base_template['mayo'] = ''
        base_template['junio'] = ''
        base_template['julio'] = ''
        base_template['agosto'] = ''
        base_template['septiembre'] = ''
        base_template['octubre'] = ''
        base_template['noviembre'] = ''
        base_template['diciembre'] = ''
        base_template['Total'] = ''

    return base_template

def month_year(folder_path):
    # Read the names of the files of raw data.
    work_files = list(folder_path.glob('*.xlsx'))
    if not work_files:
        work_files = []  # Return empty list if no files found

    # Get the months and years available in the rawdata.
    months = []
    years = []
    for file in work_files:
        filename = os.path.basename(file)
        filename = filename.split()
        filename_month = filename[3]
        filename_year = filename[4]
        filename_year = filename_year.split(sep='.')
        filename_year = filename_year[0]
        months.append(filename_month)
        years.append(filename_year)

        return months, years

def prepare_rawdata(sequence, rawdata_folder_path):
    # Read Raw Data files and create DataFrame.
    rawdata = rawdata_get_xlsx(rawdata_folder_path)

    # Get list of file months and years
    months, years = month_year(rawdata_folder_path)
    # Filter rawdata by most recent month available.
    months = pd.DataFrame(months)
    sequence = sequence[sequence['mes'].isin(months[0])]
    latest_month = sequence[-1:]

    # Construct helper keyword for Origen.
    helper_year = years[0]
    helper_current_month = latest_month['mes'].to_string(index=False)
    helper_month_year = helper_current_month + ' ' + helper_year

    return rawdata, helper_month_year, helper_current_month

def accumulated_expenditures(rawdata_budgeted):
    # SUMIF to get accumulated expenditures.
    rawdata_to_sum = rawdata_budgeted[['Cuenta','Cargos']]
    accum = rawdata_to_sum.groupby(['Cuenta']).sum()
    accum = accum.reset_index()
    accum.columns = ['Cuenta', 'EJER ACUM AL PERIODO']

    return accum

def build_result_dataframe(budget_df, last_rawdata, accum, helper_current_month):
    # Automatically assign Result method by template type.
    if len(budget_df.columns) == 3:
        type = 'a'
    elif len(budget_df.columns) == 15:
      type ='m'
    else:
      type = 'e' # Error in Budget Template fill.

    #### Build Result DataFrame
    if type == 'a':
        results = budget_df        
        results.columns = ['Cuenta', 'CONCEPTO DEL GASTO','PRESUPUESTO ANUAL']
        results['PRESUPUESTO MENSUAL'] = results['PRESUPUESTO ANUAL']/12
        results = pd.merge(results, last_rawdata[['Cuenta','Cargos']], on = 'Cuenta', how = 'left')
        results['VARIACION'] = results['PRESUPUESTO MENSUAL'] - results['Cargos']
        results = pd.merge(results, accum[['Cuenta','EJER ACUM AL PERIODO']], on = 'Cuenta', how='left')
        results['POR EJERCER'] = results['PRESUPUESTO ANUAL'] - results['EJER ACUM AL PERIODO']
        results['% EJERCIDO'] = results['EJER ACUM AL PERIODO'] / results['PRESUPUESTO ANUAL']
        results['COMENTARIOS'] = ''
    elif type == 'm':
        results = pd.DataFrame(budget_df['Número de cuenta'])
        results.columns = ['Cuenta']
        results['CONCEPTO DEL GASTO'] = budget_df['Nombre de la cuenta']
        results['PRESUPUESTO ANUAL'] = budget_df['Total']
        results['PRESUPUESTO MENSUAL'] = budget_df[f'{helper_current_month}']
        results = pd.merge(results, last_rawdata[['Cuenta','Cargos']], on = 'Cuenta', how = 'left')
        results['VARIACION'] = results['PRESUPUESTO MENSUAL'] - results['Cargos']
        results = pd.merge(results, accum[['Cuenta','EJER ACUM AL PERIODO']], on = 'Cuenta', how='left')
        results['POR EJERCER'] = results['PRESUPUESTO ANUAL'] - results['EJER ACUM AL PERIODO']
        results['% EJERCIDO'] = results['EJER ACUM AL PERIODO'] / results['PRESUPUESTO ANUAL']
        results['COMENTARIOS'] = ''


    # Remove inf or empty that are not 000-000 accounts.
    # Create a boolean mask for NOT end in 000-000
    cond1 = ~results['Cuenta'].astype(str).str.endswith('000-000')

    # Create boolean mask for inf, null, or 0
    cond2 = (results['% EJERCIDO'].isin([np.inf, -np.inf])) | (results['% EJERCIDO'].isna())

    #Combine the conditions
    rows_to_drop = cond1 & cond2

    # Drop empty rows.
    results = results[~rows_to_drop]

    # Clear rows with Account category name.
    other_columns = results.columns.difference(['Cuenta','CONCEPTO DEL GASTO'])
    results.loc[~cond1, other_columns] = np.nan

    results = results.rename(columns={'Cargos': 'EJERCIDO EN EL MES'})
    return results

def final_touches(results):
    # 1. Identify the category header rows
    is_header = results['Cuenta'].astype(str).str.endswith('000-000')

    # 2. Create a group key that increments at each header
    # This assigns the same group number to the header and all accounts following it
    results['group_key'] = is_header.cumsum()

    def add_totals(group):
            # Separate the header from the data rows
            header = group.iloc[[0]]
            data = group.iloc[1:]
    
            if len(data) == 0:
                return header  # If there are no accounts, just return the header
        
            # Calculate the totals for numeric columns
            totals = data.select_dtypes(include=[np.number]).sum()
    
            # Create the Totals row
            totals_row = pd.DataFrame([totals])
    
            # Combine header, data, and the new totals row
            return pd.concat([header, data, totals_row], ignore_index=True)

    # 3. Apply the function to each group and drop the temporary key
    final_result = results.groupby('group_key', group_keys=False).apply(add_totals)
   #final_result = final_result.drop(columns=['group_key'])
    final_result['% EJERCIDO'] = final_result['EJER ACUM AL PERIODO'] / final_result['PRESUPUESTO ANUAL']
    empty_accounts = (
        final_result['Cuenta'].isna()
        | final_result['Cuenta'].astype(str).str.strip().eq('')
    )
    final_result.loc[empty_accounts, 'CONCEPTO DEL GASTO'] = 'TOTAL'
    return final_result

def data_input_checks(rawdata_folder_path, budget_folder_path):
    # Check Raw Data folder.
    files = list(rawdata_folder_path.glob('*.xlsx'))
    if not files:
        aesthetic.error()
        print('\nNo hay archivos .xlsx en la carpeta de Balanzas de Comprobación.')
        print('Por favor agrega los archivos faltantes y vuelve a ejecutar el programa.')
        rawdata = 'n'
    else:
        print('\nSe generará el reporte con las siguientes Balanzas de Comprobación:\n')
        for file in files:
            file_basename = os.path.basename(file)
            print(file_basename)
            time.sleep(0.5)
        rawdata = 'y'      

    # Check and create Budget folder.
    budget = list(budget_folder_path.glob('*.xlsx'))
    if len(budget) == 1 and rawdata == 'y':
        print('\nY se generará con el siguiente presupuesto:')
        time.sleep(0.5)
        budget_filename = os.path.basename(budget[0]) ## Save the budget filename for later use.
        print(budget_filename)
        time.sleep(0.5)
        budget_data = 'y'
    elif len(budget) > 1:
        aesthetic.error()
        print('\nHay más de un archivo en la carpeta de Presupuesto anual.')
        print('Favor de borrar los demás y dejar solamente el corriente.')
        budget_data = 'n'
    elif len(budget) == 0:
        aesthetic.error()
        print('\nNo hay archivos .xlsx en la carpeta de Presupuesto anual.')
        print('Por favor agrega el archivo faltante y vuelve a ejecutar el programa.')
        budget_data = 'n'
    else:
        budget_data = 'n'

    if rawdata == 'y' and budget_data == 'y':
        can_continue = 'y'
    else:
        can_continue = 'n'
        budget_filename = ''

    return can_continue, budget_filename

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
