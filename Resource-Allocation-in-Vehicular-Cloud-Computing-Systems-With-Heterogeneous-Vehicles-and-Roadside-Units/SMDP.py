import math
import logging
import time
import matplotlib.pyplot as plt
import numpy as np
logging.basicConfig(level=logging.DEBUG,#控制台打印的日志级别
                    filename='new.log',
                    filemode='w',
                    format='%(asctime)s - %(pathname)s[line:%(lineno)d] - %(levelname)s: %(message)s')

K = 10 # VC能支持车辆的最大数量  3-13
M = 0 # VC中可用RUs的数量
NR = 3 # 一个服务请求能最多分配RUs的数量 NR<=M
alpha = 0.1 # 连续时间折扣因子
lambda_p = 2 # 新服务请求的到达率  1-9
lambda_v = 7 # 新车到达率  4-8
mu_p = 8 # 请求的服务速率
mu_v = 8 # 车辆离开率
gamma = 2 # 单位传输时间的开销
xi = 18 # 补偿
omega_e = 0.5 # 能量占比
omega_d = 0.5 # 时间占比 omega_e + omega_d = 1
beta_e = 2 # 能量单价
beta_d = 2 # 时间单价
delta_1 = 2 #VE和VC之间的传输延时
delta_2 = 5 #VC和RC之间的传输延时
El = 20 # 在VE上执行请求所消耗的能量
Dl = 20 # 在VE上执行请求所消耗的时间

P = 4 #VE的传输功率

state = [] # VC状态，一共NR+2项，前NR项分别为占ni个RUs的请求数量，NR+1为M，NR+2为e(事件)

Epsilon = ['A','D1','D2','D3','B1','B-1'] # 事件集合，其中D1,D2,D3....的个数为NR
Alpha = [-1,0,1,2,3] # 动作集合

def getActionByEvent(event):
	if event == 'A':  # 新的任务产生
		return 0
	else:  # 服务请求完成或者车辆进入、离开VCC系统
		return -1
# k(s, a) the instant revenue of the VCC system by taking action a under state s in case that event e occurs, which consists of both the income and cost of the VCC system.
def getInstantRevenue(action, state):
	event = state[-1]
	if action > 0 and event == 'A':
		return (omega_e*beta_e*(El - P*delta_1) + omega_d*beta_d*(Dl-1/(action*mu_p)-delta_1) - gamma*delta_1)
	elif action == 0 and event == 'A':
		return (omega_e*beta_e*(El - P*delta_1) + omega_d*beta_d*(Dl-delta_2-delta_1) - gamma*(delta_1+delta_2))
	elif action == -1 and (event == 'D1' or event == 'D2' or event == 'D3' or event == 'B1'):
		return 0
	elif action == -1 and event == 'B-1':
		if getCostRate(state) == state[-2]:
			return -xi
		else:
			return 0
	# 其他情况下
	#return 0
# c(s, a) is the cost rate of τ(s, a) in case that action a is selected. 
def getCostRate(state):
	total = 0
	for i in range(3):
		total += (i+1) * state[i]
	return total
# τ(s, a) Under a given state s and an action a, the expected service time between two continuous decision epoch is denoted by τ(s, a).
def getServiceTime(action, state):
	return 1/getMeanEventRate(action, state)
# σ(s, a) the mean event rate for specific s and a values is the sum of rates of all of the events in the VCC system
def getMeanEventRate(action, state):
	event = state[-1]
	if event == 'B1' and action == -1:
		return (state[-2]+1)*lambda_p + lambda_v + mu_v + getCostRate(state) * mu_p
	elif event == 'B-1' and action == -1:
		return (state[-2]-1)*lambda_p + lambda_v + mu_v + getCostRate(state) * mu_p
	elif event == 'A' and action >= 0:
		return state[-2]*lambda_p + lambda_v + mu_v + getCostRate(state) * mu_p + action*mu_p
	elif event == 'D1' and action == -1:
		return state[-2]*lambda_p + lambda_v + mu_v + getCostRate(state) * mu_p - 1*mu_p
	elif event == 'D2' and action == -1:
		return state[-2]*lambda_p + lambda_v + mu_v + getCostRate(state) * mu_p - 2*mu_p
	elif event == 'D3' and action == -1:
		return state[-2]*lambda_p + lambda_v + mu_v + getCostRate(state) * mu_p - 3*mu_p
