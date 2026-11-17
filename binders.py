
from pathlib import Path
import pandas as pd
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
    final_touches,
    summary_report)

from exceler import excel_styler


def path_initialize():
    """ Initialize paths. """
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
        template_file = application_path / 'plantilla_presupuestos.xlsx'
        rawdata_folder_path = static_files_path / 'Balanzas de Comprobacion'
        budget_folder_path = static_files_path / 'Presupuesto anual'
    elif not DEBUG:
        static_files_path = application_path / 'static_files'
        template_file = application_path / 'plantilla_presupuestos.xlsx'
        rawdata_folder_path = application_path / 'Balanzas de Comprobacion'
        budget_folder_path = application_path / 'Presupuesto anual'

    # This file is relative to the temporary files because it will be packaged into PyInstaller
    sequence_file = Path(__file__).resolve().parent / 'static_files' / 'secuencia_meses.csv' 

    # Load helper files.
    sequence = pd.read_csv(sequence_file)

    return template_file, rawdata_folder_path, budget_folder_path, sequence


def directory_reader(template_file, rawdata_folder_path, budget_folder_path):
    """ Check if needed directories exist. Create if not. """
    # Check if template exists in directory.
    if template_file.exists():
        plantilla = 'y'
    else:
        plantilla = 'n'

    display_str = ''

    # Check for Raw Data folder.
    if rawdata_folder_path.is_dir():
        display_str += f'++ Ya existe la carpeta Balanzas de comprobación en {rawdata_folder_path}\n'
    else:
        rawdata_folder_path.mkdir(parents=True, exist_ok=True)
        print(f'Se generó la carpeta Balanzas de comprobación en {rawdata_folder_path}')
        display_str += f'++ Se generó la carpeta Balanzas de comprobación en {rawdata_folder_path}\n'


    # Check for Budget folder.
    if budget_folder_path.is_dir():
        display_str += f'++ Ya existe la carpeta Presupuesto en {rawdata_folder_path}\n'
    else:
        budget_folder_path.mkdir(parents=True, exist_ok=True)
        print(f'Se generó la carpeta Presupuesto en {rawdata_folder_path}/n')
        display_str += f'++ Se generó la carpeta Presupuesto en {rawdata_folder_path}\n'

    return plantilla, display_str


def generate_report(rawdata_folder_path, budget_folder_path, sequence):
    """ Generate final reports. """
    ## Check for missing input files, if any.
    can_continue, budget_filename, display_str = data_input_checks(
        rawdata_folder_path,
        budget_folder_path,
    )

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

        summary = summary_report(results)
        
        message = 'Se ha guardado con el nombre "reporte_presupuesto_anual.xlsx" '
        print(message)
        display_str += message + '\n'
        excel_styler(results, 'reporte_presupuesto_anual.xlsx', summary)
    elif can_continue == 'n':
        pass

    return display_str
