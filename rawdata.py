import pandas as pd
from pathlib import Path
import os
import aesthetic
import time

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

    # Rename columns appropriately
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