# P(s'|s, a) is defined as the transition probability from state s to state s' under an action a
def getTransitionProbability(action, state, state_next):
	event = state[-1]
	i, ni, m, e = checkState(state,state_next)
	if event == 'A':
		if action == 0 and e == 'A' and i == 0:
			#print('A',state[-2]*lambda_p/getMeanEventRate(action, state))
			return state[-2]*lambda_p/getMeanEventRate(action, state)
		elif action == 0 and e == 'B1' and i == 0:
			#print('B1',lambda_v/getMeanEventRate(action, state))
			return lambda_v/getMeanEventRate(action, state)
		elif action == 0 and e == 'B-1' and i == 0:
			#print('B-1',mu_v/getMeanEventRate(action, state))
			return mu_v/getMeanEventRate(action, state)
		elif action == 0 and e[0] == 'D' and i == 0:
			#print(e, state[int(e[1])-1]*int(e[1])*mu_p/getMeanEventRate(action, state))
			return state[int(e[1])-1]*int(e[1])*mu_p/getMeanEventRate(action, state)
		elif action > 0 and i > 0 and e[0] == 'D':
			if action == int(e[1]):
				#print(ni*i*mu_p/getMeanEventRate(action, state))
				return ni*i*mu_p/getMeanEventRate(action, state)
			else:
				#print(state[int(e[1])-1]*int(e[1])*mu_p/getMeanEventRate(action, state))
				return state[int(e[1])-1]*int(e[1])*mu_p/getMeanEventRate(action, state)
		elif action > 0 and i > 0 and e == 'A':
			#print(state[-2]*lambda_p/getMeanEventRate(action, state))
			return state[-2]*lambda_p/getMeanEventRate(action, state)
		elif action > 0 and i > 0 and e == 'B1':
			#print(lambda_v/getMeanEventRate(action, state))
			return lambda_v/getMeanEventRate(action, state)
		elif action > 0 and i > 0 and e == 'B-1':
			#print(mu_v/getMeanEventRate(action, state))
			return mu_v/getMeanEventRate(action, state)
	elif event[0] == 'D':
		j = int(event[1])
		if action == -1 and i > 0 and e == 'A':
			return state[-2]*lambda_p/getMeanEventRate(action, state)
		elif action == -1 and i > 0 and e[0] == 'D':
			if j == int(e[1]):
				return ni*i*mu_p/getMeanEventRate(action, state)
			else:
				return state[int(e[1])-1]*int(e[1])*mu_p/getMeanEventRate(action, state)
		elif action == -1 and i > 0 and e == 'B1':
			return lambda_v/getMeanEventRate(action, state)
		elif action == -1 and i > 0 and e == 'B-1':
			return mu_v/getMeanEventRate(action, state)
	elif event == 'B1':
		if action == -1 and e == 'B1':
			return lambda_v/getMeanEventRate(action, state)
		elif action == -1 and e == 'B-1':
			return mu_v/getMeanEventRate(action, state)
		elif action == -1 and e == 'A':
			return (state[-2]+1)*lambda_p/getMeanEventRate(action, state)
		elif action == -1 and e[0] == 'D':
			return state[int(e[1])-1]*int(e[1])*mu_p/getMeanEventRate(action, state)
	elif event == 'B-1':
		if action == -1 and e == 'B1':
			return lambda_v/getMeanEventRate(action, state)
		elif action == -1 and e == 'B-1':
			return mu_v/getMeanEventRate(action, state)
		elif action == -1 and e == 'A':
			return (state[-2]-1)*lambda_p/getMeanEventRate(action, state)
		elif action == -1 and e[0] == 'D':
			return state[int(e[1])-1]*int(e[1])*mu_p/getMeanEventRate(action, state)
# check state 
# return i,ni,M,event
def checkState(state, state_next):
	for i in range(3):
		if state[i] != state_next[i]:
			return i+1, state_next[i], state_next[-2], state_next[-1]
	return 0, 0, state_next[-2], state_next[-1]
# r(s, a) Discounted Reward Model
def getRewardModel(action, state):
	return getInstantRevenue(action, state) - getCostRate(state)/(alpha + getMeanEventRate(action, state))
# state set
def getStateSet():
	stateSet = {}
	total = 0
	for M in range(K+1):
		for i in range(K+1):
			for j in range(K+1):
				for k in range(K+1):
					for e in Epsilon:
						s = [i,j,k,M,e]
						total += 1
						if getCostRate(s) <= M:  
							if e[0] == 'D':
								if s[int(e[1])-1] > 0:
									stateSet[getStateKey(s)] = s
							if e == 'B1':
								if s[-2] + 1 <= K:
									stateSet[getStateKey(s)] = s
							if e == 'B-1':
								if s[-2] - 1 >= 0:
									stateSet[getStateKey(s)] = s
							if e == 'A':
								stateSet[getStateKey(s)] = s
	return stateSet
