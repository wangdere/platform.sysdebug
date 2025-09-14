from .base_reporter import BaseReporter
import sighting_util as su
from typing import Optional, List, Dict, Tuple, Any, Union
from datetime import datetime, timedelta
from  hsd_connection  import HSDConnection
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict
import matplotlib.pyplot as plt
import utils as u
from hsd_types import PlatfStatusReason, PlatfStatus

import matplotlib.colors as mcolors
from concurrent.futures import ThreadPoolExecutor, as_completed
'''
The structure of the table: (basic) 
0 step ( individual sighting): raw data: 
{
  "data": [
            { "rev": "4", "id": "xxx", "title":"xxx", "bug.exposure": "2-high", "updated_date": "2025-09-13 00:07:03.88"},
            {"rev": "3", ....................},
            ...
           ]
}

1st step ( individual sighting) : 

   ww      exposure status status_reason (other_atrributes)  rule1  rule2
2025ww32  
2025ww33 
2025ww34 
... 
2026ww01
.. 
2026ww52
.. 
2027ww01 
....
this_week

data strucutre of the output of 1st step: 

{
    "id": [
                  {"ww": "2025ww32", "status": "assigned", "status_reason": "...", "exposure": "..."},
                  {"ww": "2025ww33",  ...................},
                                ...
            ] 

}

from 1st step to 2nd step: defined rules for different statistics scenario: e.g. 
rule1 = "C_H" if ( exposure == critical or high) 
rule1 =  "M"    if expsoure == M)  
rule2 = "Aassigned" (if status_reason == .....)
rule2 = "transferred" (if status_reason == .....)
rule2 = "root_caused" (if status_reason == .....)
rule2 = "implemented" (if status_reason == .....)
rule2 = "closed" (if status_reason == .....)

then output:

{
    "id": [
                  {"ww": "2025ww32", "status": "assigned", "status_reason": "...", "exposure": "...", "rule1" = c_H, "rule2": "Assigned"},
                  {"ww": "2025ww33",  ...................},
                                ...
            ] 

        
}



2nd step:

ww            rule1      rule2            ids           count
2025ww32      c_H      Assigned      [id_1, id_2]
2025ww32      C_H        transferred     [id_3]
2025ww32      C_H        root_caused     [id_4]
2025ww32      C_H        implemented     [id_5, id_6]
2025ww32      M      Assigned      [id_7, id_8]
2025ww32      M        transferred     [id_9]
2025ww32      M        root_caused     [id_10]
2025ww32      m        implemented     [id_11, id_12]
2025ww33    .........
.....
    




back up for 2nd step(may not be used): 
   ww      id_1         id_2    id_3 ..... 
2025ww32   ""  
2025ww33   assigned
2025ww34   transferred
... 
2026ww01    root caused
.. 
2026ww52    implementd
.. 
2027ww01    newlyclosed
....
this_week   closed

data strucutre of the output of 2nd step:
{
    "status_in_ww": [
                        {"ww": "2025ww32", "id_1": "new", "id_2": "assigned", .... "id_n": "new"}
                        {"ww": "2025ww33", "id_1": "transferred", "id_2": "root_caused", .... "id_n": "rejected"}
                        ........
                    ]
}

'''


