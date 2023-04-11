# turing-smart-screen-python - a Python system monitor and library for 3.5" USB-C displays like Turing Smart Screen or XuanFang
# https://github.com/mathoudebine/turing-smart-screen-python/

# Copyright (C) 2021-2023  Matthieu Houdebine (mathoudebine)
# Copyright (C) 2022-2023  Rollbacke
# Copyright (C) 2022-2023  Ebag333
# Copyright (C) 2022-2023  w1ld3r
# Copyright (C) 2022-2023  Charles Ferguson (gerph)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import datetime
import locale
import math
import os
import platform
import sys
import copy

import babel.dates
from psutil._common import bytes2human

import library.config as config
from library.display import display
from library.log import logger

#Class to allow diferent colors for objects based on value and MIN, MED, MAX
class ProgressBarColors:
    __low: tuple[float, tuple[int, int, int]] = None
    __med: tuple[float, tuple[int, int, int]] = None
    __high: tuple[float, tuple[int, int, int]] = None
    
    def __init__(self, 
                 low: tuple[float, tuple[int, int, int]] = (0, (0, 0, 0)),
                 med: tuple[float, tuple[int, int, int]] = None,
                 high: tuple[float, tuple[int, int, int]] = None ):
        self.__low = low
        
        #In case the MED is defined and greater then MIN
        if med is not None and (isinstance(med[0], float) or isinstance(med[0], int)) and self.__low[0] < med[0]:
            self.__med = med
        
        #In case the MAX is defined and greater then MED
        #and cannot have MED without MED
        if self.__med is not None and high is not None and (isinstance(high[0], float) or isinstance(high[0], int)) and self.__med[0] < high[0]:
            self.__high = high
    
    #Obtain color based on value
    def getColor(self, value: float ):
        #In case there is no MED
        if self.__med is None:
            return self.__low[1]
        
        #if the value is smaller then MED then it is MIN
        if value < self.__med[0]:
            return self.__low[1]
            
        #In case there is no MAX then it is MED
        if self.__high is None:
            return self.__med[1]
        
        #if the value is smaller then MAX then it is MED
        if value < self.__high[0]:
            return self.__med[1]
            
        #otherwise it is MAX
        return self.__high[1]

ETH_CARD = config.CONFIG_DATA["config"]["ETH"]
WLO_CARD = config.CONFIG_DATA["config"]["WLO"]
HW_SENSORS = config.CONFIG_DATA["config"]["HW_SENSORS"]

if HW_SENSORS == "PYTHON":
    import library.sensors.sensors_python as sensors
elif HW_SENSORS == "LHM":
    if platform.system() == 'Windows':
        import library.sensors.sensors_librehardwaremonitor as sensors
    else:
        logger.error("LibreHardwareMonitor integration is only available on Windows")
        try:
            sys.exit(0)
        except:
            os._exit(0)
elif HW_SENSORS == "STUB":
    logger.warning("Stub sensors, not real HW sensors")
    import library.sensors.sensors_stub_random as sensors
elif HW_SENSORS == "STATIC":
    logger.warning("Stub sensors, not real HW sensors")
    import library.sensors.sensors_stub_static as sensors
elif HW_SENSORS == "AUTO":
    if platform.system() == 'Windows':
        import library.sensors.sensors_librehardwaremonitor as sensors
    else:
        import library.sensors.sensors_python as sensors
else:
    logger.error("Unsupported SENSORS value in config.yaml")
    try:
        sys.exit(0)
    except:
        os._exit(0)


def get_full_path(path, name):
    if name:
        return path + name
    else:
        return None


