from django.db import models
from payment_source.models import PaymentSource
from ledger.models import Ledger

# This app uses existing models:
# - PaymentSource from payment_source app
# - Ledger from ledger app (which has payment_source field)

# No additional models needed for this report functionality