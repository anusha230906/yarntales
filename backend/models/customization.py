from datetime import datetime, timezone


class CustomizationModel:

    def __init__(
        self,
        customization_id,
        user_id,
        product_id,
        color,
        size,
        features=None,
        accessory=None,
        personalized_name=None
    ):
        self.customization_id = customization_id
        self.user_id = user_id
        self.product_id = product_id
        self.color = color
        self.size = size
        self.features = features or []
        self.accessory = accessory
        self.personalized_name = personalized_name
        self.created_at = datetime.now(timezone.utc)

    def to_dict(self):
        return {
            "customizationId": self.customization_id,
            "userId": self.user_id,
            "productId": self.product_id,
            "color": self.color,
            "size": self.size,
            "features": self.features,
            "accessory": self.accessory,
            "personalizedName": self.personalized_name,
            "createdAt": self.created_at
        }