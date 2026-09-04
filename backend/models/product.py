class ProductModel:

    def __init__(
        self,
        product_id,
        name,
        category,
        base_price,
        colors
    ):
        self.product_id = product_id
        self.name = name
        self.category = category
        self.base_price = base_price
        self.colors = colors

    def to_dict(self):
        return {
            "productId": self.product_id,
            "name": self.name,
            "category": self.category,
            "basePrice": self.base_price,
            "colors": self.colors
        }