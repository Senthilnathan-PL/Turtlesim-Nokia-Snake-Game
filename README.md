# Turtlesim Nokia Snake Game

Remember the Nokia snake game? I rebuilt it inside ROS 2.

Instead of a pixelated snake on a phone screen, there's a turtle in a turtlesim window that hunts down food turtles, eats them, and keeps going. It's autonomous — you just launch it and watch. The whole thing runs on standard ROS 2 communication: topics, services, and a couple of custom messages.

---

## What's actually going on

Two nodes, each with a clear job:

**TurtleBreeder** keeps the world stocked with food. It spawns turtles at random positions, tracks where they all are, and makes sure there are always at least 6 of them alive. When one gets eaten, it spawns a replacement.

**TurtleEater** is the hunter. It reads all the food positions, picks the closest one, and drives straight at it using a proportional controller. When it gets close enough, it calls the `/kill` service and that turtle disappears.

That's it. Two nodes, one pub/sub channel between them, and it looks surprisingly like the game you remember.

---

## Running it

The easiest way — one command starts everything:

```bash
ros2 launch turtle_eater_bringup turtle_eater_app.launch.xml
```

This brings up `turtlesim_node`, `turtle_breeder`, and `turtle_eater` all at once.

Or manually, if you prefer:

```bash
# Terminal 1
ros2 run turtlesim turtlesim_node

# Terminal 2
ros2 run turtle_eater turtle_breeder

# Terminal 3
ros2 run turtle_eater turtle_eater
```

---

## How the nodes talk to each other

```
TurtleBreeder
├── calls  /spawn          → creates food turtles
├── reads  /{food_n}/pose  → tracks each one dynamically
└── sends  /food           → PoseArray of all active food

TurtleEater
├── reads  /food           → where's the food?
├── reads  /turtle1/pose   → where am I?
├── sends  /turtle1/cmd_vel → move!
└── calls  /kill           → eat the food
```

One thing worth noting: TurtleBreeder detects which turtles are still alive by checking for active `/cmd_vel` topics rather than `/pose`. The reason — `/pose` keeps publishing even after a turtle is killed. It's a small detail but it matters.

---

## The control logic

The eater uses a simple proportional controller. Nothing fancy, but it works smoothly:

```
distance_error = sqrt((Xg - Xc)² + (Yg - Yc)²)
angle_error    = atan2(Yg - Yc, Xg - Xc) - current_heading

linear.x  = k * distance_error
angular.z = k * angle_error
```

The turtle turns and moves at the same time, which gives it that slightly organic-looking path rather than rotating in place first.

---

## Project structure

```
turtle_eater/
turtle_eater_bringup/
    └── launch/
        └── turtle_eater_app.launch.xml
my_msg_interfaces/
    └── msg/
        ├── PoseName.msg    ← x, y, theta, name
        └── PoseArray.msg   ← list of PoseName
```

The custom messages exist because the standard `Pose` type doesn't include the turtle's name — and the eater needs to know which turtle to kill.

---

## Requirements

- ROS 2 (Humble or Jazzy)
- `turtlesim`
- Python 3
- `my_msg_interfaces` (the custom message package in this repo)

---

## Where I'd take this next

- Self-collision so there's an actual game-over condition
- Speed that increases as food gets eaten
- Random obstacles
- A scoring overlay
- An autonomous mode using proper path planning

---

## What this is really about

It started as a way to make ROS 2 concepts concrete. Publishers, subscribers, services, custom messages, launch files — they're all here, doing real work. If you're learning ROS 2 and want to see how these pieces fit together in something that actually moves, this is a decent place to start.

---

Built by **Senthilnathan PL**

If it was useful, a star goes a long way.
