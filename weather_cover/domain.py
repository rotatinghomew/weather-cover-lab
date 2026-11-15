"""独立业务规则，仅依赖冻结资料。"""
def quote(data, request):
    station = request['station']
    if station not in data['stations']:
        raise ValueError('站点不存在')
    trigger = float(request['trigger'])
    limit = float(request['limit'])
    area = float(request['insured_area'])
    if not 12 <= trigger <= 36 or not 20 <= limit <= 150 or area <= 0:
        raise ValueError('条款超出承保范围')
    if data['stations'][station]['retired']:
        raise ValueError('迁出站点不可签新合同')
    premium = area * (limit * (0.055 + (trigger - 12) * 0.002))
    return {'station': station, 'trigger_mm': trigger, 'limit_yuan_mu': limit,
            'area_mu': area, 'premium_yuan': round(premium, 2),
            'formula': 'area_mu * min(limit_yuan_mu, max(0, trigger_mm - rain_mm) * 4)',
            'missing_weather': 'unsettled', 'contract_version': data['contract_version']}

def settle(data, request):
    contract = quote(data, request)
    rain = request.get('rain_mm')
    if rain is None:
        return {'status': 'unsettled', 'payout_yuan': None}
    payout = contract['area_mu'] * min(contract['limit_yuan_mu'], max(0, contract['trigger_mm'] - float(rain)) * 4)
    return {'status': 'settled', 'payout_yuan': round(payout, 2), 'contract': contract}

detail = settle
