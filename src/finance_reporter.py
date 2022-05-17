from selenium import webdriver
#from webdriver_manager.microsoft import EdgeChromiumDriverManager
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
import discord
from discord.ext import commands,tasks
import time
from PIL import Image
import os
import shutil as sh
from datetime import datetime

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
        self.spx_source = 'finviz.com'
        self.moex_source = 'smart-lab.ru'
        self.map_store_dir = maps_dir
        if os.path.exists(self.map_store_dir):
            sh.rmtree(self.map_store_dir)
        os.mkdir(self.map_store_dir)
        os.mkdir(os.path.join(self.map_store_dir,'s&p500'))
        os.mkdir(os.path.join(self.map_store_dir,'moex'))   
        self.include_moex = include_moex
        self.client = client
        self.__call__.start()

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
    
    @tasks.loop(hours =1.0)#seconds = 50)
    async def __call__(self):

        fin_channels = [ch for ch in self.client.get_all_channels() if ch.name in self.fin_reports_periods]
        print(fin_channels)
        if len(fin_channels)==0:
            print('каналы не созданы')
            return
        fin_channel_ids = {period: channel.id for period,channel in zip(list(self.spx_duration_dict.keys())[1:],fin_channels)}
        curr_date = datetime.now()
        #curr_date = datetime.strptime('Jul 1 2005  1:33PM', '%b %d %Y %I:%M%p')
        
        print('Today is:', curr_date.strftime('%d.%m.%Y'))
        if curr_date.hour == 1:#True
            browser = webdriver.Chrome(ChromeDriverManager().install())
            #webdriver.Edge(service=Service(EdgeChromiumDriverManager().install()))
            browser.set_window_size(1920,1280)
            if curr_date.weekday() ==0:
                curr_period_spx=list(self.spx_duration_dict.keys())[1]
                curr_period_moex=list(self.moex_duration_dict.keys())[1]
                print('запрос на информацию по месяцам ', curr_period_spx)
                im1_path =self.get_SPX(browser=browser,period=curr_period_spx)
                im2_path =self.get_MOEX(browser=browser,period=curr_period_moex)
                channel = self.client.get_channel(fin_channel_ids[curr_period_spx])
                await channel.send(f"Today is: {curr_date.strftime('%d.%m.%Y')}",files=[discord.File(im1_path),discord.File(im2_path)])
            
            if curr_date.day == 1:
                curr_period_spx=list(self.spx_duration_dict.keys())[2]
                curr_period_moex=list(self.moex_duration_dict.keys())[2]
                print('запрос на информацию по месяцам ', curr_period_spx)
                im1_path = self.get_SPX(browser=browser,period=curr_period_spx)
                im2_path = self.get_MOEX(browser=browser,period=curr_period_moex)
                channel = self.client.get_channel(fin_channel_ids[curr_period_spx])
                await channel.send(f"Today is: {curr_date.strftime('%d.%m.%Y')}",files=[discord.File(im1_path),discord.File(im2_path)])
                if curr_date.month == 4 or curr_date.month == 7 or curr_date.month == 10 or curr_date.month == 1:
                    curr_period=list(self.spx_duration_dict.keys())[3]
                    print('запрос на информацию по кварталам ',curr_period)
                    im1_path = self.get_SPX(browser=browser,period=curr_period)
                    channel = self.client.get_channel(fin_channel_ids[curr_period])
                    await channel.send(f"Today is: {curr_date.strftime('%d.%m.%Y')}",file=discord.File(im1_path))
                if curr_date.month == 7 or curr_date.month==1:
                    curr_period=list(self.spx_duration_dict.keys())[4]
                    print('запрос на информацию по полугодию ',curr_period)
                    im1_path = self.get_SPX(browser=browser,period=curr_period)
                    channel = self.client.get_channel(fin_channel_ids[curr_period])
                    await channel.send(f"Today is: {curr_date.strftime('%d.%m.%Y')}",file=discord.File(im1_path))
                if curr_date.month == 1:
                    curr_period = list(self.spx_duration_dict.keys())[-1]
                    print('запрос на информацию по году ',curr_period)
                    im1_path = self.get_SPX(browser=browser,period=curr_period)
                    channel = self.client.get_channel(fin_channel_ids[curr_period])
                    await channel.send(f"Today is: {curr_date.strftime('%d.%m.%Y')}",file=discord.File(im1_path))
            browser.quit()

    @commands.command()
    async def get_daily(self,ctx: discord.ext.commands.Context,*description):
        channel = ctx.channel
        if channel.name!='дневные':
            await channel.send('команда работает только в дневном чате',reference=ctx.message)
            time.sleep(5)
            await ctx.channel.purge(limit=2)
            return
        curr_date = datetime.now()
        #browser = webdriver.Edge(service=Service(EdgeChromiumDriverManager().install()))
        browser = webdriver.Chrome(ChromeDriverManager().install())
        browser.set_window_size(1920,1280)
        curr_period_spx=list(self.spx_duration_dict.keys())[0]
        curr_period_moex=list(self.moex_duration_dict.keys())[0]
        print('запрос на информацию по месяцам ', curr_period_spx)
        im1_path =self.get_SPX(browser=browser,period=curr_period_spx)
        im2_path =self.get_MOEX(browser=browser,period=curr_period_moex)
        if description is not None:
            await channel.send(f"Today is: {curr_date.strftime('%d.%m.%Y')} \n"+' '.join([str(i) for i in description ]),files=[discord.File(im1_path),discord.File(im2_path)],reference=ctx.message)
        else:
            await channel.send(f"Today is: {curr_date.strftime('%d.%m.%Y')} \n",files=[discord.File(im1_path),discord.File(im2_path)],reference=ctx.message)
            
        browser.quit()

    @commands.command()
    async def create_fins(self,ctx: discord.ext.commands.Context, overwrite = False):
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

