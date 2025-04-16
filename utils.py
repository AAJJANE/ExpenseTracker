from pychartjs.charts import Chart
from pychartjs.datasets import Dataset
from pychartjs.enums import ChartType
from requests import get


def format_amount(data):
    res = []
    for i in data:
        res.append((float(i[0]), i[1]))
    return res


def create_chart(label, data, background_col, labels, chart_type, border_width=2, border_color='rgb(0, 0, 0)'):
    dataset = Dataset(
        label=label,
        data=data,
        backgroundColor=background_col,
        borderWidth=border_width,
        borderColor=border_color
    )

    chart = Chart(
        labels=labels,
        chart_type=eval(f'ChartType.{chart_type}'),
        datasets=[dataset],
    )

    return chart

def generate_color(n):
    colors = []
    for i in range(n):
        i = get('https://x-colors.yurace.pro/api/random').json()
        colors.append(i['rgb'])
    return colors