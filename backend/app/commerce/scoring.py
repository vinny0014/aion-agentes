"""PulseScore uses only normalized, evidenced components; missing stays missing."""
import math

WEIGHTS={'popularity':25,'competitiveness':20,'rating':15,'real_discount':15,
         'trend':10,'commission':10,'data_quality':5}


def pulse_score(components):
    if set(components)-set(WEIGHTS):
        raise ValueError('unknown_component')
    missing=[]; total=0
    for key,weight in WEIGHTS.items():
        value=components.get(key)
        if value is None:
            missing.append(key)
            continue
        if isinstance(value,bool) or not isinstance(value,(float,int)) or not math.isfinite(value) or not 0<=value<=100:
            raise ValueError('invalid_component')
        total+=value*weight/100
    # Missing evidence is never normalized away to inflate scores.
    score=round(total,2)
    return {'score':score,'missing':missing,'eligible':not missing and score>=70
            and components['rating']>=60 and components['data_quality']>=80,
            'method':'weighted_verified_components_v1'}


def observed_discount(current_cents, reference_cents):
    if type(current_cents) is not int or type(reference_cents) is not int or min(current_cents,reference_cents)<=0:
        raise ValueError('positive_integer_cents_required')
    return round(max(0,(reference_cents-current_cents)/reference_cents*100),2)
