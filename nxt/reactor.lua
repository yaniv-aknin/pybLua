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
    instance.protocol = Protocol:New(instance)
    instance.framing = Framer:New(instance.protocol)
    instance:AddEvent(2500, nil, nil, function() nxt.SoundTone() end)
    instance:SetupBluetoothHandler(500)
    instance:SetupAbortButton(100)
    return instance
end

function Reactor:SetupAbortButton(interval)
    function AbortButton(reactor, event_id, datum)
            nxt.SoundTone(1500)
            repeat
                --
            until nxt.ButtonRead() == 0x0
            nxt.SoundTone(500)
            reactor.running = false
    end
    self:AddEvent(interval, nxt.ButtonRead, function(reactor, datum) return datum == 0x8 end, AbortButton)
end

function Reactor:SetupBluetoothHandler(interval)
    function GetBluetoothConnectionState()
        return (nxt.band(nxt.BtGetStatus(), 2) ~= 0)
    end
    function DidConnectionStateChange(reactor, currentState)
        return (reactor.connected ~= currentState)
    end
    function HandleStateChange(reactor, event_id)
        reactor.connected = not reactor.connected
        if reactor.connected then
            nxt.SoundTone(2000)
            reactor.framing:ConnectionMade()
        else
            nxt.SoundTone(500)
            reactor.framing:ConnectionLost()
        end
    end
    self:AddEvent(interval, GetBluetoothConnectionState, DidConnectionStateChange, HandleStateChange)
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
                   callback=callback,
                   id=nxt.random() + nxt.random()}
    self:InsertEventAndResortEvents(event)
    return event.id
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

function Reactor:Run()
    local data
    local current_event
    self.running = true
    while (self.running) do
        local data = nxt.BtStreamRecv()
        if ((data ~= nil) and (#data > 0)) then
            self.framing:DataReceived(data)
        end
        repeat
            local current_event = self:ConditionalPopEvent()
            if (current_event ~= nil) then
                self:HandleEvent(current_event)
            end
            collectgarbage()
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
    if (event.predicate(self, datum)) then
        if (event.callback(self, event.id, datum) ~= false) then
            self:ResumeEvent(event)
        end
    else
        self:ResumeEvent(event)
    end
end
