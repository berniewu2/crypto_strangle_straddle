import os
os.chdir('d:/')
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import re


# In[2]:

#as we have gathered all the available call and put options
#this function will only extract strike price existing in both call and put options
#this is a fundamental requirement of options straddle

def find_strike_price(df):
    
    temp=[re.search('\d{4}',i).group() for i in df.columns]
    target=[]

    for i in set(temp):
        if temp.count(i)>1:
            target.append(i)
            
    return target



# In[3]:

#this function is merely data cleansing
#merging option price information with spot price

def straddle(options,spot,contractsize,strikeprice):
        
    option=options[[i for i in options.columns if strikeprice in i]] 
    
    df=pd.merge(spot,option,left_index=True,right_index=True)

    temp=[]
    for i in df.columns:
        if 'C'+strikeprice in i:
            temp.append('call')
        elif 'P'+strikeprice in i:
            temp.append('put')
        elif 'Index' in i:
            temp.append('spot')
        else:
            temp.append(i)

    df.columns=temp
    
    #we multiply contract size with spot price here
    #it makes our life a lot easier later with visualization

    df['spot']=df['spot'].apply(lambda x:x*contractsize)
    
    return df



# In[4]:

#signal generation is actually very simple
#just find the option pair at the closest price we can

def signal_generation(df,threshold):
    
    df['signals']=np.where(
        np.abs(
            df['call']-df['put'])<threshold,
        1,0)  

    return df


# In[5]:

#ploting the payoff diagram
def plot(df,strikeprice,contractsize):
    
    #finding trading signal
    #if no signal is found
    #we declare no suitable entry point for options straddle
    
    ind=df[df['signals']!=0].index

    if ind.empty:
        print('Strike Price at',strikeprice,'\nNo trades available.\n')
        return 
    
    #calculate how much profit we can gain outta this
    
    profit=np.abs(
        df['spot'].iloc[-1]-int(strikeprice)*contractsize
    )-df['call'][ind[0]]-df['put'][ind[0]]

    y=[]
    
    #we use these two variables to plot how much we can profit at different spot price
    
    begin=round(int(strikeprice)*contractsize-5*(df['call'][ind[0]]+df['put'][ind[0]]),0)
    end=round(int(strikeprice)*contractsize+5*(df['call'][ind[0]]+df['put'][ind[0]]),0)+1
    
    x=list(np.arange(int(begin),int(end)))
    
    #as u can see from the pic
    # https://github.com/je-suis-tm/quant-trading/blob/master/preview/options%20straddle%20payoff%20diagram.png
    #we only make money (green color) if the spot price is outside of a range
    #group1 and group2 are variables that indicate which range our line plot gets red/green color
    #they keep track of the indices that we switch from profit to loss or from loss to profit
    #as indices are always positive, we initialize them to negative values

    group1,group2=-10,-10
    for j in x:
        temp=np.abs(j-int(strikeprice)*contractsize)-(df['call'][ind[0]]+df['put'][ind[0]])
        y.append(temp)
        if temp<0 and group1<0:
            group1=x.index(j)
        if temp>0 and group1>0 and group2<0:
            group2=x.index(j)
        

    ax=plt.figure(figsize=(10,5)).add_subplot(111)
    ax.spines['bottom'].set_position(('data',0))
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)
    
    #pnl in different colors, red is loss, green is profit
    
    plt.plot(x[:group1],y[:group1],c='#57bc90',lw=5)
    plt.plot(x[group2:],y[group2:],c='#57bc90',lw=5)
    plt.plot(x[group1:group2],y[group1:group2],c='#ec576b',lw=5)
    
    #ploting strike price
    
    plt.plot([int(strikeprice)*contractsize,
              int(strikeprice)*contractsize],
              [0,-(df['call'][ind[0]]+df['put'][ind[0]])],
              linestyle=':',lw=3,c='#ec576b',alpha=0.5)
    
    #ploting spot price
    
    plt.axvline(df['spot'].iloc[-1],lw=5,
                linestyle='--',c='#e5e338',alpha=0.5)
    
    #adding annotations
    
    plt.annotate('Strike Price',
                 xy=(int(strikeprice)*contractsize,
                     0),
                 xytext=(int(strikeprice)*contractsize,
                     df['call'][ind[0]]+df['put'][ind[0]]),
                 arrowprops=dict(arrowstyle='simple',
                                 facecolor='#c5c1c0',),
                 va='center',ha='center'
                 )
 
    plt.annotate('Lower Breakeven Point',
                 xy=(int(strikeprice)*contractsize-(df['call'][ind[0]]+df['put'][ind[0]]),
                     0),
                 xytext=(int(strikeprice)*contractsize-1.5*(df['call'][ind[0]]+df['put'][ind[0]]),
                         -df['call'][ind[0]]-df['put'][ind[0]]),
                 arrowprops=dict(arrowstyle='simple',
                                 facecolor='#c5c1c0'),
                 va='center',ha='center'
                 )
 
    plt.annotate('Upper Breakeven Point',
                 xy=(int(strikeprice)*contractsize+(df['call'][ind[0]]+df['put'][ind[0]]),
                     0),
                 xytext=(int(strikeprice)*contractsize+1.5*(df['call'][ind[0]]+df['put'][ind[0]]),
                         -df['call'][ind[0]]-df['put'][ind[0]]),
                 arrowprops=dict(arrowstyle='simple',
                                 facecolor='#c5c1c0'),
                 va='center',ha='center'
                 )

    plt.annotate('Spot Price',
                 xy=(df['spot'].iloc[-1],
                     2*(df['call'][ind[0]]+df['put'][ind[0]])),
                 xytext=(df['spot'].iloc[-1]*1.003,
                         2*(df['call'][ind[0]]+df['put'][ind[0]])),
                 arrowprops=dict(arrowstyle='simple',
                                 facecolor='#c5c1c0'),
                 va='center',ha='left'
                 )
    
    #limit x ticks to 3 for a tidy look
    
    plt.locator_params(axis='x',nbins=3)
    
    plt.title(f'Long Straddle Options Strategy\nP&L {round(profit,2)}')
    plt.ylabel('Profit & Loss')
    plt.xlabel('Price',labelpad=50)
    plt.show()


# In[6]:

#for stoxx 50 options, the contract size is 10 ticks per euro

contractsize=10

#the threshold determines the price disparity between call and put options
#the same call and put option price for the same strike price and the same strike date
#only exists in an ideal world, in reality, it is like royal flush
#when the price difference of call and put is smaller than 2 euros
#we consider them identically the same option price

threshold=2


# In[7]:

def main():
    
    data=pd.read_csv('output.csv')
    
    aug=data.parse('aug')
    aug.set_index('Dates',inplace=True)
    aug.index=pd.to_datetime(aug.index)
    
    spot=data.parse('spot')
    spot.set_index('Dates',inplace=True)
    spot.index=pd.to_datetime(spot.index)
    
    target=find_strike_price(aug)
    
    #we iterate through all the available option pairs
    #to find the optimal strike price to maximize our profit
    
    for strikeprice in target:
      
        df=straddle(aug,spot,contractsize,strikeprice)
        
        signal=signal_generation(df,threshold)
        
        plot(signal,strikeprice,contractsize)


# In[8]:


if __name__ == '__main__':
    main()