# state to key
def getStateKey(s):
	key = ''
	for i in s:
		key = key + str(i)+'_'
	return key

# value iteration   normalized component
def value_iteration():
	stateSet = getStateSet()
	# 初始化值函数 v(s) = 0
	v = {}
	pi = {}
	for key in stateSet:
		v[key] = 0
		pi[key] = -2
	for i in range(1000):
		logging.info('---------------'+str(i+1)+'---------------')
		delta = 0.0
		for key in stateSet:
			

			s = stateSet[key]
			vmax = -1000000
			amax = -2
			for a in Alpha:
				# 不存在情况
				if (s[-1] == 'A' and a == -1) or (s[-1][0] == 'D' and a >= 0) or (s[-1] == 'B1' and a >= 0) or (s[-1] == 'B-1' and a >= 0): 
					continue
				if a > 0 and s[-1] == 'A' and getCostRate(s) + a > s[-2]:
					continue
				#print('-----',a,s)

				nextStateSet =  getNextStateSet(a,s)
				#print(nextStateSet)
				#if s == [1,2,0,8,'A']:
				#	print(nextStateSet)
				SUM = 0
				vl = 0
				for skey in nextStateSet:
					s_pie = nextStateSet[skey]
					r_ba, lamda_ba, p_ba = uniform(a, s, s_pie)
					#print('+++++',a, s, s_pie,p_ba,r_ba)
					#if s == [1,2,0,8,'A']:
					#	if skey in v.keys():
							#vl += lamda_ba*p_ba*v[skey]
					#		print('r(s,a)',r_ba,'λ_ba',lamda_ba,'p_ba(s|s,a)',p_ba,'p(s|s,a)',getTransitionProbability(a, s, s_pie),v[skey],skey)
					if skey in v.keys():
						#print(a, s, s_pie,p_ba,r_ba,lamda_ba*p_ba*v[skey])
						vl += lamda_ba*p_ba*v[skey]
				vl += r_ba
				#if s == [1,2,0,8,'A']:
				#	print(r_ba,vl,a)
				if vl > vmax:
					vmax = vl
					amax = a
			delta += abs(vmax-v[key])
			v[key] = vmax
			pi[key] = amax
			#if s == [1,2,0,8,'A']:
			#	print(key,vmax,amax)
			#if s == [4,1,0,7,'A']:
			#if s == [0,0,0,13,'A']:
			#	print(key,vmax,amax)
				#time.sleep(5)
		#print(delta)
		if delta < 1e-6:
			break
	#for key in v:
	#	print(stateSet[key],v[key],pi[key])
	return v,pi,stateSet
	
					

# in state s action a ,the next state set
def getNextStateSet(action, state):
	nextStateSet = {}
	event = state[-1]
	if event == 'A':
		if action == 0:
			for e in Epsilon:
				s = state[0:4]
				s.append(e)
				nextStateSet[getStateKey(s)] = s
			return nextStateSet
		elif action > 0:
			for e in Epsilon:
				s = state[0:4]
				s.append(e)
				s[action-1] = s[action-1] + 1 
				nextStateSet[getStateKey(s)] = s
			return nextStateSet
	elif event[0] == 'D':
		if action == -1:
			for e in Epsilon:
				s = state[0:4]
				s.append(e)
				s[int(event[1])-1] = s[int(event[1])-1] - 1 
				nextStateSet[getStateKey(s)] = s
			return nextStateSet
	elif event == 'B1':
		if action == -1:
			for e in Epsilon:
				s = state[0:4]
				s.append(e)
				s[-2] = s[-2] + 1 
				nextStateSet[getStateKey(s)] = s
			return nextStateSet
	elif event == 'B-1':
		if action == -1:
			for e in Epsilon:
				s = state[0:4]
				s.append(e)
				s[-2] = s[-2] - 1
				# 如果原状态s处于饱和状态，此时减少一个可用资源，会出现状态集之外的状态，这里做处理，将较小的a的数量减一
				for o in range(3):
					if s[o] > 0:
						s[o] = s[o] - 1
						break
				nextStateSet[getStateKey(s)] = s
			return nextStateSet

def uniform(action, state, state_next):
	r_ba = getRewardModel(action, state) * (alpha + getMeanEventRate(action, state)) / (alpha + gety())
	lamda_ba = gety() / (gety() + alpha)
	p_ba = 0
	if state == state_next:
		p_ba = 1 - ((1 - getTransitionProbability(action, state, state_next)) * getMeanEventRate(action, state))/gety() # 按照论文中给定的公式，此概率过大，因此基本都是卸载到RC上
		#p_ba = ((1 - getTransitionProbability(action, state, state_next)) * getMeanEventRate(action, state))/gety()
	else:
		p_ba = getTransitionProbability(action, state, state_next) * getMeanEventRate(action, state)/gety()
	return r_ba, lamda_ba, p_ba