class CPU:
    @staticmethod
    def percentage():
        cpu_percentage = sensors.Cpu.percentage(
            interval=config.THEME_DATA['STATS']['CPU']['PERCENTAGE'].get("INTERVAL", None))
        # logger.debug(f"CPU Percentage: {cpu_percentage}")
        
        cpu_percentage_text = f"{int(cpu_percentage):>3}"
            
        GUI.show(hw = 'CPU', hw_type = 'PERCENTAGE', value = cpu_percentage, value_text = cpu_percentage_text, unit = '%' )

    @staticmethod
    def frequency():
        cpu_real_freq = sensors.Cpu.frequency() / 1000
        cpu_freq = f'{cpu_real_freq:.2f}'
        GUI.show(hw = 'CPU', hw_type = 'FREQUENCY', value = cpu_real_freq, value_text = cpu_freq, unit = ' GHz' )
        
        #Frequency per core group defined in the theme - MAX 10 groups
        if cores_config := config.THEME_DATA['STATS']['CPU']['FREQUENCY'].get('CORES',False):  
            #Start at group 0
            groupid = 0
            
            #go to max of 10 groups
            while groupid < 10:
                #create group name
                gname = 'C' + str(groupid)
                
                #check if it is defined in the theme
                if cores_configGroup := cores_config.get(gname, False):
                    #validate that there is a core list
                    if core_list := cores_configGroup.get("CORE_LIST", False):
                        #convert core list to tuple
                        if isinstance(core_list, str):
                            core_list = tuple(map(int, core_list.split(', ')))
                        
                        #ontain mean of the cpu group
                        cpu_real_freq = sensors.Cpu.frequencyCores(core_list) / 1000
                        cpu_freq = f'{cpu_real_freq:.2f}'
                        GUI.show(hw = 'CPU', hw_type = 'FREQUENCY', hw_subtype = 'CORES', hw_subsubtype = gname, value = cpu_real_freq, value_text = cpu_freq, unit = ' GHz' )
                
                groupid = groupid + 1
            
    @staticmethod
    def load():
        cpu_load = sensors.Cpu.load()
        # logger.debug(f"CPU Load: ({cpu_load[0]},{cpu_load[1]},{cpu_load[2]})")
        
        cpu_load_one = f"{int(cpu_load[0]):>3}"
        GUI.show(hw = 'CPU', hw_type = 'LOAD', hw_subtype = 'ONE', value = cpu_load_one, value_text = cpu_load_one, unit = '%' )
        
        
        cpu_load_five = f"{int(cpu_load[1]):>3}"
        GUI.show(hw = 'CPU', hw_type = 'LOAD', hw_subtype = 'FIVE', value = cpu_load_five, value_text = cpu_load_five, unit = '%' )
        
        cpu_load_fifteen = f"{int(cpu_load[2]):>3}"
        GUI.show(hw = 'CPU', hw_type = 'LOAD', hw_subtype = 'FIFTEEN', value = cpu_load_fifteen, value_text = cpu_load_fifteen, unit = '%' )

    @staticmethod
    def is_temperature_available():
        return sensors.Cpu.is_temperature_available()

    @staticmethod
    def temperature():
        cpu_temp_value = sensors.Cpu.temperature()
        cpu_temp = f"{int(cpu_temp_value):>3}"
        GUI.show(hw = 'CPU', hw_type = 'TEMPERATURE', value = cpu_temp_value, value_text = cpu_temp, unit = '°C' )
        
        #Temperature per core group defined in the theme - MAX 10 groups
        if cores_config := config.THEME_DATA['STATS']['CPU']['TEMPERATURE'].get('CORES',False):  
            #Start at group 0
            groupid = 0
            
            #go to max of 10 groups
            while groupid < 10:
                #create group name
                gname = 'C' + str(groupid)
                
                #check if it is defined in the theme
                if cores_configGroup := cores_config.get(gname, False):
                    #validate that there is a core list
                    if core_list := cores_configGroup.get("CORE_LIST", False):
                        #convert core list to tuple
                        if isinstance(core_list, str):
                            core_list = tuple(map(int, core_list.split(', ')))
                        
                        #ontain mean of the cpu group
                        cpu_temp_value = sensors.Cpu.temperatureCores(core_list)
                        if cpu_temp_value != math.nan:
                            cpu_temp = f"{int(cpu_temp_value):>3}"
                            GUI.show(hw = 'CPU', hw_type = 'TEMPERATURE', hw_subtype = 'CORES', hw_subsubtype = gname, value = cpu_temp_value, value_text = cpu_temp, unit = '°C' )
                
                groupid = groupid + 1


def display_gpu_stats(load, memory_percentage, memory_used_mb, temperature):
    if math.isnan(load):
        logger.warning("Your GPU load is not supported yet")
    else:
        load_text = f"{int(load):>3}"
        GUI.show(hw = 'GPU', hw_type = 'PERCENTAGE', value = int(load), value_text = load_text, unit = '%' )
    
    if math.isnan(memory_percentage):
        logger.warning("Your GPU memory relative usage (%) is not supported yet")
        logger.warning("Your GPU memory absolute usage (M) is not supported yet")
    else:
        mem_used_text = f"{int(memory_used_mb):>5}"
        GUI.show(hw = 'GPU', hw_type = 'MEMORY', value = int(memory_percentage), value_text = mem_used_text, unit = ' M' )
            
    if math.isnan(temperature):
        logger.warning("Your GPU temperature is not supported yet")
    else:
        temp_text = f"{int(temperature):>3}"
        GUI.show(hw = 'GPU', hw_type = 'TEMPERATURE', value = temperature, value_text = temp_text, unit = '°C' )


