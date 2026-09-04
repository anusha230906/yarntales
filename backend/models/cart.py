class CartModel:
    def __init__(
        self,
        cart_id,
        user_id,
        product_id,
        quantity=1,
        customization_id=None
    ):
        self.cart_id = cart_id
        self.user_id = user_id
        self.product_id = product_id
        self.quantity = quantity
        self.customization_id = customization_id

    def to_dict(self):
        return {
            "cartId": self.cart_id,
            "userId": self.user_id,
            "productId": self.product_id,
            "quantity": self.quantity,
            "customizationId": self.customization_id
        }