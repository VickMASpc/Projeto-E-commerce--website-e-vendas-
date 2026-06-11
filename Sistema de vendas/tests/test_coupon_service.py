from services.coupon_service import CouponService


class FakeCouponRepo:
    def __init__(self, coupons=None):
        self.data = {"cupons": [dict(coupon) for coupon in (coupons or [])]}

    def get_coupons(self):
        return [dict(coupon) for coupon in self.data["cupons"]]

    def read_data(self):
        return {"cupons": [dict(coupon) for coupon in self.data["cupons"]]}

    def write_data(self, data):
        self.data = {"cupons": [dict(coupon) for coupon in data.get("cupons", [])]}


def test_create_coupon_persists_normalized_payload():
    service = CouponService(FakeCouponRepo())

    result = service.create_coupon(
        {
            "code": "welcome10",
            "type": "percent",
            "value": 10,
            "active": True,
            "min_order_total": 150,
        }
    )

    assert result["ok"] is True
    assert result["coupon"]["code"] == "WELCOME10"
    assert result["coupon"]["min_subtotal"] == 150.0


def test_update_coupon_changes_activation_and_limits():
    repo = FakeCouponRepo(
        [
            {
                "code": "SHIPFREE",
                "type": "fixed",
                "value": 40,
                "active": True,
                "used_count": 1,
            }
        ]
    )
    service = CouponService(repo)

    result = service.update_coupon(
        "SHIPFREE",
        {"active": False, "usage_limit": 5, "max_discount": 40},
    )

    assert result["ok"] is True
    assert result["coupon"]["active"] is False
    assert result["coupon"]["usage_limit"] == 5
    assert result["coupon"]["max_discount"] == 40.0


def test_deactivate_coupon_marks_coupon_inactive():
    repo = FakeCouponRepo([{"code": "VIP20", "type": "percent", "value": 20, "active": True}])
    service = CouponService(repo)

    result = service.deactivate_coupon("VIP20")

    assert result["ok"] is True
    assert result["coupon"]["active"] is False


def test_validate_coupon_preserves_api_compatible_response_shape():
    repo = FakeCouponRepo(
        [
            {
                "code": "SAVE15",
                "type": "percent",
                "value": 15,
                "active": True,
                "min_order_total": 200,
                "max_discount": 50,
                "used_count": 2,
                "usage_limit": 10,
                "expires_at": "2099-12-31T23:59:59",
            }
        ]
    )
    service = CouponService(repo)

    result = service.validate_coupon("save15", 400)

    assert result == {
        "valid": True,
        "code": "SAVE15",
        "discount": 50.0,
        "message": "Cupom aplicado com sucesso.",
        "adjusted_total": 350.0,
    }
