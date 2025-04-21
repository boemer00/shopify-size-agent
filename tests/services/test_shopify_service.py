import pytest
from unittest.mock import patch, MagicMock
import os

from app.services.shopify_service import ShopifyService

class TestShopifyService:

    @pytest.fixture
    def shopify_service(self):
        # Make sure testing flag is set
        os.environ["TESTING"] = "true"
        service = ShopifyService()
        return service

    @pytest.fixture
    def mock_shopify(self):
        with patch("app.services.shopify_service.shopify") as mock_shopify:
            # Setup mock Shop
            mock_shop = MagicMock()
            mock_shopify.Shop.current.return_value = mock_shop

            # Setup mock Order
            mock_order = MagicMock()
            mock_shopify.Order.find.return_value = mock_order

            # Setup mock LineItem
            mock_line_item = MagicMock()
            mock_order.line_items = [mock_line_item]

            # Setup mock FulfillmentService
            mock_fulfillment_service = MagicMock()
            mock_shopify.FulfillmentService.find.return_value = mock_fulfillment_service

            # Setup mock Fulfillment
            mock_fulfillment = MagicMock()
            mock_shopify.Fulfillment.return_value = mock_fulfillment

            yield mock_shopify

    def test_parse_order_data(self, shopify_service):
        """Test parsing Shopify order data"""
        # Sample order data
        order_data = {
            "id": 123456789,
            "order_number": "#1001",
            "customer": {
                "id": 987654321,
                "email": "customer@example.com",
                "phone": "+1234567890",
                "first_name": "Test",
                "last_name": "Customer"
            },
            "line_items": [
                {
                    "id": 111222333,
                    "product_id": 444555666,
                    "variant_id": 777888999,
                    "title": "Test Product",
                    "variant_title": "Medium",
                    "properties": [
                        {
                            "name": "Size",
                            "value": "M"
                        }
                    ]
                }
            ]
        }

        # Call method
        customer_data, order_details = shopify_service.parse_order_data(order_data)

        # Verify customer data
        assert customer_data["shopify_customer_id"] == "987654321"
        assert customer_data["email"] == "customer@example.com"
        assert customer_data["phone"] == "+1234567890"
        assert customer_data["first_name"] == "Test"
        assert customer_data["last_name"] == "Customer"

        # Verify order details
        assert order_details["shopify_order_id"] == "123456789"
        assert order_details["order_number"] == "#1001"
        assert order_details["original_size"] == "M"
        assert order_details["product_id"] == "444555666"
        assert order_details["variant_id"] == "777888999"
        assert order_details["line_item_id"] == "111222333"
        assert order_details["product_title"] == "Test Product"

    def test_parse_order_data_no_size_property(self, shopify_service):
        """Test parsing order data with no explicit size property"""
        # Sample order data with size in variant_title but no property
        order_data = {
            "id": 123456789,
            "order_number": "#1001",
            "customer": {
                "id": 987654321,
                "email": "customer@example.com",
                "phone": "+1234567890",
                "first_name": "Test",
                "last_name": "Customer"
            },
            "line_items": [
                {
                    "id": 111222333,
                    "product_id": 444555666,
                    "variant_id": 777888999,
                    "title": "Test Product",
                    "variant_title": "Medium",
                    "properties": []  # No size property
                }
            ]
        }

        # Call method
        customer_data, order_details = shopify_service.parse_order_data(order_data)

        # Verify size is taken from variant_title
        assert order_details["original_size"] == "Medium"

    def test_parse_order_data_multiple_items(self, shopify_service):
        """Test parsing order data with multiple line items (should use first item)"""
        # Sample order data with multiple items
        order_data = {
            "id": 123456789,
            "order_number": "#1001",
            "customer": {
                "id": 987654321,
                "email": "customer@example.com",
                "phone": "+1234567890",
                "first_name": "Test",
                "last_name": "Customer"
            },
            "line_items": [
                {
                    "id": 111222333,
                    "product_id": 444555666,
                    "variant_id": 777888999,
                    "title": "Test Product 1",
                    "variant_title": "Medium",
                    "properties": [
                        {
                            "name": "Size",
                            "value": "M"
                        }
                    ]
                },
                {
                    "id": 999888777,
                    "product_id": 666555444,
                    "variant_id": 333222111,
                    "title": "Test Product 2",
                    "variant_title": "Large",
                    "properties": [
                        {
                            "name": "Size",
                            "value": "L"
                        }
                    ]
                }
            ]
        }

        # Call method
        customer_data, order_details = shopify_service.parse_order_data(order_data)

        # Verify first item is used
        assert order_details["product_title"] == "Test Product 1"
        assert order_details["original_size"] == "M"
        assert order_details["line_item_id"] == "111222333"

    async def test_update_order_size(self, shopify_service):
        """Test updating order size in Shopify"""
        # Setup
        order_id = "123456789"
        line_item_id = "111222333"
        new_size = "L"

        # Call method
        result = await shopify_service.update_order_size(order_id, line_item_id, new_size)

        # In testing mode, should always return True
        assert result is True

    async def test_trigger_fulfillment(self, shopify_service):
        """Test triggering fulfillment in Shopify"""
        # Setup
        order_id = "123456789"

        # Call method
        result = await shopify_service.trigger_fulfillment(order_id)

        # In testing mode, should always return True
        assert result is True
