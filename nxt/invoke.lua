function LoaderExecute()
    r = nil
    collectgarbage()
    r = Reactor:New()
    r:Run()
end
