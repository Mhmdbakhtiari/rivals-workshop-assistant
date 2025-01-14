local sprite = app.open(app.params["filename"])

local startFrame = tonumber(app.params["startFrame"])
local endFrame = tonumber(app.params["endFrame"])
local scale = 2

-- Hurtmask layer is subtracted from the hurtbox
local hurtmaskLayer = nil

-- Hurtbox layer, if present, is used as the initial hurtbox
--  (rather than the sprite's silhouette)
local hurtboxLayer = nil

-- All the actual content of the sprite, not special purpose utility layers.
local contentLayers = {}
for _, layer in ipairs(sprite.layers) do
    if layer.name == "HURTMASK" then
        hurtmaskLayer = layer
    elseif layer.name == "HURTBOX" then
        hurtboxLayer = layer
    else
        if layer.isVisible then
            table.insert(contentLayers, layer)
        else
            app.range.layers = { layer }
            app.command.removeLayer()
        end
    end
end

-- Deletes frames that aren't in the given range.
local _irrelevantFrames = {}
local _workingFrames = {}
for frameIndex, frame in ipairs(sprite.frames) do
    if startFrame <= frameIndex  and frameIndex <= endFrame then
        table.insert(_workingFrames, frame)
    else
        table.insert(_irrelevantFrames, frame)
    end
end
if #_irrelevantFrames > 0 then
    app.range.frames = _irrelevantFrames
    app.command.RemoveFrame()
end

local function isNonTransparent(pixel)
    return pixel() > 0
end

local function selectContent(layer, frameNumber)
    local cel = layer:cel(frameNumber)
    if cel == nil then
        return Selection()
    end

    local points = {}
    for pixel in cel.image:pixels() do
        if isNonTransparent(pixel) then
            table.insert(points, Point(pixel.x + cel.position.x, pixel.y + cel.position.y))
        end
    end

    local select = Selection()
    for _, point in ipairs(points) do
        local pixelRect = Rectangle(point.x, point.y, 1, 1)
        select:add(Selection(pixelRect))
    end
    return select
end


local function convertLayerToSelections(layer)
    selections = {}
    if layer ~= nil then
        for _, frame in ipairs(sprite.frames) do
            local selection = selectContent(layer, frame)
            table.insert(selections, selection)
        end
        app.range.layers = { layer }
        app.command.removeLayer()
    end
    return selections
end

app.activeSprite = sprite

hurtmaskSelections = convertLayerToSelections(hurtmaskLayer)
hurtboxSelections = convertLayerToSelections(hurtboxLayer)

-- Flatten content_layers.
app.range.layers = contentLayers
app.command.FlattenLayers {
    visibleOnly = True
}

-- Get content_layer
local contentLayer = nil
for _, layer in ipairs(sprite.layers) do
    if layer.name == "Flattened" then
        contentLayer = layer
    end
end
assert(contentLayer ~= nil, "no layer called Flattened")

 --If hurtboxSelections exists, replace the content with the selections.
app.activeLayer = contentLayer
for i, hurtboxSelection in ipairs(hurtboxSelections) do
    app.activeFrame = sprite.frames[i]
    app.range.frames = {sprite.frames[i]}

    -- Delete the image
    app.command.ReplaceColor {
        ui=false,
        to=Color{ r=0, g=0, b=0, a=0},
        tolerance=255
    }
    app.command.DeselectMask()

    -- Fill the selection
    sprite.selection = hurtboxSelection
    app.fgColor = Color{ r=255, g=255, b=255, a=255 }
    app.command.Fill()

    app.command.DeselectMask()
end


-- Delete hurtmaskSelections from content layer
app.activeLayer = contentLayer
for i, hurtmaskSelection in ipairs(hurtmaskSelections) do
    app.activeFrame = sprite.frames[i]
    app.range.frames = {sprite.frames[i]}
    sprite.selection = hurtmaskSelection

    app.command.ReplaceColor {
        ui=false,
        to=Color{ r=0, g=0, b=0, a=0 },
        tolerance=255
    }
    app.command.DeselectMask()
end

-- Color the content layer green.
app.activeLayer = contentLayer
for _, frame in ipairs(sprite.frames) do
    app.activeFrame = frame
    app.range.frames = {frame}
    sprite.selection = selectContent(contentLayer, frame)
    app.command.ReplaceColor {
        ui=false,
        to=Color{ r=0, g=255, b=0, a=255 },
        tolerance=255
    }
    app.command.DeselectMask()
end

app.command.SpriteSize {
    scale=scale
}

app.command.ExportSpriteSheet {
    ui=false,
    askOverwrite=false,
    type=SpriteSheetType.HORIZONTAL,
    textureFilename=app.params["dest"],
}
