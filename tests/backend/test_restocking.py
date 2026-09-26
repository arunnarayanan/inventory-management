"""
Tests for the restocking API endpoints (recommendations and order placement).
"""
import pytest


class TestRestockRecommendations:
    """Test suite for the restock recommendations endpoint."""

    def test_get_recommendations_success(self, client):
        """Test getting recommendations returns the expected response shape."""
        response = client.get("/api/restocking/recommendations?budget=1000")
        assert response.status_code == 200

        data = response.json()
        assert "budget" in data
        assert "recommended_items" in data
        assert "total_cost" in data
        assert "remaining_budget" in data
        assert isinstance(data["recommended_items"], list)

    def test_recommendation_item_structure(self, client):
        """Test that recommended items have the expected fields."""
        response = client.get("/api/restocking/recommendations?budget=100000")
        data = response.json()

        assert len(data["recommended_items"]) > 0, "Expected at least one recommendation for a large budget"

        item = data["recommended_items"][0]
        assert "item_sku" in item
        assert "item_name" in item
        assert "current_demand" in item
        assert "forecasted_demand" in item
        assert "trend" in item
        assert "unit_cost" in item
        assert "recommended_quantity" in item
        assert "line_total" in item

    def test_recommendations_respect_budget(self, client):
        """Test that total recommended cost never exceeds the given budget."""
        for budget in [10, 50, 500, 5000, 100000]:
            response = client.get(f"/api/restocking/recommendations?budget={budget}")
            assert response.status_code == 200

            data = response.json()
            assert data["total_cost"] <= budget + 0.01
            assert abs(data["remaining_budget"] - (budget - data["total_cost"])) < 0.01

    def test_recommendations_exclude_decreasing_trend_item(self, client):
        """Test that items with a non-positive demand gap (e.g. decreasing trend) are never recommended."""
        response = client.get("/api/restocking/recommendations?budget=100000")
        data = response.json()

        skus = [item["item_sku"] for item in data["recommended_items"]]
        assert "MTR-304" not in skus, "MTR-304 has decreasing demand and should never be recommended"

    def test_recommendations_only_include_costed_items(self, client):
        """Test that every recommended item has a valid, positive unit cost."""
        response = client.get("/api/restocking/recommendations?budget=100000")
        data = response.json()

        for item in data["recommended_items"]:
            assert isinstance(item["unit_cost"], (int, float))
            assert item["unit_cost"] > 0
            assert item["recommended_quantity"] > 0

    def test_recommendations_small_budget_may_be_empty_or_partial(self, client):
        """Test that a very small budget still returns a valid (possibly empty) response."""
        response = client.get("/api/restocking/recommendations?budget=1")
        assert response.status_code == 200

        data = response.json()
        assert data["total_cost"] <= 1.01
        assert isinstance(data["recommended_items"], list)

    def test_recommendations_zero_budget_rejected(self, client):
        """Test that a zero budget is rejected."""
        response = client.get("/api/restocking/recommendations?budget=0")
        assert response.status_code == 400

    def test_recommendations_negative_budget_rejected(self, client):
        """Test that a negative budget is rejected."""
        response = client.get("/api/restocking/recommendations?budget=-50")
        assert response.status_code == 400

    def test_recommendations_missing_budget_rejected(self, client):
        """Test that a missing budget query param is rejected."""
        response = client.get("/api/restocking/recommendations")
        assert response.status_code == 422

    def test_recommendations_prioritize_increasing_trend(self, client):
        """Test that increasing-trend items rank ahead of stable ones with a smaller gap."""
        response = client.get("/api/restocking/recommendations?budget=100000")
        data = response.json()

        skus_in_order = [item["item_sku"] for item in data["recommended_items"]]

        # WDG-001 (increasing, gap 150) should be recommended, and should be
        # ranked ahead of PSU-501 (stable, gap 2) when both are affordable.
        assert "WDG-001" in skus_in_order
        assert "PSU-501" in skus_in_order
        assert skus_in_order.index("WDG-001") < skus_in_order.index("PSU-501")


class TestPlaceRestockOrder:
    """Test suite for placing a restocking order."""

    def _get_recommendations(self, client, budget=1000):
        response = client.get(f"/api/restocking/recommendations?budget={budget}")
        return response.json()

    def test_place_order_success(self, client):
        """Test placing a valid restocking order succeeds."""
        recs = self._get_recommendations(client, budget=1000)
        assert len(recs["recommended_items"]) > 0

        response = client.post("/api/restocking/orders", json={
            "budget": recs["budget"],
            "items": recs["recommended_items"]
        })
        assert response.status_code == 200

        order = response.json()
        assert order["source"] == "restocking"
        assert order["status"] == "Processing"
        assert order["order_number"].startswith("ORD-RESTOCK-")
        assert order["customer"] == "Internal Restocking"

    def test_place_order_total_value_matches_items(self, client):
        """Test that the created order's total_value matches its line items."""
        recs = self._get_recommendations(client, budget=1000)

        response = client.post("/api/restocking/orders", json={
            "budget": recs["budget"],
            "items": recs["recommended_items"]
        })
        order = response.json()

        calculated_total = sum(item["quantity"] * item["unit_price"] for item in order["items"])
        assert abs(order["total_value"] - calculated_total) < 0.01

    def test_place_order_expected_delivery_after_order_date(self, client):
        """Test that expected_delivery is 7-14 days after order_date."""
        from datetime import datetime

        recs = self._get_recommendations(client, budget=1000)
        response = client.post("/api/restocking/orders", json={
            "budget": recs["budget"],
            "items": recs["recommended_items"]
        })
        order = response.json()

        order_date = datetime.fromisoformat(order["order_date"])
        expected_delivery = datetime.fromisoformat(order["expected_delivery"])
        lead_time_days = (expected_delivery - order_date).days

        assert 7 <= lead_time_days <= 14

    def test_place_order_appears_in_get_orders(self, client):
        """Test that a placed restocking order shows up via GET /api/orders."""
        recs = self._get_recommendations(client, budget=1000)
        response = client.post("/api/restocking/orders", json={
            "budget": recs["budget"],
            "items": recs["recommended_items"]
        })
        created_order = response.json()

        orders_response = client.get("/api/orders")
        all_orders = orders_response.json()
        matching = [o for o in all_orders if o["id"] == created_order["id"]]

        assert len(matching) == 1
        assert matching[0]["source"] == "restocking"

    def test_place_order_rejects_empty_items(self, client):
        """Test that an order with no items is rejected."""
        response = client.post("/api/restocking/orders", json={
            "budget": 100,
            "items": []
        })
        assert response.status_code == 400

    def test_place_order_rejects_budget_mismatch(self, client):
        """Test that a tampered payload exceeding the stated budget is rejected."""
        recs = self._get_recommendations(client, budget=1000)
        assert len(recs["recommended_items"]) > 0

        response = client.post("/api/restocking/orders", json={
            "budget": 1,  # stated budget far below the actual item cost
            "items": recs["recommended_items"]
        })
        assert response.status_code == 400
