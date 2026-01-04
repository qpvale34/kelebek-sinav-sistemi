"""Kelebek Sınav Sistemi - Utils Paketi"""

from .constants import (
    MIN_SINIF,
    MAX_SINIF,
    SINIF_SEVIYELERI,
    SINIF_ISMI_PATTERN,
    TEACHER_DESK_BASE,
    CP_SAT_FORBID_SAME_GRADE_ADJACENT,
    sinif_seviyesinden_sayi,
    sinif_ismi_gecerli_mi,
)

from .resource_helper import (
    is_frozen,
    get_base_path,
    get_resource_path,
    get_user_data_path,
    ensure_user_data_dir,
    get_app_info,
)


def format_sira_label(sira_no, empty: str = "-") -> str:
    """Ekran/rapor için sıra etiketi üret."""
    if sira_no is None or sira_no == "":
        return empty
    if isinstance(sira_no, str):
        stripped = sira_no.strip()
        if not stripped.isdigit():
            return stripped or empty
        try:
            value = int(stripped)
        except ValueError:
            return stripped
    else:
        try:
            value = int(sira_no)
        except (TypeError, ValueError):
            return str(sira_no)
    if value >= TEACHER_DESK_BASE:
        return "Ö.Masa"
    return f"{value:03d}"


__all__ = [
    "MIN_SINIF",
    "MAX_SINIF",
    "SINIF_SEVIYELERI",
    "SINIF_ISMI_PATTERN",
    "TEACHER_DESK_BASE",
    "CP_SAT_FORBID_SAME_GRADE_ADJACENT",
    "format_sira_label",
    "sinif_seviyesinden_sayi",
    "sinif_ismi_gecerli_mi",
    "is_frozen",
    "get_base_path",
    "get_resource_path",
    "get_user_data_path",
    "ensure_user_data_dir",
    "get_app_info",
]
