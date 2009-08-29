Protocol = {
    OPCODES = {INCOMING = {ADD = "A", REMOVE = "R", EVAL = "E", HEARTBEAT='H'},
               OUTGOING = {ACK = "A", NAK="N", BAD="B", ASYNC = "X", INITIALIZE='I'}
    },
}

function Protocol:New(reactor)
    local instance = {reactor = reactor}
    setmetatable(instance, self)
    self.__index = self
    return instance
end

function Protocol:StringReceived(data)
    local opcode, payload = string.sub(data, 1, 1), string.sub(data, 2)
    status, err = pcall(self:ResolveOpcode(opcode), self, payload)
    if not status then
        self:BadOperation(data, err)
    end
end

function Protocol:ConnectionMade()
    self.reactor.framing:SendString(self.OPCODES.OUTGOING.INITIALIZE..'pybLua-1')
end

function Protocol:ResolveOpcode(opcode)
    if opcode == self.OPCODES.INCOMING.ADD then
        return self.Add
    elseif opcode == self.OPCODES.INCOMING.REMOVE then
        return self.Remove
    elseif opcode == self.OPCODES.INCOMING.EVAL then
        return self.Evaluate
    elseif opcode == self.OPCODES.INCOMING.HEARTBEAT then
        return self.Heartbeat
    else
        return self.UnknownOpcode
    end
end

function Protocol:Add(string)
    -- TODO: implementation
    self:ACK()
end

function Protocol:Remove(string)
    -- TODO: implementation
    self:ACK()
end

function Protocol:Heartbeat(string)
    local kilobytes, bytes = collectgarbage("count")
    self:ACK(string.format("%s", (kilobytes*1024)+bytes))
end

function Protocol:Evaluate(string)
    func, err = loadstring(string)
    if func == nil then
        print('pyblua-load-failure', err)
        self:NAK('load-failure')
    else
        self:ACK(func(reactor))
    end
end

function Protocol:UnknownOpcode(string)
    print("pyblua-unknown", string)
    self:NAK('unknown-opcode:'..string)
end

function Protocol:BadOperation(data, err)
    print("pyblua-bad", data, err)
    self:BAD()
end

function Protocol:Reply(code, message)
    if message == nil then
        self.reactor.framing:SendString(code)
    else
        self.reactor.framing:SendString(code..message)
    end
end

function Protocol:ACK(message)
    self:Reply(self.OPCODES.OUTGOING.ACK, message)
end
function Protocol:NAK(message)
    self:Reply(self.OPCODES.OUTGOING.NAK, message)
end
function Protocol:BAD(message)
    self:Reply(self.OPCODES.OUTGOING.BAD, message)
end
function Protocol:ASYNC(message)
    self:Reply(self.OPCODES.OUTGOING.ASYNC, message)
end
