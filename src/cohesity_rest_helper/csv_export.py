"""Excel and CSV export helpers."""
import dataclasses
from pathlib import Path

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

    def _sheets(self):
        return [
            ("Warm Granular", "warm_granular.csv", self.df_warm),
            ("Warm Sum", "warm_summary.csv", self.df_warm_sum),
            ("Replica Granular", "replica_granular.csv", self.df_replica),
            ("Replica Sum", "replica_summary.csv", self.df_replica_sum),
            ("Cold Granular", "cold_granular.csv", self.df_view),
            ("Cold Sum", "cold_summary.csv", self.df_view_sum),
            ("Frozen Granular", "vault_granular.csv", self.df_vault),
            ("Frozen Sum", "vault_summary.csv", self.df_vault_sum),
        ]

    def save_as_excel(self, reportname: str) -> None:
        """Write all frames to an .xlsx workbook, one sheet each (requires openpyxl)."""
        with pd.ExcelWriter(reportname) as writer:  # pylint: disable=abstract-class-instantiated
            for sheet_name, _, frame in self._sheets():
                self._formula_safe(frame).to_excel(writer, sheet_name=sheet_name, index=False)

    @staticmethod
    def _formula_safe(frame: pd.DataFrame) -> pd.DataFrame:
        """Copy a frame and neutralize values that spreadsheets may treat as formulas."""
        safe = frame.copy()
        for column in safe.select_dtypes(include=["object", "string"]).columns:
            safe[column] = safe[column].map(
                lambda value: "'" + value
                if isinstance(value, str) and value.startswith(("=", "+", "-", "@"))
                else value
            )
        return safe

    @classmethod
    def _csv_safe(cls, frame: pd.DataFrame) -> pd.DataFrame:
        """Copy a frame, add UTC timestamps, and neutralize spreadsheet formulas."""
        safe = cls._formula_safe(frame)
        if "Time" in safe.columns:
            safe["Time (UTC)"] = pd.to_datetime(safe["Time"], unit="ms", utc=True).dt.strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            )
        return safe

    def save_as_csv_files(self, directory: str) -> list[str]:
        """Write one UTF-8 CSV per report frame and return the created paths."""
        output = Path(directory)
        output.mkdir(parents=True, exist_ok=True)
        written = []
        for _, filename, frame in self._sheets():
            path = output / filename
            self._csv_safe(frame).to_csv(path, index=False, lineterminator="\n")
            written.append(str(path))
        return written

    # Original method name, kept for compatibility (it has always written .xlsx).
    save_as_csv = save_as_excel
