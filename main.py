from math import pi, sin, cos
from direct.showbase.ShowBase import ShowBase
from direct.gui.OnscreenImage import OnscreenImage
from panda3d.core import loadPrcFile
from panda3d.core import DirectionalLight, AmbientLight
from panda3d.core import CollisionTraverser, CollisionNode, CollisionBox, CollisionRay, CollisionHandlerQueue
from panda3d.core import TransparencyAttrib
from panda3d.core import WindowProperties

# left at 1:04:16

loadPrcFile("settings.prc")

def degToRad(degrees):
  return degrees * (pi / 180.0)

class Game(ShowBase):
  def __init__(self):
    ShowBase.__init__(self)

    self.load_models()
    self.generate_terrain()
    self.setup_lights()
    self.setup_camera()
    self.setup_skybox()
    self.setup_controls()
    self.capture_mouse()

    taskMgr.add(self.update, "update")
  
  def update(self, task):
    # update camera position based on mouse movement
    dt = globalClock.getDt()

    # player speed
    playerMoveSpeed = 10

    # movement controls
    x_movement = 0
    y_movement = 0
    z_movement = 0

    # check key presses and change position
    if self.key_map["forward"]:
      x_movement -= dt * playerMoveSpeed * sin(degToRad(camera.getH()))
      y_movement += dt * playerMoveSpeed * cos(degToRad(camera.getH()))
    if self.key_map["backward"]:
      x_movement +=  dt * playerMoveSpeed * sin(degToRad(camera.getH()))
      y_movement -=  dt * playerMoveSpeed * cos(degToRad(camera.getH()))
    if self.key_map["left"]:
      x_movement -= dt * playerMoveSpeed * cos(degToRad(camera.getH()))
      y_movement -= dt * playerMoveSpeed * sin(degToRad(camera.getH()))
    if self.key_map["right"]:
      x_movement += dt * playerMoveSpeed * cos(degToRad(camera.getH()))
      y_movement += dt * playerMoveSpeed * sin(degToRad(camera.getH()))
    if self.key_map["up"]:
      z_movement += dt * playerMoveSpeed
    if self.key_map["down"]:
      z_movement -= dt * playerMoveSpeed

    # adjust camera position after movement
    self.camera.setPos(
        camera.getX() + x_movement,
        camera.getY() + y_movement,
        camera.getZ() + z_movement
        )

    # run only if mouse is captured
    if self.cameraSwingActivated:
    # get current mouse position
      md = self.win.getPointer(0)
      mouse_x = md.getX()
      mouse_y = md.getY()
  
      # getting the mouse movement changes by subtracting the last mouse position from the current one
      mouse_change_x = mouse_x - self.last_mouse_x
      mouse_change_y = mouse_y - self.last_mouse_y
  
      # getting the values for the new Hpr in setHpr for the camera
      current_h = self.camera.getH() # used in setHpr
      current_p = self.camera.getP() # used in setHpr
      self.cameraSwingFactor = 10 # how fast the camera moves
  
      self.camera.setHpr(
          current_h - mouse_change_x * dt * self.cameraSwingFactor,
          min(90, max(-90, current_p - mouse_change_y * dt * self.cameraSwingFactor)),
          0
          )
  
      self.last_mouse_x = mouse_x
      self.last_mouse_y = mouse_y

    return task.cont

  def setup_controls(self):
    # setup keymap
    self.key_map = {
        "forward": False,
        "backward": False,
        "left": False,
        "right": False,
        "up": False,
        "down": False
        }

    # listen for the following key presses to call a corresponding function
    # for mouse control 
    self.accept("escape", self.release_mouse)
    self.accept("mouse1", self.capture_mouse)

    # movement controls
    self.accept("w", self.update_keymap, ["forward", True]) # extra args are a third argument passed as a list
    self.accept("s", self.update_keymap, ["backward", True])
    self.accept("a", self.update_keymap, ["left", True])
    self.accept("d", self.update_keymap, ["right", True])
    self.accept("w-up", self.update_keymap, ["forward", False]) 
    self.accept("s-up", self.update_keymap, ["backward", False])
    self.accept("a-up", self.update_keymap, ["left", False]) 
    self.accept("d-up", self.update_keymap, ["right", False])
    self.accept("space", self.update_keymap, ["up", True])
    self.accept("space-up", self.update_keymap, ["up", False])
    self.accept("lshift", self.update_keymap, ["down", True])
    self.accept("lshift-up", self.update_keymap, ["down", False])

  def update_keymap(self, key, value):
    self.key_map[key] = value

  def capture_mouse(self):
    # lock mouse in the window

    # set mouse as captured
    self.cameraSwingActivated = True

    # capture mouse position
    md = self.win.getPointer(0)
    self.last_mouse_x = md.getX()
    self.last_mouse_y = md.getY()

    # set mouse properties so it becomes invisible
    properties = WindowProperties()
    properties.setCursorHidden(True)
    properties.setMouseMode(WindowProperties.M_relative)
    self.win.requestProperties(properties)

  def release_mouse(self):
    # release the mouse so it can move outside the window

    # set mouse as released
    self.cameraSwingActivated = False

    properties = WindowProperties()
    properties.setCursorHidden(False)
    properties.setMouseMode(WindowProperties.M_absolute)
    self.win.requestProperties(properties)

  def setup_skybox(self):
    # works on wsl2, should work on linux, should check if it works in windows
    skybox = loader.loadModel("skybox/skybox.egg")
    skybox.setScale(500)
    skybox.setBin("background", 1)
    skybox.setDepthWrite(0)
    skybox.setLightOff()
    skybox.reparentTo(render)

  def setup_camera(self):
    # disable default camera movement and add crosshairs
    self.disableMouse() # disable panda3d mouse control => lets us program our own camera controls
    self.camera.setPos(0, 0, 3) # set camera position to the top of the platflorm

    crosshairs = OnscreenImage(
        image= "crosshairs.png",
        pos= (0, 0, 0),
        scale= .05
        )
    crosshairs.setTransparency(TransparencyAttrib.MAlpha)

  def generate_terrain(self):
    # generates a 20x20x10 block platform
    for z in range(10):
      for y in range(20):
        for x in range(20):
          new_block_node = render.attachNewNode("new-block-placeholder")
          new_block_node.setPos(
              x * 2 - 20,
              y * 2 - 20,
              -z * 2
              )
          if z == 0:
            self.grass_block.instanceTo(new_block_node)
          else:
            self.dirt_block.instanceTo(new_block_node)

  def load_models(self):
    # load models, since the loading is computationally expensive we want to do it only once
    self.grass_block = loader.loadModel("grass-block.glb")
    self.dirt_block = loader.loadModel("dirt-block.glb")
    self.stone_block = loader.loadModel("stone-block.glb")
    self.sand_block = loader.loadModel("sand-block.glb")

  def setup_lights(self):
    # load directional light
    main_light = DirectionalLight("main light")
    main_light_node_path = render.attachNewNode(main_light)
    main_light_node_path.setHpr(30, -60, 0) # set so it comes from the top
    render.setLight(main_light_node_path)

    # load ambient light
    ambient_light = AmbientLight("ambient light")
    ambient_light.setColor((.3, .3, .3, 1)) # (R, G, B, Alpha) => (red, green, blue, transparency)
    ambient_light_node_path = render.attachNewNode(ambient_light)
    render.setLight(ambient_light_node_path)

app = Game()
app.run()
