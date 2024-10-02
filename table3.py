import dash
from dash.dependencies import Input, Output, State
from dash import dash_table, html
import pandas as pd
import numpy as np

def defineDF():
    data = [['car', 'ford', 'focus', 'blue', 10],
            ['car', 'ford', 'focus', 'red', 12],
            ['car', 'bmw', 'm3', 'blue', 2],
            ['car', 'bmw', 'm3', 'black', 7],
            ['car', 'bmw', 'i3', 'red', 2],
            ['car', 'bmw', 'i3', 'blue', 2],
            ['motorcycle', 'yamaha', 'td2', 'black', 3],
            ['motorcycle', 'yamaha', 'td2', 'green', 4],
            ['motorcycle', 'honda', 'crf', 'white', 9]
            ]

    df = pd.DataFrame(data=data, columns=['vehicle', 'manufacturer', 'model', 'color', 'sold'])

    return df

startDF = defineDF()

app = dash.Dash(__name__)

app.layout = html.Div([
    dash_table.DataTable(
    id='testtable',
    columns=[{"name": i, "id": i} for i in startDF.columns],
    data=startDF.to_dict('records'),
    editable=True,
    selected_rows=[],
    ),
    html.Div(id='datatable-row-ids-container')
])


@app.callback(Output('testtable', 'data'),
              [Input('testtable', 'active_cell')],
              [State('testtable', 'data'),
               State('testtable', 'columns')],
              )
def updateGrouping(active_cell, power_position, power_position_cols):
    if active_cell is None:
        returndf = defineDF()
    else:
        currentColNames = [iii['name'] for iii in power_position_cols]
        tableData = pd.DataFrame(data=power_position, columns=currentColNames)
        columnNames = tableData.columns.values.tolist()

        lastColNumberList = [active_cell['column'] + 1]
        groupingColList = [columnNames[:lastColNumberList[0]]]
        presentingColList = [columnNames[:lastColNumberList[0]] + [columnNames[-1]]]

        rowNumber = active_cell['row']
        rowValueList = [pd.DataFrame(data=[tableData.iloc[rowNumber, :lastColNumberList[0]].values],
                                     columns=groupingColList[0])]

        cellValue = tableData.iloc[rowNumber, lastColNumberList[0] - 1]

        if cellValue is None:
            nullElements = np.where(pd.isnull(tableData))
            nullRowColumn = np.column_stack((nullElements[0].tolist(), nullElements[1].tolist()))
            nullRowColumnDF = pd.DataFrame(nullRowColumn, columns=['row', 'column'])
            nullRowColumnDF = nullRowColumnDF.drop_duplicates(subset=['row'], keep='first')
            for index, rowColPair in nullRowColumnDF.iterrows():
                currentRow = rowColPair['row']
                currentColumn = rowColPair['column']
                if currentRow == rowNumber:
                    continue
                lastColNumberList += [currentColumn]
                currentGrouping = columnNames[:currentColumn]
                groupingColList += [currentGrouping]
                presentingColList += [currentGrouping  + [columnNames[-1]]]
                rowValueList += [pd.DataFrame(data=[tableData.iloc[currentRow, :currentColumn].values],
                                              columns=currentGrouping)]

            tableData = defineDF()

        returndf = tableData.fillna('-')
        for iii in range(len(rowValueList)):
            rowValueDF = rowValueList[iii]
            rowValueDF = rowValueDF.fillna('-')
            groupingCols = groupingColList[iii]
            presentingCols = presentingColList[iii]
            lastColNumber = lastColNumberList[iii]

            numberEmptyCells = len(np.where(rowValueDF.iloc[0,:] == '-')[0])
            lastColNumber -= numberEmptyCells
            rowValueDF = rowValueDF[:(len(rowValueDF.columns)-numberEmptyCells)]
            relevantRows = pd.merge(returndf.iloc[:, :lastColNumber].reset_index(), rowValueDF, how='inner').set_index('index')
            rowsToGroup = returndf.loc[relevantRows.index, :]
            rowsNotToGroup = returndf.drop(relevantRows.index)

            groupedDF = rowsToGroup.groupby(groupingCols, sort=False).sum().reset_index()[presentingCols]
            lenGrouopedDF = len(groupedDF.index)
            groupedDF = groupedDF.set_index(rowsToGroup.index[:lenGrouopedDF])
            returndf = pd.concat([groupedDF, rowsNotToGroup])[columnNames]
            returndf = returndf.sort_index(inplace=False).reset_index(drop=True)
        returndf = returndf.replace({'-': None})

    return returndf.to_dict('records')


if __name__ == '__main__':
    app.run_server(debug=False)
