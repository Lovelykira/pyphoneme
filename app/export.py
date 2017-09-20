from datetime import datetime
import json
import xlsxwriter


class JSONExport:

    def __init__(self, data, file_name=None):
        self.data = data
        self.file_name = file_name or 'reports/synthesis_by_{}_{}_by_{}_{}.json'.format(data['mode'], data['synthesis_mode'], data['criteria'], datetime.now())

    def save(self):
        file = open(self.file_name, "w")
        file.write(json.dumps(self.data, indent=2, sort_keys=True))
        file.close()


class SpreadsheetExport:
    def __init__(self, data, file_name=None):
        self.data = data
        self.file_name = file_name or 'reports/synthesis_by_{}_{}_by_{}_{}.xlsx'.format(data['mode'], data['synthesis_mode'], data['criteria'], datetime.now())

    def save(self):

        workbook = xlsxwriter.Workbook(self.file_name)
        worksheet = workbook.add_worksheet()

        worksheet.write(0, 0, 'Mode:')
        worksheet.write(0, 1, self.data['mode'])

        worksheet.write(0, 3, 'Synthesis:')
        worksheet.write(0, 4, self.data['synthesis_mode'])

        worksheet.write(1, 0, 'Criteria:')
        worksheet.write(1, 1, self.data['criteria'])

        worksheet.write(1, 3, 'P Value:')
        worksheet.write(1, 4, self.data['p_value_level'])

        worksheet.write(1, 5, 'Result P Value:')
        worksheet.write(1, 6, self.data['test_p_value_level'])

        worksheet.write(2, 0, 'Initial words:')
        worksheet.write(2, 1, self.data['initial_words'])

        worksheet.write(3, 0, 'Result words:')
        worksheet.write(3, 1, self.data['result_words'])

        worksheet.write(4, 0, 'Running time:')
        worksheet.write(4, 1, self.data['run_time'])

        worksheet.write(4, 3, 'Iterations:')
        worksheet.write(4, 4, self.data['iterations_number'])

        worksheet.write(5, 0, 'Date:')
        worksheet.write(5, 1, self.data['date'])

        worksheet.write(7, 0, 'Initial distribution:')
        chart1 = workbook.add_chart({'type': 'column'})
        chart1.set_size({'width': 1200, 'height': 800})
        row = 8
        col = 0
        for key in sorted(self.data['initial_distribution'].keys()):
            worksheet.write(row, col, key)
            worksheet.write(row, col + 1, self.data['initial_distribution'][key] * 100)
            row += 1

        chart1.add_series({
            'name': ['Sheet1', 7, 0],
            'categories': ['Sheet1', 8, col, row, col],
            'values': ['Sheet1', 8, col + 1, row, col + 1],
        })

        worksheet.write(7, 4, 'Result distribution:')
        row = 8
        col = 4
        for key in sorted(self.data['initial_distribution'].keys()):
            worksheet.write(row, col, key)
            worksheet.write(row, col + 1, self.data['result_distribution'].get(key, 0) * 100)
            row += 1

        chart1.add_series({
            'name': ['Sheet1', 7, 4],
            'categories': ['Sheet1', 8, col, row, col],
            'values': ['Sheet1', 8, col + 1, row, col + 1],
        })

        # Add a chart title and some axis labels.
        chart1.set_title({'name': 'Phonems distribution'})
        chart1.set_x_axis({'name': 'Phoneme'})
        chart1.set_y_axis({'name': 'Percentage'})

        # Set an Excel chart style. Colors with white outline and shadow.
        chart1.set_style(10)

        # Insert the chart into the worksheet (with an offset).
        worksheet.insert_chart('I8', chart1, {'x_offset': 25, 'y_offset': 10})

        worksheet.write(row + 2, 0, 'Answer')
        worksheet.insert_textbox(row + 3, 0, self.data['answer'], {'x_scale': 3, 'y_scale': 3})

        workbook.close()
