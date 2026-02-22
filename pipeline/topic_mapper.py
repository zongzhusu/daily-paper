HARDWARE_HINTS = ("asic", "fpga", "chip", "chiplet", "accelerator", "hbm")


def map_topic(item: dict) -> str:
    categories = [x.lower() for x in item.get("categories", [])]
    title = item.get("title", "").lower()
    if "cs.ar" in categories or any(k in title for k in HARDWARE_HINTS):
        return "芯片与硬件架构"
    if any(x in categories for x in ["cs.cv", "cs.cl", "eess.iv", "eess.as"]):
        return "多模态与感知"
    if "cs.cr" in categories:
        return "评测、安全与对齐"
    if "cs.ma" in categories:
        return "Agent与推理范式"
    return "模型与学习算法"
