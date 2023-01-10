#!/usr/bin/env python
"""
ACT-R / CARLA connection
Model adjusts traffic violations based on risk
Risk perception is just based on vehicle count nearby
"""

import pyactr as actr


risk_measure = actr.ACTRModel()

#Create declarative memory, check goal and retrieval buffers
dm = risk_measure.decmem
goal = risk_measure.goal
retrieval = risk_measure.retrieval



# Defining chunk types
# Count of vehicles the driver recognizes, 
# Number is there for utility 
actr.chunktype("vehicleCount", ("count", "number"))

# Increments the current vehicle count
#actr.chunktype("incrementVehicle","arg1", "arg2", "sum", "count")
# Vehicle chunk
#actr.chunktype("vehicle", "vehicleID")

# Counting order for numbers, will go to decmem
actr.chunktype("counting_order", ("prev", "current", "next"))

# Subtraction chunk for goal buffers


# At the moment, maximum risk posed by other vehicles in traffic
# is capped to 12. It is arbitrarily picked, it seemed like the max number
# of vehicles surrounding the driver at any given time to me.
# Will change how this works later.
dm.add(actr.makechunk("counter0", "counting_order", prev=0, current=0, next=1))
for i in range(1,15):
        dm.add(actr.makechunk("counter"+str(i), "counting_order", prev=i-1, current=i, next=i+1))

vCountInMemory = 0
#newVCount = 0

# Addition chunk for goal buffers
actr.chunktype("add", ("arg1", "arg2", "sum", "count"))
#
#### Production Segment for incrementing car count
#
risk_measure.productionstring(name="init_add", string="""
        =g>
        isa     add
        arg1    =num1
        arg2    =num2
        sum     None
        ==>
        =g>
        isa     add
        sum     =num1
        count   0
        +retrieval>
        isa     counting_order
        current =num1
""")

risk_measure.productionstring(name="terminate_addition", string="""
        =g>
        isa     add
        count   =num
        arg2    =num
        sum     =answer
        ==>
        ~g>
""")

risk_measure.productionstring(name="increment_count", string="""
        =g>
        isa     add
        count   =count
        sum     =sum
        =retrieval>
        isa     counting_order
        current =count
        next    =newcount
        ==>
        =g>
        isa     add
        count   =newcount
        +retrieval>
        isa     counting_order
        current =sum
""")

risk_measure.productionstring(name="increment_sum", string="""
        =g>
        isa     add
        count   =count
        arg2    ~=count
        sum     =sum
        =retrieval>
        isa     counting_order
        current =sum
        next    =newSum
        ==>
        =g>
        isa     add
        sum     =newSum
        +retrieval>
        isa     counting_order
        current =count
""")


#
#### Production Segment for decrementing car count
#


# Subtraction chunk for goal buffers
actr.chunktype("sbtr", ("arg1", "arg2", "sub", "count2"))

risk_measure.productionstring(name="init_sub", string="""
        =g>
        isa     sbtr
        arg1    =num1
        arg2    =num2
        sub     None
        ==>
        =g>
        isa     sbtr
        sub     =num2
        count2  =num1
        +retrieval>
        isa     counting_order
        current =num1
""")

risk_measure.productionstring(name="terminate_sub", string="""
        =g>
        isa     sbtr
        count2  =num
        arg2    ~=num
        sub     0
        ==>
        ~g>
""")

risk_measure.productionstring(name="decrement_sub", string="""
        =g>
        isa     sbtr
        count2   =count2
        arg1    ~=count2
        sub     =sub
        ?retrieval>
        state free
        =retrieval>
        isa     counting_order
        current =sub
        prev    =newSub
        ==>
        =g>
        isa     sbtr
        sub     =newSub
        +retrieval>
        isa     counting_order
        current =count2
""")

risk_measure.productionstring(name="decrement_count", string="""
        =g>
        isa     sbtr
        count2  =count2
        sub     =sub
        =retrieval>
        isa     counting_order
        current =count2
        prev    =newcount
        newcount ~=arg2
        ==>
        =g>
        isa     sbtr
        count2  =newcount
        +retrieval>
        isa     counting_order
        current =sub
""")

"""
Checks the number of vehicles around the driver
"""
def check_vehicles():
        #TODO: Move this to ACT-R From CARLA script
        pass


"""
Increments the risk factor posed by vehicles around current driver
Currently gets the number of vehicles from CARLA directly, will delegate this to ACT-R Later
"""
def increment_vehicle_risk(currentCount, newCount):
        risk_measure.goal.add(actr.makechunk("start", "add", arg1=str(currentCount), arg2=str(newCount)))
        sim = risk_measure.simulation(realtime=True)
        sim.run()
        # Returns the current risk factor posed by vehicles around the driver
        vCountInMemory = (int)((str)(retrieval.pop()[0][1]))
        return(vCountInMemory)

def decrement_vehicle_risk(currentCount, newCount):
        num1 = 0
        num2 = 0
        if (currentCount < newCount):
                num1 = newCount
                num2 = currentCount
        elif(currentCount == newCount):
                return 0
        else:
                num1 = currentCount
                num2 = newCount
        risk_measure.goal.add(actr.makechunk("start", "sbtr", arg1=str(num1), arg2=str(num2)))
        sim = risk_measure.simulation(realtime = True)
        sim.run()

        # Debug
        #pprint(inspect.getmembers(sim))
        print(retrieval)
        # Returns the current risk factor posed by vehicles around the driver
        vCountInMemory = (int)((str)(retrieval.pop()[0][1]))
        return(vCountInMemory)


