import os

import httpx
import pytest
from jose import jwt


@pytest.mark.asyncio
async def test_send_code_does_not_return_plain_code(app, fake_redis):
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        email = "user1@example.com"
        resp = await client.post("/api/v1/auth/send-code", json={"email": email, "purpose": "register"})
        assert resp.status_code == 200
        body = resp.json()
        assert body == {"message": "Verification code sent"}

        # Code must exist in Redis, but never in API response.
        code = fake_redis.get(f"verification_code:{email}:register")
        assert code is not None
        assert code.isdigit()
        assert len(code) == 6


@pytest.mark.asyncio
async def test_register_login_and_points_floor_rule(app, fake_redis):
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        email = "user2@example.com"

        # Send register code
        resp = await client.post("/api/v1/auth/send-code", json={"email": email, "purpose": "register"})
        assert resp.status_code == 200
        register_code = fake_redis.get(f"verification_code:{email}:register")
        assert register_code is not None

        # Register
        resp = await client.post(
            "/api/v1/auth/register",
            json={"email": email, "code": register_code, "nickname": "Tester"},
        )
        assert resp.status_code == 200
        token = resp.json()["access_token"]

        # Token must carry explicit role claim.
        payload = jwt.decode(
            token,
            os.environ["JWT_SECRET_KEY"],
            algorithms=["HS256"],
        )
        assert payload["role"] == "user"

        # Profile
        resp = await client.get("/api/v1/members/me", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        masked_email = resp.json()["email"]
        assert masked_email != email
        assert "***" in masked_email
        assert masked_email.endswith("@example.com")

        # Rate limit: sending another code immediately should be blocked.
        resp2 = await client.post("/api/v1/auth/send-code", json={"email": email, "purpose": "login"})
        assert resp2.status_code == 400
        assert resp2.json()["code"] == "VERIFICATION_CODE_RATE_LIMIT"

        # Simulate waiting one minute by removing the minute limiter key, then do a normal login flow.
        fake_redis.delete(f"rate_limit:verification:{email}:minute")
        resp = await client.post("/api/v1/auth/send-code", json={"email": email, "purpose": "login"})
        assert resp.status_code == 200
        login_code = fake_redis.get(f"verification_code:{email}:login")
        assert login_code is not None

        resp = await client.post("/api/v1/auth/login", json={"email": email, "code": login_code})
        assert resp.status_code == 200
        login_token = resp.json()["access_token"]
        payload = jwt.decode(login_token, os.environ["JWT_SECRET_KEY"], algorithms=["HS256"])
        assert payload["role"] == "user"

        # Create order with decimal amount: points = floor(amount)
        order_amount = 12.99
        resp = await client.post(
            "/api/v1/orders",
            headers={"Authorization": f"Bearer {token}"},
            json={"amount": order_amount, "product_name": "P", "product_description": "D"},
        )
        assert resp.status_code == 200
        order_id = resp.json()["id"]

        # Complete order
        resp = await client.post(
            f"/api/v1/orders/{order_id}/complete",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "completed"

        # Points should be 12 (floor of 12.99)
        resp = await client.get("/api/v1/points/balance", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert resp.json()["available_points"] == 12

        # Refund should deduct earned points back to 0
        resp = await client.post(
            f"/api/v1/orders/{order_id}/refund",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "refunded"

        resp = await client.get("/api/v1/points/balance", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        assert resp.json()["available_points"] == 0
