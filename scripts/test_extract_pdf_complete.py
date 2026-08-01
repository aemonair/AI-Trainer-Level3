from pathlib import Path
import importlib.util

spec = importlib.util.spec_from_file_location(
    "extract_pdf_complete",
    Path(__file__).with_name("extract_pdf_complete.py"),
)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


def test_parse_exam_blocks_from_text():
    sample_pages = [
        "试题名称：智能医疗系统中的业务数据处理流程设计\n考核时间：30min\n1. 场地设备要求",
        "第二部分\n请完成该题的任务。",
        "试题名称：智能农业系统中的业务数据采集和处理流程设计\n考核时间：30min",
    ]
    blocks = module.parse_exam_blocks_from_text(sample_pages)
    assert len(blocks) == 2
    assert blocks[0][0] == "智能医疗系统中的业务数据处理流程设计"
    assert blocks[1][0] == "智能农业系统中的业务数据采集和处理流程设计"