# λ
def getLambda(action, state):
	lamda = getMeanEven·tRate(action, state)/(alpha + getMeanEventRate(action, state))
	return lamda
# y
def gety():
	#print(K*lambda_p + lambda_v + mu_v + K * NR * mu_p)
	return K*lambda_p + lambda_v + mu_v + K * NR * mu_p

def Fig3():
	Case0 = []
	Case1 = []
	Case2 = []
	Case3 = []
	for i in range(1,10):
		global lambda_v
		lambda_v = i
		logging.info('------The vehicle arrival rate per minute lambdav = '+str(lambda_v)+'  K = 10   lambdap = 2---------------')
		v,pi,stateSet = value_iteration()
		case0 = 0
		case1 = 0
		case2 = 0
		case3 = 0
		for key in pi:
			if pi[key] == 0:
				case0 += 1
			elif pi[key] == 1:
				case1 += 1
			elif pi[key] == 2:
				case2 += 1
			elif pi[key] == 3:
				case3 += 1
		Case0.append(case0/(case0+case1+case2+case3))
		Case1.append(case1/(case0+case1+case2+case3))
		Case2.append(case2/(case0+case1+case2+case3))
		Case3.append(case3/(case0+case1+case2+case3))
		#print(case0,case1,case2,case3,(case0+case1+case2+case3))
		#print(case0/(case0+case1+case2+case3),case1/(case0+case1+case2+case3),case2/(case0+case1+case2+case3),case3/(case0+case1+case2+case3))
	x = np.arange(1,10)
	l3=plt.plot(x,Case0,color = '#FFFF00',marker='1',linestyle = '-',label='case0')
	l1=plt.plot(x,Case1,'ro-',label='case1')
	l2=plt.plot(x,Case2,'g+-',label='case2')
	l3=plt.plot(x,Case3,'b^-',label='case3')
	#plt.plot(x,Case0,color = '#FFFF00',marker='2',linestyle = '-',x,Case1,'ro-',x,Case2,'g+-',x,Case3,'b^-')
	plt.title('Action probabilities under different arrival rates of service requests per vehicle (λv = 7, and K = 10).')
	plt.xlabel('Arrival rate of the requests(λp)')
	plt.ylabel('Action Probability of VCC System')
	plt.legend()
	plt.show()

def Fig2():
	Case0 = []
	Case1 = []
	Case2 = []
	Case3 = []
	V = []
	for i in range(1,10):
		global lambda_p
		lambda_p = i
		logging.info('------The arrival rate of the requests per vehicle lambdap = '+str(lambda_p)+'  K = 10   lambdav = 7---------------')
		v,pi,stateSet = value_iteration()
		case0 = 0
		case1 = 0
		case2 = 0
		case3 = 0
		vx = 0
		for key in pi:
			if pi[key] == 0:
				case0 += 1
			elif pi[key] == 1:
				case1 += 1
			elif pi[key] == 2:
				case2 += 1
			elif pi[key] == 3:
				case3 += 1
		Case0.append(case0/(case0+case1+case2+case3))
		Case1.append(case1/(case0+case1+case2+case3))
		Case2.append(case2/(case0+case1+case2+case3))
		Case3.append(case3/(case0+case1+case2+case3))
		k = 0
		for key in stateSet:
			print(k,v[key],key)
			k += 1
			vx += v[key] 
		V.append(vx)
	print(case0+case1+case2+case3)
		#print(case0,case1,case2,case3,(case0+case1+case2+case3))
		#print(case0/(case0+case1+case2+case3),case1/(case0+case1+case2+case3),case2/(case0+case1+case2+case3),case3/(case0+case1+case2+case3))
	x = np.arange(1,10)
	l3=plt.plot(x,Case0,color = '#FFFF00',marker='1',linestyle = '-',label='case0')
	l1=plt.plot(x,Case1,'ro-',label='case1')
	l2=plt.plot(x,Case2,'g+-',label='case2')
	l3=plt.plot(x,Case3,'b^-',label='case3')
	#plt.plot(x,Case0,color = '#FFFF00',marker='2',linestyle = '-',x,Case1,'ro-',x,Case2,'g+-',x,Case3,'b^-')
	plt.title('Action probabilities under different arrival rates of service requests per vehicle (λv = 7, and K = 10).')
	plt.xlabel('Arrival rate of the requests(λp)')
	plt.ylabel('Action Probability of VCC System')
	plt.legend()
	plt.show()
	print('---')
	l1=plt.plot(x,V,'ro-',label='case1')
	#plt.plot(x,Case0,color = '#FFFF00',marker='2',linestyle = '-',x,Case1,'ro-',x,Case2,'g+-',x,Case3,'b^-')
	plt.title('Action probabilities under different arrival rates of service requests per vehicle (λv = 7, and K = 10).')
	plt.xlabel('Arrival rate of the requests(λp)')
	plt.ylabel('Action Probability of VCC System')
	plt.legend()
	plt.show()