class Gpu:
    @staticmethod
    def stats():
        load, memory_percentage, memory_used_mb, temperature = sensors.Gpu.stats()
        display_gpu_stats(load, memory_percentage, memory_used_mb, temperature)

    @staticmethod
    def is_available():
        return sensors.Gpu.is_available()


class Memory:
    @staticmethod
    def stats():
        #backwards compatible
        swap_percent = sensors.Memory.swap_percent()
        GUI.show(hw = 'MEMORY', hw_type = 'SWAP', value = int(swap_percent), value_text = str(int(swap_percent)), unit = '%' )
        
        virtual_percent = sensors.Memory.virtual_percent()
        GUI.show(hw = 'MEMORY', hw_type = 'VIRTUAL', value = int(virtual_percent), value_text = str(int(virtual_percent)), unit = '%' )
        
        #for backwards compatibility allow to use USED as USED->TEXT
        if config.THEME_DATA['STATS']['MEMORY']['VIRTUAL'].get('USED',False) and config.THEME_DATA['STATS']['MEMORY']['VIRTUAL']['USED'].get('TEXT',False) == False:
            config.THEME_DATA['STATS']['MEMORY']['VIRTUAL']['USED']['TEXT'] = copy.copy(config.THEME_DATA['STATS']['MEMORY']['VIRTUAL']['USED'])
            
        #for backwards compatibility allow to use FREE as FREE->TEXT
        if config.THEME_DATA['STATS']['MEMORY']['VIRTUAL'].get('FREE',False) and config.THEME_DATA['STATS']['MEMORY']['VIRTUAL']['FREE'].get('TEXT',False) == False:
            config.THEME_DATA['STATS']['MEMORY']['VIRTUAL']['FREE']['TEXT'] = copy.copy(config.THEME_DATA['STATS']['MEMORY']['VIRTUAL']['FREE'])
        
        #SWAP
        swap_percent = sensors.Memory.swap_percent()
        GUI.show(hw = 'MEMORY', hw_type = 'SWAP', hw_subtype = 'PERCENT', value = int(swap_percent), value_text = str(int(swap_percent)), unit = '%' )
        
        swap_used = sensors.Memory.swap_used()
        swap_used_text = f"{int(swap_used / 1000000):>5}"
        GUI.show(hw = 'MEMORY', hw_type = 'SWAP', hw_subtype = 'USED', value = swap_used, value_text = swap_used_text, unit = ' M' )
        
        swap_free = sensors.Memory.swap_free()
        swap_free_text = f"{int(swap_free / 1000000):>5}"
        GUI.show(hw = 'MEMORY', hw_type = 'SWAP', hw_subtype = 'FREE', value = swap_free, value_text = swap_free_text, unit = ' M' )


        #VIRTUAL
        virtual_percent = sensors.Memory.virtual_percent()
        GUI.show(hw = 'MEMORY', hw_type = 'VIRTUAL', hw_subtype = 'PERCENT', value = int(virtual_percent), value_text = str(int(virtual_percent)), unit = '%' )
        
        virtual_used = sensors.Memory.virtual_used()
        virtual_used_text = f"{int(virtual_used / 1000000):>5}"
        GUI.show(hw = 'MEMORY', hw_type = 'VIRTUAL', hw_subtype = 'USED', value = virtual_used, value_text = virtual_used_text, unit = ' M' )
        
        virtual_free = sensors.Memory.virtual_free()
        virtual_free_text = f"{int(virtual_free / 1000000):>5}"
        GUI.show(hw = 'MEMORY', hw_type = 'VIRTUAL', hw_subtype = 'FREE', value = virtual_free, value_text = virtual_free_text, unit = ' M' )


