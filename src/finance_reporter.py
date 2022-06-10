from selenium import webdriver
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import discord
from discord.ext import commands,tasks
import time
from PIL import Image
import os
import shutil as sh
from datetime import datetime
from loguru import logger
import yfinance as yf
import emoji
class FininceReporter(commands.Cog):
    def __init__(self,
                client = None,
                maps_dir = 'maps',
                include_moex=True):
        self.spx_duration_dict = {'1d':'',
                '1week':'?t=sec&st=w1',
                '1month':'?t=sec&st=w4',
                '3months':'?t=sec&st=w13',
                '6months':'?t=sec&st=w26',
                '1year':'?t=sec&st=w52'}
        self.moex_duration_dict= {'1d':'/html/body/div[2]/div[2]/span[1]',
                '1week':'/html/body/div[2]/div[2]/span[2]',
                '1months':'/html/body/div[2]/div[2]/span[3]'}
        self.fin_reports_periods=['неделя','месяц','квартал','полугодие','год' ]
        self.yfinance_periods = ['5d','1mo','3mo','6mo','1y']
        self.spx_source = 'finviz.com'
        self.moex_source = 'smart-lab.ru'
        self.map_store_dir = maps_dir
        if os.path.exists(self.map_store_dir):
            sh.rmtree(self.map_store_dir)
        os.mkdir(self.map_store_dir)
        os.mkdir(os.path.join(self.map_store_dir,'s&p500'))
        os.mkdir(os.path.join(self.map_store_dir,'moex'))   
        self.include_moex = include_moex
        self.moex = yf.Ticker("MOEX.ME")
        self.spx =  yf.Ticker("SPY")
        self.client = client
        self.__call__.start()
        logger.debug("FininceReporter is initialized")
    def form_string(self,hist,spy = False):
        start_val = hist['Open'][0]
        end_val = hist['Close'][-1]
        percentage = (end_val-start_val)/start_val*100
        if percentage>=0:
            emoj = emoji.emojize('\U0001F4c8')
        else:
            emoj = emoji.emojize('\U0001F4c9')
        if spy:
            return  ('\nПрирост SPX: %.2f' % percentage) + f'% {emoj}'
        else:
            return ('\nПрирост MoEX: %.2f' % percentage) + f'% {emoj}'

    def get_SPX(self,browser,period = '1d'):
        browser.get('https://finviz.com/map.ashx'+self.spx_duration_dict[period])
        time.sleep(2)
        browser.find_element(By.XPATH,'/html/body/div[2]/div/div/div[1]/div[3]/button[2]').click()
        time.sleep(2)
        img = browser.find_element(By.XPATH,'/html/body/div[9]/div/div/div[2]/div[2]/div/div/div[1]/label/div/textarea').text
        browser.get(img)
        element =  browser.find_element(By.XPATH,'/html/body/div[2]/div/div/a[1]/img')
        location = element.location
        size = element.size
        res_im_path = os.path.join(self.map_store_dir,'s&p500',f"sp500_{period}.png")
        browser.save_screenshot(res_im_path)
        x = location['x']
        y = location['y']
        width = location['x']+size['width']
        height = location['y']+size['height']
        im = Image.open(res_im_path)
        im = im.crop((int(x), int(y), int(width), int(height)))
        im.save(res_im_path)
        return res_im_path
        
    def get_MOEX(self,browser,period = '1d'):
        browser.get('https://smart-lab.ru/q/map/')
        time.sleep(2)
        browser.find_element(By.XPATH,self.moex_duration_dict[period]).click()
        time.sleep(2)
        element =  browser.find_element(By.XPATH,'//*[@id="chart_div_shares"]')
        location = element.location
        size = element.size
        res_im_path = os.path.join(self.map_store_dir,'moex',f"moex_{period}.png")
        browser.save_screenshot(res_im_path)
        # crop image
        x = location['x']
        y = location['y']
        width = location['x']+size['width']
        height = location['y']+size['height']
        im = Image.open(res_im_path)
        im = im.crop((int(x), int(y), int(width), int(height)))
        
        im.save(res_im_path)
        return res_im_path
    
    @tasks.loop(hours =1.0)#hours =1.0)#seconds = 50)
    async def __call__(self):

        fin_channels = [ch for ch in self.client.get_all_channels() if ch.name in self.fin_reports_periods]
        #logger.info(fin_channels)
        if len(fin_channels)==0:
            logger.info('каналы не созданы')
            return
        fin_channel_ids = {period: channel.id for period,channel in zip(list(self.spx_duration_dict.keys())[1:],fin_channels)}
        curr_date = datetime.now()
        #curr_date = datetime.strptime('Jul 1 2005  1:33PM', '%b %d %Y %I:%M%p')
        
        logger.info(f'Today is:{curr_date.strftime("%d.%m.%Y")}')
        if curr_date.hour == 1:#True
            options = Options()
            options.BinaryLocation = "/usr/bin/chromium-browser"
            #browser = webdriver.Chrome(options=options)
            #browser = webdriver.Chro me(ChromeDriverManager().install())
            #browser = webdriver.Edge(service=Service(EdgeChromiumDriverManager().install()))
            opts = webdriver.ChromeOptions()
            opts.add_argument('--no-sandbox')
            opts.add_argument('--disable-setuid-sandbox')
            browser = webdriver.Chrome(options=opts)
            browser.set_window_size(1920,1280)
            if curr_date.weekday() ==0:
                curr_period_spx=list(self.spx_duration_dict.keys())[1]
                curr_period_moex=list(self.moex_duration_dict.keys())[1]
                logger.info(f'запрос на информацию по неделям {curr_period_spx}')
                im1_path =self.get_SPX(browser=browser,period=curr_period_spx)
                im2_path =self.get_MOEX(browser=browser,period=curr_period_moex)
                channel = self.client.get_channel(fin_channel_ids[curr_period_spx])
                str_moex = self.form_string(self.moex.history(period=self.yfinance_periods[0]))
                str_spx = self.form_string(self.spx.history(period=self.yfinance_periods[0]), True)
                
                await channel.send(emoji.emojize('\U0001F4c5')+f" {curr_date.strftime('%d.%m.%Y')}"+str_spx+str_moex,files=[discord.File(im1_path),discord.File(im2_path)])
                logger.info(f'запрос на информацию по неделям выполнен')
            if curr_date.day == 1:
                curr_period_spx=list(self.spx_duration_dict.keys())[2]
                curr_period_moex=list(self.moex_duration_dict.keys())[2]
                logger.info(f'запрос на информацию по месяцам {curr_period_spx}')
                im1_path = self.get_SPX(browser=browser,period=curr_period_spx)
                im2_path = self.get_MOEX(browser=browser,period=curr_period_moex)
                str_moex = self.form_string(self.moex.history(period=self.yfinance_periods[1]))
                str_spx = self.form_string(self.spx.history(period=self.yfinance_periods[1]), True)
                channel = self.client.get_channel(fin_channel_ids[curr_period_spx])
                await channel.send(emoji.emojize('\U0001F4c5')+f" {curr_date.strftime('%d.%m.%Y')}"+str_spx+str_moex,files=[discord.File(im1_path),discord.File(im2_path)])
                logger.info(f'запрос на информацию по месяцам выполнен')
                if curr_date.month == 4 or curr_date.month == 7 or curr_date.month == 10 or curr_date.month == 1:
                    curr_period=list(self.spx_duration_dict.keys())[3]
                    logger.info(f'запрос на информацию по кварталам {curr_period}')
                    im1_path = self.get_SPX(browser=browser,period=curr_period)
                    channel = self.client.get_channel(fin_channel_ids[curr_period])
                    str_moex = self.form_string(self.moex.history(period=self.yfinance_periods[2]))
                    str_spx = self.form_string(self.spx.history(period=self.yfinance_periods[2]), True)
                    await channel.send(emoji.emojize('\U0001F4c5')+f" {curr_date.strftime('%d.%m.%Y')}"+str_spx+str_moex,file=discord.File(im1_path))
                    logger.info(f'запрос на информацию по кварталам выполнен')
                if curr_date.month == 7 or curr_date.month==1:
                    curr_period=list(self.spx_duration_dict.keys())[4]
                    logger.info(f'запрос на информацию по полугодию {curr_period}')
                    im1_path = self.get_SPX(browser=browser,period=curr_period)
                    channel = self.client.get_channel(fin_channel_ids[curr_period])
                    str_moex = self.form_string(self.moex.history(period=self.yfinance_periods[3]))
                    str_spx = self.form_string(self.spx.history(period=self.yfinance_periods[3]), True)
                    await channel.send(emoji.emojize('\U0001F4c5')+f" {curr_date.strftime('%d.%m.%Y')}"+str_spx+str_moex,file=discord.File(im1_path))
                    logger.info('запрос на информацию по полугодию выполнен')
                if curr_date.month == 1:
                    curr_period = list(self.spx_duration_dict.keys())[-1]
                    logger.info(f'запрос на информацию по году {curr_period}')
                    im1_path = self.get_SPX(browser=browser,period=curr_period)
                    channel = self.client.get_channel(fin_channel_ids[curr_period])
                    str_moex = self.form_string(self.moex.history(period=self.yfinance_periods[-1]))
                    str_spx = self.form_string(self.spx.history(period=self.yfinance_periods[-1]), True)
                    await channel.send(emoji.emojize('\U0001F4c5')+f" {curr_date.strftime('%d.%m.%Y')}"+str_spx+str_moex,file=discord.File(im1_path))
                    logger.info('запрос на информацию по году выполнен')
            browser.quit()

    @commands.command()
    async def get_daily(self,ctx: discord.ext.commands.Context,*description ):
        channel = ctx.channel
        if channel.name!='дневные':
            await channel.send('команда работает только в дневном чате',reference=ctx.message)
            time.sleep(5)
            await ctx.channel.purge(limit=2)
            return
        curr_date = datetime.now()
        #webdriver.Edge(service=Service(EdgeChromiumDriverManager(version="92.0.878.0").install()))
        opts = webdriver.ChromeOptions()
        opts.add_argument('--no-sandbox')
        opts.add_argument('--disable-setuid-sandbox')
        browser = webdriver.Chrome(options=opts)
        browser.set_window_size(1920,1280)
        await ctx.channel.purge(limit=2)
        curr_period_spx=list(self.spx_duration_dict.keys())[0]
        curr_period_moex=list(self.moex_duration_dict.keys())[0]
        logger.info(f'запрос на информацию за день {curr_period_spx}')
        im1_path =self.get_SPX(browser=browser,period=curr_period_spx)
        im2_path =self.get_MOEX(browser=browser,period=curr_period_moex)
        str_moex = self.form_string(self.moex.history(period='1d'))
        str_spx = self.form_string(self.spx.history(period='1d'), True)
        
        if len(description)>0:
            await channel.send(emoji.emojize('\U0001F4c5')+f" {curr_date.strftime('%d.%m.%Y')} \n"+' '.join([str(i) for i in description ])+str_moex+str_spx \
                                                        ,files=[discord.File(im1_path),discord.File(im2_path)])#,reference=ctx.message)
        else:
            await channel.send(emoji.emojize('\U0001F4c5')+f" {curr_date.strftime('%d.%m.%Y')}"+str_moex+str_spx,files=[discord.File(im1_path),discord.File(im2_path)],reference=ctx.message)
        logger.info('запрос выполенен')    
        browser.quit()

    @commands.command()
    async def create_fins(self,ctx: discord.ext.commands.Context, overwrite = False):
        channel = ctx.channel
        if channel.name!='general':
            await channel.send('команда работает только в общем чате',reference=ctx.message)
            time.sleep(5)
            await ctx.channel.purge(limit=2)
            return
        guild = ctx.message.guild
        fins_name = 'Finance_reports'
        for category in guild.categories:
            if fins_name == category.name and not overwrite:
                await ctx.send('Финансовая часть уже добавлена')
                return
            elif fins_name == category.name and  overwrite:
                for text_channel in category.text_channels:
                    await text_channel.delete()
                await category.delete()

        
        category = await guild.create_category('Finance_reports')
        for period in self.fin_reports_periods:
            await guild.create_text_channel(name=period,category = category)
        await guild.create_text_channel(name='дневные',category = category)

        await ctx.send(f"Created a channel named financial categories")

