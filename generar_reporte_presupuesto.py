import aesthetic
from pathlib import Path
import pandas as pd
import time
import sys

from environs import env

from rawdata import (
    prepare_rawdata,
    data_input_checks,
    template_generator,
)

from reporter import (
    accumulated_expenditures,
    build_result_dataframe,
    final_touches)

from exceler import excel_styler

## Read environment setting for switching folders dynamically.
env.read_env()
DEBUG = env.bool("DEBUG", default=False)

application_path = (
    Path(sys.executable).resolve().parent
    if getattr(sys, 'frozen', False)
    else Path(__file__).resolve().parent
)

## Initialize Path names to be used.
if DEBUG:
    static_files_path = application_path / 'test_files'
    template_file = static_files_path / 'plantilla_presupuestos.xlsx'
    rawdata_folder_path = static_files_path / 'Balanzas de Comprobacion'
    budget_folder_path = static_files_path / 'Presupuesto anual'
elif not DEBUG:
    static_files_path = application_path / 'static_files'
    template_file = static_files_path / 'plantilla_presupuestos.xlsx'
    rawdata_folder_path = application_path / 'Balanzas de Comprobacion'
    budget_folder_path = application_path / 'Presupuesto anual'

# This file is relative to the temporary files because it will be packaged into PyInstaller
sequence_file = Path(__file__).resolve().parent / 'static_files' / 'secuencia_meses.csv' 

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
            template = template_generator(type)
            template.to_excel('plantilla_presupuestos.xlsx',index=False)
            print('¡Plantilla descargada!')
            time.sleep(0.5)
            download = 'n'

        if download == 'y':
            template = template_generator(type)
            template.to_excel('plantilla_presupuestos.xlsx',index=False)
            print('¡Plantilla descargada!')
            time.sleep(0.5)
        elif download == 'n':
            pass

    elif choice == 3:
        ## Check for missing input files, if any.
        can_continue, budget_filename = data_input_checks(rawdata_folder_path,budget_folder_path)

        if can_continue == 'y':
            # region Preparation of all data needed to construct results.
            rawdata, helper_month_year, helper_current_month = prepare_rawdata(sequence,rawdata_folder_path)

            # Read template and create DataFrame.
            budget_file = budget_folder_path / budget_filename
            budget_df = pd.read_excel(budget_file)

            # Keep only rows whose accounts are budgeted.
            rawdata_budgeted = rawdata[rawdata['Cuenta'].isin(budget_df['Número de cuenta'])]

            # Reduce rawdata to only latest month.
            last_rawdata = rawdata_budgeted[rawdata_budgeted['Origen']==helper_month_year]

            # Get accumulated expenditures for use in the Result.
            accum = accumulated_expenditures(rawdata_budgeted)
            # endregion

            # Automatically assign Result method by template type.
            results = build_result_dataframe(budget_df, last_rawdata, accum, helper_current_month)
           
            results = final_touches(results)
           
            print('\n¡Se generó el reporte!')
            print('Se ha guardado con el nombre "reporte_presupuesto_anual.xlsx" ')
            excel_styler(results, 'reporte_presupuesto_anual.xlsx')
            break
        elif can_continue == 'n':
            break
        
    elif choice == 4:
        break

input('\nVuelve a presionar Enter para cerrar el programa.')