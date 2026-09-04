from datetime import datetime, timezone


class OrderModel:
    def __init__(
        self,
        order_id,
        user_id,
        items,
        total_amount,
        shipping_address,
        payment_method="Simulated Payment",
        payment_status="Paid",
        status="Order Confirmed"
    ):
        self.order_id = order_id
        self.user_id = user_id
        self.items = items
        self.total_amount = total_amount
        self.shipping_address = shipping_address
        self.payment_method = payment_method
        self.payment_status = payment_status
        self.status = status
        self.created_at = datetime.now(timezone.utc)

    def to_dict(self):
        return {
            "orderId": self.order_id,
            "userId": self.user_id,
            "items": self.items,
            "totalAmount": self.total_amount,
            "shippingAddress": self.shipping_address,
            "paymentMethod": self.payment_method,
            "paymentStatus": self.payment_status,
            "status": self.status,
            "createdAt": self.created_at
        }