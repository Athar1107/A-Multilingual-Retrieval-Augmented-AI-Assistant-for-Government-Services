from app.rag.fallback_routing import FallbackRouter, FALLBACK_CAVEAT

def test_fallback_router_direct_route():
    router = FallbackRouter(confidence_threshold=0.6)
    
    result = router.route("query", 0.8, "The scheme provides ₹500.")
    
    assert result["route"] == "direct"
    assert result["answer"] == "The scheme provides ₹500."
    assert result["confidence"] == 0.8


def test_fallback_router_fallback_route():
    router = FallbackRouter(confidence_threshold=0.6)
    
    result = router.route("query", 0.4, "The scheme might provide ₹500.")
    
    assert result["route"] == "fallback"
    assert FALLBACK_CAVEAT in result["answer"]
    assert result["answer"].startswith("The scheme might provide ₹500.")
    assert result["confidence"] == 0.4


def test_fallback_router_confidence_clamping():
    router = FallbackRouter(confidence_threshold=0.6)
    
    # Should clamp above 1.0 to 1.0
    result_high = router.route("query", 1.5, "Answer")
    assert result_high["confidence"] == 1.0
    
    # Should clamp below 0.0 to 0.0
    result_low = router.route("query", -0.5, "Answer")
    assert result_low["confidence"] == 0.0
