Framer = {
    STATES = {DATA=0, LENGTH=1},
    buffer = "",
    length = nil,
    state = nil
}

function Framer:New(UpperCallback, TransportCallback)
    local instance = {upper = UpperCallback, lower=TransportCallback}
    setmetatable(instance, self)
    self.__index = self
    instance.state = Framer.STATES.LENGTH
    return instance
end

function Framer:ConnectionMade()
    self:SendFrame('pyblua-1')
end

function Framer:ConnectionLost()
    self.state = Framer.STATES.LENGTH
    self.buffer = ""
    self.length = nil
end

function Framer:DataReceived(data)
    self.unprocessed = data
    while (self.unprocessed ~= "") do
        self.buffer = self.buffer .. self.unprocessed
        self.unprocessed = ""
        if self.state == Framer.STATES.DATA then
            self:DoData()
        elseif self.state == Framer.STATES.LENGTH then
            self:DoLength()
        else
            error("Framer reached unknown state")
        end
    end
end

function Framer:DoLength()
    if (#self.buffer >= 4) then
        self.length = tonumber(string.sub(self.buffer, 1, 4), 16)
        self.state = Framer.STATES.DATA
        self.unprocessed = string.sub(self.buffer, 5)
        self.buffer = ""
    end
end

function Framer:DoData()
    if (#self.buffer >= self.length) then
        local frame = string.sub(self.buffer, 1, self.length)
        self.unprocessed = string.sub(self.buffer, self.length + 1)
        self.buffer = ""
        self.length = nil
        self.state = Framer.STATES.LENGTH
        return self.upper(frame)
    end
end

function Framer:SendFrame(payload)
    if (#payload > (2^16-4)) then
        error(string.format('bad msg len: %d > 2^16', #payload))
    end
    return nxt.BtStreamSend(0, string.format('%04x%s', #payload, payload))
end
