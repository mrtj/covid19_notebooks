import os
import shutil
import logging
import re

import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

class TimeSeriesViz:

    def __init__(self, series, last_modified, fig_folder=None, csv_folder=None, figsize=(16, 10)):
        self.series = series
        self.last_modified = last_modified
        self.figsize = figsize
        self.fig_folder = fig_folder
        self.csv_folder = csv_folder
        self.logger = logging.getLogger()
    
    def diff(self):
        return self.series - self.series.shift()
    
    @staticmethod
    def config_axis(ax=None, figsize=None, title=None, xgrid=True):
        if ax is None:
            fig, ax = plt.subplots(figsize=figsize)
        else:
            fig = plt.gcf()
        ax.yaxis.grid(True, which='major')
        if xgrid:
            ax.xaxis.grid(True, which='major')
        locator = mdates.DayLocator(interval=7)
        ax.xaxis.set_major_locator(locator)
        ax.xaxis.set_minor_locator(mdates.DayLocator(interval=1))
        ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(locator))
        ax.xaxis.set_label_text('')
        if title:
            ax.set_title(title)
        return fig, ax

    def _get_title(self, title):
        full_title = title
        if self.last_modified is not None:
            full_title += f'\n(dati aggiornati: {self.last_modified:%d/%m/%Y %H:%M:%S})'
        return full_title
    
    def _save_fig(self, fig_name):
        series_name = re.sub("\W", '_', self.series.name).lower()
        fn_date = f'{series_name}-{fig_name}-{self.last_modified:%Y%m%d}.png'
        fn_last = f'{series_name}-{fig_name}.png'
        if self.fig_folder is not None:
            fn_date = os.path.join(self.fig_folder, fn_date)
            fn_last = os.path.join(self.fig_folder, fn_last)
        plt.savefig(fn_date)
        shutil.copyfile(fn_date, fn_last)
        self.logger.info(f'Figure saved to {fn_date} and {fn_last}')
        return fn_date, fn_last
        
    def _save_csv(self, df, csv_name):
        series_name = re.sub("\W", '_', self.series.name).lower()
        fn_date = f'{series_name}-{csv_name}-{self.last_modified:%Y%m%d}.csv'
        fn_last = f'{series_name}-{csv_name}.csv'
        if self.csv_folder is not None:
            fn_date = os.path.join(self.csv_folder, fn_date)
            fn_last = os.path.join(self.csv_folder, fn_last)
        df.to_csv(fn_date)
        shutil.copyfile(fn_date, fn_last)
        self.logger.info(f'Data saved to {fn_date} and {fn_last}')
        return fn_date, fn_last
    
    def show_series(self, title, save_fig=False, save_csv=False, figsize=None, ax=None):
        _figsize = figsize or self.figsize
        fig, ax = TimeSeriesViz.config_axis(title=self._get_title(title), figsize=_figsize, ax=ax)
        ax.plot(self.series.index, self.series)
        ax.set_xlim((self.series.index.min(), self.series.index.max()))
        locator = mdates.MonthLocator()
        ax.xaxis.set_major_locator(locator)
        ax.xaxis.set_minor_locator(mdates.DayLocator())
        ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(locator))
        if save_fig:
            self._save_fig('series')
        if save_csv:
            self._save_csv(self.series.to_frame(), 'series')
        return fig, ax

    def show_new(self, title, zero_min=False, window=7, save_fig=False, save_csv=False, figsize=None, ax=None):
        _figsize = figsize or self.figsize
        fig, ax = TimeSeriesViz.config_axis(title=self._get_title(title), xgrid=False, figsize=_figsize, ax=ax)
        diff = self.diff()
        ax.bar(diff.index, diff, align='center', width=1)
        sma = diff.rolling(window, center=True).mean()
        ax.plot(sma.index, sma, color='tab:red', lw=2)
        ax.set_xlim((diff.index.min() + pd.Timedelta(days=.5), diff.index.max() + pd.Timedelta(days=.5)))
        locator = mdates.MonthLocator(interval=1)
        ax.xaxis.set_major_locator(locator)
        ax.xaxis.set_minor_locator(mdates.DayLocator(interval=1))
        ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(locator))
        if zero_min:
            ax.set_ylim((0, None))
        if save_fig:
            self._save_fig('new')
        if save_csv:
            self._save_csv(diff.to_frame(), 'new')
        return fig, ax
        
    def show_growth_factor(self, title, lookback=35, window=3, raw=True, sma=True, smd=False, ema=True, ylim=None, 
                           save_fig=False, save_csv=False, figsize=None, ax=None):
        active_cases = self.series - self.series.shift(lookback)
        growth_factor = active_cases / active_cases.shift()
        _figsize = figsize or self.figsize
        fig, ax = TimeSeriesViz.config_axis(title=self._get_title(title), figsize=_figsize, ax=ax)
        
        gf_sma = growth_factor.rolling(window, center=True).mean()
        gf_sma.name = f'{self.series.name} (SMA {window} giorni)'

        gf_ema = growth_factor.ewm(window).mean()
        gf_ema.name = f'{self.series.name} (EMA {window} giorni)'
        
        gf_smd = growth_factor.rolling(window).median()
        gf_smd.name = f'{self.series.name} (SMD {window} giorni)'

        if raw:
            ax.plot(growth_factor.index, growth_factor, label=growth_factor.name)

        if sma:
            ax.plot(gf_sma.index, gf_sma, label=gf_sma.name, color='tab:red', lw=2)

        if ema:
            ax.plot(gf_ema.index, gf_ema, label=gf_ema.name)
            
        if smd:
            ax.plot(gf_smd.index, gf_smd, label=gf_smd.name)

        ax.axhline(1.0, linestyle='--', linewidth=1, color='r')
        ax.set_xlim((self.series.index.min(), self.series.index.max()))
        locator = mdates.MonthLocator(interval=1)
        ax.xaxis.set_major_locator(locator)
        ax.xaxis.set_minor_locator(mdates.DayLocator(interval=1))
        ax.xaxis.set_major_formatter(mdates.ConciseDateFormatter(locator))
        ax.legend()
        if ylim is not None:
            ax.set_ylim(ylim)
        if save_fig:
            self._save_fig('gf')
        if save_csv:
            df = pd.DataFrame({growth_factor.name: growth_factor, gf_sma.name: gf_sma, gf_ema.name: gf_ema})
            self._save_csv(df, 'gf')
        return fig, ax



