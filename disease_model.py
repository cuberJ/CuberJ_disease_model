import random
from decimal import Decimal
import math
import os
import time
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.font_manager import FontProperties

def DistenceCount(x1, y1, x2, y2):
    return math.sqrt((x1 - x2)*(x1 - x2) + (y1 - y2)*(y1 - y2))

class People:
    def __init__(self, x, y, age):
        '''
        x, y: 表示这个人的坐标
        age: 表示年龄
        hiddenday: 表示潜伏期
        immune: 表示是否具有抗体
        state: 表示状态(susceptible, infected, removed, dead)四种
        infectedrate: 感染率，取决于该人的年龄和周围人的感染情况
        deathrate: 感染后的致死率,与年龄相关，40岁以下的人群致死率为0，住院会减少致死率
        inroom : 仍需住院多少天
        roundpeople：周围的有效感染者总数
        isCount: 当这个人新成为患者或者新成为免疫者的时候，置True，在第一次遍历统计后置False，表明后面不需要再以这个身份进行统计数据了
        InHospital: 感染者是否住院，只有住院后才会停止传播
        '''
        self.x = x
        self.y = y
        self.age = age
        self.hidenday = 0
        self.immune = False
        self.state = "susceptible"
        self.infectedrate = (float)(0.005 * self.age)
        self.deathrate = 0.0
        self.inroom = 0
        self.roundpeople = 0
        self.isCount = True
        self.InHospital = False
        # Susceptible, Infected, Removed, dead

