from django.db import transaction

from .models import Order


def select_bid(order, bid):
    """Taklifni tanlash: mijoz (M6) va admin qo'lda biriktirganda (A2) bir xil ishlaydi.

    Chaqiruvchi tranzaksiya ichida va order select_for_update bilan qulflangan bo'lishi kerak.
    """
    from apps.bids.models import Bid
    from apps.notifications.tasks import enqueue, notify_bid_selected

    order.bids.exclude(pk=bid.pk).update(status=Bid.StatusChoice.REJECTED)
    bid.status = Bid.StatusChoice.ACCEPTED
    bid.save(update_fields=['status'])

    order.selected_bid = bid
    order.status = Order.StatusChoice.SELECTED
    order.save(update_fields=['selected_bid', 'status', 'updated_at'])

    order_id = order.pk
    transaction.on_commit(lambda: enqueue(notify_bid_selected, order_id))
    return order
