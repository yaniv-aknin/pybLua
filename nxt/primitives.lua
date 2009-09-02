primitives = {
    find = function (array, predicate)
        for index, value in ipairs(array) do
            if predicate(value) then
                return index
            end
        end
    end
}

