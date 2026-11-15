import aesthetic
import utils
from pathlib import Path
import pandas as pd
import time

## Initialize Path names to be used.
application_path = Path(__file__).parent
static_files_path = application_path / 'static_files'
template_file = static_files_path / 'plantilla_presupuestos.xlsx'
rawdata_folder_path = application_path / 'Balanzas de Comprobacion'
budget_folder_path = application_path / 'Presupuesto anual'
sequence_file = static_files_path/ 'secuencia_meses.csv'

# Load helper files.
sequence = pd.read_csv(sequence_file)

# Check if template exists in directory.
if template_file.exists():
    plantilla = 'y'
else:
    plantilla = 'n'

# Check for Raw Data folder.
if rawdata_folder_path.is_dir():
    pass
else:
    rawdata_folder_path.mkdir(parents=True, exist_ok=True)
    print(f'Se generó la carpeta Balanzas de comprobación en {rawdata_folder_path}')

# Check for Budget folder.
if budget_folder_path.is_dir():
    pass
else:
    budget_folder_path.mkdir(parents=True, exist_ok=True)
    print(f'Se generó la carpeta Presupuesto en {rawdata_folder_path}')

# region User interactions. Inputs.

while True:
    print('Por favor, escoge una opción.')
    time.sleep(0.5)
    print('\n   1) Leer Instrucciones de uso.')
    time.sleep(0.5)
    print('\n   2) Descargar Plantilla de Presupuesto.')
    time.sleep(0.5)
    print('\n   3) Generar Reporte de Presupuesto Mensual.')
    time.sleep(0.5)
    print('\n   4) Cerrar programa.')
    time.sleep(0.5)
    choice = int(input('\nIngresa el número correspondiente y presiona Enter: '))
    time.sleep(0.5)
    if choice == 1:
        aesthetic.instructions()

    elif choice == 2:
        # Generate template and write to directory.
        if plantilla == 'y':
            print('\nParece que ya tienes descargada la plantilla de Presupuesto Anual.')
            time.sleep(0.5)
            print('¿Deseas volverla a descargar?')
            time.sleep(0.5)
            print(f'Reemplazará la que se encuentra en {application_path}')
            time.sleep(0.5)
            download = input('Descargar (y/n): ').lower()
        elif plantilla == 'n':
            print('\nParece que no tienes descargada la plantilla de Presupuesto Anual.')
            time.sleep(0.5)
            print(f'Se descargará automáticamente en {application_path}')
            time.sleep(0.5)
            template = utils.template_generator(type)
            template.to_excel('plantilla_presupuestos.xlsx',index=False)
            print('¡Plantilla descargada!')
            time.sleep(0.5)
            download = 'n'

        if download == 'y':
            template = utils.template_generator(type)
            template.to_excel('plantilla_presupuestos.xlsx',index=False)
            print('¡Plantilla descargada!')
            time.sleep(0.5)
        elif download == 'n':
            pass

    elif choice == 3:
        ## Check for missing input files, if any.
        can_continue, budget_filename = utils.data_input_checks(rawdata_folder_path,budget_folder_path)

        if can_continue == 'y':
            # region Preparation of all data needed to construct results.
            rawdata, helper_month_year, helper_current_month = utils.prepare_rawdata(sequence,rawdata_folder_path)

            # Read template and create DataFrame.
            budget_file = budget_folder_path / budget_filename
            budget_df = pd.read_excel(budget_file)

            # Keep only rows whose accounts are budgeted.
            rawdata_budgeted = rawdata[rawdata['Cuenta'].isin(budget_df['Número de cuenta'])]

            # Reduce rawdata to only latest month.
            last_rawdata = rawdata_budgeted[rawdata_budgeted['Origen']==helper_month_year]

            # Get accumulated expenditures for use in the Result.
            accum = utils.accumulated_expenditures(rawdata_budgeted)
            # endregion

            # Automatically assign Result method by template type.
            results = utils.build_result_dataframe(budget_df, last_rawdata, accum, helper_current_month)
           
            results = utils.final_touches(results)
           
            print('\n¡Se generó el reporte!')
            print('Se ha guardado con el nombre "reporte_presupuesto_anual.xlsx" ')
            utils.excel_styler(results, 'reporte_presupuesto_anual.xlsx')
            break
        elif can_continue == 'n':
            break
        
    elif choice == 4:
        break

input('\nVuelve a presionar Enter para cerrar el programa.')