class Disk:
    @staticmethod
    def stats():
        used = sensors.Disk.disk_used()
        used_text = f"{int(used / 1000000000):>5}"
        used_perc = int(sensors.Disk.disk_usage_percent())
        
        free = sensors.Disk.disk_free()
        free_text = f"{int(free / 1000000000):>5}"
        
        total_text = f"{int((free + used) / 1000000000):>5}"
        
        #Used
        GUI.show(hw = 'DISK', hw_type = 'USED', value = used_perc, value_text = used_text, unit = ' G' )
        
        #Free
        GUI.show(hw = 'DISK', hw_type = 'FREE', value = used_perc, value_text = free_text, unit = ' G' )
        
        #Total
        GUI.show(hw = 'DISK', hw_type = 'TOTAL', value = used_perc, value_text = total_text, unit = ' G' )
        

class Net:
    @staticmethod
    def stats():
        #WIFI
        interval = config.THEME_DATA['STATS']['CPU']['PERCENTAGE'].get("INTERVAL", None)
        upload_wlo, uploaded_wlo, download_wlo, downloaded_wlo = sensors.Net.stats(WLO_CARD, interval)
        
        upload_wlo_text = f"{bytes2human(upload_wlo, '%(value).1f %(symbol)s/s')}"
        upload_wlo_text_f = f"{upload_wlo_text:>10}"
        GUI.show(hw = 'NET', hw_type = 'WLO', hw_subtype = 'UPLOAD', value_text = upload_wlo_text_f, unit = '' )
        
        uploaded_wlo_text = f"{bytes2human(uploaded_wlo)}"
        uploaded_wlo_text_f = f"{uploaded_wlo_text:>6}"
        GUI.show(hw = 'NET', hw_type = 'WLO', hw_subtype = 'UPLOADED', value_text = uploaded_wlo_text_f, unit = '' )
            
        download_wlo_text = f"{bytes2human(download_wlo, '%(value).1f %(symbol)s/s')}"
        download_wlo_text_f = f"{download_wlo_text:>10}"
        GUI.show(hw = 'NET', hw_type = 'WLO', hw_subtype = 'DOWNLOAD', value_text = download_wlo_text_f, unit = '' )
        
        downloaded_wlo_text = f"{bytes2human(downloaded_wlo)}"
        downloaded_wlo_text_f = f"{downloaded_wlo_text:>6}"
        GUI.show(hw = 'NET', hw_type = 'WLO', hw_subtype = 'DOWNLOADED', value_text = downloaded_wlo_text_f, unit = '' )

        #ETH
        upload_eth, uploaded_eth, download_eth, downloaded_eth = sensors.Net.stats(ETH_CARD, interval)
        
        upload_eth_text = f"{bytes2human(upload_eth, '%(value).1f %(symbol)s/s')}"
        upload_eth_text_f = f"{upload_eth_text:>10}"
        GUI.show(hw = 'NET', hw_type = 'ETH', hw_subtype = 'UPLOAD', value_text = upload_eth_text_f, unit = '' )
        
        uploaded_eth_text = f"{bytes2human(uploaded_eth)}"
        uploaded_eth_text_f = f"{uploaded_eth_text:>6}"
        GUI.show(hw = 'NET', hw_type = 'ETH', hw_subtype = 'UPLOADED', value_text = uploaded_eth_text_f, unit = '' )
        
        download_eth_text = f"{bytes2human(download_eth, '%(value).1f %(symbol)s/s')}"
        download_eth_text_f = f"{download_eth_text:>10}"
        GUI.show(hw = 'NET', hw_type = 'ETH', hw_subtype = 'DOWNLOAD', value_text = download_eth_text_f, unit = '' )
        
        downloaded_eth_text = f"{bytes2human(downloaded_eth)}"
        downloaded_eth_text_f = f"{downloaded_eth_text:>6}"
        GUI.show(hw = 'NET', hw_type = 'ETH', hw_subtype = 'DOWNLOADED', value_text = downloaded_eth_text_f, unit = '' )


class Date:
    @staticmethod
    def stats():
        date_now = datetime.datetime.now()

        if platform.system() == "Windows":
            # Windows does not have LC_TIME environment variable, use deprecated getdefaultlocale() that returns language code following RFC 1766
            lc_time = locale.getdefaultlocale()[0]
        else:
            lc_time = babel.dates.LC_TIME
            
        date_format = config.THEME_DATA['STATS']['DATE']['DAY']['TEXT'].get("FORMAT", 'medium')
        datenow = f"{babel.dates.format_date(date_now, format=date_format, locale=lc_time)}"
        GUI.show(hw = 'DATE', hw_type = 'DAY', value_text = datenow, unit = '' )

        time_format = config.THEME_DATA['STATS']['DATE']['HOUR']['TEXT'].get("FORMAT", 'medium')
        timenow = f"{babel.dates.format_time(date_now, format=time_format, locale=lc_time)}"
        GUI.show(hw = 'DATE', hw_type = 'HOUR', value_text = timenow, unit = '' )