class OverviewViz:
    
    def __init__(self, area_name, df, last_modified=None, fig_folder=None, csv_folder=None, figsize=(20, 16)):
        self.area_name = area_name
        self.df = df
        self.figsize = figsize
        self.last_modified = last_modified
        self.fig_folder = fig_folder
        self.logger = logging.getLogger()
        total_series = df['totale_casi'].resample('D').last()
        total_series.name = f'totali {area_name}'
        self.total_viz = TimeSeriesViz(series=total_series, last_modified=None, 
                                       fig_folder=fig_folder, csv_folder=csv_folder)
        deaths_series = df['deceduti'].resample('D').last()
        deaths_series.name = f'deceduti {area_name}'
        self.deaths_viz = TimeSeriesViz(series=deaths_series, last_modified=None, 
                                        fig_folder=fig_folder, csv_folder=csv_folder)
        ti_series = df['terapia_intensiva'].resample('D').last()
        ti_series.name = f'terapia intensiva {area_name}'
        self.ti_viz = TimeSeriesViz(series=ti_series, last_modified=None, 
                                    fig_folder=fig_folder, csv_folder=csv_folder)

    def _save_fig(self, fig_name):
        series_name = re.sub("\W", '_', self.area_name).lower()
        fn_date = f'{series_name}-{fig_name}-{self.last_modified:%Y%m%d}.png'
        fn_last = f'{series_name}-{fig_name}.png'
        if self.fig_folder is not None:
            fn_date = os.path.join(self.fig_folder, fn_date)
            fn_last = os.path.join(self.fig_folder, fn_last)
        plt.savefig(fn_date)
        shutil.copyfile(fn_date, fn_last)
        self.logger.info(f'Figure saved to {fn_date} and {fn_last}')
        return fn_date, fn_last
        
    def show_overview(self, save_fig=False):
        plt.figure(figsize=self.figsize)
        fig_names = ['', 'deceduti', 'in terapia intensiva']
        vizualizers = [self.total_viz, self.deaths_viz, self.ti_viz]
        for idx, (fig_name, viz) in enumerate(zip(fig_names, vizualizers)):
            zero_min = not fig_name in ['in terapia intensiva']
            viz.show_series(title=f'Casi {fig_name}{" " if fig_name else ""}in {self.area_name}', ax=plt.subplot(331 + idx * 3))
            viz.show_new(title=f'Nuovi casi giornalieri {fig_name}{" " if fig_name else ""}in {self.area_name}', 
                         zero_min=zero_min,
                         ax=plt.subplot(332 + idx * 3))
            viz.show_growth_factor(title=f'Tasso di crescita dei casi {fig_name}{" " if fig_name else ""}in {self.area_name}', 
                                   sma=False, ax=plt.subplot(333 + idx * 3), ylim=(0, 2))
        plt.suptitle(f'Situazione COVID-19 in {self.area_name}\n(dati aggiornati: {self.last_modified:%d/%m/%Y %H:%M:%S})',
                    fontsize='x-large', y=0.95)
        plt.subplots_adjust(hspace=0.3)
        if save_fig:
            return self._save_fig('overview')
        return None
