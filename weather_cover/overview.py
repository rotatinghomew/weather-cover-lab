"""已有资料的描述性概览。"""
def summarize(data):
    rows = data["rows"]
    return {'farmer_years': len(rows), 'farmers': len({row['farmer'] for row in rows}), 'years': sorted({row['year'] for row in rows}), 'missing_weather_records': sum(row['rain_mm'] is None for row in rows)}
