from .base_reporter import BaseReporter
from typing import List, Dict
from collections import Counter
from datetime import datetime, timedelta
from typing import Any, Dict

class ReporterRegression(BaseReporter):
    SUSPECT_AREAS = [
        "silicon", "system_boards", "hardware.component.dram",
        "io_device", "bios", "bmc_fw", "cpld_fw", "pfr",
        "operating_system", "platform.simics", "DDR5 DIMM",
        "documentation", "script", "tool", "test_content", "unknown"
    ]

    def generate(self, *, last_weeks: int = None) -> Dict[str, Any]:
        now = datetime.now()
        start_date = self.DMR_START_DATE
        if last_weeks:
            start_date = now - timedelta(weeks=last_weeks)
        relevant = [s for s in self.sightings if start_date <= s.get('submitted_date') <= now]
        counter = Counter()
        details = []
        for s in relevant:
            if s.get('regression', False):
                area = s.get('suspect_area', 'unknown')
                area = area if area in self.SUSPECT_AREAS else 'others'
                counter[area] += 1
                details.append({
                    'id': s.get('id'),
                    'title': s.get('title'),
                    'exposure': s.get('exposure'),
                    'status': s.get('status'),
                    'ingredient': s.get('ingredient'),
                    'proposed_counter_measure': self.get_counter_measure(s)  # placeholder
                })
        return {
            'summary': sorted(counter.items(), key=lambda x: x[1], reverse=True),
            'details': details
        }

    def get_counter_measure(self, sighting: Dict) -> str:
        # TODO: placeholder
        return ""