class GUI:
    @staticmethod
    def show(hw: str, hw_type: str, hw_subtype: str = None, hw_subsubtype: str = None, value = None, value_text: str = '', unit: str = '' ):
            
        hw_config = config.THEME_DATA['STATS'][hw][hw_type]
        
        #Obtain sub type of HW - Example HW = NET | HW_TYPE = WLO | HW_SUBTYPE = UPLOAD
        if hw_subtype is not None:
            if hw_config.get(hw_subtype, False):
                hw_config = hw_config[hw_subtype]
            else:
                return
        
        #Obtain sub type of the sub type of HW - Example HW = CPU | HW_TYPE = FREQUENCY | HW_SUBTYPE = CORES | HW_SUBSUBTYPE = C1
        if hw_subsubtype is not None:
            if hw_config.get(hw_subsubtype, False):
                hw_config = hw_config[hw_subsubtype]
            else:
                return

        #Graphs
        #Bar Graph
        if graph_config := hw_config.get("GRAPH", False):
            
            if graph_config.get("SHOW", False):
                if value is None:
                    return
                                 
                if graph_config.get("TEXT", False):
                    textGraph = value_text
                    
                    if graph_config.get("SHOW_UNIT", True):
                        textGraph += unit
                else:
                    textGraph = ''
                    
                #Graph Color
                back_color = GUI.createProgressColor(graph_config.get("BAR_COLOR", None))
                
                #Graph Text Color                                
                text_color = GUI.createProgressColor(graph_config.get("FONT_COLOR", None))
                    
                display.lcd.DisplayProgressBar(
                    x=graph_config.get("X", 0),
                    y=graph_config.get("Y", 0),
                    width=graph_config.get("WIDTH", 0),
                    height=graph_config.get("HEIGHT", 0),
                    value=int(value),
                    font=graph_config.get("FONT", "roboto-mono/RobotoMono-Regular.ttf"),
                    font_size=graph_config.get("FONT_SIZE", 10),
                    stroke_width=graph_config.get("STROKE_WIDTH", 10),
                    font_color=text_color.getColor(int(value)),
                    text=textGraph,
                    min_value=graph_config.get("MIN_VALUE", 0),
                    max_value=graph_config.get("MAX_VALUE", 100),
                    bar_color=back_color.getColor(int(value)),
                    bar_outline=graph_config.get("BAR_OUTLINE", False),
                    background_color=graph_config.get("BACKGROUND_COLOR", (255, 255, 255)),
                    background_image=get_full_path(config.THEME_DATA['PATH'],
                                                   graph_config.get("BACKGROUND_IMAGE", None))
                )
                
        #Circular Graph
        if graph_circle_config := hw_config.get("GRAPH_CIRC", False):
            
            if graph_circle_config.get("SHOW", False):
                if value is None:
                    return
                    
                if graph_circle_config.get("TEXT", False):
                    textGraph = value_text
                    
                    if graph_circle_config.get("SHOW_UNIT", True):
                        textGraph += unit
                else:
                    textGraph = ''
                    
                #Graph Color
                back_color = GUI.createProgressColor(graph_circle_config.get("BAR_COLOR", None))
                
                #Graph Text Color                                
                text_color = GUI.createProgressColor(graph_circle_config.get("FONT_COLOR", None))
                    
                display.lcd.DisplayRoundProgressBar(
                    x=graph_circle_config.get("X", 0),
                    y=graph_circle_config.get("Y", 0),
                    r=graph_circle_config.get("R", 0),
                    min_value=graph_circle_config.get("MIN_VALUE", 0),
                    max_value=graph_circle_config.get("MAX_VALUE", 100),
                    thick=graph_circle_config.get("THICKNESS", 0),
                    value=int(value),
                    start_angle=graph_circle_config.get("START_ANGLE", 0),
                    font=graph_circle_config.get("FONT", "roboto-mono/RobotoMono-Regular.ttf"),
                    font_size=graph_circle_config.get("FONT_SIZE", 10),
                    stroke_width=graph_circle_config.get("STROKE_WIDTH", 0),
                    font_color=text_color.getColor(int(value)),
                    text=textGraph,
                    bar_color=back_color.getColor(int(value)),
                    bar_outline=graph_circle_config.get("BAR_OUTLINE", 0),
                    background_color=graph_circle_config.get("BACKGROUND_COLOR", (255, 255, 255)),
                    background_image=get_full_path(config.THEME_DATA['PATH'],
                                                   graph_circle_config.get("BACKGROUND_IMAGE", None))
                )
        
        #Texts
        if text_config := hw_config.get("TEXT", False):
        
            if text_config.get("SHOW", False):
                
                if value_text != '':                
                    load_text = str(value_text)
                else:
                    load_text = str(value)
                if text_config.get("SHOW_UNIT", False):
                    load_text += unit
                    
                #Text Color                                
                text_color = GUI.createProgressColor(text_config.get("FONT_COLOR", None))
                
                if value is None:
                    text_color = text_color.getColor(0)
                else:
                    text_color = text_color.getColor(value)

                display.lcd.DisplayText(
                    text=load_text,
                    x=text_config.get("X", 0),
                    y=text_config.get("Y", 0),
                    font=text_config.get("FONT", "roboto-mono/RobotoMono-Regular.ttf"),
                    font_size=text_config.get("FONT_SIZE", 10),
                    font_color=text_color,
                    background_color=text_config.get("BACKGROUND_COLOR", (255, 255, 255)),
                    background_image=get_full_path(config.THEME_DATA['PATH'], text_config.get("BACKGROUND_IMAGE", None))
                )
                
        #Percentage Text - for backwards compatibility
        if text_perc_config := hw_config.get("PERCENT_TEXT", False):
        
            if text_perc_config.get("SHOW", False):
                
                load_text = f"{int(value):>3}"
                if text_perc_config.get("SHOW_UNIT", False):
                    load_text += "%"

                #Text Color                                
                text_color = GUI.createProgressColor(text_perc_config.get("FONT_COLOR", None))
                
                if value is None:
                    text_color = text_color.getColor(0)
                else:
                    text_color = text_color.getColor(value)
                
                display.lcd.DisplayText(
                    text=load_text,
                    x=text_perc_config.get("X", 0),
                    y=text_perc_config.get("Y", 0),
                    font=text_perc_config.get("FONT", "roboto-mono/RobotoMono-Regular.ttf"),
                    font_size=text_perc_config.get("FONT_SIZE", 10),
                    font_color=text_color,
                    background_color=text_perc_config.get("BACKGROUND_COLOR", (255, 255, 255)),
                    background_image=get_full_path(config.THEME_DATA['PATH'], text_perc_config.get("BACKGROUND_IMAGE", None))
                )
              
    @staticmethod  
    def createProgressColor(yaml_entry) -> ProgressBarColors:
        #Only one color is defined, backwards compatibility
        if isinstance(yaml_entry, str):
            low_color = (0, tuple(map(int, yaml_entry.split(', '))))
            med_color = None
            high_color = None
        #None is defined, set black
        elif yaml_entry is None or yaml_entry.get("LOW", None) is None:
            low_color = (0, (0, 0, 0))
            med_color = None
            high_color = None
        else:
            #Obtain LOW color, or use default
            low_color = yaml_entry.get("LOW", None)
            low_color_value = low_color.get("VALUE", 0)
            low_color_tuple = low_color.get("COLOR", "0, 0, 0")
            low_color = (low_color_value, tuple(map(int, low_color_tuple.split(', '))))
            
            #In case there is a MED defined, use it
            med_color = yaml_entry.get("MED", None)
            if med_color is not None:
                med_color_value = med_color.get("VALUE", None)
                med_color_tuple = med_color.get("COLOR", "0, 0, 0")
                med_color = (med_color_value, tuple(map(int, med_color_tuple.split(', '))))
            else:
                med_color = None
            
            #In case there is a HIGH defined, use it
            high_color = yaml_entry.get("HIGH", None)
            if high_color is not None:
                high_color_value = high_color.get("VALUE", None)
                high_color_tuple = high_color.get("COLOR", "0, 0, 0")
                high_color = (high_color_value, tuple(map(int, high_color_tuple.split(', '))))
            else:
                high_color = None
            
        #Create Progress Bar Color Class Instance
        return ProgressBarColors(low = low_color, med = med_color, high = high_color)
        