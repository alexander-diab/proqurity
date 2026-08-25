from app import connection
from app.workflow import find_candidates, Handover

with connection.session() as s:
    po_items = Handover.run(find_candidates(s))

print(f"{len(po_items)} PO items: {po_items[:3]} ...")
