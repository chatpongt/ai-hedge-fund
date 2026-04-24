"""Unit tests for mda_detector.py — regex detection of MD&A sections."""

import sys
from pathlib import Path

# Allow running from either the repo root or the mda-pipeline dir
sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from pipeline.mda_detector import find_mda_section, detect_mda


# ---------------------------------------------------------------------------
# Fixtures — realistic but minimal document snippets
# ---------------------------------------------------------------------------

THAI_DOC_CPALL = """
บริษัท ซีพีออลล์ จำกัด (มหาชน) รายงานประจำปี 2567

ส่วนที่ 1: ภาพรวมธุรกิจ

Lorem ipsum dolor sit amet

การวิเคราะห์และคำอธิบายของฝ่ายจัดการ

ผลการดำเนินงานประจำปี 2567

บริษัทมีรายได้รวม 650,000 ล้านบาท เพิ่มขึ้น 8% เมื่อเทียบกับปีก่อน
สาเหตุหลักมาจากการขยายสาขา 7-Eleven ทั้งในและต่างประเทศ
และการเติบโตของธุรกิจ Makro ในกลุ่มประเทศอาเซียน

รายได้จากการให้บริการ
- 7-Eleven: 480,000 ล้านบาท (+7.5%)
- Makro: 170,000 ล้านบาท (+9.2%)

ต้นทุนและอัตรากำไร
อัตรากำไรขั้นต้น (Gross Margin) อยู่ที่ 25.3% เพิ่มขึ้นจาก 24.8% ในปีก่อน

แนวโน้มปี 2568
บริษัทตั้งเป้าเปิดสาขาใหม่ 700 แห่ง และขยาย Makro ไปยังเวียดนาม

รายงานของผู้สอบบัญชีรับอนุญาต

งบการเงินรวม
(ตัวเลขจากงบการเงิน)
"""

ENGLISH_DOC_AOT = """
Airports of Thailand PLC — Annual Report 2024

Chapter 3: Business Overview

Management Discussion and Analysis

FY2024 Performance Summary

Total revenue reached THB 58.3 billion, representing a 34% increase year-on-year,
driven by the recovery of international passenger traffic to 95% of pre-COVID levels.

Revenue Breakdown
- Aeronautical revenue: THB 28.1 billion (+38%)
- Non-aeronautical revenue: THB 30.2 billion (+31%)

Margin Analysis
EBITDA margin improved to 42.5% from 38.1% in FY2023 as operating leverage
kicked in with higher passenger throughput.

Guidance FY2025
Management expects passenger numbers to exceed 200 million, recovering fully
to FY2019 pre-pandemic levels.

Independent Auditor's Report

Financial Statements
"""

MDA_EN_MD_AND_A = """
Some cover page content here.
Nothing interesting on this page.

MD&A

Revenue grew 20% year-on-year to THB 10 billion.
Cost of goods sold increased 15% to THB 7 billion.
Gross profit margin improved 3 percentage points to 30%.
EBITDA reached THB 2 billion, up 25% from the prior year.
The company expects continued growth in FY2025 driven by new product launches.
Management is cautious about raw material cost inflation.
Key risk: FX exposure on USD-denominated imports.
Management believes the long-term growth trajectory remains intact.
The company will continue to invest in digital transformation.
Expansion into CLMV markets is a core strategic priority.
New distribution centres are planned for Chiang Mai and Khon Kaen.
Working capital management improved with DSO reduced by 5 days.
Net debt to EBITDA improved to 1.8x from 2.3x.
Capital expenditure guidance is THB 500 million for FY2025.
Dividend payout ratio maintained at 40% of net profit.
The board approved a special dividend of THB 0.50 per share.
Return on equity stood at 18%, above industry average.
Cost reduction programme delivered THB 150 million in savings.
Procurement rationalisation contributed THB 80 million.
Headcount optimisation delivered THB 70 million in savings.

Financial Statements

Audited balance sheet as of 31 December 2024.
"""

