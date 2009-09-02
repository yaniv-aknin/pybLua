Protocol = {
    OPCODES = {INCOMING = {EVAL = "E", HEARTBEAT='H'},
               OUTGOING = {ACK = "A", NAK="N", ERROR="E", ASYNC = "X", INITIALIZE='I'}
    },
}

function Protocol:New(reactor)
    local instance = {reactor = reactor}
    setmetatable(instance, self)
    self.__index = self
    return instance
end

function Protocol:StringReceived(data)
    self:ResolveOpcode(string.sub(data, 1, 1))(self, string.sub(data, 2))
end

function Protocol:ConnectionMade()
    self.reactor.framing:SendString(self.OPCODES.OUTGOING.INITIALIZE..'pybLua-1')
end

function Protocol:ResolveOpcode(opcode)
    if opcode == self.OPCODES.INCOMING.EVAL then
        return self.Evaluate
    elseif opcode == self.OPCODES.INCOMING.HEARTBEAT then
        return self.Heartbeat
    else
        return self.UnknownOpcode
    end
end

function Protocol:Heartbeat(string)
    local kilobytes, bytes = collectgarbage("count")
    self:ACK(string.format("%s", (kilobytes*1024)+bytes))
end

function Protocol:Evaluate(string)
    local func, err = loadstring(string)
    if func == nil then
        return self:ERROR('load: '..err)
    end

    success, result, ack = pcall(func, reactor)
    if success == false then
        return self:ERROR('error: '..result)
    end
    if ack == false then
        return self:NAK(result)
    end
    self:ACK(result)
end

function Protocol:UnknownOpcode(string)
    print("pyblua-unknown", string)
    self:NAK('unknown-opcode:'..string)
end

function Protocol:ERROR(data, err)
    print("pyblua-error", data, err)
    self:ERROR()
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
function Protocol:ERROR(message)
    self:Reply(self.OPCODES.OUTGOING.ERROR, message)
end
function Protocol:ASYNC(message)
    self:Reply(self.OPCODES.OUTGOING.ASYNC, message)
end
