# origin_signature: MrLiouWord
# Fusion Strategies — Strategy pattern for AI fusion modes

ORIGIN = "MrLiouWord"

def apply_strategy(mode, stack, prompt, **kwargs):
    if mode == "sequential":
        return stack.sequential(prompt)
    elif mode == "parallel":
        return stack.parallel(prompt)
    elif mode == "weighted":
        return stack.weighted(prompt, kwargs.get("weights"))
    elif mode == "mobius":
        from ai_fusion_core import MobiusLoop
        loop = MobiusLoop(stack, kwargs.get("max_iterations", 5))
        return loop.run(prompt)
    return {"error": f"unknown mode: {mode}", "origin_signature": ORIGIN}
