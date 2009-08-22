IO = {}

function IO:read()
    return nxt.BtStreamRecv()
end

function IO:write(data, connection)
    connection = connection or 0
    return nxt.BtStreamSend(0, data)
end

function IO:initialize()
    return nxt.BtStreamMode(1)
end
