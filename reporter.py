import pandas as pd
import numpy as np


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
    cond2 = results['EJER ACUM AL PERIODO'].isna() | results['EJER ACUM AL PERIODO'].isin([np.inf, -np.inf, 0])

    cond3 = results['PRESUPUESTO ANUAL'].isna() | results['PRESUPUESTO ANUAL'].isin([np.inf, -np.inf, 0])

    #Combine the conditions
    rows_to_drop = cond1 & cond2 & cond3

    # Drop empty rows.
    results = results[~rows_to_drop]

    # Clear rows with Account category name.
    other_columns = results.columns.difference(['Cuenta','CONCEPTO DEL GASTO'])
    results.loc[~cond1, other_columns] = np.nan

    results = results.rename(columns={'Cargos': 'EJERCIDO EN EL MES'})
    return results

def final_touches(results):
    """ Add TOTALS rows to base report, grouped by account Number. """
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

def summary_report(results):
    """ Create secondary report, grouped by Concept name. """
    working_result = results.drop(columns=['Cuenta','PRESUPUESTO MENSUAL','% EJERCIDO','POR EJERCER','VARIACION'])
    working_result = working_result.groupby(
        'CONCEPTO DEL GASTO',
        as_index=False,
    ).sum(numeric_only=True)

    working_result['% VARIACION'] = working_result['EJER ACUM AL PERIODO'] / working_result['PRESUPUESTO ANUAL']
    working_result['POR EJERCER'] = working_result['PRESUPUESTO ANUAL'] - working_result['EJER ACUM AL PERIODO']

    subtotal = {column: np.nan for column in working_result.columns}
    subtotal['CONCEPTO DEL GASTO'] = 'SUBTOTAL OPERATIVO'
    subtotal['PRESUPUESTO ANUAL'] = working_result['PRESUPUESTO ANUAL'].sum()
    subtotal['EJER ACUM AL PERIODO'] = working_result['EJER ACUM AL PERIODO'].sum()
    working_result = pd.concat(
        [working_result, pd.DataFrame([subtotal])],
        ignore_index=True,
    )

    return working_result