class World:

    def __init__(self, bedquantity, deadrate, token, Reinfected):
        '''
        坐标系大小 100 x 100
        people_container: 存放people的列表
        bedquantity: 病床数(100 / 1000)
        deadrate: 致死率(0.005 / 0.01)
        infectedrate: 感染率
        token: Boolean, 标识是否主动自我隔离(True: 会; False: 不会)
        date:疾病开始爆发后经历的总天数
        '''
        #self.people_container = [] # 用于存放people
        self.bedquantity = bedquantity
        self.deadrate = deadrate
        self.Reinfect = Reinfected
        self.token = token
        self.SUSCEPTIBLE, self.INFECTED, self.REMOVED, self.DEAD = [], [], [], []  # 三种人群的数组
        self.date = 0
        self.Medicine = 0.02


    def initialize_container(self):
        '''
        产生1w个人, 坐标, 年龄都是随机
        '''
        for i in range(6000):
            x = Decimal(random.uniform(0, 100)).quantize(Decimal("0.0"))
            y = Decimal(random.uniform(0, 100)).quantize(Decimal("0.0"))
            age = random.randint(1, 80)
            new_people = People(x, y, age)
            self.SUSCEPTIBLE.append(new_people)
        for i in range(2): # 产生两个零号病人
            x = Decimal(random.uniform(0, 100)).quantize(Decimal("0.0"))
            y = Decimal(random.uniform(0, 100)).quantize(Decimal("0.0"))
            age = 40
            new_people = People(x, y, age)
            new_people.hidenday = 4
            new_people.deathrate = 0
            self.INFECTED.append(new_people)
    
    def UpdateSusInfo(self):
        '''
        更新易感人群的基本信息，判断该人是否会成为感染者，并为其随机生成一个固定范围内的潜伏日期.初始化的住院日期由当天的医疗水平决定
        '''
        count = 0
        for people in self.SUSCEPTIBLE: # 遍历所有的健康易感人群
            # 修改易感人群的感染率
            if self.token is True:
                people.infectedrate = 0.06 * (1 - self.Medicine)

            else:
                if 0.01 * people.age >= 0.1:
                    people.infectedrate = (0.01 * people.age) * pow(1.07, people.roundpeople) * (1 - self.Medicine)
                else:
                    people.infectedrate = 0.1 * pow(1.07, people.roundpeople) * (1 - self.Medicine)

            if people.infectedrate >= 0.8:
                people.infectedrate = 0.8
            elif people.infectedrate < 0:
                people.infectedrate = 0
            if people.roundpeople <= 0:
                people.infectedrate = 0



            index = np.random.choice([1, 0], 1, p=[people.infectedrate, 1 - people.infectedrate]) # index 为0，表示不会感染


            if index[0] == 1:
                people.state = 'infected'
                print("正常人被感染")
                if (people.roundpeople >= 1):
                    print("\n#########################", people.infectedrate, "周围人数：", people.roundpeople, "\n")
                count += 1
                people.hidenday = random.randrange(4, 7) # 生成一个随机的潜伏日期
                if people.age > 40: # 致死率初始化
                    people.deathrate = (float) (self.deadrate * people.age/10)
                people.inroom = int(0.2 * people.age)
                people.isCount = True
                # 将这个新患者加入到感染者队列
                self.INFECTED.append(people)
                self.SUSCEPTIBLE.remove(people)
        print(self.date, "日感染人数：", count)

    def UpdateInfecInfo(self):
        '''
        更新感染者的基本信息，判断感染者是否需要进入医院，以及是否痊愈。感染者的潜伏期遍历时减少一天.致死率会根据初始值，逐步根据当今的医疗水平进行修改。
        同时改变感染者周围的正常人感染概率
        考虑两种传播模式：如果当前爆发的天数小于默认潜伏期，则指数传播，每次两人；如果天数大于，则改为环境影响
        '''
        temp_size = len(self.INFECTED)
        for people in self.INFECTED:
            temp_size -= 1
            if temp_size < 0:
                break
            # 每过一天，感染者的潜伏日期或者住院日期减少一天
            if people.InHospital == True:
                people.inroom -= 1
                if people.inroom <= 0: # 痊愈
                    people.isCount = True
                    people.deathrate = 0.1
                    people.infectedrate = 0.4
                    if self.Reinfect == True:
                        self.REMOVED.append(people)
                    else:
                        self.SUSCEPTIBLE.append(people)
                    self.INFECTED.remove(people)
                    self.bedquantity += 1
                    #print("患者痊愈")
                    continue
                else:
                    #print("患者仍在医院治疗,还需天数：", people.inroom)
                    pass

            else:
                people.hidenday -= 1
                if people.hidenday <= 0 :
                    if self.bedquantity > 0: # 住院成功
                        self.bedquantity -= 1
                        people.InHospital = True
                        #print("住院成功")
                    else:
                        people.hidenday = 1
                        #print("未能成功住院")

            index = np.random.choice([1, 0], 1, p=[people.deathrate, 1 - people.deathrate])  # index 为0，表示不会死亡
            #print(index, "\t", people.infectedrate)

            if index[0] == 1:
                print("患者死亡...其死亡率此时为", people.deathrate,"年龄为", people.age,"是否死于医院：",people.InHospital)
                people.state = 'dead'
                people.isCount = True
                #people.deathrate = 0
                #people.infectedrate = 0
                if people.InHospital == True:
                    self.bedquantity += 1
                self.DEAD.append(people)
                self.INFECTED.remove(people)
                continue

            else: # 患者存活，则修改病人的死亡率,同时进行疾病传播
                if people.hidenday > 0 and people.age > 40: # 针对40岁以上，仍处于潜伏期的人，死亡率增高
                    people.deathrate += self.deadrate
                elif people.hidenday <= 0 and people.age > 40: # 针对40岁以上且已经住院的人
                    people.deathrate = self.deadrate * people.age/10

                if self.date < 4 and people.InHospital is False :  # 4为默认的第一潜伏期时间
                    temp_count = 2
                    for survival in self.SUSCEPTIBLE: #指数传播,每次感染有效距离内最多两个人
                        if DistenceCount(people.x, people.y, survival.x, survival.y) <= 10:
                            survival.state = "infected"
                            #print("指数增长下感染了一人")
                            survival.hidenday = random.randrange(6, 12)
                            if people.age > 40:  # 致死率更新
                                people.deathrate = (float)(0.001 * people.age)
                            people.inroom = 20 * people.age * 0.01
                            # 将这个新患者加入到感染者队列
                            self.INFECTED.append(survival)
                            self.SUSCEPTIBLE.remove(survival)

                            temp_count -= 1
                            if temp_count <= 0:
                                break

                if (self.date >= 4) and (people.isCount is True) and (people.InHospital is False):
                    people.isCount = False
                    #print("aaaaaaaaaaa$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
                    for survival in self.SUSCEPTIBLE:
                        if DistenceCount(people.x, people.y, survival.x, survival.y) <= 3.0:
                                survival.roundpeople += 1
                                #print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")


    def UpdateRemInfo(self):
        '''
        更新免疫者和死亡人数的信息，即更新其周围人的感染者人数
        '''
        for people in self.REMOVED:
            if people.isCount == True:
                people.isCount = False
                people.immune = True
                people.state = 'removed'
                for survival in self.SUSCEPTIBLE:
                    if DistenceCount(people.x, people.y, survival.x, survival.y) <= 3:
                        if(survival.roundpeople >= 1):
                            survival.roundpeople -= 1

        for people in self.DEAD:
            if people.isCount == True:
                people.isCount = False
                for survival in self.SUSCEPTIBLE:
                    if DistenceCount(people.x, people.y, survival.x, survival.y) <= 3:
                        if (survival.roundpeople >= 1):
                            survival.roundpeople -= 1

    def Happen(self):
        self.initialize_container()
        time.sleep(6)
        self.max_infect = 2
        while len(self.INFECTED) > 0 and len(self.SUSCEPTIBLE) > 0:
            self.Draw(False)
            self.date += 1
            print("当前是疫情爆发的第", self.date, "天")
            self.UpdateRemInfo()
            print("治愈人数当前共有", len(self.REMOVED))
            self.UpdateInfecInfo()
            print("当前患者总计人数", len(self.INFECTED))
            if self.date >= 5:
                self.UpdateSusInfo()
                if self.Medicine < 1:
                    self.Medicine += 0.01
            print("易感人群总计人数", len(self.SUSCEPTIBLE))
            print("医院床位还有", self.bedquantity)
            print("当前死亡人数为", len(self.DEAD))
            if len(self.INFECTED) <= 0 or len(self.SUSCEPTIBLE) <= 0:
                print("sleep")
                time.sleep(10)
                self.Draw(True)
            if len(self.INFECTED) > self.max_infect:
                self.max_infect = len(self.INFECTED)


        if len(self.DEAD) >= 10002 or len(self.SUSCEPTIBLE) <= 0:
            print("最终所有人都没能逃脱感染和死亡，您的错误决策毁灭了这个世界")
            plt.title("最终所有人都没能逃脱感染和死亡，您的错误决策毁灭了这个世界")
            plt.show()

        else:
            print("最终挽回了一切，健康人群还有：", len(self.SUSCEPTIBLE), "死亡人数总计为：", len(self.DEAD), "\t感染总人数当前达到：", len(self.DEAD + self.REMOVED))

    def Draw(self, choose):
        fig = plt.figure()
        plt.rcParams['figure.figsize'] = (18, 9)
        myfont = FontProperties(fname='/Library/Fonts/Arial Unicode.ttf', size=15)
        plt.rcParams['axes.unicode_minus'] = False
        left, bottom, width, height = 0.1, 0.1, 0.8, 0.8

        agraphic = fig.add_axes([left, bottom, width, height])
        day = "Days:" + str(self.date) + "  当前患者人数:" + str(len(self.INFECTED)) +  "  当前死亡人数:" + str(len(self.DEAD)) + "  尚未感染人数：" + str(len(self.SUSCEPTIBLE))
        agraphic.set_title(day, fontproperties=myfont)
        npx1, npy1, npx2,npy2,npx3,npy3,npx4,npy4= [], [],[],[],[],[],[],[]
        for people in self.SUSCEPTIBLE:
            npx1.append(people.x)
            npy1.append(people.y)
        for people in self.INFECTED:
            npx2.append(people.x)
            npy2.append(people.y)
        for people in self.REMOVED:
            npx3.append(people.x)
            npy3.append(people.y)
        for people in self.DEAD:
            npx4.append(people.x)
            npy4.append(people.y)
        agraphic.scatter(npx1, npy1, marker="o", color="blue", s=5, label="SUSCEPTIBLE")
        agraphic.scatter(npx2, npy2, marker="o", color="red", s=5, label="INFECTED")
        agraphic.scatter(npx3, npy3, marker="o", color="green", s=5, label="REMOVED")
        #plt.scatter(npx4, npy4, marker="o", color="white", s=5, label="DEAD")


        agraphic.legend(loc = "best")
        if choose == False:
            plt.ion()
            plt.pause(0.1)
            plt.close()
        else:
            plt.show()

start = World(100, 0.0001, True, True)#床位，杀伤力，是否拥有防护意识，治愈者是否带有抗体
start.Happen()
