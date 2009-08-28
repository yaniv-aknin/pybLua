Reactor = {
    running = false,
    connected = false,
    events = {}
}

function Reactor:New()
    local instance = {}
    setmetatable(instance, self)
    self.__index = self
    nxt.BtStreamMode(1)
    instance.framer = Framer:New(function(data) nxt.DisplayText(data) end)
    self:AddEvent(2500, nil, nil, function() nxt.SoundTone() end)
    return instance
end

function Reactor:AddEvent(interval, data_source, predicate, callback)
    local interval = interval or 1
    local data_source = data_source or function() return true end
    local predicate = predicate or function() return true end
    local callback = callback or function() return nil end

    local event = {next_call=self:ComputeNextTime(interval),
                   interval=interval,
                   data_source=data_source,
                   predicate=predicate,
                   callback=callback}
    self:InsertEventAndResortEvents(event)
end

function Reactor:ComputeNextTime(interval)
    return nxt.TimerRead() + interval
end

function Reactor:InsertEventAndResortEvents(event)
    table.insert(self.events, event)
    table.sort(self.events, function(t1, t2) return t1.next_call > t2.next_call end)
end

function Reactor:ResumeEvent(event)
    event.next_call = self:ComputeNextTime(event.interval)
    self:InsertEventAndResortEvents(event)
end

function Reactor:TestAbortButton()
    if nxt.ButtonRead() == 0x1 then -- 0x1: rectangular grey button
        nxt.SoundTone()
        repeat
            --
        until nxt.ButtonRead() == 0x0
        nxt.SoundTone(500)
        error('abort button pressed')
    end
end


function Reactor:TestBTConnection()
    local current = (nxt.band(nxt.BtGetStatus(), 2) ~= 0) -- 0x02: BT_STATE_CONNECTED
    if current ~= self.connected then
        self.connected = current
        if current then
            nxt.SoundTone(2000)
            self.framer:ConnectionMade()
        else
            nxt.SoundTone(500)
            self.framer:ConnectionLost()
        end
    end
end

function Reactor:Run()
    local data
    local current_event
    self.running = true
    while (self.running) do
        self:TestAbortButton()
        self:TestBTConnection()
        data = nxt.BtStreamRecv()
        if ((data ~= nil) and (#data > 0)) then
            self.framer:DataReceived(data)
        end
        repeat
            current_event = self:ConditionalPopEvent()
            if (current_event ~= nil) then
                self:HandleEvent(current_event)
            end
        until (current_event == nil)
    end
end

function Reactor:ConditionalPopEvent()
    if (self.events[#self.events].next_call <= nxt.TimerRead()) then
        return table.remove(self.events)
    else
        return nil
    end
end

function Reactor:HandleEvent(event)
    local datum = event.data_source()
    if (event.predicate(datum)) then
        if (event.callback(datum) ~= false) then
            self:ResumeEvent(event)
        end
    end
end
