import os
import json
import hmac
import hashlib
import base64
import shopify
from typing import Dict, Any, Optional, List, Tuple


class ShopifyService:
    def __init__(self):
        # Check if we're in testing mode
        self.testing = os.environ.get("TESTING", "").lower() == "true"

        self.api_key = os.environ.get("SHOPIFY_API_KEY")
        self.api_secret = os.environ.get("SHOPIFY_API_SECRET")
        self.shop_url = os.environ.get("SHOPIFY_STORE_URL")
        self.api_version = os.environ.get("SHOPIFY_API_VERSION", "2023-07")
        self.webhook_secret = os.environ.get("SHOPIFY_WEBHOOK_SECRET")

        # Initialize the Shopify API if not in testing mode
        if not self.testing:
            shop_url = f"https://{self.api_key}:{self.api_secret}@{self.shop_url}/admin/api/{self.api_version}"
            try:
                shopify.ShopifyResource.set_site(shop_url)
            except Exception as e:
                if not self.testing:
                    print(f"Warning: Could not initialize Shopify API: {e}")

    def verify_webhook(self, data: bytes, hmac_header: str) -> bool:
        """
        Verify that the webhook request came from Shopify

        Args:
            data: The raw request body
            hmac_header: The X-Shopify-Hmac-SHA256 header value

        Returns:
            True if the webhook is verified, False otherwise
        """
        if self.testing:
            return True

        if not self.webhook_secret:
            return False

        calculated_hmac = base64.b64encode(
            hmac.new(
                key=self.webhook_secret.encode(),
                msg=data,
                digestmod=hashlib.sha256
            ).digest()
        ).decode()

        return hmac.compare_digest(calculated_hmac, hmac_header)

    def parse_order_data(self, order_data: Dict[str, Any]) -> Tuple[Dict[str, Any], Optional[Dict[str, Any]]]:
        """
        Parse the order data to extract relevant information

        Args:
            order_data: The order data from Shopify webhook

        Returns:
            Tuple of (customer_data, order_details) or (customer_data, None) if no item found
        """
        try:
            # Extract customer information
            customer_data = {
                "shopify_customer_id": str(order_data["customer"]["id"]),
                "email": order_data["customer"].get("email"),
                "phone": order_data["customer"].get("phone"),
                "first_name": order_data["customer"].get("first_name", ""),
                "last_name": order_data["customer"].get("last_name", "")
            }

            # Find the first line item (clothing product)
            if "line_items" in order_data and len(order_data["line_items"]) > 0:
                item = order_data["line_items"][0]

                # Get size from properties or variant title
                original_size = None
                if "properties" in item and item["properties"]:
                    for prop in item["properties"]:
                        if prop.get("name") == "Size":
                            original_size = prop.get("value")
                            break

                # If no size property, use variant title
                if not original_size and "variant_title" in item:
                    original_size = item["variant_title"]

                # Create order details
                order_details = {
                    "shopify_order_id": str(order_data["id"]),
                    "order_number": order_data["order_number"],
                    "original_size": original_size,
                    "product_id": str(item["product_id"]),
                    "variant_id": str(item["variant_id"]),
                    "line_item_id": str(item["id"]),
                    "product_title": item["title"]
                }
                return customer_data, order_details

            # No suitable line item found
            return customer_data, None

        except (KeyError, IndexError) as e:
            # Handle missing data
            print(f"Error parsing order data: {e}")
            return {}, None

    async def update_order_size(self, order_id: str, line_item_id: str, new_size: str) -> bool:
        """
        Update the order size in Shopify

        Args:
            order_id: The Shopify order ID
            line_item_id: The line item ID to update
            new_size: The new size to set

        Returns:
            True if successful, False otherwise
        """
        if self.testing:
            return True

        try:
            # Get the order
            order = shopify.Order.find(order_id)

            # Add a note about the size change
            note = f"Size confirmation: Changed to {new_size} via WhatsApp conversation"

            # Update order note
            order.note = f"{order.note or ''}\n{note}".strip()
            order.save()

            # For full implementation, we would need to find the correct variant ID
            # for the new size and update the line item
            # This would require additional API calls to get the product variants

            # Instead, we'll just add a metafield to track the confirmed size
            order.add_metafield(
                shopify.Metafield({
                    'namespace': 'size_confirmation',
                    'key': 'confirmed_size',
                    'value': new_size,
                    'value_type': 'string'
                })
            )

            return True

        except Exception as e:
            print(f"Error updating order size: {e}")
            return False

    async def trigger_fulfillment(self, order_id: str) -> bool:
        """
        Trigger fulfillment for an order

        Args:
            order_id: The Shopify order ID

        Returns:
            True if successful, False otherwise
        """
        if self.testing:
            return True

        try:
            # Get the order
            order = shopify.Order.find(order_id)

            # Create a new fulfillment for all line items
            fulfillment = shopify.Fulfillment({
                'order_id': order_id,
                'notify_customer': True,
                'tracking_info': {
                    'number': 'N/A',
                    'company': 'Size Confirmation Service'
                }
            })

            # Add all line items to the fulfillment
            line_items = []
            for item in order.line_items:
                line_items.append({
                    'id': item.id
                })

            fulfillment.line_items = line_items
            result = fulfillment.save()

            return result

        except Exception as e:
            print(f"Error triggering fulfillment: {e}")
            return False
