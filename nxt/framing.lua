Framer = {
    STATES = {DATA=0, LENGTH=1},
    buffer = "",
    length = nil,
    state = nil
}

function Framer:New(protocol)
    local instance = {protocol = protocol}
    setmetatable(instance, self)
    self.__index = self
    instance.state = Framer.STATES.LENGTH
    return instance
end

function Framer:ConnectionMade()
    self.protocol:ConnectionMade()
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
    if (#self.buffer >= 2) then
        local high, low = string.sub(self.buffer, 1, 1), string.sub(self.buffer, 2, 2)
        self.length = nxt.blshift(string.byte(high), 8) + string.byte(low)
        self.unprocessed = string.sub(self.buffer, 3)
        self.state = Framer.STATES.DATA
        self.buffer = ""
    end
end

function Framer:DoData()
    if (#self.buffer >= self.length) then
        local data = string.sub(self.buffer, 1, self.length)
        self.unprocessed = string.sub(self.buffer, self.length + 1)
        self.buffer = ""
        self.length = nil
        self.state = Framer.STATES.LENGTH
        return self.protocol:StringReceived(data)
    end
end

function Framer:SendString(payload)
    if (#payload >= (2^16)) then
        error(string.format('bad msg len: %d >= 2^16', #payload))
    end
    local high_length, low_length = nxt.brshift(#payload, 8), nxt.band(#payload, 255)
    return nxt.BtStreamSend(0, string.char(high_length)..string.char(low_length)..payload)
end
