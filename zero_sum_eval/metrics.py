from zero_sum_eval.registry import METRIC_REGISTRY

@METRIC_REGISTRY.register()
def exact_match(pred: str, gt: str):
    return pred == gt

@METRIC_REGISTRY.register()
def exact_match_lower(pred: str, gt: str):
    return pred.lower() == gt.lower()

