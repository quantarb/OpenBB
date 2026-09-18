import pytest
from openbb_fmp.models.institutional_ownership import FMPInstitutionalOwnershipData


@pytest.mark.parametrize('percentage,expected', [(0, 0.), (None, None), (12.5, .125)])
def test_institutional_ownership_preserves_zero_and_missing_percentages(percentage, expected):
    fields = FMPInstitutionalOwnershipData.model_fields
    payload = {name: 1 for name, field in fields.items() if field.is_required()}
    payload.update(symbol='COIN', date='2021-03-31', ownership_percent=percentage,
                   last_ownership_percent=percentage, ownership_percent_change=percentage)
    row = FMPInstitutionalOwnershipData.model_validate(payload)
    assert row.ownership_percent == expected
    assert row.last_ownership_percent == expected
    assert row.ownership_percent_change == expected