# value iteration
def value_iteration1():
	stateSet = getStateSet()
	# 初始化值函数 v(s) = 0
	v = {}
	pi = {}
	for key in stateSet:
		v[key] = 0
		pi[key] = -2
	for i in range(2000):
		logging.info('---------------'+str(i+1)+'---------------')
		delta = 0.0
		for key in stateSet:
			s = stateSet[key]
			vmax = -1000000
			amax = -2
			for a in Alpha:
				# 不存在情况
				if (s[-1] == 'A' and a == -1) or (s[-1][0] == 'D' and a >= 0) or (s[-1] == 'B1' and a >= 0) or (s[-1] == 'B-1' and a >= 0): 
					continue
				if a > 0 and s[-1] == 'A' and getCostRate(s) + a > s[-2]:
					continue
				#print('-----',a,s)

				nextStateSet =  getNextStateSet(a,s)
				#print(nextStateSet)
				if s == [2,0,0,8,'A']:
					print(nextStateSet)
				SUM = 0
				vl = 0
				for skey in nextStateSet:
					s_pie = nextStateSet[skey]
					r = getRewardModel(a, s)
					lamda = getMeanEventRate(a, s)/(alpha+getMeanEventRate(a, s))
					p = getTransitionProbability(a,s,s_pie)
					#if s == [2,0,0,5,'A']:
					#print('+++++',a, s, s_pie,p,r)
					#print(r,lamda,p)
					#r_ba, lamda_ba, p_ba = uniform(a, s, s_pie)
					#if s == [0,0,0,13,'A']:
					#	if skey in v.keys():
							#vl += lamda_ba*p_ba*v[skey]
					#		print('r(s,a)',r_ba,'λ_ba',lamda_ba,'p_ba(s|s,a)',p_ba,'p(s|s,a)',getTransitionProbability(a, s, s_pie),v[skey],skey)
					if skey in v.keys():
						if s == [2,0,0,8,'A']:
							print(a, s, s_pie,p,r,v[skey],lamda*p*v[skey])
						vl += lamda*p*v[skey]
				vl += r
				if s == [2,0,0,8,'A']:
					print(r,vl,a)
				if vl > vmax:
					vmax = vl
					amax = a
			delta += abs(vmax-v[key])
			v[key] = vmax
			pi[key] = amax
			#print(key,vmax,amax)
			#if s == [4,1,0,7,'A']:
			#if s == [0,0,0,13,'A']:
			#	print(key,vmax,amax)
				#time.sleep(5)
		#print(i,delta)
		if delta < 1e-6:
			break
	for key in v:
		
		if pi[key] == 2:
			print(stateSet[key],v[key],pi[key])
			time.sleep(1)
	return v,pi,stateSet



if __name__ == '__main__':
	state1 = [4,1,0,7,'D1']
	state2 = [0,0,0,13,'A']
	sets = getStateSet()
	#print(len(sets))
	#for key in sets:
	#	print(sets[key])
	Fig2()
	#value_iteration()
	'''
	v,pi,stateSet = value_iteration()
	v1,pi1,stateSet1 = value_iteration1()
	t = 0
	c0=0
	c1=0
	c2=0
	c3 = 0
	a0=0
	a1=0
	a2=0
	a3 = 0
	for key in stateSet:
		if stateSet[key][-1] == 'A':
			t += 1
		if pi[key] == 0:
			a0 += 1
		if pi[key] == 1:
			a1 += 1
		if pi[key] == 2:
			a2 += 1
		if pi[key] == 3:
			a3 += 1
		if pi1[key] == 0:
			c0 += 1
		if pi1[key] == 1:
			c1 += 1
		if pi1[key] == 2:
			c2 += 1
		if pi1[key] == 3:
			c3 += 1
		print(stateSet[key],v[key],v1[key],'--------',pi[key],pi1[key])
	print(t)
	print(a0,a1,a2,a3,a0+a1+a2+a3)
	print(c0,c1,c2,c3,c0+c1+c2+c3)
	'''