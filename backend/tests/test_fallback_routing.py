from app.rag.fallback_routing import FallbackRouter, FALLBACK_CAVEAT


def test_fallback_router_direct_route():
    router = FallbackRouter(confidence_threshold=0.50)
    result = router.route("query", 0.8, "The scheme provides ₹500.", is_recovered=False)

    assert result["route"] == "direct"
    assert result["answer"] == "The scheme provides ₹500."
    assert result["confidence"] == 0.8


def test_fallback_router_recovered_route():
    router = FallbackRouter(confidence_threshold=0.50)
    result = router.route("query", 0.75, "Recovered scheme info.", is_recovered=True)

    assert result["route"] == "fallback_recovered"
    assert result["answer"] == "Recovered scheme info."
    assert result["confidence"] == 0.75


def test_fallback_router_failed_route():
    router = FallbackRouter(confidence_threshold=0.50)
    result = router.route("query", 0.3, "Uncertain answer", is_recovered=False)

    assert result["route"] == "fallback_failed"
    assert "https://www.myscheme.gov.in" in result["answer"]
    assert result["confidence"] == 0.3


def test_fallback_router_confidence_clamping():
    router = FallbackRouter(confidence_threshold=0.50)

    # Should clamp above 1.0 to 1.0
    result_high = router.route("query", 1.5, "Answer")
    assert result_high["confidence"] == 1.0

    # Should clamp below 0.0 to 0.0
    result_low = router.route("query", -0.5, "Answer")
    assert result_low["confidence"] == 0.0
