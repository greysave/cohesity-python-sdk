"""Excel export module."""
import dataclasses

import pandas as pd


@dataclasses.dataclass
class CSVData:
    """Holds the granular and summary frames for each storage tier."""
    df_warm: pd.DataFrame
    df_warm_sum: pd.DataFrame
    df_replica: pd.DataFrame
    df_replica_sum: pd.DataFrame
    df_view: pd.DataFrame
    df_view_sum: pd.DataFrame
    df_vault: pd.DataFrame
    df_vault_sum: pd.DataFrame

    def save_as_excel(self, reportname: str) -> None:
        """Write all frames to an .xlsx workbook, one sheet each (requires openpyxl)."""
        sheets = [
            ("Warm Granular", self.df_warm), ("Warm Sum", self.df_warm_sum),
            ("Replica Granular", self.df_replica), ("Replica Sum", self.df_replica_sum),
            ("Cold Granular", self.df_view), ("Cold Sum", self.df_view_sum),
            ("Frozen Granular", self.df_vault), ("Frozen Sum", self.df_vault_sum),
        ]
        with pd.ExcelWriter(reportname) as writer:  # pylint: disable=abstract-class-instantiated
            for name, frame in sheets:
                frame.to_excel(writer, sheet_name=name, index=False)

    # Original method name, kept for compatibility (it has always written .xlsx).
    save_as_csv = save_as_excel
