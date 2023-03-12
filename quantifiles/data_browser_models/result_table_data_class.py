from dataclasses import dataclass, asdict
import datetime

from quantify_core.data.types import TUID


@dataclass
class m_result_item:
    my_id: int
    uuid: TUID
    name: str
    start_time: datetime
    project: str
    set_up: str
    sample: str
    starred: str
    _keywords: list = None

    __attr_order = [
        "my_id",
        "uuid",
        "name",
        "date",
        "project",
        "set_up",
        "sample",
        "starred",
        "keywords",
    ]
    __search_key_idx = 3

    @property
    def keywords(self):
        kw = ""
        if isinstance(self._keywords, list):
            for i in self._keywords:
                if "raw" not in i:
                    kw += str(i) + ", "
        if len(kw) == 0:
            return kw

        if len(kw) > 80:
            kw = kw[:80] + " ...."
        return kw[:-2]

    @property
    def date(self):
        return self.start_time.strftime("%d/%m/%Y %H:%M:%S")

    @property
    def time(self):
        return self.start_time.strftime("%H:%M:%S")

    def set_sort_idx(self, i):
        self.__search_key_idx = i

    def __getitem__(self, i):
        return getattr(self, self.__attr_order[i])

    def __len__(self):
        return len(self.__attr_order)

    def __eq__(self, other):
        return self[self.__search_key_idx] == other[self.__search_key_idx]

    def __lt__(self, other):
        return self[self.__search_key_idx] < other[self.__search_key_idx]


class m_result_overview:
    def __init__(self, query_input_data):
        self.data = []
        for data in query_input_data:
            self.data.append(m_result_item(**asdict(data)))

        self.sort(3, True)

    def __len__(self):
        return len(self.data)

    def __getitem__(self, item):
        return self.data[item]

    def sort(self, idx, order):
        # sorts the interal array accoring to a column
        for i in self.data:
            i.set_sort_idx(idx)
        self.data.sort(reverse=order)
