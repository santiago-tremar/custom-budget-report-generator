import pytest

import pandas as pd
from pathlib import Path

from rawdata import (
    rawdata_get_xlsx,
    month_year,
    prepare_rawdata,
    )

from reporter import(
    accumulated_expenditures,
    build_result_dataframe,
    final_touches
)

@pytest.fixture
def rawdata_folder_path():
    """ Define common file path.  """
    application_path = Path(__file__).parent
    test_file_path = application_path / 'test_files'
    rawdata_folder_path = test_file_path / 'Balanzas de Comprobacion'

    return rawdata_folder_path

@pytest.fixture
def budget_file():
    """ Define common file. """
    application_path = Path(__file__).parent
    test_file_path = application_path / 'test_files'
    budget_file_path = test_file_path / 'Presupuesto anual' / 'plantilla_presupuestos.xlsx'
    budget_file = pd.read_excel(budget_file_path)

    return budget_file

def test_rawdata_dataframe_construction(rawdata_folder_path):
    """ Rawdata Datafrime size is as expected from inputs. """
    test_rawdata = rawdata_get_xlsx(rawdata_folder_path)

    df_size = test_rawdata.size

    assert df_size == (34*2 * 9)

def test_month_year_inference(rawdata_folder_path):
    """ Function correctly records months from list. """
    months, years = month_year(rawdata_folder_path)

    assert '2026' in years
    assert 'abril' in months
    assert 'enero' in months

def test_rawdata_preparation_by_latest_month(rawdata_folder_path):
    """ Rawdata is filtered by latest month from list. """
    sequence_file = Path(__file__).parent / 'test_files' / 'secuencia_meses.csv'
    sequence = pd.read_csv(sequence_file)

    rawdata, helper_month_year, latest_month = prepare_rawdata(sequence, rawdata_folder_path)

    rawdata_size = rawdata.size

    assert latest_month == 'abril'
    assert helper_month_year == 'abril 2026'
    assert rawdata_size == (34*2 * 9)

def test_accumulated_expenditures_calculation(budget_file,rawdata_folder_path):
    """ Calculation of accumulated expenditures is as expected. """
    sequence_file = Path(__file__).parent / 'test_files' / 'secuencia_meses.csv'
    sequence = pd.read_csv(sequence_file)

    rawdata, a, b = prepare_rawdata(sequence, rawdata_folder_path)
    rawdata_budgeted = rawdata[rawdata['Cuenta'].isin(budget_file['Número de cuenta'])]

    accum = accumulated_expenditures(rawdata_budgeted)
    test_accum = accum.loc[1,'EJER ACUM AL PERIODO']
    print(accum)

    assert test_accum == 50000 + 150000

def test_result_calculation_before_grouping(budget_file,rawdata_folder_path):
    """ Check correct calculations of result dataframe. """
    sequence_file = Path(__file__).parent / 'test_files' / 'secuencia_meses.csv'
    sequence = pd.read_csv(sequence_file)
    
    rawdata, month_year, latest_month = prepare_rawdata(sequence, rawdata_folder_path)
    rawdata_budgeted = rawdata[rawdata['Cuenta'].isin(budget_file['Número de cuenta'])]
    
    last_rawdata = rawdata_budgeted[rawdata_budgeted['Origen']==month_year]
    
    accum = accumulated_expenditures(rawdata_budgeted)

    results = build_result_dataframe(budget_file, last_rawdata, accum, latest_month)

    assert results.loc[1, 'PRESUPUESTO ANUAL'] == 250_000
    assert results.loc[1, 'EJERCIDO EN EL MES'] == 50_000

def test_result_calculation_after_grouping_totals(budget_file,rawdata_folder_path):
    """ Check correct calculations of result dataframe by grouping totals. """
    sequence_file = Path(__file__).parent / 'test_files' / 'secuencia_meses.csv'
    sequence = pd.read_csv(sequence_file)
    rawdata, month_year, latest_month = prepare_rawdata(sequence, rawdata_folder_path)
    rawdata_budgeted = rawdata[rawdata['Cuenta'].isin(budget_file['Número de cuenta'])]
    last_rawdata = rawdata_budgeted[rawdata_budgeted['Origen']==month_year]
    accum = accumulated_expenditures(rawdata_budgeted)
    results = build_result_dataframe(budget_file, last_rawdata, accum, latest_month)

    results_grouped = final_touches(results)

    expected_budget = 250_000 + 300_000 + 10 + 1_000_000 + 200
    expected_spent = 50_000 + 150_000 + 5 + 500_000 + 100

    total_rows = results_grouped[
        (results_grouped['CONCEPTO DEL GASTO'] == 'TOTAL')
        & (results_grouped['PRESUPUESTO ANUAL'] == expected_budget)
    ]

    assert len(total_rows) == 1
    assert total_rows['EJERCIDO EN EL MES'].iloc[0] == expected_spent
    assert results_grouped['EJER ACUM AL PERIODO'].iloc[-2] != 0