class ReporterNtrri(BaseReporter): 
 
    def __init__(self):
        super().__init__()  # 如果基类有初始化，建议调用
        self.description = "Diagram of debugging phase " 
        self.sighting_field_list=["exposure", "status", "status_reason", "updated_date", "id","rev", "report_type"]

    def generate(self, sighting_list, start_date=None, **kwargs) -> Dict[str, List[List[Any]]]:
        self.sightings = sighting_list
        result_table = []
        all_timelines = {}
        print(f"Diagram Ntrri start to run")


        # 设置线程池大小，根据CPU/IO情况调整，通常IO密集型可以多一些线程
        with ThreadPoolExecutor(max_workers=10) as executor:
            # 提交所有任务
            futures = [executor.submit(self.fetch_and_build, s) for s in self.sightings]
            # 等待完成并收集结果
            for future in as_completed(futures):
                sighting_id, timeline = future.result()
                if sighting_id is not None:
                    all_timelines[sighting_id] = timeline

        '''
        for s in self.sightings:
            o_hsd_conn = HSDConnection()
            o_hsd_conn.fetch_data(sighting_id=s, sighting_field_list=self.sighting_field_list, fetch_history=True )

            history_data = o_hsd_conn.get_sighting_history()["data"]

            all_timelines[s]  = self.build_sighting_timeline(history_data) #history_data is a list
        '''
        # print(f"generated all timelines {all_timelines}")

        aggr = self.aggregate_sightings(all_timelines)
        print(f"aggregated all timelines {aggr}")

        self.plot_stacked_bar(aggr[self.description])
        #self.plot_with_trendline(aggr[self.description])



    def fetch_and_build(self, sighting):
        o_hsd_conn = HSDConnection()
        o_hsd_conn.fetch_data(
            sighting_id=sighting, 
            sighting_field_list=self.sighting_field_list, 
            fetch_history=True
        )
        history_data = o_hsd_conn.get_sighting_history()["data"]
        
        #print(f" repot_type of sighting  {sighting}:  {temp_json }, report_type: {repot_type_str} ")

        if ( o_hsd_conn.get_sighting_field_value("report_type") == "sighting"): 
            return sighting, self.build_sighting_timeline(history_data)
        else:
            # print(f"report type is not sighting, skipped")
            return None, None



    def append_and_update_prev(self, all_weeks, ww, exposure, status, status_reason, rule1_value,rule2_value, prev_dict): 
        #this fucntion is the real append to for the rev entry.
        all_weeks.append({
            "ww": ww,
            "status": status,
            "status_reason":status_reason,
            "exposure": exposure,
            "rule1": rule1_value ,
            "rule2": rule2_value
        })

        # 更新 prev_dict
        prev_dict["ww"] = ww
        prev_dict["status"] = status
        prev_dict["status_reason"] = status_reason
        prev_dict["exposure"] = exposure
        prev_dict["rule1_value"] = rule1_value
        prev_dict["rule2_value"] = rule2_value   

    def fill_missing_weeks(self, all_weeks, mw,  prev_dict): 
        #this fucntion is the real append to for the rev entry.
        all_weeks.append({
            "ww": mw,
            "status": prev_dict["status"],
            "status_reason":prev_dict ["status_reason"],
            "exposure":prev_dict ["exposure"],
            "rule1": prev_dict["rule1_value"] ,
            "rule2": prev_dict["rule2_value"]
        })

        # 更新 prev_dict
        prev_dict["ww"] = mw

    # Step 1.0 → Step 1.1 : 每个 sighting 的时间线补齐
    def build_sighting_timeline(self, history_data, start_ww="2025ww34", end_ww="2025ww37") -> List:
        """
        history_data: 一个 sighting 的历史记录 (list of dict, 按rev升序)
        输出: list of dict, 每周一条记录 (ww, status, exposure, rule1, rule2)
        """
        # 按 rev 排序
        history_data = sorted(history_data, key=lambda x: int(x["rev"])) #default rev1 is the 1st , rev n is the last, otherwise reverse = True


        # print(f"sorted history data   is: {history_data}")
        # 建立完整时间线
        all_weeks = []
        total_versions_count = len(history_data)
        prev_dict = {}
        prev_dict["ww"] = ""
        prev_dict["status"] = ""
        prev_dict["status_reason"] = ""
        prev_dict["exposure"] = ""
        prev_dict["rule1_value"] = ""
        prev_dict["rule2_value"] = ""
        for i, rec in enumerate(history_data):
            ww = u.date_to_workweek(rec.get("updated_date"))
            
            exposure = rec.get("bug.exposure", "").lower()
            current_status = rec.get("status", "").lower()
            current_status_reason = rec.get("status_reason", "").lower()
            
            if ("critical" in exposure or "high" in exposure ): 
                    rule1_value= "C_H"
            elif ("medium" in exposure):  
                    rule1_value= "M"
            else:
                    rule1_value= "L"

            rule2_value = "assigned" if (current_status == PlatfStatus.open and current_status_reason != PlatfStatusReason.transferred and current_status_reason !=PlatfStatusReason.root_caused)  \
                           else "transferred" if (current_status == PlatfStatus.open and current_status_reason == PlatfStatusReason.transferred)  \
                           else "root_caused" if (current_status == PlatfStatus.open and current_status_reason == PlatfStatusReason.root_caused) \
                           else "implemented" if (current_status == PlatfStatus.implemented) \
                           else  "closed"
            # print(f"ww {ww}, and prev week {prev_dict['ww']}, history-data len is {len(history_data)}, i = {i}")
            # 补齐中间的 workweek and append
            # 如果不是第一个记录，补齐前一个 ww 到当前 ww 之间的周
            if (i== 0 ):  #first record
                missing_weeks = u.get_missing_workweeks(ww, "")
                for mw in missing_weeks:
                    self.fill_missing_weeks(all_weeks, mw, prev_dict)
                
            elif i > 0:
                if (prev_dict["ww"] != ww):
                    missing_weeks = u.get_missing_workweeks(ww, prev_dict["ww"])
                    for mw in missing_weeks:
                        self.fill_missing_weeks(all_weeks, mw, prev_dict)
        
            # append 当前记录        , once appended, the prev_* should follow
            if (i + 1)< total_versions_count:  #not the last one
                next_ww = u.date_to_workweek(history_data[i+1].get("updated_date"))
                # print(f"next_ww {next_ww}")
                if( next_ww == ww):
                    pass
                else:
                    self.append_and_update_prev(all_weeks, ww, exposure, current_status, current_status_reason, rule1_value, rule2_value, prev_dict)
            else:            # the last one, must append
                self.append_and_update_prev(all_weeks, ww, exposure, current_status, current_status_reason, rule1_value, rule2_value, prev_dict)

        #append to the today's ww. 
        # 今天的时间（只取到秒）
        this_ww = u.date_to_workweek(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        missing_weeks = u.get_missing_workweeks(this_ww, prev_dict["ww"])

        for mw in missing_weeks:
            self.fill_missing_weeks(all_weeks, mw, prev_dict)
        #last thing, to append this week's because the mw is always ( )
        if this_ww == prev_dict["ww"]:  # last rev is right in this week of today, no need to fill anything. 
            pass
        else:  # this week is 1 week later than last rev, so fill it.  In our algorithm aobve, only 1 week later can happen
            self.fill_missing_weeks(all_weeks, this_ww, prev_dict)
            

        df = pd.DataFrame(all_weeks)
        min_ww, max_ww = df["ww"].min(), df["ww"].max()
        # print(f"all timelines: {all_weeks}")
        return all_weeks


    # Step 2.0: 聚合成统计表
    def aggregate_sightings(self, all_timelines):
        """
        输入: 所有 sighting 的时间线
        输出: 聚合表 [{ww, rule1, rule2, ids, count}]
        """
        agg = defaultdict(lambda: {"ids": []})
        for sid, timeline in all_timelines.items():
            for rec in timeline:
                key = (rec["ww"], rec["rule1"], rec["rule2"])
                agg[key]["ids"].append(sid)
        result_data = []
        for (ww, r1, r2), val in agg.items():
            result_data.append({"ww": ww, "rule1": r1, "rule2": r2,
                        "ids": val["ids"], "count": len(val["ids"])})
        result_data.sort(key=lambda x: x["ww"])
        return {self.description: result_data }


    def lighten_color(self, color, amount=0.5):
        """
        color: hex string 或 matplotlib color
        amount: 0-1，越大越亮
        """
        c = mcolors.to_rgb(color)
        c = [1 - (1-x)*(1-amount) for x in c]
        return c

    # Step 2.1: 绘制堆叠柱状图
    def plot_stacked_bar(self, agg_data):
        df = pd.DataFrame(agg_data)
        try:
            df.to_csv("stacked_data.csv", index=False)
        except PermissionError as e:
            print(f"⚠️ can't save stacked_data.csv, skip the saving, error: {e}")

        if df.empty or "ww" not in df.columns:
            print("No data to plot.")
            return  # 直接返回，不绘图

        # 按 rule1 拆成 C_H 和 M
        weeks = sorted(df["ww"].unique())
        status_order = ["assigned", "transferred", "root_caused", "implemented"]
        rule1_list = sorted(df["rule1"].unique())  # 自动取 agg_data 中所有 rule1
        '''
        base_colors = {
            "assigned": "#1f77b4",        # 蓝
            "transferred": "#ff7f0e",     # 橙
            "root_caused": "#90ee90",     # 深绿
            "implemented": "#006400"      # 浅绿
        }
        color_map = {}
        for idx, rule in enumerate(rule1_list):
            color_map[rule] = {}
            for status in status_order:
                if status in ["root_caused", "implemented"]:
                    # 深浅区分：rule index 偶数用深色，奇数用浅色
                    if idx % 2 == 0:
                        color_map[rule][status] = base_colors[status]      # 原色
                    else:
                        color_map[rule][status] = self.lighten_color(base_colors[status], 0.5)  # 调浅
                else:
                    color_map[rule][status] = base_colors[status]

        '''
        fig, ax = plt.subplots(figsize=(12, 6))
        bar_width = 0.35
        x = range(len(weeks))

        for idx, rule1 in enumerate(["C_H", "M"]):
            bottom = [0] * len(weeks)
            for status in status_order:
                vals = []
                for ww in weeks:
                    row = df[(df["ww"] == ww) & (df["rule1"] == rule1) & (df["rule2"] == status)]
                    vals.append(row["count"].sum() if not row.empty else 0)
                bars = ax.bar([i + idx * bar_width for i in x], vals, bar_width, bottom=bottom, label=f"{rule1}-{status}")

                # 在每个小柱上显示数量
                for bar, val, btm in zip(bars, vals, bottom):
                    if val > 0:
                        ax.text(
                            bar.get_x() + bar.get_width()/2, 
                            btm + val/2,  # 在堆叠柱中间
                            str(val), 
                            ha='center', 
                            va='center', 
                            fontsize=9, 
                            color='white'
                        )
                bottom = [b + v for b, v in zip(bottom, vals)]

        valid_status = ["assigned", "transferred", "root_caused", "implemented"]
        def top_counts(rule1):
            return [df[(df["ww"] == ww) & (df["rule1"] == rule1) &(df["rule2"].isin(valid_status))  ]["count"].sum() for ww in weeks]

        ch_top = top_counts("C_H")
        m_top = top_counts("M")

        # 注意折线的 x 坐标要和柱子中心对齐
        ch_x = [i + bar_width/2 for i in x]  # C_H线在左柱中心
        m_x = [i + 1.5*bar_width for i in x]  # M线在右柱中心

        ax.plot(ch_x, ch_top, "o-", color="red", label="C_H top")
        ax.plot(m_x, m_top, "o-", color="blue", label="M top")

        # 在折线每个点上写数量
        for xi, yi in zip(ch_x, ch_top):
            if yi > 0:
                ax.text(xi, yi + 0.1, str(yi), ha='center', va='bottom', fontsize=9, color='red')
        for xi, yi in zip(m_x, m_top):
            if yi > 0:
                ax.text(xi, yi + 0.1, str(yi), ha='center', va='bottom', fontsize=9, color='blue')

        ax.set_xticks([i + bar_width/2 for i in x])
        ax.set_xticklabels(weeks, rotation=45)
        ax.set_ylabel("Sighting Count")
        ax.legend()
        plt.tight_layout()
        plt.show()

    # Step 3: 连接顶点 (平滑线)
    def plot_with_trendline(self, agg_data):
        df = pd.DataFrame(agg_data)
        weeks = sorted(df["ww"].unique())

        def top_counts(rule1):
            return [
                df[(df["ww"] == ww) & (df["rule1"] == rule1)]["count"].sum()
                for ww in weeks
            ]

        ch_top = top_counts("C_H")
        m_top = top_counts("M")

        plt.plot(weeks, ch_top, "o-", label="C_H top")
        plt.plot(weeks, m_top, "o-", label="M top")
        plt.xticks(rotation=45)
        plt.legend()
        plt.show()