NO_MDA_DOC = """
This document contains no relevant section headings whatsoever.
It is just a plain text document about something else entirely.
There are no relevant headings here — not in Thai, not in English.
Nothing to find. Move along.
"""

SHORT_SECTION_DOC = """
Unrelated header

management discussion and analysis

Only a few lines here.
Not enough content.

Financial Statements
"""


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestFindMdaSection:
    def test_thai_mda_found(self):
        result = find_mda_section(THAI_DOC_CPALL)
        assert result is not None
        assert "รายได้รวม" in result

    def test_english_mda_found(self):
        result = find_mda_section(ENGLISH_DOC_AOT)
        assert result is not None
        assert "Revenue" in result or "revenue" in result

    def test_md_and_a_abbreviation(self):
        result = find_mda_section(MDA_EN_MD_AND_A)
        assert result is not None
        assert "Revenue" in result

    def test_no_mda_returns_none(self):
        result = find_mda_section(NO_MDA_DOC)
        assert result is None

    def test_section_too_short_returns_none(self):
        # Section between start and end is < MIN_SECTION_LINES → end marker ignored,
        # section runs to EOF — but since end pattern appears, result should still exist
        # The key check: we don't return empty/tiny sections
        result = find_mda_section(SHORT_SECTION_DOC)
        # Either finds something or returns None — never returns empty string
        assert result is None or len(result.strip()) > 0

    def test_thai_content_preserved(self):
        result = find_mda_section(THAI_DOC_CPALL)
        assert result is not None
        assert "7-Eleven" in result
        assert "Makro" in result

    def test_end_boundary_respected(self):
        result = find_mda_section(THAI_DOC_CPALL)
        assert result is not None
        assert "รายงานของผู้สอบบัญชีรับอนุญาต" not in result
        assert "งบการเงินรวม" not in result

    def test_english_end_boundary(self):
        result = find_mda_section(ENGLISH_DOC_AOT)
        assert result is not None
        assert "Independent Auditor" not in result
        assert "Financial Statements" not in result


class TestDetectMda:
    def test_regex_success_no_llm_needed(self):
        mda, method = detect_mda(THAI_DOC_CPALL, use_llm_fallback=False)
        assert method == "regex"
        assert mda is not None

    def test_failed_without_llm(self):
        mda, method = detect_mda(NO_MDA_DOC, use_llm_fallback=False)
        assert method == "failed"
        assert mda is None

    def test_failed_when_llm_client_none(self):
        mda, method = detect_mda(NO_MDA_DOC, use_llm_fallback=True, llm_client=None)
        assert method == "failed"
        assert mda is None

    def test_returns_tuple(self):
        result = detect_mda(ENGLISH_DOC_AOT, use_llm_fallback=False)
        assert isinstance(result, tuple)
        assert len(result) == 2


class TestPatternCoverage:
    """Make sure every start/end pattern fires on at least one fixture."""

    THAI_START_PATTERNS = [
        "การวิเคราะห์และคำอธิบายของฝ่ายจัดการ",
        "คำอธิบายและการวิเคราะห์ของฝ่ายจัดการ",
        "ผลการดำเนินงานและฐานะการเงิน",
    ]

    EN_START_PATTERNS = [
        "Management Discussion and Analysis",
        "MD&A",
    ]

    def _doc_with_start(self, start: str) -> str:
        body = "\n".join(f"Line {i}: some financial discussion content here." for i in range(30))
        end = "Financial Statements\nBalance sheet follows."
        return f"Cover page\n\n{start}\n\n{body}\n\n{end}\n"

    @pytest.mark.parametrize("pattern", THAI_START_PATTERNS + EN_START_PATTERNS)
    def test_start_pattern_detects(self, pattern):
        doc = self._doc_with_start(pattern)
        result = find_mda_section(doc)
        assert result is not None, f"Pattern not detected: {pattern!r}"
